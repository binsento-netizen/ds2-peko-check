"""Generic (non-game) unlock icons for the public viewer: catalog/generic_icons.json.

The game's own item pictures are copyrighted and stay private (assets_private/icons). The public viewer shows a
generic icon per kind of unlock instead, from game-icons.net (CC BY 3.0, credit per icon: assets/icons-generic/CREDITS.md).

  python -B catalog/build_generic_icons.py           # build catalog/generic_icons.json (+ CREDITS.md and
                                                     # design/icons-generic-preview.html), print coverage
  python -B catalog/build_generic_icons.py --fetch   # first download missing SVGs from the game-icons GitHub repo

Icons: assets/icons-generic/<name>.svg, monochrome, fill="currentColor" (the viewer tints them via CSS color),
black background square of the game-icons originals removed. SOURCES records author + original icon name.
Assignment: RULES_KEY (special cases) -> RULES_NAME (name / subrig keywords inside a category) -> RULES_CAT
(category / subcategory) -> "misc". Hidden unlocks (cat None) get no icon.
Output: {"icons": {name: "<svg ...>"}, "map": {catalogue key: icon name}}; path coordinates snapped to a 1-unit grid (STEP).
"""
import collections, json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons-generic"
SRC = ROOT / "catalog" / "unlock_items.json"
OUT = ROOT / "catalog" / "generic_icons.json"
RAW = "https://raw.githubusercontent.com/game-icons/icons/master/{}/{}.svg"
LICENCE = "https://creativecommons.org/licenses/by/3.0/"

# icon name -> (game-icons author folder, game-icons icon name)
SOURCES = {
    # weapons
    "handgun": ("skoll", "glock"),
    "rifle": ("skoll", "ak47"),
    "shotgun": ("delapouite", "sawed-off-shotgun"),
    "machine-gun": ("skoll", "machine-gun"),
    "sniper": ("skoll", "steyr-aug"),
    "grenade-launcher": ("lorc", "bolter-gun"),
    "rocket-launcher": ("delapouite", "missile-launcher"),
    "cannon": ("lorc", "ray-gun"),
    "bola": ("lorc", "bolas"),
    "tether": ("lorc", "grapple"),
    "turret": ("lorc", "sentry-gun"),
    "shield": ("lorc", "riot-shield"),
    "pizza": ("delapouite", "pizza-slice"),
    "grenade": ("lorc", "grenade"),
    "mine": ("lorc", "land-mine"),
    "melee": ("skoll", "telescopic-baton"),
    "airstrike": ("lorc", "cluster-bomb"),
    # body gear
    "skeleton": ("delapouite", "robot-leg"),
    "boots": ("lorc", "boots"),
    "gloves": ("delapouite", "gloves"),
    # equipment
    "blood-bag": ("delapouite", "medical-drip"),
    "antigravity": ("delapouite", "floating-platforms"),
    "oxygen-mask": ("lorc", "gas-mask"),
    "canteen": ("delapouite", "water-flask"),
    "thermal": ("delapouite", "thermometer-hot"),
    "spray": ("lorc", "spray"),
    "ladder": ("delapouite", "ladder"),
    "anchor": ("delapouite", "carabiner"),
    "guidepost": ("delapouite", "old-lantern"),
    "pcc": ("lorc", "auto-repair"),
    # backpack
    "backpack": ("delapouite", "backpack"),
    "ammo": ("sbed", "ammo-box"),
    "battery": ("sbed", "battery-pack"),
    "armor": ("skoll", "kevlar-vest"),
    "electric": ("sbed", "electric"),
    "charm": ("lorc", "gem-pendant"),
    "patch": ("lorc", "winged-emblem"),
    # outfits
    "hat": ("delapouite", "billed-cap"),
    "glasses": ("delapouite", "sunglasses"),
    "mask": ("delapouite", "carnival-mask"),
    "suit": ("lucasms", "shirt"),
    "bb-pod": ("skoll", "fetus"),
    "palette": ("delapouite", "palette"),
    # vehicles
    "truck": ("skoll", "flatbed"),
    "bike": ("delapouite", "aero-bike"),
    "tire": ("delapouite", "car-wheel"),
    "ship": ("delapouite", "cargo-ship"),
    "decal": ("delapouite", "stamper"),
    # structures
    "bridge": ("delapouite", "suspension-bridge"),
    "postbox": ("delapouite", "mailbox"),
    "safe-house": ("delapouite", "house"),
    "watchtower": ("delapouite", "watchtower"),
    "generator": ("delapouite", "power-generator"),
    "catapult": ("heavenly-dog", "catapult"),
    "structure": ("delapouite", "block-house"),
    # other kinds
    "apas": ("lorc", "processor"),
    "martial-arts": ("delapouite", "high-kick"),
    "hologram": ("lord-berandas", "holosphere"),
    "character": ("delapouite", "person"),
    "music": ("delapouite", "musical-notes"),
    "hot-spring": ("sbed", "hot-surface"),
    "crystal": ("lorc", "crystal-cluster"),
    "rest": ("delapouite", "bed"),
    "camera": ("delapouite", "photo-camera"),
    "cryptobiote": ("delapouite", "caterpillar"),
    "feature": ("delapouite", "upgrade"),
    "misc": ("delapouite", "cardboard-box"),
}
AUTHOR_NAMES = {"delapouite": "Delapouite", "lorc": "Lorc", "skoll": "Skoll", "sbed": "Sbed",
                "lucasms": "Lucas", "heavenly-dog": "HeavenlyDog", "lord-berandas": "Lord Berandas"}

