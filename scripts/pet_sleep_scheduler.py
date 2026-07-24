#!/usr/bin/env python3
"""Switch 一二/布布 between awake and sleeping Codex Pet variants."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


AWAKE_TO_SLEEP = {
    "custom:yier": "custom:yier-sleep",
    "custom:bubu": "custom:bubu-sleep",
}
SLEEP_TO_AWAKE = {value: key for key, value in AWAKE_TO_SLEEP.items()}
SETTING_RE = re.compile(
    r'^(?P<indent>\s*)selected-avatar-id\s*=\s*"(?P<value>[^"]*)"\s*(?P<comment>#.*)?$'
)


def parse_args() -> argparse.Namespace:
    codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    parser = argparse.ArgumentParser(
        description="22:00–08:00 自动切换一二/布布的睡眠形象。"
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "sleep", "awake"),
        default="auto",
        help="auto 按本地时间判断；sleep/awake 用于手动测试。",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=codex_root / "config.toml",
        help="Codex config.toml 路径。",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=codex_root / "pet-sleep-mode" / "state.json",
        help="保存白天角色选择的状态文件。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出目标，不修改 config.toml。",
    )
    return parser.parse_args()


def get_selected_avatar(config_text: str) -> str | None:
    in_desktop = False
    for line in config_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_desktop = stripped == "[desktop]"
            continue
        if in_desktop:
            match = SETTING_RE.match(line)
            if match:
                return match.group("value")
    return None


def set_selected_avatar(config_text: str, avatar_id: str) -> str:
    lines = config_text.splitlines(keepends=True)
    in_desktop = False
    desktop_found = False
    insert_at: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_desktop and insert_at is None:
                insert_at = index
            in_desktop = stripped == "[desktop]"
            desktop_found = desktop_found or in_desktop
            continue
        if in_desktop:
            match = SETTING_RE.match(line.rstrip("\r\n"))
            if match:
                newline = "\r\n" if line.endswith("\r\n") else "\n"
                comment = f" {match.group('comment')}" if match.group("comment") else ""
                lines[index] = (
                    f'{match.group("indent")}selected-avatar-id = "{avatar_id}"'
                    f"{comment}{newline}"
                )
                return "".join(lines)

    if desktop_found:
        if insert_at is None:
            insert_at = len(lines)
        lines.insert(insert_at, f'selected-avatar-id = "{avatar_id}"\n')
        return "".join(lines)

    suffix = "" if not lines or lines[-1].endswith(("\n", "\r")) else "\n"
    return "".join(lines) + suffix + f'\n[desktop]\nselected-avatar-id = "{avatar_id}"\n'


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = path.stat().st_mode if path.exists() else 0o600
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    os.chmod(temp_path, existing_mode)
    os.replace(temp_path, path)


def load_state(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def notify_running_app(target: str) -> None:
    script_path = Path(__file__).with_name("select_codex_pet.mjs")
    bundled_node = Path(
        "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node"
    )
    node_path = Path(os.environ.get("CODEX_PET_NODE", bundled_node))
    if not node_path.exists() or not script_path.exists():
        print("提示：Codex 将在下次启动时读取新角色；未找到实时刷新组件。")
        return
    try:
        result = subprocess.run(
            [str(node_path), str(script_path), target],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"提示：实时刷新未完成（{error}），下次启动 Codex 时会生效。")
        return
    output = (result.stdout or result.stderr).strip()
    if result.returncode == 0:
        print(f"Codex 宠物窗口已同步：{target}")
    elif output:
        print(f"提示：{output}；下次启动 Codex 时会生效。")


def desired_mode(requested_mode: str, now: dt.datetime) -> str:
    if requested_mode != "auto":
        return requested_mode
    return "sleep" if now.hour >= 22 or now.hour < 8 else "awake"


def choose_target(current: str | None, mode: str, state: dict[str, object]) -> tuple[str | None, str]:
    if mode == "sleep":
        if current in AWAKE_TO_SLEEP:
            state["awake_avatar_id"] = current
            return AWAKE_TO_SLEEP[current], "进入夜间睡眠"
        if current in SLEEP_TO_AWAKE:
            state.setdefault("awake_avatar_id", SLEEP_TO_AWAKE[current])
            return current, "已经在睡觉"
        return None, "当前不是一二或布布，不做切换"

    if current in SLEEP_TO_AWAKE:
        remembered = state.get("awake_avatar_id")
        fallback = SLEEP_TO_AWAKE[current]
        target = (
            remembered
            if remembered in AWAKE_TO_SLEEP
            and AWAKE_TO_SLEEP[str(remembered)] == current
            else fallback
        )
        return str(target), "恢复白天角色"
    return None, "当前已经是白天角色，不做切换"


def main() -> int:
    args = parse_args()
    try:
        config_text = args.config.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"未找到 Codex 配置：{args.config}")
        return 1

    now = dt.datetime.now().astimezone()
    mode = desired_mode(args.mode, now)
    current = get_selected_avatar(config_text)
    state = load_state(args.state)
    target, reason = choose_target(current, mode, state)

    if target is None or target == current:
        state.update(
            {
                "last_mode": mode,
                "last_seen_avatar_id": current,
                "updated_at": now.isoformat(timespec="seconds"),
            }
        )
        if not args.dry_run:
            save_state(args.state, state)
        print(f"{reason}：{current or '未选择宠物'}")
        return 0

    print(f"{reason}：{current} → {target}")
    if args.dry_run:
        return 0

    if target != current:
        atomic_write(args.config, set_selected_avatar(config_text, target))
    state.update(
        {
            "last_mode": mode,
            "last_seen_avatar_id": target,
            "updated_at": now.isoformat(timespec="seconds"),
        }
    )
    save_state(args.state, state)
    notify_running_app(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
