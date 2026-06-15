from __future__ import annotations

from pathlib import Path

from .store import SearchHit, Store

SYSTEM_PROMPT = """You are Toy Local Chat, a context-management sandbox assistant.
Your job is to answer using only the current user message, recent chat, and retrieved local notes/history.
Be explicit when context is missing. Prefer short, practical answers.
Do not pretend durable memory exists unless it appears in the supplied context.
"""


def safe_fts_query(text: str) -> str:
    # FTS5 bare queries can error on punctuation. This MVP uses quoted phrase search.
    text = text.replace('"', ' ')
    return f'"{text.strip()}"' if text.strip() else '""'


def format_hits(title: str, hits: list[SearchHit]) -> str:
    if not hits:
        return f"## {title}\n(none)\n"
    lines = [f"## {title}"]
    for h in hits:
        body = h.body.strip().replace("\n", " ")
        if len(body) > 700:
            body = body[:700] + "..."
        lines.append(f"- [{h.kind} #{h.rowid} | {h.created_at}] {h.title}: {body}")
    return "\n".join(lines) + "\n"


def build_context(store: Store, user_message: str, *, recent_limit: int = 10) -> str:
    q = safe_fts_query(user_message)
    note_hits = store.search_notes(q, limit=5) if user_message.strip() else []
    msg_hits = store.search_messages(q, limit=5) if user_message.strip() else []
    recent = store.recent_messages(recent_limit)

    recent_lines = []
    for row in recent:
        content = row["content"].strip()
        if len(content) > 1000:
            content = content[:1000] + "..."
        recent_lines.append(f'{row["role"]}: {content}')

    return "\n\n".join(
        [
            "# System",
            SYSTEM_PROMPT,
            format_hits("Retrieved durable notes", note_hits),
            format_hits("Retrieved transcript hits", msg_hits),
            "## Recent conversation\n" + ("\n".join(recent_lines) if recent_lines else "(none)"),
            "## Current user message\n" + user_message,
        ]
    )


def write_debug_context(context: str, path: Path = Path(".debug/last_context.md")) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(context, encoding="utf-8")