# special cases by catalogue key (checked first)
RULES_KEY = {}
# (category or "*", regex on "name | subrig") -> icon; first match within the category wins
RULES_NAME = [
    ("Weapons", r"\| Magellan$", "airstrike"),  # DHV Magellan support weapons (fireworks, cluster bomb)
    ("Weapons", r"Handgun|Pistol", "handgun"),
    ("Weapons", r"Sniper", "sniper"),
    ("Weapons", r"Shotgun", "shotgun"),
    ("Weapons", r"Machine Gun", "machine-gun"),
    ("Weapons", r"Assault Rifle", "rifle"),
    ("Weapons", r"Grenade Launcher", "grenade-launcher"),
    ("Weapons", r"(?i)rocket", "rocket-launcher"),
    ("Weapons", r"Cannon", "cannon"),
    ("Weapons", r"Bola", "bola"),
    ("Weapons", r"Sticky Gun", "tether"),
    ("Weapons", r"Sentry", "turret"),
    ("Weapons", r"Shield", "shield"),
    ("Weapons", r"Pizza", "pizza"),
    ("Weapons", r"Mine\b", "mine"),
    ("Weapons", r"Electric Trap", "electric"),
    ("Weapons", r"Grenade|Bomb|Hologrenade", "grenade"),
    ("Equipment", r"Blood Bag", "blood-bag"),
    ("Equipment", r"Floating Carrier|Coffin Board", "antigravity"),
    ("Equipment", r"Oxygen Mask", "oxygen-mask"),
    ("Equipment", r"Canteen", "canteen"),
    ("Equipment", r"Thermal", "thermal"),
    ("Equipment", r"Spray", "spray"),
    ("Equipment", r"Ladder", "ladder"),
    ("Equipment", r"Climbing Anchor", "anchor"),
    ("Equipment", r"Guidepost", "guidepost"),
    ("Equipment", r"PCC", "pcc"),
    ("Backpack Attachments", r"Ammo", "ammo"),
    ("Backpack Attachments", r"Battery|Solar Generator", "battery"),
    ("Backpack Attachments", r"Antigravity", "antigravity"),
    ("Backpack Attachments", r"Protector", "armor"),
    ("Backpack Attachments", r"Electric", "electric"),
    ("Outfits", r"\| Hood\b|Hat|Cap|Bandana|Headband", "hat"),
    ("Outfits", r"\| Mask\b", "mask"),
    ("Vehicles", r"Tri-Cruiser|\| Moto\b", "bike"),
    ("Vehicles", r"Off-Roader|\| Truck\b", "truck"),
    ("Vehicles", r"Cannon|Machine Gun|Mortar|Launcher|Active Defense", "turret"),
    ("Vehicles", r"Battery", "battery"),
    ("Vehicles", r"Antigravity", "antigravity"),
    ("Vehicles", r"Electrical", "electric"),
    ("Vehicles", r"Armor", "armor"),
    ("Vehicles", r"Tires", "tire"),
    ("Structures", r"Bridge", "bridge"),
    ("Structures", r"Postbox", "postbox"),
    ("Structures", r"Safe House|Shelter", "safe-house"),
    ("Structures", r"Watchtower", "watchtower"),
    ("Structures", r"Generator", "generator"),
    ("Structures", r"Catapult", "catapult"),
    ("Melee techniques", r"Karate", "martial-arts"),
    ("Melee techniques", r"Pizza", "pizza"),
    ("Hot springs", r".", "hot-spring"),
    ("Features", r"Rest at", "rest"),
    ("Features", r"Bridge", "bridge"),
    ("Features", r"Catapult", "catapult"),
    ("Features", r"Backpack", "backpack"),
    ("Features", r"Magellan Color", "palette"),
    ("Features", r"Camera", "camera"),
    ("Features", r"Odradek Light", "guidepost"),
    ("Features", r"Jump Ramp", "structure"),
    ("Other", r"Signboard", "structure"),
    ("Other", r"biote|\| Grb", "cryptobiote"),
    ("Other", r"Strand", "tether"),
    ("Other", r"Harmonica", "music"),
    ("Other", r"Dollman Cam", "camera"),
]
# (category, subcategory or None = any) -> icon
RULES_CAT = {
    ("Weapons", "Melee"): "melee",
    ("Weapons", "Support weapons"): "airstrike",
    ("Weapons", "Grenades, bombs & traps"): "grenade",
    ("Weapons", None): "rifle",
    ("Skeletons", None): "skeleton",
    ("Boots", None): "boots",
    ("Equipment", "Gloves"): "gloves",
    ("Equipment", None): "pcc",
    ("Backpack Attachments", "Charms"): "charm",
    ("Backpack Attachments", None): "backpack",
    ("Patches", None): "patch",
    ("Outfits", "Hats & Hoods"): "hat",
    ("Outfits", "Glasses & Masks"): "glasses",
    ("Outfits", "Suits"): "suit",
    ("Outfits", "BB Pod patterns"): "bb-pod",
    ("Outfits", "Color schemes"): "palette",
    ("Vehicles", "DHV Magellan"): "ship",
    ("Vehicles", "Vehicle decals"): "decal",
    ("Vehicles", "Vehicles"): "truck",
    ("Vehicles", "Vehicle parts"): "truck",
    ("Structures", None): "structure",
    ("APAS enhancements", None): "apas",
    ("Melee techniques", None): "martial-arts",
    ("Holograms", None): "hologram",
    ("Character rewards", None): "character",
    ("Music", None): "music",
    ("Hot springs", None): "hot-spring",
    ("Collectibles", None): "crystal",
    ("Features", None): "feature",
    ("Other", None): "misc",
}


