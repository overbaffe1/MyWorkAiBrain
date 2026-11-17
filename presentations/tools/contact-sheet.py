#!/usr/bin/env python3
"""Build a labeled overview contact sheet (JPEG/PNG) from slide-XX.png previews.

Lets an AI agent (or human) inspect all slides of a presentation at once for text
clipping, bad line wraps, overlaps, or small font sizes.

Usage:
  python3 presentations/tools/contact-sheet.py presentations/cantillon/preview exports/cantillon-preview.jpg
  python3 presentations/tools/contact-sheet.py 'presentations/schumpeter/preview/slide-*.png' exports/schumpeter-preview.jpg --cols 3
"""
import argparse
import glob
import os
import sys
from PIL import Image, ImageDraw, ImageFont


def collect_images(source: str) -> list[str]:
    if os.path.isdir(source):
        paths = sorted(glob.glob(os.path.join(source, "slide-*.png")))
        if not paths:
            paths = sorted(glob.glob(os.path.join(source, "*.png")))
        return paths
    return sorted(glob.glob(source))


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a contact-sheet grid from slide PNG previews.")
    ap.add_argument("source", help="Directory containing slide-*.png or a glob pattern")
    ap.add_argument("output", help="Output image path (e.g. exports/my-deck-preview.jpg)")
    ap.add_argument("--cols", type=int, default=2, help="Grid columns (default: 2)")
    ap.add_argument("--thumb-width", type=int, default=680, help="Thumbnail width in px (default: 680)")
    args = ap.parse_args()

    paths = collect_images(args.source)
    if not paths:
        print(f"No preview PNG files found for: {args.source}", file=sys.stderr)
        sys.exit(1)

    margin, gap, label_h = 28, 18, 34
    thumbs: list[tuple[str, Image.Image]] = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        h = round(im.height * args.thumb_width / im.width)
        thumbs.append((os.path.basename(p), im.resize((args.thumb_width, h), Image.Resampling.LANCZOS)))

    cols = max(1, min(args.cols, len(thumbs)))
    rows = (len(thumbs) + cols - 1) // cols
    cell_h = thumbs[0][1].height + label_h
    width = margin * 2 + cols * args.thumb_width + (cols - 1) * gap
    height = margin * 2 + rows * cell_h + (rows - 1) * gap

    sheet = Image.new("RGB", (width, height), (12, 10, 14))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except OSError:
        font = ImageFont.load_default()

    for i, (name, im) in enumerate(thumbs):
        x = margin + (i % cols) * (args.thumb_width + gap)
        y = margin + (i // cols) * (cell_h + gap)
        sheet.paste(im, (x, y))
        draw.rectangle([x, y, x + im.width - 1, y + im.height - 1], outline=(62, 52, 46), width=1)
        draw.text((x + 4, y + im.height + 7), f"СЛАЙД {i + 1:02d}  ·  {name}", fill=(215, 185, 130), font=font)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    if args.output.lower().endswith(".png"):
        sheet.save(args.output, "PNG", optimize=True)
    else:
        sheet.save(args.output, "JPEG", quality=91, optimize=True)
    print(f"wrote {args.output} ({len(thumbs)} slides, {cols}x{rows}, {width}x{height}px)")


if __name__ == "__main__":
    main()
