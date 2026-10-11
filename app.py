
"""Modern Streamlit frontend for the LangGraph + Gemini chatbot."""

import uuid

import streamlit as st
from langchain_core.messages import AIMessageChunk, HumanMessage

from backend import chatbot, delete_thread, retrieve_all_threads, touch_thread
from utils import extract_text, get_display_role


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Gemini AI | Chat Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# COMPLETE CUSTOM CSS
# =========================================================
st.markdown(
    """
    <style>

    /* GLOBAL THEME */

    :root {
        color-scheme: dark;
        --app-bg: #0b0d16;
        --sidebar-bg: #10121e;
        --surface: #171a29;
        --border: #292c42;
        --accent: #9d87ff;
        --text: #ececf6;
        --muted: #9295b1;
    }

    .stApp {
        background: var(--app-bg) !important;
        color: var(--text) !important;
    }

    html, body {
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    #MainMenu,
    footer,
    header[data-testid="stHeader"] {
        visibility: hidden;
    }

    .block-container {
        max-width: 960px;
        padding-top: 1.5rem;
        padding-bottom: 7rem;
    }


    /* ===========================================
       BOTTOM INPUT CONTAINER
    =========================================== */

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInputContainer"] {
        background: #0b0d16 !important;
        background-color: #0b0d16 !important;
    }

    [data-testid="stBottomBlockContainer"] {
        max-width: 960px;
        margin: 0 auto;
        padding: 12px 20px 18px;
    }

    [data-testid="stBottom"]::before,
    [data-testid="stBottom"]::after {
        background: transparent !important;
        box-shadow: none !important;
    }


    /* ===========================================
       CHAT INPUT - TEXT VISIBILITY FIX
    =========================================== */

    [data-testid="stChatInput"] {
        background: #1a1c2d !important;
        background-color: #1a1c2d !important;
        border: 1px solid #393c56 !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 30px #00000022 !important;
        overflow: hidden;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #9d87ff !important;
        box-shadow: 0 0 0 2px #9d87ff22 !important;
    }

    /* Make typed text visible */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:active,
    [data-testid="stChatInput"] [contenteditable="true"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: transparent !important;
        background-color: transparent !important;
        caret-color: #ffffff !important;
        opacity: 1 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    /* Placeholder */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #a1a5bf !important;
        -webkit-text-fill-color: #a1a5bf !important;
        opacity: 1 !important;
    }

    /* Send button */
    [data-testid="stChatInput"] button {
        color: #b4a3ff !important;
    }

    [data-testid="stChatInput"] button:hover {
        color: #ffffff !important;
    }

    [data-testid="stChatInput"] button:disabled {
        color: #777b98 !important;
    }


    /* ===========================================
       SIDEBAR
    =========================================== */

    section[data-testid="stSidebar"] {
        background: #10121e !important;
        border-right: 1px solid #25283b;
    }

    section[data-testid="stSidebar"] > div {
        background: #10121e !important;
    }

    section[data-testid="stSidebar"]
    [data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 2px 20px;
    }

    .brand-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 43px;
        height: 43px;
        flex-shrink: 0;
        background: linear-gradient(135deg, #966cf1, #5865e9);
        color: white;
        border-radius: 13px;
        font-size: 25px;
        font-weight: 700;
        box-shadow: 0 5px 20px #7956ea25;
    }

    .brand-title {
        color: #f4f2ff;
        font-size: 19px;
        font-weight: 750;
        letter-spacing: -0.5px;
    }

    .brand-subtitle {
        color: #8389a9;
        font-size: 10px;
        letter-spacing: 0.7px;
        margin-top: 3px;
    }

    .sidebar-section {
        color: #858ba9;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.4px;
        margin: 19px 0 12px 3px;
    }


    /* ===========================================
       BUTTONS
    =========================================== */

    .stButton > button {
        background: #191c2b;
        color: #cbd0e7;
        border: 1px solid #292d43;
        border-radius: 10px;
        min-height: 41px;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #272a40;
        color: #ffffff;
        border-color: #7163b7;
    }

    .stButton > button:focus {
        color: #ffffff;
        border-color: #8d74ed;
    }

    .stButton > button:disabled {
        background: #171927;
        color: #686e8a;
        opacity: 0.75;
        border-color: #222539;
    }

    /* New conversation button */

    section[data-testid="stSidebar"]
    button[kind="primary"] {
        background: linear-gradient(110deg, #7958e8, #5969e8);
        border: none;
        border-radius: 11px;
        min-height: 46px;
        color: white;
        font-size: 13px;
        font-weight: 650;
    }

    section[data-testid="stSidebar"]
    button[kind="primary"]:hover {
        background: linear-gradient(110deg, #8c6cf4, #6878f4);
        color: white;
        border: none;
        box-shadow: 0 4px 18px #715de533;
    }

    /* Conversation list */

    section[data-testid="stSidebar"]
    div[data-testid="stHorizontalBlock"] {
        gap: 5px;
        align-items: center;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stHorizontalBlock"] button {
        text-align: left;
        padding-left: 11px;
        padding-right: 8px;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stHorizontalBlock"] button p {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }


    /* ===========================================
       SIDEBAR INFO PANEL
    =========================================== */

    .sidebar-info {
        background: #191c2c;
        border: 1px solid #292d44;
        border-radius: 12px;
        padding: 14px;
        margin-top: 10px;
    }

    .sidebar-info-title {
        color: #e7e4ff;
        font-size: 12px;
        font-weight: 650;
        margin-bottom: 7px;
    }

    .sidebar-info-text {
        color: #858aa9;
        font-size: 11px;
        line-height: 1.7;
    }


    /* ===========================================
       CHAT HEADER
    =========================================== */

    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
        padding: 8px 0 20px;
        border-bottom: 1px solid #26293b;
        margin-bottom: 24px;
    }

    .chat-heading {
        color: #f0effb;
        font-size: 20px;
        font-weight: 750;
        letter-spacing: -0.6px;
    }

    .chat-heading span {
        color: #a995ff;
    }

    .chat-subheading {
        color: #858aa9;
        font-size: 12px;
        margin-top: 5px;
    }

    .model-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #1a1c30;
        border: 1px solid #343650;
        border-radius: 30px;
        color: #b6a8ff;
        padding: 8px 13px;
        font-size: 11px;
        font-weight: 650;
        white-space: nowrap;
    }

    .online-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #42d6a0;
    }


    /* ===========================================
       WELCOME SCREEN
    =========================================== */

    .welcome-area {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        text-align: center;
        min-height: 48vh;
        padding: 24px 12px 35px;
    }

    .welcome-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ac94ff;
        font-size: 45px;
        margin-bottom: 23px;
        text-shadow: 0 0 35px #7959e955;
    }

    .welcome-title {
        color: #f3f1ff;
        font-size: clamp(25px, 3.5vw, 36px);
        font-weight: 760;
        letter-spacing: -1.2px;
        line-height: 1.3;
        margin-bottom: 15px;
    }

    .welcome-title span {
        background: linear-gradient(95deg, #baa4ff, #8399ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .welcome-description {
        color: #9296b3;
        font-size: 14px;
        line-height: 1.9;
        max-width: 470px;
    }


    /* ===========================================
       CHAT MESSAGE STYLING
    =========================================== */

    div[data-testid="stChatMessage"] {
        background: #161927;
        border: 1px solid #292c40;
        border-radius: 15px;
        padding: 16px 18px;
        margin-bottom: 13px;
    }

    div[data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
    ) {
        background: #202038;
        border-color: #393657;
    }

    div[data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarAssistant"]
    ) {
        background: #161927;
        border-color: #292c40;
    }

    div[data-testid="stChatMessage"] p {
        color: #e3e4f1;
        font-size: 14px;
        line-height: 1.8;
    }

    div[data-testid="stChatMessage"] ul,
    div[data-testid="stChatMessage"] ol {
        line-height: 1.8;
    }

    div[data-testid="stChatMessage"] pre {
        background: #0d101b;
        border: 1px solid #30334a;
        border-radius: 11px;
    }

    div[data-testid="stChatMessage"] code {
        font-size: 12px;
    }

    div[data-testid="stChatMessage"]
    [data-testid="stChatMessageAvatarUser"] {
        background: #333050;
        border-radius: 10px;
    }

    div[data-testid="stChatMessage"]
    [data-testid="stChatMessageAvatarAssistant"] {
        background: #30274d;
        color: #b49dff;
        border-radius: 10px;
    }


    /* ===========================================
       SCROLLBARS AND DIVIDERS
    =========================================== */

    hr {
        border-color: #282b40 !important;
    }

    ::-webkit-scrollbar {
        width: 7px;
        height: 7px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: #393b50;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #61617c;
    }


    /* ===========================================
       MOBILE RESPONSIVENESS
    =========================================== */

    @media (max-width: 768px) {

        .block-container {
            padding-top: 0.8rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .welcome-area {
            min-height: 42vh;
            padding: 25px 8px;
        }

        .welcome-title {
            font-size: 27px;
        }

        .welcome-description {
            font-size: 13px;
        }

        .chat-header {
            gap: 8px;
        }

        .chat-heading {
            font-size: 18px;
        }

        .model-pill {
            font-size: 10px;
            padding: 7px 10px;
        }

        div[data-testid="stChatMessage"] {
            padding: 13px 12px;
        }

        [data-testid="stBottomBlockContainer"] {
            padding-left: 12px;
            padding-right: 12px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS - ORIGINAL FUNCTIONALITY
# =========================================================
def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def load_conversation(thread_id: str) -> list[dict]:
    """Load a saved thread as a list of role/content dictionaries."""

    state = chatbot.get_state(_config(thread_id))
    history = []

    for msg in state.values.get("messages", []):
        role = get_display_role(msg)

        if role is not None:
            history.append(
                {
                    "role": role,
                    "content": extract_text(msg.content),
                }
            )

    return history


def start_new_chat() -> None:
    st.session_state["thread_id"] = str(uuid.uuid4())
    st.session_state["message_history"] = []


def open_thread(thread_id: str) -> None:
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = load_conversation(thread_id)


def stream_reply(user_input: str, thread_id: str):
    """Yield the assistant's text token by token."""

    for chunk, _metadata in chatbot.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=_config(thread_id),
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk):
            text = extract_text(chunk.content)

            if text:
                yield text


