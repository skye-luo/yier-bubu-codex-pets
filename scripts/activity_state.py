"""Best-effort local task-kind detection; never persists prompt or tool text."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

TAIL_BYTES = 512 * 1024
MAX_FILES = 16
MAX_AGE_SECONDS = 30 * 60
HOLD_SECONDS = 30
KINDS = ("coding", "research", "writing")
PATTERNS = {
    "research": r"查资料|查找资料|搜索|调研|检索|search_query|web__run|web\.run|research|browse|look up",
    "writing": r"写作|写文章|写报告|写文案|写正文|写周报|写方案|写邮件|做PPT|做演示|写文档|规划|润色|改写|生成文档|docx|pptx|write (?:a |an )?(?:report|article|email)|draft",
    "coding": r"写代码|编程|修复|修bug|改代码|开发|实现|测试|重构|coding|debug|refactor|pytest|npm test|apply_patch",
}


def classify(text: str) -> str:
    scores = {kind: len(re.findall(pattern, text, re.I)) for kind, pattern in PATTERNS.items()}
    return max(KINDS, key=lambda kind: scores[kind]) if any(scores.values()) else "coding"


def parse_records(records: list[dict]) -> tuple[bool, str, str]:
    """Classify the current turn, retaining its intent over individual tool calls."""
    active, turn, prompt, tool_text = False, "", "", []
    for record in records:
        payload = record.get("payload") or {}
        kind = payload.get("type")
        if record.get("type") == "event_msg":
            if kind == "task_started":
                active, turn, prompt, tool_text = True, str(payload.get("turn_id", "")), "", []
            elif kind in ("task_complete", "task_aborted", "turn_aborted"):
                active = False
            elif kind == "user_message":
                prompt = str(payload.get("message", ""))[:16000]
        if record.get("type") == "response_item":
            if kind == "message" and payload.get("role") == "assistant" and payload.get("phase") == "final_answer":
                active = False
            if kind == "message" and payload.get("role") == "user":
                content = payload.get("content") or []
                texts = [str(part.get("text", "")) for part in content if isinstance(part, dict)]
                value = "\n".join(texts)[:16000]
                # Environment/AGENTS injections are not task intent.
                if value and not value.lstrip().startswith(("<environment_context>", "# AGENTS.md", "<recommended_plugins>")):
                    prompt = value
            elif kind in ("function_call", "custom_tool_call"):
                active = True
                tool_text.append(str(payload.get("name", "")) + " " + str(payload.get("arguments", payload.get("input", "")))[:8000])
                tool_text = tool_text[-8:]
    if not active:
        return False, "coding", turn
    # An explicit user request wins; otherwise use recent tool names/arguments.
    known_intent = any(re.search(pattern, prompt, re.I) for pattern in PATTERNS.values())
    return True, classify(prompt if known_intent else "\n".join(tool_text)), turn


def recent_activity(codex_root: Path, now: dt.datetime) -> tuple[str, str]:
    candidates = []
    for days_back in range(3):
        day = now - dt.timedelta(days=days_back)
        folder = codex_root / "sessions" / day.strftime("%Y/%m/%d")
        try:
            for path in folder.glob("*.jsonl"):
                stamp = path.stat().st_mtime
                if 0 <= now.timestamp() - stamp <= MAX_AGE_SECONDS:
                    candidates.append((stamp, path))
        except OSError:
            continue
    for _, path in sorted(candidates, reverse=True)[:MAX_FILES]:
        try:
            with path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(max(0, size - TAIL_BYTES))
                lines = handle.read(TAIL_BYTES).decode("utf-8", errors="replace").splitlines()
            records = []
            for line in lines:
                try:
                    value = json.loads(line.lstrip("\ufeff"))
                    if isinstance(value, dict):
                        records.append(value)
                except (ValueError, TypeError):
                    continue
            active, kind, turn = parse_records(records)
            if active:
                key = hashlib.sha256(f"{path.name}:{turn}".encode()).hexdigest()[:16]
                return kind, key
        except OSError:
            continue
    return "coding", ""


def stable_activity(candidate: str, key: str, state: dict, now: dt.datetime) -> tuple[str, str]:
    previous = state.get("last_activity", "coding")
    try:
        elapsed = now.timestamp() - float(state.get("activity_changed_at", 0))
    except (ValueError, TypeError):
        elapsed = HOLD_SECONDS
    if key and key == state.get("activity_key") and previous in KINDS and elapsed < HOLD_SECONDS:
        return previous, key
    return candidate, key