def assign(row):
    if row["key"] in RULES_KEY:
        return RULES_KEY[row["key"]]
    text = f'{row["name"]} | {row.get("subrig") or ""}'
    for cat, rx, icon in RULES_NAME:
        if cat in ("*", row["cat"]) and re.search(rx, text):
            return icon
    return RULES_CAT.get((row["cat"], row["sub"])) or RULES_CAT.get((row["cat"], None)) or "misc"


def clean(svg):
    """game-icons original -> monochrome currentColor SVG (background square dropped)."""
    svg = svg.replace('<path d="M0 0h512v512H0z"/>', "").replace(' fill="#fff"', "")
    if 'fill="currentColor"' not in svg:
        svg = svg.replace("<svg ", '<svg fill="currentColor" ', 1)
    return svg.strip() + "\n"


def fetch():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for name, (author, icon) in SOURCES.items():
        dst = ICON_DIR / f"{name}.svg"
        if dst.exists():
            continue
        with urllib.request.urlopen(RAW.format(author, icon), timeout=30) as r:
            raw = r.read().decode("utf-8")
        if raw.count("<path") != 2 or 'M0 0h512v512H0z' not in raw:
            sys.exit(f"{author}/{icon}: unexpected SVG structure, check by hand")
        dst.write_text(clean(raw), encoding="utf-8", newline="\n")
        print("fetched", name, "<-", f"{author}/{icon}")


NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")


STEP = 1  # coordinate grid in viewBox units (512 wide; 1 unit = 0.06 px at 32 px, checked visually)
ARGS = {"m": 2, "l": 2, "t": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "a": 7, "z": 0}


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)


def snap(v):
    return round(v / STEP) * STEP


