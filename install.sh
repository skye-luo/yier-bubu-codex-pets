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

for pet_id in yier bubu; do
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

echo
echo "安装完成。请重启 Codex，然后前往 设置 → 外观 → Pets 切换一二或布布。"
