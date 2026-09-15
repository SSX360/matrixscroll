"""Patch SSX360 README hero footer: version 0.10.0 and PQC overlay label."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"C:\Users\ryanj\.cursor\projects\c-Users-ryanj-OneDrive-Desktop-MATRIX-SCROLL-SSX360"
    r"\assets\c__Users_ryanj_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"bb22a03f7da2e0017eaa784b471f057a_images_image-c9736cb9-4e29-473a-855a-9134bfffcc68.png"
)
OUT = ROOT / "docs" / "assets" / "ssx360-trust-checkable.png"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/courbd.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
    ):
        p = Path(name)
        if p.is_file():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def _bg_fill(im: Image.Image, box: tuple[int, int, int, int], sample: tuple[int, int]) -> None:
    """Fill box with sampled CRT background and faint scanlines."""
    x0, y0, x1, y1 = box
    base = im.getpixel(sample)
    # Nudge toward black so residual glyphs disappear.
    base = tuple(max(0, c - 8) for c in base)
    draw = ImageDraw.Draw(im)
    draw.rectangle(box, fill=base)
    line = tuple(min(255, c + 10) for c in base)
    for y in range(y0, y1, 2):
        draw.line([(x0, y), (x1 - 1, y)], fill=line)


def main() -> None:
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    print(f"source={w}x{h}")

    # Measured from the source PNG (cyan OPEN VERIFIER row; green SIGNED SOURCES row).
    version_box = (48, 428, 530, 452)
    pqc_box = (640, 470, 980, 492)

    _bg_fill(im, version_box, sample=(70, 420))
    _bg_fill(im, pqc_box, sample=(700, 460))

    draw = ImageDraw.Draw(im)
    font = _font(16)

    cyan = (120, 215, 255)
    green = (70, 255, 130)

    left = "OPEN VERIFIER · MATRIXSCROLL 0.10.0"
    right = "SIGNED SOURCES · ED25519 + ML-DSA"

    draw.text((54, 432), left, fill=cyan, font=font)
    rb = draw.textbbox((0, 0), right, font=font)
    tw = rb[2] - rb[0]
    draw.text((980 - tw - 8, 474), right, fill=green, font=font)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")

    crop = im.crop((0, 400, w, 520))
    crop_path = OUT.parent / "_footer_check.png"
    crop.save(crop_path)
    print(f"wrote {crop_path}")


if __name__ == "__main__":
    main()
