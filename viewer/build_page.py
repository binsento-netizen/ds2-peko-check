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
favicon = "data:image/svg+xml," + quote((assets / "logo-kit/logo-minimal-color.svg").read_text(encoding="utf-8").strip(), safe=" =:/")   # tab icon: the minimal mark (made for 16-32 px); quotes, <, > and # stay escaped
html = (here / "template.html").read_text(encoding="utf-8")
# the Leaflet styles and code between the MAP markers are only used by the game-map build (--map); drop them otherwise
for start, end in (("<!--MAP-CSS-->\n", "<!--/MAP-CSS-->\n"), ("  /*MAP-JS*/\n", "  /*/MAP-JS*/\n")):
    i, j = html.index(start), html.index(end)
    html = html[:i] + (html[i + len(start):j] if '"map":null' not in data else "") + html[j + len(end):]
html = html.replace("__LOGO__", logo).replace("__FAVICON__", favicon).replace("__DATA__", data)
if '"sample":null' in data:   # public build (opened as a local file): standards mode. Builds with an embedded sample
    html = "<!doctype html>\n" + html   # save are hosted elsewhere, and that host adds the doctype.
dst.write_text(html, encoding="utf-8", newline="\n")
print(f"{dst.name} {len(html.encode()):,} bytes")
