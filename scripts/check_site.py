"""Check local website links and anchors before publication."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "site"

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])

pages = {p.resolve(): Page(p) for p in ROOT.rglob("*.html")}
errors = []
if (ROOT / "index.html").resolve() not in pages:
    errors.append("Missing site/index.html")
for path, page in pages.items():
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
print(f"Validated links and anchors in {len(pages)} HTML pages.")