def minify_path(d):
    """Snap path coordinates to a STEP grid and drop needless separators.

    Relative commands are snapped in absolute terms (exact pen position tracked next to the emitted, snapped one),
    so rounding errors do not add up along a long relative subpath.
    """
    toks = NUM.findall(d)
    i, out, prev = 0, [], ""
    pen, pen_s, start, start_s = [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]

    def emit(v):
        nonlocal prev
        s = fmt(v)
        if prev and not prev.isalpha() and not s.startswith("-") and not (s.startswith(".") and "." in prev):
            out.append(" ")
        out.append(s)
        prev = s

    cmd = ""
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            out.append(cmd)
            prev = cmd
            i += 1
            if cmd in "zZ":
                pen, pen_s = start[:], start_s[:]
                continue
        lc, rel, n = cmd.lower(), cmd.islower(), ARGS[cmd.lower()]
        args = [float(t) for t in toks[i:i + n]]
        if len(args) != n or any(t.isalpha() for t in toks[i:i + n]):
            sys.exit(f"bad path data near token {i}: {toks[i:i + n]}")
        if lc == "a" and any(toks[i + k] not in ("0", "1") for k in (3, 4)):
            sys.exit(f"compact arc flags not supported: {toks[i:i + n]}")  # would need flag-aware tokenising
        i += n
        base, base_s = (pen, pen_s) if rel else ([0.0, 0.0], [0.0, 0.0])
        if lc == "h":
            x = base[0] + args[0]; xs = snap(x)
            emit(xs - base_s[0]); pen, pen_s = [x, pen[1]], [xs, pen_s[1]]
        elif lc == "v":
            y = base[1] + args[0]; ys = snap(y)
            emit(ys - base_s[1]); pen, pen_s = [pen[0], y], [pen_s[0], ys]
        else:
            if lc == "a":
                for v in args[:2]:
                    emit(snap(v))
                emit(round(args[2]))
                emit(args[3]); emit(args[4])
                pairs = [args[5:7]]
            else:
                pairs = [args[k:k + 2] for k in range(0, n, 2)]
            for dx, dy in pairs:
                x, y = base[0] + dx, base[1] + dy
                xs, ys = snap(x), snap(y)
                emit(xs - base_s[0]); emit(ys - base_s[1])
            pen, pen_s = [x, y], [xs, ys]
        if lc == "m":
            start, start_s = pen[:], pen_s[:]
            cmd = "l" if rel else "L"  # extra pairs after M are line-tos
    return "".join(out)


def minify_svg(svg):
    paths = re.findall(r'<path d="([^"]+)"', svg)
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    d = "".join(minify_path(p) for p in paths)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" fill="currentColor"><path d="{d}"/></svg>'


