"""Assemble viewer/index.html from template.html + viewer_data.json.  Optional: build_page.py DATA.json OUT.html"""
import sys
from pathlib import Path
from urllib.parse import quote
here = Path(__file__).resolve().parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "viewer_data.json"
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "index.html"
data = src.read_text(encoding="utf-8").replace("</", "<\\/")  # keep "</script>" out of the inline JSON
assets = here.parent / "assets"
logo = (assets / "logo.svg").read_text(encoding="utf-8").strip()             # animated header logo (design/build_logo.js)
favicon = "data:image/svg+xml," + quote((assets / "logo-static.svg").read_text(encoding="utf-8").strip(), safe=" =:/")   # quotes, <, > and # stay escaped inside the href
html = (here / "template.html").read_text(encoding="utf-8").replace("__LOGO__", logo).replace("__FAVICON__", favicon).replace("__DATA__", data)
if '"sample":null' in data:   # public build (opened as a local file): standards mode. The private build is published
    html = "<!doctype html>\n" + html   # as an artifact, whose host adds the doctype and page skeleton itself.
dst.write_text(html, encoding="utf-8", newline="\n")
print(f"{dst.name} {len(html.encode()):,} bytes")
