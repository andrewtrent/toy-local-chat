# toy-local-chat

A toy context-management sandbox for learning how local chat history, durable notes, retrieval, and task packets work.

This is deliberately portfolio-free and low-stakes. The point is not to build a smart assistant yet; the point is to make context selection visible.

## Features in this MVP

- SQLite message history
- SQLite FTS5 search over messages and durable notes
- `/remember` durable notes
- `/recall` note search
- `/search` transcript search
- `/task` structured task packet generator
- `/context` writes the last prompt bundle to `.debug/last_context.md`
- Local model call through Ollama by default
- Dry-run mode when Ollama is not available

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m toychat.cli --model llama3.2:3b
```

Run without a model call:

```bash
python -m toychat.cli --dry-run
```

## Commands

```text
/help                         Show commands
/remember TEXT                Save a durable note
/recall QUERY                 Search durable notes
/search QUERY                 Search chat history and notes
/history [N]                  Show recent N messages
/task TITLE :: GOAL           Create a task packet in tasks/
/context                      Save/show the current context bundle
/exit                         Quit
```

## Mental model

Raw transcript is cheap storage. Durable memory is curated. Retrieval is selected evidence. The model should see less than the system knows.
