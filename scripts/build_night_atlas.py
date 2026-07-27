#!/usr/bin/env python3
"""Build a hybrid atlas: sleeping idle row plus original active-state rows."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_COLUMNS = 8
V1_ROW_NAMES = (
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
)
V1_FRAME_COUNTS = (6, 8, 8, 4, 5, 8, 6, 6, 6)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--awake", type=Path, required=True)
    sleep_input = parser.add_mutually_exclusive_group(required=True)
    sleep_input.add_argument(
        "--sleep",
        type=Path,
        help="完整睡眠图集；取其第 0 行。",
    )
    sleep_input.add_argument(
        "--sleep-strip",
        type=Path,
        help="包含 6 个透明睡眠姿势的横向素材。",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    return parser.parse_args()


def load_awake_atlas(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    expected_width = CELL_WIDTH * ATLAS_COLUMNS
    valid_heights = (CELL_HEIGHT * 9, CELL_HEIGHT * 11)
    if image.width != expected_width or image.height not in valid_heights:
        raise ValueError(
            f"{path} 尺寸应为 {expected_width}x1872 或 "
            f"{expected_width}x2288，实际为 {image.size}"
        )
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


def alpha_column_runs(alpha: Image.Image, threshold: int = 12) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for x in range(alpha.width):
        column = alpha.crop((x, 0, x + 1, alpha.height))
        populated = column.getextrema()[1] > threshold
        if populated and start is None:
            start = x
        elif not populated and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, alpha.width))
    return runs


def extract_sleep_poses(path: Path) -> list[Image.Image]:
    strip = clear_hidden_rgb(Image.open(path).convert("RGBA"))
    alpha = strip.getchannel("A")
    runs = alpha_column_runs(alpha)
    if len(runs) != 6:
        raise ValueError(f"{path} 应包含 6 个分离睡眠姿势，检测到 {len(runs)} 个")

    poses: list[Image.Image] = []
    for left, right in runs:
        box = alpha.crop((left, 0, right, alpha.height)).getbbox()
        if box is None:
            raise ValueError(f"{path} 中检测到透明空姿势")
        top = box[1]
        bottom = box[3]
        poses.append(strip.crop((left, top, right, bottom)))
    return poses


def normalize_sleep_poses(poses: list[Image.Image]) -> list[Image.Image]:
    max_width = max(pose.width for pose in poses)
    max_height = max(pose.height for pose in poses)
    scale = min(180 / max_width, 164 / max_height)
    cells: list[Image.Image] = []

    for pose in poses:
        size = (
            max(1, round(pose.width * scale)),
            max(1, round(pose.height * scale)),
        )
        resized = pose.resize(size, Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
        x = (CELL_WIDTH - resized.width) // 2
        y = CELL_HEIGHT - resized.height - 10
        cell.alpha_composite(resized, (x, y))
        cells.append(clear_hidden_rgb(cell))
    return cells


def make_sleep_row_from_strip(path: Path) -> tuple[Image.Image, list[Image.Image]]:
    cells = normalize_sleep_poses(extract_sleep_poses(path))
    row = Image.new(
        "RGBA",
        (CELL_WIDTH * ATLAS_COLUMNS, CELL_HEIGHT),
        (0, 0, 0, 0),
    )
    for index, cell in enumerate(cells):
        row.alpha_composite(cell, (index * CELL_WIDTH, 0))
    # v2 的第 7 格是 neutral/default；夜间也应保持睡觉形象。
    row.alpha_composite(cells[0], (6 * CELL_WIDTH, 0))
    return clear_hidden_rgb(row), cells


def make_sleep_row_from_atlas(
    path: Path,
    awake_size: tuple[int, int],
) -> tuple[Image.Image, list[Image.Image]]:
    sleep = Image.open(path).convert("RGBA")
    if sleep.size != awake_size:
        raise ValueError(f"{path} 尺寸应为 {awake_size}，实际为 {sleep.size}")
    row = clear_hidden_rgb(sleep.crop((0, 0, awake_size[0], CELL_HEIGHT)))
    cells = [
        row.crop((index * CELL_WIDTH, 0, (index + 1) * CELL_WIDTH, CELL_HEIGHT))
        for index in range(6)
    ]
    return row, cells


def save_preview(path: Path, frames: list[Image.Image]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=(520, 480, 440, 440, 480, 560),
        loop=0,
        disposal=2,
        transparency=0,
    )


def checker_cell() -> Image.Image:
    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (242, 242, 242, 255))
    draw = ImageDraw.Draw(cell)
    tile = 16
    for y in range(0, CELL_HEIGHT, tile):
        for x in range(0, CELL_WIDTH, tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle(
                    (
                        x,
                        y,
                        min(x + tile - 1, CELL_WIDTH - 1),
                        min(y + tile - 1, CELL_HEIGHT - 1),
                    ),
                    fill=(224, 224, 224, 255),
                )
    return cell


def save_contact_sheet(path: Path, atlas: Image.Image) -> None:
    row_count = atlas.height // CELL_HEIGHT
    row_names = V1_ROW_NAMES + (
        ("look 000-157.5", "look 180-337.5") if row_count == 11 else ()
    )
    frame_counts = V1_FRAME_COUNTS + ((8, 8) if row_count == 11 else ())
    header_height = 22
    sheet = Image.new(
        "RGB",
        (atlas.width, row_count * (CELL_HEIGHT + header_height)),
        (0, 0, 0),
    )
    draw = ImageDraw.Draw(sheet)
    checker = checker_cell()

    for row_index in range(row_count):
        header_y = row_index * (CELL_HEIGHT + header_height)
        count_label = (
            "6 + neutral"
            if row_index == 0 and row_count == 11
            else f"{frame_counts[row_index]} frames"
        )
        draw.text((4, header_y + 5), f"row {row_index} {row_names[row_index]}", fill="white")
        draw.text((1348, header_y + 5), count_label, fill="white")
        cell_y = header_y + header_height
        used_count = 7 if row_index == 0 and row_count == 11 else frame_counts[row_index]
        for column in range(ATLAS_COLUMNS):
            x = column * CELL_WIDTH
            sheet.paste(checker.convert("RGB"), (x, cell_y))
            cell = atlas.crop(
                (
                    x,
                    row_index * CELL_HEIGHT,
                    x + CELL_WIDTH,
                    (row_index + 1) * CELL_HEIGHT,
                )
            )
            background = sheet.crop((x, cell_y, x + CELL_WIDTH, cell_y + CELL_HEIGHT)).convert(
                "RGBA"
            )
            background.alpha_composite(cell)
            sheet.paste(background.convert("RGB"), (x, cell_y))
            border = (0, 126, 79) if column < used_count else (220, 38, 38)
            draw.rectangle(
                (x, cell_y, x + CELL_WIDTH - 1, cell_y + CELL_HEIGHT - 1),
                outline=border,
                width=1,
            )
            draw.text((x + 3, cell_y + 3), str(column), fill=(20, 20, 20))

    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)


def main() -> int:
    args = parse_args()
    awake = load_awake_atlas(args.awake)
    if args.sleep_strip:
        idle_row, preview_frames = make_sleep_row_from_strip(args.sleep_strip)
    else:
        idle_row, preview_frames = make_sleep_row_from_atlas(args.sleep, awake.size)

    night = awake.copy()
    night.paste(idle_row, (0, 0))
    night = clear_hidden_rgb(night)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    night.save(args.output, "WEBP", lossless=True, method=6, exact=True)

    if args.preview:
        save_preview(args.preview, preview_frames)
    if args.contact_sheet:
        save_contact_sheet(args.contact_sheet, night)

    print(f"已生成夜间混合图集：{args.output} ({night.width}x{night.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
