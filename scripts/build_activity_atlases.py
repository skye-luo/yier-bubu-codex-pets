"""Compose already-generated, cleaned work rows; never synthesizes poses."""
import argparse
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pet-dir", type=Path, required=True)
    parser.add_argument("--research-row", type=Path, required=True)
    parser.add_argument("--writing-row", type=Path, required=True)
    args = parser.parse_args()
    output = args.pet_dir / "variants"
    output.mkdir(parents=True, exist_ok=True)
    for name, path in (("research", args.research_row), ("writing", args.writing_row)):
        row = Image.open(path).convert("RGBA")
        if row.size == (1152, 208):
            padded = Image.new("RGBA", (1536, 208), (0, 0, 0, 0))
            padded.paste(row, (0, 0))
            row = padded
        if row.size != (1536, 208):
            raise ValueError(f"{path}: expected normalized 1152x208 or 1536x208 work row")
        for column in range(8):
            populated = row.getchannel("A").crop((column * 192, 0, (column + 1) * 192, 208)).getbbox() is not None
            if populated != (column < 6):
                raise ValueError(f"{path}: incorrect frame occupancy in column {column}")
        for mode, base_name in (("awake", "spritesheet.webp"), ("sleep", "spritesheet-night.webp")):
            atlas = Image.open(args.pet_dir / base_name).convert("RGBA")
            atlas.paste(row, (0, 7 * 208))
            atlas.save(output / f"{name}-{mode}.webp", "WEBP", lossless=True, exact=True)
            print(output / f"{name}-{mode}.webp")


if __name__ == "__main__":
    main()
