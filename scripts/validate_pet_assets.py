#!/usr/bin/env python3
"""Validate packaged Codex pet atlases and day/night invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


CELL_WIDTH = 192
CELL_HEIGHT = 208
FRAME_COUNTS = {
    9: (6, 8, 8, 4, 5, 8, 6, 6, 6),
    11: (7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    return parser.parse_args()


def has_hidden_rgb(image: Image.Image) -> bool:
    rgba = image.convert("RGBA")
    return any(
        alpha == 0 and (red != 0 or green != 0 or blue != 0)
        for red, green, blue, alpha in rgba.getdata()
    )


def validate_occupancy(path: Path, image: Image.Image) -> None:
    row_count = image.height // CELL_HEIGHT
    expected_counts = FRAME_COUNTS[row_count]
    alpha = image.getchannel("A")
    for row, expected_count in enumerate(expected_counts):
        for column in range(8):
            cell = alpha.crop(
                (
                    column * CELL_WIDTH,
                    row * CELL_HEIGHT,
                    (column + 1) * CELL_WIDTH,
                    (row + 1) * CELL_HEIGHT,
                )
            )
            populated = cell.getbbox() is not None
            expected = column < expected_count
            if populated != expected:
                state = "非空" if populated else "透明"
                raise ValueError(
                    f"{path}: row {row} col {column} 实际为{state}，"
                    f"预期 {'非空' if expected else '透明'}"
                )


def load_and_validate_atlas(path: Path) -> Image.Image:
    source = Image.open(path)
    if source.mode != "RGBA":
        raise ValueError(f"{path}: 应为 RGBA，实际为 {source.mode}")
    image = source.copy()
    row_count = image.height // CELL_HEIGHT
    if image.width != CELL_WIDTH * 8 or row_count not in FRAME_COUNTS:
        raise ValueError(f"{path}: 非法尺寸 {image.size}")
    if image.height != row_count * CELL_HEIGHT:
        raise ValueError(f"{path}: 高度不是 {CELL_HEIGHT} 的整数倍")
    if has_hidden_rgb(image):
        raise ValueError(f"{path}: 全透明像素中残留 RGB")
    validate_occupancy(path, image)
    return image


def validate_pet(pet_dir: Path) -> None:
    manifest_path = pet_dir / "pet.json"
    awake_path = pet_dir / "spritesheet.webp"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("id") != pet_dir.name:
        raise ValueError(f"{manifest_path}: id 与目录名不一致")
    if manifest.get("spritesheetPath") != "spritesheet.webp":
        raise ValueError(f"{manifest_path}: spritesheetPath 不正确")

    awake = load_and_validate_atlas(awake_path)
    row_count = awake.height // CELL_HEIGHT
    version = manifest.get("spriteVersionNumber", 1)
    expected_version = 2 if row_count == 11 else 1
    if version != expected_version:
        raise ValueError(
            f"{manifest_path}: spriteVersionNumber={version}，"
            f"图集应使用 {expected_version}"
        )

    night_path = pet_dir / "spritesheet-night.webp"
    if night_path.exists():
        night = load_and_validate_atlas(night_path)
        if night.size != awake.size:
            raise ValueError(f"{night_path}: 与白天图集尺寸不一致")
        active_box = (0, CELL_HEIGHT, awake.width, awake.height)
        if ImageChops.difference(
            awake.crop(active_box),
            night.crop(active_box),
        ).getbbox(alpha_only=False):
            raise ValueError(f"{night_path}: 除待机行外的工作动作发生变化")
        if not ImageChops.difference(
            awake.crop((0, 0, awake.width, CELL_HEIGHT)),
            night.crop((0, 0, night.width, CELL_HEIGHT)),
        ).getbbox(alpha_only=False):
            raise ValueError(f"{night_path}: 夜间待机行与白天完全相同")

    variants = pet_dir / "variants"
    if variants.exists():
        if not night_path.exists():
            raise ValueError(f"{variants}: 任务造型需要配套夜间图集")
        for activity in ("research", "writing"):
            for mode, base in (("awake", awake), ("sleep", night)):
                variant_path = variants / f"{activity}-{mode}.webp"
                variant = load_and_validate_atlas(variant_path)
                if variant.size != base.size:
                    raise ValueError(f"{variant_path}: 变体尺寸不一致")
                for row in range(row_count):
                    box = (0, row * CELL_HEIGHT, base.width, (row + 1) * CELL_HEIGHT)
                    differs = ImageChops.difference(base.crop(box), variant.crop(box)).getbbox(alpha_only=False) is not None
                    if differs != (row == 7):
                        raise ValueError(f"{variant_path}: 必须仅修改工作行 row 7；检查 row {row}")

    print(f"{pet_dir.name}: {awake.width}x{awake.height} RGBA，结构通过")


def main() -> int:
    args = parse_args()
    pets_root = args.repo_root / "pets"
    for pet_dir in sorted(path for path in pets_root.iterdir() if path.is_dir()):
        if (pet_dir / "pet.json").exists():
            validate_pet(pet_dir)
    print("宠物图集与日夜状态校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
