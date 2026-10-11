#!/usr/bin/env python3
"""Combine the four per-model GIF loops into one 2×2 preview for the deck."""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

KEYS = ("chestnut", "smartphone", "cart", "wallet")
LABELS = {"chestnut": "КАШТАН", "smartphone": "ТЕЛЕФОН", "cart": "КОРЗИНА", "wallet": "КОШЕЛЁК"}


def frames_for(source, key):
    image = Image.open(os.path.join(source, key + ".gif"))
    frames = []
    try:
        while True:
            frames.append(image.convert("RGB").copy())
            image.seek(len(frames))
    except EOFError:
        pass
    return frames


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default=os.path.join(here, "_anim"),
                        help="folder containing chestnut.gif, smartphone.gif, cart.gif and wallet.gif")
    parser.add_argument("output", nargs="?", default=os.path.join(here, "../../../exports/impulse-spending-animations-preview.gif"))
    args = parser.parse_args()

    loops = {key: frames_for(args.source, key) for key in KEYS}
    n = min(map(len, loops.values()))
    width = height = 760
    margin, gap = 18, 14
    cell = (width - 2 * margin - gap) // 2
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 22) if os.path.exists(font_path) else ImageFont.load_default()
    frames = []
    for frame_no in range(n):
        canvas = Image.new("RGB", (width, height), (17, 12, 16))
        draw = ImageDraw.Draw(canvas)
        for i, key in enumerate(KEYS):
            x = margin + (i % 2) * (cell + gap)
            y = margin + (i // 2) * (cell + gap)
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=16,
                                   fill=(28, 18, 22), outline=(95, 69, 45), width=2)
            draw.text((x + 16, y + 12), LABELS[key], font=font, fill=(227, 182, 99))
            im = loops[key][frame_no]
            max_w, max_h = cell - 30, cell - 62
            scale = min(max_w / im.width, max_h / im.height)
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)
            px = x + (cell - im.width) // 2
            py = y + 48 + (max_h - im.height) // 2
            canvas.paste(im, (px, py))
        frames.append(canvas)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=500,
                   loop=0, optimize=True, disposal=2)
    print(f"wrote {args.output} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
