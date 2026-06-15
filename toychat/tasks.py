from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "task"


def create_task(title: str, goal: str, tasks_dir: Path = Path("tasks")) -> Path:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = tasks_dir / f"{date}-{slugify(title)}.md"
    n = 2
    while path.exists():
        path = tasks_dir / f"{date}-{slugify(title)}-{n}.md"
        n += 1
    body = f"""# Task: {title}

## Goal
{goal}

## Current state
Unknown.

## Attempted
Nothing yet.

## Relevant files
None yet.

## Commands run
None yet.

## Blockers
None yet.

## Desired output
A concrete next step or a complete small patch.

## Escalation question
What should a stronger model or human decide if this gets blocked?
"""
    path.write_text(body, encoding="utf-8")
    return path
