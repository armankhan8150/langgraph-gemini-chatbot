"""Small helpers shared by the UI (kept free of Streamlit so they are easy to test)."""

from langchain_core.messages import AIMessage, HumanMessage


def extract_text(content) -> str:
    """Extract plain text from LangChain/Gemini message content.

    Handles plain strings and lists of content blocks (strings or
    ``{"type": "text", "text": ...}`` dicts); everything else is ignored.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif (
                isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ):
                parts.append(block["text"])
        return "".join(parts)

    return ""


def get_display_role(message) -> str | None:
    """Map a LangChain message to a Streamlit chat role (None = don't display)."""
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    return None