#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
codex_root="${CODEX_HOME:-$HOME/.codex}"
pets_root="$codex_root/pets"
install_stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$codex_root/pets-backups/yier-bubu-$install_stamp"

if command -v shasum >/dev/null 2>&1; then
  (cd "$repo_root" && shasum -a 256 -c SHA256SUMS)
else
  echo "提示：未找到 shasum，跳过 SHA-256 校验。"
fi

mkdir -p "$pets_root"

for pet_id in yier bubu dianzai; do
  source_dir="$repo_root/pets/$pet_id"
  target_dir="$pets_root/$pet_id"

  if [ ! -f "$source_dir/pet.json" ] || [ ! -f "$source_dir/spritesheet.webp" ]; then
    echo "安装失败：$source_dir 缺少 pet.json 或 spritesheet.webp。" >&2
    exit 1
  fi

  if [ -e "$target_dir" ]; then
    mkdir -p "$backup_root"
    mv "$target_dir" "$backup_root/$pet_id"
    echo "已备份原有宠物：$backup_root/$pet_id"
  fi

  mkdir -p "$target_dir"
  cp "$source_dir/pet.json" "$target_dir/pet.json"
  cp "$source_dir/spritesheet.webp" "$target_dir/spritesheet.webp"
  echo "已安装：$pet_id"
done

for legacy_pet_id in yier-sleep bubu-sleep; do
  legacy_dir="$pets_root/$legacy_pet_id"
  if [ -e "$legacy_dir" ]; then
    mkdir -p "$backup_root/legacy-pets"
    mv "$legacy_dir" "$backup_root/legacy-pets/$legacy_pet_id"
    echo "已移出旧独立睡觉角色：$legacy_pet_id"
  fi
done

echo
echo "安装完成。请重启 Codex，然后前往 设置 → 外观 → Pets 切换一二、布布或点仔。"
echo "如需 22:00–08:00 自动睡觉，再运行：bash install-sleep-mode.sh"
