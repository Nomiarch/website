"""Check website links and social-preview metadata before publication."""
from html.parser import HTMLParser
from pathlib import Path
import struct
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "site"

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = set()
        self.meta = {}
        self.canonical = None
        self.in_head = False
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head":
            self.in_head = True
        if tag == "meta" and self.in_head:
            key = attrs.get("property", attrs.get("name"))
            self.meta.setdefault(key, []).append(attrs.get("content", ""))
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False

pages = {p.resolve(): Page(p) for p in ROOT.rglob("*.html")}
errors = []
if (ROOT / "index.html").resolve() not in pages:
    errors.append("Missing site/index.html")
for path, page in pages.items():
    if "noindex" not in ",".join(page.meta.get("robots", [])):
        required = ("og:title", "og:description", "og:type", "og:url", "og:site_name",
                    "og:image", "og:image:type", "og:image:width", "og:image:height",
                    "og:image:alt", "twitter:card", "twitter:image", "twitter:image:alt")
        for key in required:
            values = page.meta.get(key, [])
            if len(values) != 1 or not values[0].strip():
                errors.append(f"{path.relative_to(ROOT)}: expected one nonempty {key} in head")
        def meta(key):
            return page.meta.get(key, [""])[0]
        if meta("twitter:card") != "summary_large_image":
            errors.append(f"{path.name}: expected a large-image social card")
        if meta("og:url") != page.canonical or not (page.canonical or "").startswith("https://nomiarch.com/"):
            errors.append(f"{path.name}: social URL must match the HTTPS canonical URL")
        image_url = urlsplit(meta("og:image"))
        if image_url.scheme != "https" or image_url.netloc != "nomiarch.com" or image_url.query or image_url.fragment:
            errors.append(f"{path.name}: preview must use an absolute HTTPS image on nomiarch.com")
        else:
            preview = (ROOT / unquote(image_url.path).lstrip("/")).resolve()
            if not preview.is_relative_to(ROOT.resolve()) or not preview.is_file():
                errors.append(f"{path.name}: preview image is missing from the deployed site")
            else:
                data = preview.read_bytes()
                if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
                    errors.append(f"{path.name}: expected a PNG preview")
                else:
                    width, height = struct.unpack(">II", data[16:24])
                    if (str(width), str(height)) != (meta("og:image:width"), meta("og:image:height")):
                        errors.append(f"{path.name}: preview dimensions do not match metadata")
                    if (width, height) != (1200, 630) or len(data) > 5_000_000:
                        errors.append(f"{path.name}: preview must be 1200x630 and under 5 MB")
        if meta("og:image:type") != "image/png" or meta("twitter:image") != meta("og:image"):
            errors.append(f"{path.name}: social image metadata is inconsistent")
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        local = unquote(url.path)
        target = path if not local else (ROOT / local.lstrip("/") if local.startswith("/") else path.parent / local)
        target = target.resolve()
        if not target.is_relative_to(ROOT.resolve()):
            errors.append(f"{path.name}: link escapes site: {link}")
            continue
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"{path.relative_to(ROOT)}: missing target: {link}")
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f"{path.relative_to(ROOT)}: missing anchor: {link}")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Validated links, anchors, and social-preview metadata in {len(pages)} HTML pages.")
