#!/usr/bin/env python3
"""Build a hybrid atlas: sleeping idle row plus original active-state rows."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_SIZE = (CELL_WIDTH * 8, CELL_HEIGHT * 9)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--awake", type=Path, required=True)
    parser.add_argument("--sleep", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_atlas(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if image.size != ATLAS_SIZE:
        raise ValueError(f"{path} 尺寸应为 {ATLAS_SIZE}，实际为 {image.size}")
    return image


def clear_hidden_rgb(image: Image.Image) -> Image.Image:
    red, green, blue, alpha = image.split()
    visible_mask = alpha.point(lambda value: 255 if value else 0)
    empty = Image.new("L", image.size, 0)
    return Image.merge(
        "RGBA",
        (
            Image.composite(red, empty, visible_mask),
            Image.composite(green, empty, visible_mask),
            Image.composite(blue, empty, visible_mask),
            alpha,
        ),
    )


def main() -> int:
    args = parse_args()
    awake = load_atlas(args.awake)
    sleep = load_atlas(args.sleep)
    night = awake.copy()
    idle_row = sleep.crop((0, 0, ATLAS_SIZE[0], CELL_HEIGHT))
    night.paste(idle_row, (0, 0))
    night = clear_hidden_rgb(night)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    night.save(args.output, "WEBP", lossless=True, method=6, exact=True)
    print(f"已生成夜间混合图集：{args.output} ({night.width}x{night.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
