#!/usr/bin/env python3
"""Build a Codex v1 8x9 atlas from eight transparent sleeping poses."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_COLUMNS = 8
ROW_FRAME_COUNTS = (6, 8, 8, 4, 5, 8, 6, 6, 6)
ROW_FRAME_INDEXES = (
    (0, 1, 2, 3, 4, 5),
    (0, 1, 2, 3, 4, 5, 6, 7),
    (0, 1, 2, 3, 4, 5, 6, 7),
    (0, 2, 4, 6),
    (0, 2, 4, 6, 7),
    (0, 1, 2, 3, 4, 5, 6, 7),
    (0, 1, 2, 3, 4, 5),
    (0, 1, 2, 3, 4, 5),
    (0, 1, 2, 3, 4, 5),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--prefix", required=True)
    return parser.parse_args()


def load_pose(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError(f"透明空帧：{path}")
    subject = image.crop(alpha_box)
    target_width = CELL_WIDTH - 12
    target_height = CELL_HEIGHT - 14
    scale = min(target_width / subject.width, target_height / subject.height)
    size = (
        max(1, round(subject.width * scale)),
        max(1, round(subject.height * scale)),
    )
    subject = subject.resize(size, Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    x = (CELL_WIDTH - subject.width) // 2
    y = CELL_HEIGHT - subject.height - 6
    cell.alpha_composite(subject, (x, y))
    return cell


def build_atlas(poses: list[Image.Image]) -> Image.Image:
    atlas = Image.new(
        "RGBA",
        (CELL_WIDTH * ATLAS_COLUMNS, CELL_HEIGHT * len(ROW_FRAME_COUNTS)),
        (0, 0, 0, 0),
    )
    for row_index, frame_indexes in enumerate(ROW_FRAME_INDEXES):
        if len(frame_indexes) != ROW_FRAME_COUNTS[row_index]:
            raise AssertionError("行帧数配置不一致")
        for column_index, pose_index in enumerate(frame_indexes):
            atlas.alpha_composite(
                poses[pose_index],
                (column_index * CELL_WIDTH, row_index * CELL_HEIGHT),
            )
    return atlas


def save_preview(path: Path, frames: list[Image.Image]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:6],
        duration=(520, 480, 480, 520, 480, 560),
        loop=0,
        disposal=2,
        transparency=0,
    )


def save_contact_sheet(path: Path, atlas: Image.Image) -> None:
    checker = Image.new("RGBA", atlas.size, (242, 242, 242, 255))
    tile = 16
    for y in range(0, atlas.height, tile):
        for x in range(0, atlas.width, tile):
            if (x // tile + y // tile) % 2:
                patch = Image.new(
                    "RGBA",
                    (min(tile, atlas.width - x), min(tile, atlas.height - y)),
                    (224, 224, 224, 255),
                )
                checker.alpha_composite(patch, (x, y))
    checker.alpha_composite(atlas)
    path.parent.mkdir(parents=True, exist_ok=True)
    checker.convert("RGB").save(path, optimize=True)


def main() -> int:
    args = parse_args()
    frame_paths = [
        args.frames / f"{args.prefix}-sleep-{index:02d}.png"
        for index in range(1, 9)
    ]
    missing = [str(path) for path in frame_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("缺少睡眠帧：" + ", ".join(missing))

    poses = [load_pose(path) for path in frame_paths]
    atlas = build_atlas(poses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(args.output, "WEBP", lossless=True, method=6)

    if args.preview:
        save_preview(args.preview, poses)
    if args.contact_sheet:
        save_contact_sheet(args.contact_sheet, atlas)

    print(f"已生成：{args.output} ({atlas.width}x{atlas.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
