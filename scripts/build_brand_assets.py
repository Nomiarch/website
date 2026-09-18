#!/usr/bin/env python3
"""Build Nomiarch's Signature assets from editable vector geometry.

Requires Python 3, Pillow, fontTools, and either CairoSVG or the Inkscape CLI.
The default headline fonts are DejaVu Sans installed on common Linux systems;
use --font-regular and --font-bold to specify the same fonts elsewhere.
SVGs contain outlines, not font references. Normal site builds do not run this.
"""

from __future__ import annotations

import argparse
import html
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "assets" / "brand"
DARK = "#0b1110"
MINT = "#b5efcd"
WHITE = "#f4f7f4"

# The distinctive shoulder takes two curves down from the horizontal top.
# Reuse this exact path in the wordmark, icon, avatar, and social card.
N = (
    "M0 32H54C67 32 72 37 75 45C77 49 79 50 84 51"
    "C98 56 104 67 104 83V120H76V84C76 67 65 54 50 54"
    "H31Q27 54 27 58V120H0Z"
)

# Custom lowercase outlines: 120-unit cap height, 88-unit x-height.
# Filled counters use evenodd so they remain correct in every renderer.
GLYPHS = {
    "n": (104, N),
    "o": (112,
        "M50 32H64C98 32 112 47 112 76C112 107 97 120 64 120"
        "H50C16 120 0 107 0 76C0 46 16 32 50 32Z"
        "M50 54C33 54 28 60 28 76C28 92 34 98 50 98H64"
        "C80 98 84 92 84 76C84 60 79 54 64 54Z"),
    "m": (146,
        "M0 32H42C54 32 63 34 70 38C79 33 89 32 101 32H108"
        "C134 32 146 45 146 69V120H119V72C119 59 114 54 101 54"
        "H99C87 54 84 57 84 66V120H57V72C57 59 52 54 39 54H31"
        "Q27 54 27 58V120H0Z"),
    "i": (28,
        "M14 0C22 0 28 6 28 13C28 20 22 26 14 26"
        "C6 26 0 20 0 13C0 6 6 0 14 0Z"
        "M0 32H28V120H0Z"),
    "a": (106,
        "M10 32H68C94 32 106 44 106 69V120H30"
        "C10 120 0 109 0 94C0 76 12 66 35 66H77V63"
        "C77 56 72 54 63 54H10Z"
        "M38 84C30 84 26 87 26 94C26 100 30 102 38 102H77"
        "V88Q77 84 73 84Z"),
    "r": (61,
        "M0 120V71C0 45 14 32 42 32H61V54H43"
        "C32 54 27 60 27 73V120Z"),
    "c": (88,
        "M49 32H88V54H51C34 54 28 60 28 76"
        "C28 92 34 98 51 98H88V120H49"
        "C17 120 0 104 0 76C0 47 17 32 49 32Z"),
    "h": (104,
        "M0 0H27V27Q27 32 32 32H54C67 32 72 37 75 45"
        "C77 49 79 50 84 51C98 56 104 67 104 83V120H76"
        "V84C76 67 65 54 50 54H31Q27 54 27 58V120H0Z"),
}
SPACING = [10, 10, 10, 10, 10, 10, 12]
WORD_WIDTH = sum(GLYPHS[c][0] for c in "nomiarch") + sum(SPACING)


def svg(body: str, width: int, height: int, title: str, desc: str = "") -> str:
    description = f"<desc>{html.escape(desc)}</desc>" if desc else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img">'
        f"<title>{html.escape(title)}</title>{description}{body}</svg>\n"
    )


def wordmark(fill: str, x: float = 0, y: float = 0, scale: float = 1) -> str:
    output = [f'<g fill="{fill}" fill-rule="evenodd" transform="translate({x} {y}) scale({scale})">']
    cursor = 0
    for index, char in enumerate("nomiarch"):
        width, path = GLYPHS[char]
        output.append(f'<path d="{path}" transform="translate({cursor} 0)"/>')
        cursor += width + (SPACING[index] if index < len(SPACING) else 0)
    output.append("</g>")
    return "".join(output)


def icon(fill: str, x: float, y: float, width: float) -> str:
    scale = width / 104
    return (
        f'<g transform="translate({x} {y}) scale({scale})">'
        f'<path fill="{fill}" d="{N}" transform="translate(0 -32)"/></g>'
    )