def write_credits(used):
    lines = ["# Generic unlock icons: credits", "",
             "The public viewer shows these generic icons instead of the game's own item pictures (which are copyrighted",
             "and stay private). All icons come from [game-icons.net](https://game-icons.net)",
             "([source repo](https://github.com/game-icons/icons)) and are licensed under",
             f"[CC BY 3.0]({LICENCE}).", "",
             "Changes made: black background square removed, colour set to `currentColor` (tinted by the viewer),",
             "path coordinates snapped to a 1-unit grid (of 512) in `catalog/generic_icons.json`. Files here are renamed by meaning.", "",
             "One-line attribution (README / THIRD_PARTY_NOTICES):", "",
             "> Unlock icons by " + ", ".join(sorted({AUTHOR_NAMES[a] for a, _ in SOURCES.values()}))
             + " from [game-icons.net](https://game-icons.net), licensed under [CC BY 3.0](" + LICENCE + "); recoloured.",
             "", "| File | Original icon | Author | Licence |", "|---|---|---|---|"]
    for name, (author, icon) in sorted(SOURCES.items()):
        lines.append(f"| `{name}.svg` | [{icon}](https://game-icons.net/1x1/{author}/{icon}.html) | "
                     f"{AUTHOR_NAMES[author]} | [CC BY 3.0]({LICENCE}) |")
    unused = sorted(set(SOURCES) - used)
    if unused:
        lines += ["", "Not used by the current catalogue: " + ", ".join(unused) + "."]
    (ICON_DIR / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_preview(rows, mapping, icons):
    """design/icons-generic-preview.html: every icon + one example unlock per icon, on dark and light."""
    import html
    by_icon = {}
    for r in rows:
        if r["key"] in mapping:
            by_icon.setdefault(mapping[r["key"]], r)
    def cell(n):
        return f'<span class="ic">{icons[n]}</span>'
    grid = "".join(f'<figure>{cell(n)}<figcaption>{n}</figcaption></figure>' for n in sorted(icons))
    sample = "".join(
        f'<tr><td class="d">{cell(n)}</td><td class="l">{cell(n)}</td><td>{html.escape(r["name"])}</td>'
        f'<td>{html.escape(r["cat"])}{" / " + html.escape(r["sub"]) if r["sub"] else ""}</td><td><code>{n}</code></td></tr>'
        for n, r in sorted(by_icon.items(), key=lambda kv: (kv[1]["cat"], kv[1]["sub"] or "", kv[0])))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Generic unlock icons</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--dk:#0b1724;--dkfg:#7fe3f0;--lt:#f3f0e8;--ltfg:#1c2b3a}}
body{{margin:0;background:#18222d;color:#dbe6ef;font:14px system-ui,sans-serif;padding:16px}}
h1{{font-size:18px;margin:0 0 4px}} h2{{font-size:15px;margin:20px 0 8px}} p{{margin:0 0 8px;color:#9fb0bf}}
.panels{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:6px;padding:10px;border-radius:6px}}
.dark{{background:var(--dk);color:var(--dkfg)}} .light{{background:var(--lt);color:var(--ltfg)}}
figure{{margin:0;text-align:center;font-size:10px}} figure .ic svg{{width:40px;height:40px}}
figcaption{{opacity:.85;word-break:break-word}}
table{{border-collapse:collapse;width:100%}} td{{padding:3px 8px;border-bottom:1px solid #2a3846}}
td.d{{background:var(--dk);color:var(--dkfg)}} td.l{{background:var(--lt);color:var(--ltfg)}}
td .ic svg{{width:26px;height:26px;display:block}} code{{color:#9fb0bf}}
</style></head><body>
<h1>Generic unlock icons ({len(icons)})</h1>
<p>From game-icons.net, CC BY 3.0 (credits: assets/icons-generic/CREDITS.md). Built by catalog/build_generic_icons.py.</p>
<div class="panels"><div class="grid dark">{grid}</div><div class="grid light">{grid}</div></div>
<h2>One example unlock per icon ({len(by_icon)})</h2>
<table>{sample}</table>
</body></html>
"""
    (ROOT / "design" / "icons-generic-preview.html").write_text(page, encoding="utf-8", newline="\n")


def main():
    if "--fetch" in sys.argv:
        fetch()
    rows = json.load(open(SRC, encoding="utf-8"))
    mapping, cov = {}, collections.defaultdict(collections.Counter)
    for r in rows:
        if not r["cat"]:
            continue
        icon = assign(r)
        if icon not in SOURCES:
            sys.exit(f"rule gives unknown icon {icon!r} for {r['key']} {r['name']}")
        mapping[r["key"]] = icon
        cov[(r["cat"], r["sub"])][icon] += 1
    used = set(mapping.values())
    missing = [n for n in used if not (ICON_DIR / f"{n}.svg").exists()]
    if missing:
        sys.exit(f"missing SVGs (run with --fetch): {missing}")
    icons = {n: minify_svg((ICON_DIR / f"{n}.svg").read_text(encoding="utf-8")) for n in sorted(used)}
    OUT.write_text(json.dumps({"icons": icons, "map": dict(sorted(mapping.items()))}, ensure_ascii=False,
                              separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    write_credits(used)
    write_preview(rows, mapping, icons)

    visible = sum(1 for r in rows if r["cat"])
    print(f"{len(mapping)}/{visible} visible unlocks mapped ({len(rows) - visible} hidden skipped); "
          f"{len(icons)} icons used of {len(SOURCES)}; {OUT.name} {OUT.stat().st_size // 1024} KB")
    for (cat, sub), c in sorted(cov.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        print(f"  {cat}{' / ' + sub if sub else ''}: {sum(c.values())} -> "
              + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    if "misc" in used:
        print("  misc fallback:", ", ".join(sorted({r["name"] for r in rows if mapping.get(r["key"]) == "misc"})))


if __name__ == "__main__":
    main()
