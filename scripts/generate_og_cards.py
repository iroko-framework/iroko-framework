#!/usr/bin/env python3
"""
Iroko Framework OG Image Generator  --  companion to Per Medjat's generate-og.py
=================================================================================
Generates one distinct social-preview card (1200x630 PNG) per page on
ontology.irokosociety.org: the homepage, the vocabulary index, the full term
index, each documentation page, the white paper, and all 18 published
modules (drawn from scripts/iroko_config.MODULE_CONFIG).

Run from the iroko-framework repo root:

    pip install Pillow
    python scripts/generate_og_cards.py           # skip existing PNGs, always update HTML tags
    python scripts/generate_og_cards.py --force    # regenerate all PNGs

Fonts are fetched from Google Fonts on first run and cached in fonts-onto/.
If that download is blocked, common Windows system fonts are used as a
fallback so the script still produces usable (if not pixel-identical) cards.
"""

import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("pillow not installed  -- run: pip install Pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iroko_config import MODULE_CONFIG  # noqa: E402

W, H = 1200, 630

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
# The "family" of IHS sites each hold a distinct identity color: IHS-Website
# is deep green (#1E4A27), IAO-Website is navy (#0F2044), Per Medjat runs a
# purple/terracotta/lapis scheme by section. The ontology site's own
# stylesheet (assets/iroko-style.css) already carries a muted violet
# (--purple: #5c3d8f) used for module tagging but never claimed as a site
# identity color. INDIGO below deepens that same hue for OG-card contrast --
# coordinated with the family, not a new arbitrary color, and a fit for a
# semantic-vocabulary project: structured, a little esoteric, legible.
INDIGO       = (43, 30, 74)         # #2B1E4A  -- OG card background
PALE_GOLD    = (241, 231, 201)      # #F1E7C9  -- title text (family paper/gold warmth)
GOLD_LABEL   = (214, 178, 110)      # #D6B26E  -- eyebrow label
CREAM_BOX    = (246, 241, 219)      # #F6F1DB  -- logo plate (matches Per Medjat's PAPER)


def _blend(fg, alpha, bg):
    return tuple(int(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


COL_SUB    = _blend(PALE_GOLD, 0.86, INDIGO)   # brightened for handheld/small-screen legibility
COL_DOMAIN = _blend(PALE_GOLD, 0.45, INDIGO)   # quieter footer tone

BASE_URL  = "https://ontology.irokosociety.org"
LOGO_PATH = Path("assets/IHS-Logo.jpg")
FORCE     = "--force" in sys.argv

LOGO_BOX                = dict(x=75, y=180, w=269, h=269)
TEXT_X_LOGO             = LOGO_BOX["x"] + LOGO_BOX["w"] + 75
RIGHT_PAD               = 72
LABEL_Y                 = 170
TITLE_OFFSET_FROM_LABEL = 38

SZ_LABEL  = 18
SZ_TITLE  = 46
SZ_SUB    = 25
SZ_DOMAIN = 22

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
# Space Grotesk (bold) for the title: a structured geometric sans with a
# semantic-web / data-schema feel, distinct from the site's inscriptional
# display serif (Cinzel) used for prose headings elsewhere on the site.
# Source Sans 3 for label/subtitle/domain: already the family's shared sans
# (IHS-Website, IAO-Website, and iroko-style.css's own --font-sans), so the
# card reads as part of the family even with a new title face and color.
_GOOGLE_SPECS = {
    "grotesk_bold":  ("Space Grotesk",  "700", "0"),
    "sourcesans":    ("Source Sans 3",  "400", "0"),
    "sourcesans_it": ("Source Sans 3",  "400", "1"),
}
_WIN_FALLBACKS = {
    "grotesk_bold":  ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "sourcesans":    ["C:/Windows/Fonts/calibri.ttf",  "C:/Windows/Fonts/segoeui.ttf",  "C:/Windows/Fonts/arial.ttf"],
    "sourcesans_it": ["C:/Windows/Fonts/calibrii.ttf", "C:/Windows/Fonts/segoeuii.ttf", "C:/Windows/Fonts/ariali.ttf"],
}
_font_cache: dict = {}
FONTS = Path("fonts-onto")
FONTS.mkdir(exist_ok=True)


def _download_font(key: str) -> Optional[Path]:
    dest = FONTS / f"{key}.ttf"
    if dest.exists() and dest.stat().st_size > 4000:
        return dest
    if dest.exists():
        dest.unlink()
    family, weight, ital = _GOOGLE_SPECS[key]
    css_url = (
        "https://fonts.googleapis.com/css2"
        f"?family={family.replace(' ', '+')}:ital,wght@{ital},{weight}"
    )
    headers = {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"}
    print(f"  Downloading font: {family} weight={weight} ital={ital} ...")
    try:
        req = urllib.request.Request(css_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            css = r.read().decode()
        m = re.search(r"url\((https?://[^)]+\.ttf)\)", css)
        if m:
            ttf_url = m.group(1).strip()
            urllib.request.urlretrieve(ttf_url, dest)
            if dest.stat().st_size > 4000:
                print(f"  Saved  -> fonts-onto/{key}.ttf ({dest.stat().st_size} bytes)")
                return dest
            dest.unlink()
            print(f"  WARNING: downloaded {family} too small, skipping")
        else:
            print(f"  WARNING: no .ttf URL in CSS for {family}")
    except Exception as e:
        print(f"  WARNING: could not download {family}: {e}")
    for fallback in _WIN_FALLBACKS.get(key, []):
        fb = Path(fallback)
        if fb.exists():
            print(f"  Using system fallback: {fallback}")
            return fb
    return None


def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    p = _download_font(key)
    path = str(p) if p else None
    f = None
    if path:
        try:
            f = ImageFont.truetype(path, size)
        except Exception as e:
            print(f"  WARNING: truetype() failed for {key} at {path}: {e}")
    if f is None:
        for emergency in ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
            try:
                f = ImageFont.truetype(emergency, size)
                print(f"  EMERGENCY fallback: {emergency} at {size}pt")
                break
            except Exception:
                pass
    if f is None:
        print(f"  CRITICAL: no font loaded for {key} at {size}pt -- output broken")
        f = ImageFont.load_default()
    _font_cache[cache_key] = f
    return f


# ---------------------------------------------------------------------------
# Text layout helpers
# ---------------------------------------------------------------------------
def _text_w(draw, text, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _text_h(draw, text, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def wrap_text(draw, text, font, max_w) -> list:
    lines = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if _text_w(draw, candidate, font) <= max_w:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def draw_wrapped(draw, text, font, x, y, max_w, color, leading_mult=1.25) -> int:
    for line in wrap_text(draw, text, font, max_w):
        draw.text((x, y), line, font=font, fill=color)
        y += int(_text_h(draw, line, font) * leading_mult)
    return y


def auto_size_title(draw, title, max_w):
    size = SZ_TITLE
    while size >= 24:
        f = get_font("grotesk_bold", size)
        if len(wrap_text(draw, title, f, max_w)) <= 3:
            return f, size
        size -= 4
    return get_font("grotesk_bold", 24), 24


def render_logo_panel(img: Image.Image) -> int:
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = LOGO_BOX["x"], LOGO_BOX["y"], LOGO_BOX["w"], LOGO_BOX["h"]
    draw.rectangle([bx, by, bx + bw, by + bh], fill=CREAM_BOX)
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGB").resize((bw, bh), Image.LANCZOS)
        img.paste(logo, (bx, by))
    return TEXT_X_LOGO


def make_og_image(page: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), color=INDIGO)
    draw = ImageDraw.Draw(img)
    text_x = render_logo_panel(img)
    max_w = W - text_x - RIGHT_PAD

    f_label = get_font("sourcesans", SZ_LABEL)
    draw.text((text_x, LABEL_Y), page["label"], font=f_label, fill=GOLD_LABEL)

    f_title, _ = auto_size_title(draw, page["title"], max_w)
    title_y = LABEL_Y + TITLE_OFFSET_FROM_LABEL + _text_h(draw, "A", f_label)
    title_end = draw_wrapped(draw, page["title"], f_title, text_x, title_y, max_w, PALE_GOLD, 1.18)

    f_sub = get_font("sourcesans_it", SZ_SUB)
    draw_wrapped(draw, page["subtitle"], f_sub, text_x, title_end + 20, max_w, COL_SUB, 1.45)

    f_dom = get_font("sourcesans", SZ_DOMAIN)
    domain = "ontology.irokosociety.org"
    dh = _text_h(draw, domain, f_dom)
    draw.text((text_x, H - 42 - dh), domain, font=f_dom, fill=COL_DOMAIN)
    return img


# ---------------------------------------------------------------------------
# Page registry
# ---------------------------------------------------------------------------
PAGES = [
    dict(file="index.html", slug="og-onto-home",
         label="IROKO FRAMEWORK",
         title="Iroko Framework",
         subtitle="Semantic vocabularies for Afro-Atlantic\nsacred knowledge systems",
         og_url=f"{BASE_URL}/"),
    dict(file="vocab/index.html", slug="og-onto-vocab",
         label="IROKO FRAMEWORK · VOCABULARIES",
         title="Controlled Vocabularies",
         subtitle="Sixteen modules of open access vocabulary\nfor Afro-Atlantic sacred knowledge systems",
         og_url=f"{BASE_URL}/vocab/"),
    dict(file="vocab/iroko-index.html", slug="og-onto-fullindex",
         label="IROKO FRAMEWORK · FULL INDEX",
         title="Full Vocabulary Index",
         subtitle="Every class, property, and concept across\nall published modules",
         og_url=f"{BASE_URL}/vocab/iroko-index.html"),
    dict(file="vocab/iroko-termlist.html", slug="og-onto-fullindex",
         label="IROKO FRAMEWORK · FULL INDEX",
         title="Full Vocabulary Index",
         subtitle="Every class, property, and concept across\nall published modules",
         og_url=f"{BASE_URL}/vocab/iroko-termlist.html"),
    dict(file="docs/index.html", slug="og-onto-docs",
         label="IROKO FRAMEWORK · DOCUMENTATION",
         title="Documentation",
         subtitle="Architecture, contribution guidelines, and\nvocabulary reuse guidance",
         og_url=f"{BASE_URL}/docs/"),
    dict(file="docs/ARCHITECTURE.html", slug="og-onto-architecture",
         label="DOCUMENTATION · TECHNICAL ARCHITECTURE",
         title="Technical Architecture",
         subtitle="Module combination patterns and the\naccess-level enforcement contract",
         og_url=f"{BASE_URL}/docs/ARCHITECTURE.html"),
    dict(file="docs/CONTRIBUTING.html", slug="og-onto-contributing",
         label="DOCUMENTATION · CONTRIBUTING",
         title="Contributing Guide",
         subtitle="How to propose changes to the\nIroko Framework vocabulary",
         og_url=f"{BASE_URL}/docs/CONTRIBUTING.html"),
    dict(file="docs/REUSE.html", slug="og-onto-reuse",
         label="DOCUMENTATION · VOCABULARY REUSE",
         title="Vocabulary Reuse Guide",
         subtitle="Terms of reuse for the Iroko Framework's\nCC0 vocabulary modules",
         og_url=f"{BASE_URL}/docs/REUSE.html"),
    dict(file="whitepaper/index.html", slug="og-onto-whitepaper",
         label="IROKO FRAMEWORK · WHITE PAPER",
         title="White Paper",
         subtitle="The postcustodial argument for the\nIroko Framework's design",
         og_url=f"{BASE_URL}/whitepaper/"),
]

_LAYER_LABELS = {
    "Foundation": "FOUNDATION MODULE",
    "Governance": "GOVERNANCE LAYER MODULE",
    "Domain":     "DOMAIN MODULE",
    "Alignment":  "ALIGNMENT MODULE",
}

def _no_emdash(text: str) -> str:
    """OG card titles use a middot instead of an em dash as separator."""
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s*—\s*", " · ", text)
    text = re.sub(r"\s*--\s*", " · ", text)
    return text


def _clean_subtitle(text: str) -> str:
    """Iroko/IHS writing convention avoids 'diaspora'/'diasporic' -- the term
    carries assumptions about exile and return that don't apply here. See
    the framework's own iroko-sankofa module note on self-description terms;
    this substitution keeps the card copy consistent with that convention."""
    text = re.sub(r"\bdiaspora returns\b", "Atlantic-crossing returns", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdiasporic\b", "Atlantic-crossing", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdiaspora\b", "Atlantic-crossing", text, flags=re.IGNORECASE)
    return text


for stem, cfg in MODULE_CONFIG.items():
    PAGES.append(dict(
        file=f"vocab/{stem}.html",
        slug=f"og-onto-{stem.replace('iroko-', '')}",
        label=f"{_LAYER_LABELS.get(cfg['layer'], 'MODULE')} · IROKO FRAMEWORK",
        title=_no_emdash(cfg["title"]),
        subtitle=_clean_subtitle(cfg["subtitle"]),
        og_url=f"{BASE_URL}/vocab/{stem}.html",
    ))


# ---------------------------------------------------------------------------
# HTML tag injection -- surgical: only touches og:image / twitter:image and
# the three og:image:* dimension/type tags. Leaves og:title, og:description,
# and every other tag exactly as-is.
# ---------------------------------------------------------------------------
def update_image_tags(html_path: Path, png_filename: str) -> bool:
    if not html_path.exists():
        return False
    src = html_path.read_text(encoding="utf-8")
    og_image = f"{BASE_URL}/assets/{png_filename}"

    new_src, n1 = re.subn(
        r'(<meta property="og:image" content=")[^"]*(")',
        rf'\g<1>{og_image}\g<2>', src, count=1,
    )
    new_src, n2 = re.subn(
        r'(<meta name="twitter:image" content=")[^"]*(")',
        rf'\g<1>{og_image}\g<2>', new_src, count=1,
    )
    if n1 == 0 and n2 == 0:
        return False
    html_path.write_text(new_src, encoding="utf-8")
    return True


def main():
    print("Iroko Framework OG Image Generator")
    print("=" * 50)
    print(f"Mode: {'--force' if FORCE else 'incremental'}\n")
    print("Checking fonts ...")
    for key in _GOOGLE_SPECS:
        p = _download_font(key)
        print(f"  {key:15s} -> {p or 'NOT FOUND'}")

    assets = Path("assets")
    assets.mkdir(exist_ok=True)
    seen_slugs = set()
    generated, updated = [], []

    for page in PAGES:
        html_path = Path(page["file"])
        png_filename = f"{page['slug']}.png"
        png_path = assets / png_filename
        print(f"\n[{page['file']}]")
        if not html_path.exists():
            print("  SKIP (file not found)")
            continue
        if (not png_path.exists() or FORCE) and page["slug"] not in seen_slugs:
            print(f"  Generating {png_filename} ...")
            img = make_og_image(page)
            img.save(str(png_path), "PNG", optimize=True)
            print(f"  Saved -> assets/{png_filename}")
            generated.append(png_filename)
        else:
            print(f"  PNG: {png_filename} exists (use --force to regenerate)")
        seen_slugs.add(page["slug"])
        if update_image_tags(html_path, png_filename):
            print(f"  Tags: updated {page['file']}")
            updated.append(page["file"])
        else:
            print(f"  Tags: no og:image/twitter:image tags found in {page['file']} (skipped)")

    print(f"\n{'=' * 50}")
    print(f"Generated {len(generated)} PNG(s), updated {len(updated)} HTML file(s)")
    print("Done. Review, then commit assets/og-onto-*.png and the updated HTML files.")


if __name__ == "__main__":
    main()
