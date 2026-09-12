"""Behavior tests: stable task intent, completion, tail recovery and atlas selection."""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from activity_state import classify, parse_records, recent_activity, stable_activity
from pet_sleep_scheduler import desired_mode


def event(kind, **fields):
    return {"type": "event_msg", "payload": {"type": kind, **fields}}


def call(text):
    return {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "input": text}}


class ActivityTests(unittest.TestCase):
    def test_explicit_intent_survives_utility_commands(self):
        rows = [event("task_started", turn_id="a"), event("user_message", message="帮我查资料做调研"), call("tools.exec_command({cmd:'ls'})")]
        self.assertEqual(parse_records(rows)[:2], (True, "research"))

    def test_completed_task_is_not_active(self):
        self.assertFalse(parse_records([event("task_started"), call("apply_patch"), event("task_complete")])[0])

    def test_tail_without_start_can_read_tool_activity(self):
        self.assertEqual(parse_records([call("web__run search_query")])[:2], (True, "research"))

    def test_new_turn_resets_previous_intent(self):
        rows = [event("task_started"), event("user_message", message="查资料"), event("task_complete"), event("task_started"), event("user_message", message="写文案")]
        self.assertEqual(parse_records(rows)[1], "writing")

    def test_all_three_kinds(self):
        for text, expected in [("帮我修复代码并测试", "coding"), ("搜索周边咖啡店", "research"), ("帮我写文章和润色", "writing"), ("hello", "coding")]:
            with self.subTest(text=text):
                self.assertEqual(classify(text), expected)

    def test_hold_prevents_short_tool_flips(self):
        now = dt.datetime.now().astimezone()
        state = {"last_activity": "writing", "activity_key": "same", "activity_changed_at": now.timestamp() - 5}
        self.assertEqual(stable_activity("research", "same", state, now)[0], "writing")
        self.assertEqual(stable_activity("research", "new", state, now)[0], "research")

    def test_conversational_chinese_requests(self):
        for text, expected in [("写一篇文章", "writing"), ("帮我写一个小红书文案", "writing"),
                               ("做个PPT", "writing"), ("查一下资料", "research")]:
            self.assertEqual(classify(text), expected)

    def test_day_night_boundaries(self):
        for hour, expected in [(0, "sleep"), (7, "sleep"), (8, "awake"), (21, "awake"), (22, "sleep")]:
            self.assertEqual(desired_mode("auto", dt.datetime(2026, 9, 12, hour)), expected)

    def test_malformed_tail_and_completed_newer_task(self):
        now = dt.datetime.now().astimezone()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            logs = root / "sessions" / now.strftime("%Y/%m/%d")
            logs.mkdir(parents=True)
            (logs / "active.jsonl").write_text("broken partial line\n" + json.dumps(event("task_started")) + "\n" + json.dumps(event("user_message", message="写报告")) + "\n", encoding="utf-8")
            (logs / "complete.jsonl").write_text(json.dumps(event("task_complete")) + "\n", encoding="utf-8")
            kind, key = recent_activity(root, now + dt.timedelta(seconds=1))
            self.assertEqual(kind, "writing")
            self.assertEqual(len(key), 16)
            self.assertNotIn("写报告", key)

    def test_new_turn_has_a_distinct_anonymous_key(self):
        now = dt.datetime.now().astimezone()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            logs = root / "sessions" / now.strftime("%Y/%m/%d")
            logs.mkdir(parents=True)
            path = logs / "session.jsonl"
            keys = []
            for turn in ("a", "b"):
                path.write_text(json.dumps(event("task_started", turn_id=turn)) + "\n", encoding="utf-8")
                keys.append(recent_activity(root, now + dt.timedelta(seconds=1))[1])
            self.assertNotEqual(keys[0], keys[1])


if __name__ == "__main__":
    unittest.main()
