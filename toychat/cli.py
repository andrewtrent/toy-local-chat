from __future__ import annotations

import argparse
from pathlib import Path

from .context import build_context, write_debug_context
from .model import call_ollama
from .store import Store
from .tasks import create_task

HELP = """
Commands:
  /help                         Show this help
  /remember TEXT                Save a durable note
  /recall QUERY                 Search durable notes
  /search QUERY                 Search notes and messages
  /history [N]                  Show recent messages
  /task TITLE :: GOAL           Create a structured task packet
  /context                      Write/show last context bundle path
  /exit                         Quit
""".strip()


def print_hits(hits):
    if not hits:
        print("(no hits)")
        return
    for h in hits:
        print(f"[{h.kind} #{h.rowid} | {h.created_at}] {h.title}\n{h.body[:1000]}\n")


def handle_command(line: str, store: Store) -> bool:
    if line in {"/exit", "/quit"}:
        return False
    if line == "/help":
        print(HELP)
        return True
    if line.startswith("/remember "):
        body = line.removeprefix("/remember ").strip()
        title = body.split(".")[0][:80] or "Note"
        note_id = store.add_note(title=title, body=body)
        print(f"Saved note #{note_id}.")
        return True
    if line.startswith("/recall "):
        q = line.removeprefix("/recall ").strip().replace('"', ' ')
        print_hits(store.search_notes(f'"{q}"', limit=10))
        return True
    if line.startswith("/search "):
        q = line.removeprefix("/search ").strip().replace('"', ' ')
        print("Notes:")
        print_hits(store.search_notes(f'"{q}"', limit=5))
        print("Messages:")
        print_hits(store.search_messages(f'"{q}"', limit=5))
        return True
    if line.startswith("/history"):
        parts = line.split()
        limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
        for row in store.recent_messages(limit):
            print(f'{row["id"]} {row["created_at"]} {row["role"]}: {row["content"][:500]}')
        return True
    if line.startswith("/task "):
        raw = line.removeprefix("/task ").strip()
        if "::" in raw:
            title, goal = [p.strip() for p in raw.split("::", 1)]
        else:
            title, goal = raw, "Clarify this task and propose the next action."
        path = create_task(title, goal)
        print(f"Created {path}")
        return True
    if line == "/context":
        print("Last context bundle is written to .debug/last_context.md after every normal chat turn.")
        return True
    print("Unknown command. Type /help.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="memory.db")
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    store = Store(Path(args.db))
    print("toy-local-chat. Type /help or /exit.")

    try:
        while True:
            line = input("you> ").strip()
            if not line:
                continue
            if line.startswith("/"):
                if not handle_command(line, store):
                    break
                continue

            store.add_message("user", line)
            context = build_context(store, line)
            write_debug_context(context)

            if args.dry_run:
                answer = "[dry-run] Built context and saved it to .debug/last_context.md."
            else:
                result = call_ollama(context, args.model)
                answer = result.text

            print(f"bot> {answer}\n")
            store.add_message("assistant", answer)
    finally:
        store.close()


if __name__ == "__main__":
    main()
