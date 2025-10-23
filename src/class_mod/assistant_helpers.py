import logging
from datetime import datetime

from livekit import api
from livekit.agents import AgentSession, get_job_context

logger = logging.getLogger("assistant_helpers")

async def hangup_current_room():
    """Gracefully close the LiveKit room."""
    ctx = get_job_context()
    if not ctx or not ctx.room:
        logger.warning("No active room found. Cannot hang up.")
        return
    try:
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
        logger.info("Room '%s' deleted successfully.", ctx.room.name)
    except Exception as e:
        logger.error("Failed to delete room: %s", e)

def extract_conversation(session: AgentSession, *, max_messages: int = 5000, max_chars: int = 800000) -> str:
    """
    Extract conversation history as a clean, readable text block.

    - Handles history keys: 'items', 'messages', or 'entries'.
    - Flattens content lists/dicts into readable text.
    - Returns up to `max_messages` last messages and truncates to `max_chars`.
    """
    history_dict = session.history.to_dict()
    logger.info("Extracting conversation history from session. : %s", history_dict)

    # support various history shapes
    raw_items = history_dict.get("items") or history_dict.get("messages") or history_dict.get("entries") or []
    # take last N messages to avoid huge prompts
    raw_items = raw_items[-max_messages:]

    def _flatten_content(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for elem in content:
                if isinstance(elem, str):
                    parts.append(elem)
                elif isinstance(elem, dict):
                    # common shapes: {"text": "..."} or {"content": "..."}
                    text = elem.get("text") or elem.get("content") or elem.get("value") or None
                    if text and isinstance(text, str):
                        parts.append(text)
                    else:
                        # fallback to serializing small dicts
                        parts.append(" ".join(str(v) for v in elem.values() if isinstance(v, str)))
                else:
                    parts.append(str(elem))
            return " ".join([p for p in parts if p])
        if isinstance(content, dict):
            return content.get("text") or content.get("content") or " ".join(
                str(v) for v in content.values() if isinstance(v, str)
            )
        return str(content)

    messages = []
    for item in raw_items:
        # make sure we only process messages
        if item.get("type") and item["type"] != "message":
            continue

        role = item.get("role", "unknown")
        content = item.get("content", "")
        content_text = _flatten_content(content).strip()
        if not content_text:
            # sometimes 'transcript' or nested fields are present
            alt = item.get("transcript") or item.get("text") or item.get("message")
            content_text = _flatten_content(alt).strip()
        if not content_text:
            # skip empty messages
            continue

        # optional timestamp formatting
        ts = item.get("timestamp") or item.get("created_at") or item.get("time")
        if ts is not None:
            try:
                # if numeric epoch
                ts_float = float(ts)
                ts_str = datetime.fromtimestamp(ts_float).isoformat()
            except Exception:
                ts_str = str(ts)
            messages.append(f"{role} [{ts_str}]: {content_text}")
        else:
            messages.append(f"{role}: {content_text}")

    result = "\n".join(messages)

    # truncate to max_chars (keep tail which contains the latest content)
    if len(result) > max_chars:
        result = result[-max_chars:]
        # safe cutoff: start from next line break to avoid cutting mid-token
        first_newline = result.find("\n")
        if first_newline > 0:
            result = result[first_newline + 1 :]

    return result

