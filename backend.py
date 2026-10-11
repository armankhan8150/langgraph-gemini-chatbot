"""LangGraph backend: Gemini chat graph, SQLite persistence and thread metadata."""

import logging
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Configuration (override through environment variables)
# ---------------------------------------------------------
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
DB_PATH = os.getenv("CHATBOT_DB_PATH", "chatbot.db")
TITLE_MAX_LENGTH = 40

llm = ChatGoogleGenerativeAI(model=MODEL_NAME)


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState) -> dict:
    """Call Gemini with the conversation so far and return its reply."""
    try:
        response = llm.invoke(state["messages"])
    except Exception:  # noqa: BLE001 - show a friendly message instead of crashing
        logger.exception("Gemini request failed")
        response = AIMessage(
            content="⚠️ Sorry, I couldn't get a response from the model. "
            "Please check your API key / connection and try again."
        )
    # Return the real AIMessage so it is stored with the correct role.
    return {"messages": [response]}


conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

_graph = StateGraph(ChatState)
_graph.add_node("chat_node", chat_node)
_graph.add_edge(START, "chat_node")
_graph.add_edge("chat_node", END)

chatbot = _graph.compile(checkpointer=checkpointer)


# ---------------------------------------------------------
# Thread metadata (titles + ordering)
# ---------------------------------------------------------
_meta_lock = threading.Lock()
_meta_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_meta_conn.execute(
    """
    CREATE TABLE IF NOT EXISTS thread_meta (
        thread_id  TEXT PRIMARY KEY,
        title      TEXT NOT NULL,
        updated_at REAL NOT NULL
    )
    """
)
_meta_conn.commit()


def _make_title(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= TITLE_MAX_LENGTH:
        return text or "New chat"
    return text[: TITLE_MAX_LENGTH - 1] + "…"


def touch_thread(thread_id: str, first_message: str) -> None:
    """Create the thread entry (titled from the first message) or bump its timestamp."""
    with _meta_lock:
        _meta_conn.execute(
            """
            INSERT INTO thread_meta (thread_id, title, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (thread_id, _make_title(first_message), time.time()),
        )
        _meta_conn.commit()


def _backfill_missing_threads() -> None:
    """Register threads that exist in checkpoints but not in thread_meta."""
    latest_ts: dict[str, float] = {}
    for item in checkpointer.list(None):  # newest checkpoints first
        tid = item.config["configurable"]["thread_id"]
        if tid in latest_ts:
            continue
        ts = item.checkpoint.get("ts")
        try:
            latest_ts[tid] = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except (AttributeError, ValueError):
            latest_ts[tid] = time.time()

    with _meta_lock:
        known = {r[0] for r in _meta_conn.execute("SELECT thread_id FROM thread_meta")}

    for tid, ts in latest_ts.items():
        if tid in known:
            continue
        state = chatbot.get_state({"configurable": {"thread_id": tid}})
        first_human = next(
            (m for m in state.values.get("messages", []) if isinstance(m, HumanMessage)),
            None,
        )
        title = _make_title(first_human.content) if first_human and isinstance(first_human.content, str) else "Untitled chat"
        with _meta_lock:
            _meta_conn.execute(
                "INSERT OR IGNORE INTO thread_meta VALUES (?, ?, ?)", (tid, title, ts)
            )
            _meta_conn.commit()


def retrieve_all_threads() -> list[dict]:
    """Return all conversations as {'thread_id', 'title'}, newest first."""
    _backfill_missing_threads()
    with _meta_lock:
        rows = _meta_conn.execute(
            "SELECT thread_id, title FROM thread_meta ORDER BY updated_at DESC"
        ).fetchall()
    return [{"thread_id": r[0], "title": r[1]} for r in rows]


def delete_thread(thread_id: str) -> None:
    """Delete a conversation and its saved checkpoints."""
    checkpointer.delete_thread(thread_id)
    with _meta_lock:
        _meta_conn.execute("DELETE FROM thread_meta WHERE thread_id = ?", (thread_id,))
        _meta_conn.commit()