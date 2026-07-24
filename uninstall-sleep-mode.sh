#!/usr/bin/env bash
set -euo pipefail

codex_root="${CODEX_HOME:-$HOME/.codex}"
runtime_root="$codex_root/pet-sleep-mode"
launch_agent_path="$HOME/Library/LaunchAgents/com.oneday.codex-pet-sleep.plist"
user_domain="gui/$(id -u)"
uninstall_stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$codex_root/pets-backups/yier-bubu-sleep-uninstalled-$uninstall_stamp"

if [ -f "$runtime_root/pet_sleep_scheduler.py" ]; then
  /usr/bin/python3 "$runtime_root/pet_sleep_scheduler.py" --mode awake || true
fi

launchctl bootout "$user_domain" "$launch_agent_path" >/dev/null 2>&1 || true

for pet_id in yier-sleep bubu-sleep; do
  target_dir="$codex_root/pets/$pet_id"
  if [ -e "$target_dir" ]; then
    mkdir -p "$backup_root"
    mv "$target_dir" "$backup_root/$pet_id"
    echo "已移出：$pet_id"
  fi
done

if [ -e "$launch_agent_path" ]; then
  mkdir -p "$backup_root/launchd"
  mv "$launch_agent_path" "$backup_root/launchd/"
fi

if [ -e "$runtime_root" ]; then
  mkdir -p "$backup_root/runtime"
  mv "$runtime_root" "$backup_root/runtime/"
fi

echo "睡眠定时已停用；可恢复文件位于：$backup_root"
