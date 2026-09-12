#!/usr/bin/env bash
set -euo pipefail

codex_root="${CODEX_HOME:-$HOME/.codex}"
pets_root="$codex_root/pets"
uninstall_stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$codex_root/pets-backups/yier-bubu-uninstalled-$uninstall_stamp"
moved=0

for pet_id in yier bubu dianzai; do
  target_dir="$pets_root/$pet_id"
  if [ -e "$target_dir" ]; then
    mkdir -p "$backup_root"
    mv "$target_dir" "$backup_root/$pet_id"
    echo "已移出：$pet_id"
    moved=1
  fi
done

if [ "$moved" -eq 1 ]; then
  echo "宠物已移动到：$backup_root"
else
  echo "没有发现已安装的一二、布布或点仔。"
fi
