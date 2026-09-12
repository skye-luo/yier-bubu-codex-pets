#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v shasum >/dev/null 2>&1; then
  echo "校验失败：系统中没有 shasum。" >&2
  exit 1
fi

(cd "$repo_root" && shasum -a 256 -c SHA256SUMS)
python3 "$repo_root/scripts/validate_pet_assets.py" --repo-root "$repo_root"
python3 -m unittest discover -s "$repo_root/tests" -p 'test_*.py'
echo "一二 × 布布宠物包校验通过。"
