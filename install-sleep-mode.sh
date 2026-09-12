#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
codex_root="${CODEX_HOME:-$HOME/.codex}"
runtime_root="$codex_root/pet-sleep-mode"
runtime_assets="$runtime_root/assets"
launch_agents_root="$HOME/Library/LaunchAgents"
launch_agent_path="$launch_agents_root/com.oneday.codex-pet-sleep.plist"
launch_label="com.oneday.codex-pet-sleep"
user_domain="gui/$(id -u)"
install_stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$codex_root/pets-backups/yier-bubu-sleep-mode-$install_stamp"

if command -v shasum >/dev/null 2>&1; then
  (cd "$repo_root" && shasum -a 256 -c SHA256SUMS)
else
  echo "提示：未找到 shasum，跳过 SHA-256 校验。"
fi

launchctl bootout "$user_domain" "$launch_agent_path" >/dev/null 2>&1 || true

# Migrate the former two-character install so two timers cannot overwrite assets.
legacy_agent="$launch_agents_root/com.oneday.yier-bubu-pet-sleep.plist"
legacy_runtime="$codex_root/yier-bubu-pet-sleep-mode"
if [ -e "$legacy_agent" ]; then
  launchctl bootout "$user_domain" "$legacy_agent" >/dev/null 2>&1 || true
  mkdir -p "$backup_root/legacy-launchd"
  mv "$legacy_agent" "$backup_root/legacy-launchd/"
fi
if [ -e "$legacy_runtime" ]; then
  mkdir -p "$backup_root"
  mv "$legacy_runtime" "$backup_root/legacy-runtime"
fi

for pet_id in yier bubu dianzai; do
  source_dir="$repo_root/pets/$pet_id"
  target_dir="$codex_root/pets/$pet_id"

  if [ ! -f "$source_dir/pet.json" ] ||
     [ ! -f "$source_dir/spritesheet.webp" ] ||
     [ ! -f "$source_dir/spritesheet-night.webp" ]; then
    echo "安装失败：$source_dir 缺少 pet.json、白天图集或夜间图集。" >&2
    exit 1
  fi

  mkdir -p "$target_dir"
  cp "$source_dir/pet.json" "$target_dir/pet.json"
  if [ ! -f "$target_dir/spritesheet.webp" ]; then
    cp "$source_dir/spritesheet.webp" "$target_dir/spritesheet.webp"
    echo "已安装原角色：$pet_id"
  fi
done

for legacy_pet_id in yier-sleep bubu-sleep; do
  legacy_dir="$codex_root/pets/$legacy_pet_id"
  if [ -e "$legacy_dir" ]; then
    mkdir -p "$backup_root/legacy-pets"
    mv "$legacy_dir" "$backup_root/legacy-pets/$legacy_pet_id"
    echo "已合并并移出旧独立角色：$legacy_pet_id"
  fi
done

if [ -e "$runtime_root" ]; then
  mkdir -p "$backup_root"
  mv "$runtime_root" "$backup_root/runtime"
fi
if [ -e "$launch_agent_path" ]; then
  mkdir -p "$backup_root/launchd"
  mv "$launch_agent_path" "$backup_root/launchd/"
fi

mkdir -p "$runtime_assets" "$launch_agents_root"
cp "$repo_root/scripts/pet_sleep_scheduler.py" "$runtime_root/pet_sleep_scheduler.py"
cp "$repo_root/scripts/select_codex_pet.mjs" "$runtime_root/select_codex_pet.mjs"
cp "$repo_root/scripts/activity_state.py" "$runtime_root/activity_state.py"
cp "$repo_root/scripts/refresh_pet_overlay.mjs" "$runtime_root/refresh_pet_overlay.mjs"
for pet_id in yier bubu dianzai; do
  cp "$repo_root/pets/$pet_id/spritesheet.webp" "$runtime_assets/$pet_id-awake.webp"
  cp "$repo_root/pets/$pet_id/spritesheet-night.webp" "$runtime_assets/$pet_id-sleep.webp"
  for activity in research writing; do
    for mode in awake sleep; do
      variant="$repo_root/pets/$pet_id/variants/$activity-$mode.webp"
      if [ -f "$variant" ]; then
        cp "$variant" "$runtime_assets/$pet_id-$activity-$mode.webp"
      fi
    done
  done
done
chmod 755 "$runtime_root/pet_sleep_scheduler.py" "$runtime_root/select_codex_pet.mjs"

sed \
  -e "s|__SCHEDULER_PATH__|$runtime_root/pet_sleep_scheduler.py|g" \
  -e "s|__LOG_PATH__|$runtime_root/scheduler.log|g" \
  -e "s|__ERROR_LOG_PATH__|$runtime_root/scheduler-error.log|g" \
  "$repo_root/launchd/com.oneday.codex-pet-sleep.plist" > "$launch_agent_path"

plutil -lint "$launch_agent_path"
launchctl bootstrap "$user_domain" "$launch_agent_path"
launchctl kickstart -k "$user_domain/$launch_label"

echo
echo "睡眠模式已启用：设置中为“一二”“布布”和“点仔”，不会新增独立睡觉角色。"
echo "22:00–08:00 无任务时睡觉；工作、等待和检查动作保持正常。"
echo "每 10 秒检查本地任务类型：查资料、写代码、写作规划会保持不同的工作造型。"
echo "现在也已按当前本地时间执行一次。"
if [ -d "$backup_root" ]; then
  echo "旧睡觉角色与定时组件备份在：$backup_root"
fi