def text_path(text: str, font_path: Path, size: float, x: float, y: float,
              fill: str, tracking: float = 0) -> str:
    """Outline the headline; no installed font is required to display the SVG."""
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    cursor = 0.0
    paths = []
    for char in text:
        name = cmap[ord(char)]
        pen = SVGPathPen(glyph_set)
        glyph_set[name].draw(pen)
        path = pen.getCommands()
        if path:
            paths.append(f'<path d="{path}" transform="translate({cursor:.4f} 0)"/>')
        cursor += font["hmtx"].metrics[name][0] + tracking / scale
    font.close()
    return (
        f'<g aria-label="{html.escape(text, quote=True)}" fill="{fill}" '
        f'transform="translate({x} {y}) scale({scale:.8f} {-scale:.8f})">'
        + "".join(paths) + "</g>"
    )


def render(svg_source: str, size: tuple[int, int], opaque: bool = False) -> Image.Image:
    try:
        import cairosvg
    except ImportError:
        if not shutil.which("inkscape"):
            raise SystemExit("Install CairoSVG or Inkscape to render the PNG assets.")
        with tempfile.TemporaryDirectory(prefix="nomiarch-brand-") as directory:
            source = Path(directory) / "source.svg"
            target = Path(directory) / "render.png"
            source.write_text(svg_source, encoding="utf-8")
            subprocess.run(
                ["inkscape", str(source), "--export-type=png", f"--export-filename={target}",
                 f"--export-width={size[0] * 2}", f"--export-height={size[1] * 2}"],
                check=True, capture_output=True,
            )
            with Image.open(target) as opened:
                result = opened.convert("RGBA")
    else:
        raw = cairosvg.svg2png(bytestring=svg_source.encode(), output_width=size[0] * 2,
                              output_height=size[1] * 2)
        with Image.open(io.BytesIO(raw)) as opened:
            result = opened.convert("RGBA")
    result = result.resize(size, Image.Resampling.LANCZOS)
    if opaque:
        background = Image.new("RGB", size, DARK)
        background.paste(result, mask=result.getchannel("A"))
        return background
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-regular", type=Path,
                        default=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    parser.add_argument("--font-bold", type=Path,
                        default=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    args = parser.parse_args()
    for path in [args.font_regular, args.font_bold]:
        if not path.is_file():
            parser.error(f"Font not found: {path}")
    OUT.mkdir(parents=True, exist_ok=True)

    vectors = {}
    for name, color in [("wordmark-dark", DARK), ("wordmark-mint", MINT)]:
        vectors[name] = svg(wordmark(color), WORD_WIDTH, 120, "Nomiarch")
    vectors["icon"] = svg(icon(MINT, 0, 0, 104), 104, 88, "Nomiarch n symbol")
    vectors["favicon"] = svg(
        f'<rect width="64" height="64" rx="14" fill="{DARK}"/>'
        + icon(MINT, 12, 15, 40), 64, 64, "Nomiarch",
    )
    avatar = svg(
        f'<rect width="512" height="512" fill="{DARK}"/>'
        + icon(MINT, 111, 133, 290), 512, 512, "Nomiarch",
    )
    social = svg(
        f'<rect width="1200" height="630" fill="{DARK}"/>'
        + wordmark(MINT, 64, 64, 310 / WORD_WIDTH)
        + text_path("Infrastructure & AI.", args.font_bold, 46, 64, 284, WHITE, -0.4)
        + text_path("Under your authority.", args.font_bold, 46, 64, 350, MINT, -0.4)
        + icon(MINT, 924, 223, 208)
        + text_path("nomiarch.com", args.font_regular, 25, 64, 554, WHITE, 1.1),
        1200, 630, "Nomiarch — Infrastructure & AI. Under your authority.",
        "Nomiarch's Signature wordmark and n symbol on a dark background. nomiarch.com",
    )
    vectors["social-preview"] = social
    for name, content in vectors.items():
        (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    for filename, source, dimensions, opaque in [
        ("favicon-32.png", vectors["favicon"], (32, 32), False),
        ("apple-touch-icon.png", avatar, (180, 180), True),
        ("avatar.png", avatar, (512, 512), True),
        ("social-preview-v1.png", social, (1200, 630), True),
    ]:
        rendered = render(source, dimensions, opaque)
        rendered.save(OUT / filename, format="PNG", optimize=True)
        print(f"{filename}: {dimensions[0]}×{dimensions[1]}, {(OUT / filename).stat().st_size:,} bytes")
    print(f"Wordmark: {WORD_WIDTH}×120, ratio {WORD_WIDTH / 120:.4f}:1")


if __name__ == "__main__":
    main()
