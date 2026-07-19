#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v shasum >/dev/null 2>&1; then
  echo "校验失败：系统中没有 shasum。" >&2
  exit 1
fi

(cd "$repo_root" && shasum -a 256 -c SHA256SUMS)
echo "宠物包校验通过。"
