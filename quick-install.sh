#!/usr/bin/env bash
set -euo pipefail

repo_url="${YIER_BUBU_REPO_URL:-https://github.com/skye-luo/yier-bubu-codex-pets.git}"
release_tag="${YIER_BUBU_RELEASE_TAG:-v2.0.0}"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/yier-bubu-codex-pets.XXXXXX")"

cleanup() {
  rm -rf "$temp_root"
}
trap cleanup EXIT

if ! command -v git >/dev/null 2>&1; then
  echo "安装失败：请先安装 Git。" >&2
  exit 1
fi

echo "正在下载一二 × 布布 Codex 宠物包……"
git clone --depth 1 --branch "$release_tag" "$repo_url" "$temp_root/repo"

cd "$temp_root/repo"
bash install.sh
bash install-sleep-mode.sh

echo
echo "全部完成。请重启 Codex，然后前往 设置 → 外观 → Pets 选择一二或布布。"
