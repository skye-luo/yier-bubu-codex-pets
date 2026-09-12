#!/usr/bin/env bash
set -euo pipefail

codex_root="${CODEX_HOME:-$HOME/.codex}"
runtime_root="$codex_root/pet-sleep-mode"
launch_agent_path="$HOME/Library/LaunchAgents/com.oneday.codex-pet-sleep.plist"
user_domain="gui/$(id -u)"
uninstall_stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$codex_root/pets-backups/yier-bubu-sleep-uninstalled-$uninstall_stamp"

launchctl bootout "$user_domain" "$launch_agent_path" >/dev/null 2>&1 || true

if [ -f "$runtime_root/pet_sleep_scheduler.py" ]; then
  /usr/bin/python3 "$runtime_root/pet_sleep_scheduler.py" --mode awake --activity coding || true
fi

if [ -e "$launch_agent_path" ]; then
  mkdir -p "$backup_root/launchd"
  mv "$launch_agent_path" "$backup_root/launchd/"
fi

if [ -e "$runtime_root" ]; then
  mkdir -p "$backup_root/runtime"
  mv "$runtime_root" "$backup_root/runtime/"
fi

echo "睡眠定时已停用，一二、布布和点仔已恢复普通待机。"
echo "可恢复的定时组件位于：$backup_root"