# =========================================================
# SESSION STATE
# =========================================================
if "thread_id" not in st.session_state:
    start_new_chat()

threads = retrieve_all_threads()
saved_ids = {t["thread_id"] for t in threads}


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-icon">✦</div>
            <div>
                <div class="brand-title">Gemini AI</div>
                <div class="brand-subtitle">
                    YOUR INTELLIGENT ASSISTANT
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # New conversation
    if st.button(
        "＋ New Conversation",
        key="new_chat_btn",
        type="primary",
        use_container_width=True,
    ):
        start_new_chat()
        st.rerun()

    st.markdown(
        '<div class="sidebar-section">YOUR CONVERSATIONS</div>',
        unsafe_allow_html=True,
    )

    # Unsaved conversation
    if st.session_state["thread_id"] not in saved_ids:
        st.button(
            "✦ New conversation",
            disabled=True,
            use_container_width=True,
        )

    # Previous conversations
    for t in threads:
        tid = t["thread_id"]
        is_current = tid == st.session_state["thread_id"]

        col_open, col_del = st.columns([5, 1], gap="small")

        with col_open:
            label = (
                f"✦ {t['title']}"
                if is_current
                else f"☰ {t['title']}"
            )

            if st.button(
                label,
                key=f"open_{tid}",
                use_container_width=True,
                help="Open conversation",
            ):
                open_thread(tid)
                st.rerun()

        with col_del:
            if st.button(
                "🗑",
                key=f"del_{tid}",
                use_container_width=True,
                help="Delete conversation",
            ):
                delete_thread(tid)

                if is_current:
                    start_new_chat()

                st.rerun()

    st.divider()

    st.markdown(
        """
        <div class="sidebar-info">
            <div class="sidebar-info-title">
                ✧ Powered by LangGraph
            </div>
            <div class="sidebar-info-text">
                Intelligent conversations powered by
                Gemini with persistent chat memory.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CHAT HEADER
# =========================================================
st.markdown(
    """
    <div class="chat-header">
        <div>
            <div class="chat-heading">
                Gemini <span>Assistant</span>
            </div>
            <div class="chat-subheading">
                Your intelligent AI companion
            </div>
        </div>
        <div class="model-pill">
            <span class="online-dot"></span>
            Gemini AI
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# WELCOME SCREEN
# =========================================================
if not st.session_state["message_history"]:

    st.markdown(
        """
        <div class="welcome-area">
            <div class="welcome-logo">✦</div>
            <div class="welcome-title">
                How can I <span>help you today?</span>
            </div>
            <div class="welcome-description">
                Ask anything, explore ideas, solve problems,
                or just have a conversation.
                I'm here to help you get things done.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CHAT HISTORY
# =========================================================
for message in st.session_state["message_history"]:

    avatar = "🧑" if message["role"] == "user" else "🤖"

    with st.chat_message(
        message["role"],
        avatar=avatar,
    ):
        st.markdown(message["content"])


# =========================================================
# CHAT INPUT
# =========================================================
user_input = st.chat_input(
    "Message Gemini..."
)


# =========================================================
# MESSAGE PROCESSING AND STREAMING
# =========================================================
if user_input:

    thread_id = st.session_state["thread_id"]

    # Save user message
    st.session_state["message_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # Register/update thread
    touch_thread(thread_id, user_input)

    # Generate assistant response
    with st.chat_message("assistant", avatar="🤖"):

        try:
            reply = st.write_stream(
                stream_reply(user_input, thread_id)
            )

        except Exception as exc:  # noqa: BLE001
            reply = ""
            st.error(f"Something went wrong: {exc}")

        # Existing fallback
        if not reply:

            saved = load_conversation(thread_id)

            if saved and saved[-1]["role"] == "assistant":
                reply = saved[-1]["content"]
                st.markdown(reply)

    # Save assistant reply
    if reply:

        st.session_state["message_history"].append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        st.rerun()
