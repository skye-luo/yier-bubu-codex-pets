#!/usr/bin/env python3
"""Swap the idle row for 一二/布布 without creating separate Codex pets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from activity_state import KINDS, recent_activity, stable_activity


PET_IDS = ("yier", "bubu", "dianzai")
LEGACY_AVATAR_IDS = {
    "custom:yier-sleep": "custom:yier",
    "custom:bubu-sleep": "custom:bubu",
}
SETTING_RE = re.compile(
    r'^(?P<indent>\s*)selected-avatar-id\s*=\s*"(?P<value>[^"]*)"\s*(?P<comment>#.*)?$'
)


def parse_args() -> argparse.Namespace:
    codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    runtime_root = codex_root / "pet-sleep-mode"
    parser = argparse.ArgumentParser(
        description=(
            "22:00–08:00 自动把一二/布布的待机动作换成睡觉，"
            "工作动作与宠物 ID 保持不变。"
        )
    )
    parser.add_argument(
        "--activity",
        choices=("auto", *KINDS),
        default="auto",
        help="auto 根据本地近期任务日志选择工作造型；也可手动指定。",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "sleep", "awake"),
        default="auto",
        help="auto 按本地时间判断；sleep/awake 用于手动测试。",
    )
    parser.add_argument(
        "--codex-root",
        type=Path,
        default=codex_root,
        help="Codex 数据目录。",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=runtime_root / "assets",
        help="白天/夜间图集目录。",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=codex_root / "config.toml",
        help="Codex config.toml 路径；只用于迁移旧睡觉宠物 ID。",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=runtime_root / "state.json",
        help="记录最近一次图集切换结果。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出目标，不修改图集、配置或状态。",
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


def atomic_write_text(path: Path, text: str) -> None:
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


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_copy_if_changed(source: Path, target: Path, dry_run: bool) -> bool:
    if not source.is_file():
        raise FileNotFoundError(f"缺少睡眠模式图集：{source}")
    if target.is_file() and file_digest(source) == file_digest(target):
        return False
    if dry_run:
        return True

    target.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = target.stat().st_mode if target.exists() else 0o644
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=f".{target.name}.",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        with source.open("rb") as source_handle:
            shutil.copyfileobj(source_handle, handle)
    os.chmod(temp_path, existing_mode)
    os.replace(temp_path, target)
    return True


def load_state(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, data: dict[str, object]) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def notify_running_app(target: str) -> None:
    script_path = Path(__file__).with_name("refresh_pet_overlay.mjs")
    bundled_node = Path(
        "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node"
    )
    node_path = Path(os.environ.get("CODEX_PET_NODE", bundled_node))
    if not node_path.exists() or not script_path.exists():
        print("提示：Codex 将在下次启动时读取新图集；未找到实时刷新组件。")
        return
    try:
        result = subprocess.run(
            [str(node_path), str(script_path)],
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


def migrate_legacy_selection(
    config_path: Path,
    config_text: str,
    selected_avatar: str | None,
    dry_run: bool,
) -> tuple[str | None, bool]:
    target = LEGACY_AVATAR_IDS.get(selected_avatar or "")
    if target is None:
        return selected_avatar, False
    if not dry_run:
        atomic_write_text(config_path, set_selected_avatar(config_text, target))
    print(f"迁移旧睡觉宠物选择：{selected_avatar} → {target}")
    return target, True


def main() -> int:
    args = parse_args()
    now = dt.datetime.now().astimezone()
    mode = desired_mode(args.mode, now)
    state = load_state(args.state)
    if args.activity == "auto":
        candidate, activity_key = recent_activity(args.codex_root, now)
        activity, activity_key = stable_activity(candidate, activity_key, state, now)
    else:
        activity, activity_key = args.activity, "manual"

    try:
        config_text = args.config.read_text(encoding="utf-8")
    except FileNotFoundError:
        config_text = ""
    selected_avatar = get_selected_avatar(config_text)
    selected_avatar, migrated = migrate_legacy_selection(
        args.config,
        config_text,
        selected_avatar,
        args.dry_run,
    )

    changed_pet_ids: list[str] = []
    skipped_pet_ids: list[str] = []
    for pet_id in PET_IDS:
        source = args.assets / f"{pet_id}-{mode}.webp"
        variant = args.assets / f"{pet_id}-{activity}-{mode}.webp"
        if activity != "coding" and variant.is_file():
            source = variant
        target = args.codex_root / "pets" / pet_id / "spritesheet.webp"
        if not target.parent.is_dir():
            skipped_pet_ids.append(pet_id)
            continue
        if atomic_copy_if_changed(source, target, args.dry_run):
            changed_pet_ids.append(pet_id)

    if activity != state.get("last_activity") or activity_key != state.get("activity_key"):
        state["activity_changed_at"] = now.timestamp()
    state.update(
        {
            "last_mode": mode,
            "last_activity": activity,
            "activity_key": activity_key,
            "selected_avatar_id": selected_avatar,
            "changed_pet_ids": changed_pet_ids,
            "skipped_pet_ids": skipped_pet_ids,
            "updated_at": now.isoformat(timespec="seconds"),
        }
    )
    if not args.dry_run:
        save_state(args.state, state)

    label = "夜间睡觉待机" if mode == "sleep" else "白天普通待机"
    changed_text = "、".join(changed_pet_ids) if changed_pet_ids else "无需更新"
    if changed_pet_ids or args.dry_run:
        print(f"{label} / {activity}：{changed_text}")
    if skipped_pet_ids:
        print(f"未安装，已跳过：{'、'.join(skipped_pet_ids)}")

    if not args.dry_run and (migrated or changed_pet_ids):
        notify_running_app(selected_avatar or "installed pets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
