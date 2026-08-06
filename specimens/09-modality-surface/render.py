"""Text -> PNG. Every image in this specimen is generated here, at runtime.

No binary fixture is committed. An injection specimen that shipped a PNG of
unknown provenance would be asking you to trust exactly the thing it is about
to argue you cannot inspect.

Two styles matter:

  normal   17px, near-black on white          ~19:1 contrast
  fine     9px, light grey on white           ~1.7:1 contrast

The second is the channel that has no text equivalent. A reader skims past it;
the model reads it at full weight. `contrast_ratio` computes the WCAG figure so
that claim is a measured number rather than an adjective.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (255, 255, 255)
WIDTH = 780
MARGIN = 28

# Tried in order. The fallback is Pillow's built-in bitmap face, so the specimen
# renders on a machine with no system fonts at all — legibility to the model is
# checked at runtime by the probe, not assumed here.
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)


@dataclass(frozen=True)
class Style:
    name: str
    size: int
    fill: tuple[int, int, int]


STYLES = {
    "normal": Style("normal", 17, (17, 17, 17)),
    "fine": Style("fine", 9, (200, 200, 200)),
}


def _luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.x relative luminance."""
    chans = []
    for c in rgb:
        s = c / 255
        chans.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    r, g, b = chans
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int] = BG) -> float:
    """WCAG contrast ratio, 1.0 (invisible) to 21.0 (black on white).

    4.5:1 is the AA threshold for body text. The `fine` style sits far below it,
    which is the point: it is under the floor for a human and irrelevant to a
    model that reads pixels.
    """
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def _wrap(text: str, font, max_px: int, draw: ImageDraw.ImageDraw) -> list[str]:
    lines: list[str] = []
    for para_line in text.split("\n"):
        words, cur = para_line.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            trial = f"{cur} {w}".strip()
            if draw.textlength(trial, font=font) <= max_px or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def render_blocks(blocks: list[tuple[str, str]], width: int = WIDTH) -> Image.Image:
    """Render (text, style_name) blocks to a page image.

    Deterministic: the same blocks produce byte-identical output on the same
    machine, so a fixture can be diffed rather than eyeballed.
    """
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    laid_out: list[tuple[str, Style, object, int]] = []
    y = MARGIN
    for text, style_name in blocks:
        style = STYLES[style_name]
        font = _font(style.size)
        line_h = int(style.size * 1.45)
        for line in _wrap(text, font, width - 2 * MARGIN, scratch):
            laid_out.append((line, style, font, y))
            y += line_h
        y += int(style.size * 0.8)

    img = Image.new("RGB", (width, y + MARGIN), BG)
    draw = ImageDraw.Draw(img)
    for line, style, font, top in laid_out:
        draw.text((MARGIN, top), line, font=font, fill=style.fill)
    return img


def render_png(blocks: list[tuple[str, str]], out_dir: Path, stem: str) -> bytes:
    """Render and persist. Returns the PNG bytes.

    Written without any text chunks — `pnginfo` is deliberately not passed. A
    PNG that carried its source text in a tEXt chunk would be readable by a
    string scanner, and this specimen's whole claim is that it is not.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.png"
    render_blocks(blocks).save(path, format="PNG", optimize=False)
    return path.read_bytes()


def png_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]
