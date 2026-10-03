"""Build viewer/viewer_data.json: order catalogue, unlock catalogue and one sample save (read-only)."""
import base64, csv, glob, json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ds2_decode import decode, PNG_MAGIC
from ds2_savestate import R, SaveState
from ds2lib import load

# optional example save embedded in the page: `--sample PATH`. Without it the page starts empty (public build).
args = sys.argv[1:]
SAMPLE = args[args.index("--sample") + 1] if "--sample" in args else None
OUT = Path(args[args.index("--out") + 1]) if "--out" in args else ROOT / "viewer/viewer_data.json"
# public build: an example save the visitor can open on request (`--example JSON`, made with `--sample SAVE --write-example JSON`;
# the example has no thumbnail and only the short file name)
EXAMPLE = args[args.index("--example") + 1] if "--example" in args else None
WRITE_EXAMPLE = args[args.index("--write-example") + 1] if "--write-example" in args else None
# optional map (private build only, game-derived): `--map assets_private/map` (made by tools/build_map.py)
MAP = Path(args[args.index("--map") + 1]) if "--map" in args else None
# optional item pictures (private build only, game-derived): `--icons assets_private/icons` (tools/odradek/build_icons.py)
ICONS = Path(args[args.index("--icons") + 1]) if "--icons" in args else None

# order catalogue: every field from the game's own data (catalog/build_catalog.py <- catalog/missions_game.csv);
# all 474 numbered orders have a mission id, so no community-guide fallback rows are needed any more
cat = json.load(open(ROOT / "catalog/mission_catalog.json", encoding="utf-8"))
ids_by_type = json.load(open(ROOT / "catalog/ids_by_type.json"))
kind_of = {i: int(t) for t, lst in ids_by_type.items() for i in lst}          # save mission type per internal ID
game8 = {int(k): v for k, v in json.load(open(ROOT / "catalog/game8_order_pages.json")).items()}  # main orders 1-48
SECTION = {"Main": "M", "Standard": "S", "Sub": "U"}
orders = [[int(k), v["no"], SECTION[v["section"]], v["Order"], v["From"], v["To"], v["Cargo"], v["confidence"][0], v.get("Episode", ""),
           kind_of.get(int(k), 0), game8.get(v["no"]) if v["section"] == "Main" else None] for k, v in cat.items()]

# unlock catalogue: game data only (catalog/unlock_items.json from catalog/build_unlock_items.py; docs/UNLOCKS_GAME.md).
# Names are the game's own English text; categories come from the game's fields (catalog/fabrication_categories.py).
sys.path.insert(0, str(ROOT / "catalog"))
from fabrication_categories import ABOUT

# [key, English name ("" = none: the viewer shows "Unnamed entry"), "", usage, e = game text / x = no name, cat, sub, tag]
recipes = [[int(it["key"], 16), it["name"], "", it["usage"], "e" if it["name"] else "x", it["cat"], it["sub"], it.get("tag", "")]
           for it in json.load(open(ROOT / "catalog/unlock_items.json", encoding="utf-8"))]

# APAS enhancement catalogue (catalog/apas_game.json from catalog/build_apas.py): [hash, name, points, category, unlock keys, step]
APAS = [r for r in json.load(open(ROOT / "catalog/apas_game.json", encoding="utf-8"))] if (ROOT / "catalog/apas_game.json").exists() else []
apas_cat = [[int(r["hash"], 16), r["name"], r["points"], r["category"], [int(k, 16) for k in r["unlock_keys"]], r["step"]] for r in APAS if r["points"] > 0]

# cargo (section 0aa0d44e, tools/review_cargo.py): baggage NameCode -> [English name, raw-material amount or 0], and
# private-locker container w0 -> [facility code, name]. Game text only (catalog/baggage_names.json).
import review_cargo
_bag = json.load(open(ROOT / "catalog/baggage_names.json", encoding="utf-8"))
bags = {int(k, 16): [b["name"], 1 if b["contents_type"] == "RawMaterial" else 0] for k, b in _bag.items() if b["name"]}   # 1 = material (amount per item)
_facn = {int(r["code"]): r["name"] for r in csv.DictReader(open(ROOT / "catalog/facilities_game.csv", encoding="utf-8"))}
_facn[300] = "DHV Magellan"
lockers = {w0: [code, _facn.get(code, f"Facility {code}")] for w0, code in review_cargo.FACILITY_LOCKERS.items()}


def cargo_of(path):
    """[where, baggage key, material amount] per item: "eq" = Sam equipped, "bp" = backpack, "L:<w0>" = a private locker (same rules as the viewer)."""
    out = []
    for it in review_cargo.inspect(path)["items"]:
        kind, w0, w1, w2 = it["container"].split()
        where = ("eq" if kind == "00" and w0 == review_cargo.EQUIPPED and w1 == review_cargo.SAM else
                 "bp" if kind == "34" and w1 == review_cargo.SAM else
                 "L:" + w0 if kind == "1f" and w2 == review_cargo.PRIVATE and w1 not in (review_cargo.STRUCTURE, review_cargo.WORLDSTORE) else None)
        if where and int(it["baggage"], 16) in bags:
            out.append([where, int(it["baggage"], 16), it["amount"] or 0])
    return out


def read_sample(path):
    raw = open(path, "rb").read()
    meta, payload = load(path)
    thumb = next(dec for (_, _, dec, _) in decode(raw)[3] if dec.startswith(PNG_MAGIC))
    s = SaveState(payload)
    sb = s.section_bytes()
    sec = sb[0x4AFA625B]
    pos, missions = 8, []
    for _ in range(struct.unpack_from("<I", sec, 4)[0]):
        op, od, st = sec[pos + 4], sec[pos + 5], struct.unpack_from("<H", sec, pos + 6)[0]
        mid, up = struct.unpack_from("<II", sec, pos + 12)
        missions.append([mid, up & 0x3F, op, od, st])
        pos += 84 + struct.unpack_from("<I", sec, pos + 0x4E)[0]
    c = sb[0x3EF4DC4D]
    r = R(c, 4); n = r.vint(); r.vint()
    flags = [list(struct.unpack_from("<II", c, r.pos + 8 * i)) for i in range(n)]
    text = [x.decode("utf-8", "replace") for x in re.findall(rb"[\x20-\x7e\x80-\xff]{4,}", meta)]
    from review_routes import parse_routes  # section 48ea52a4: map route history, [mode, x0, y0, x1, y1, ...] per segment
    routes = [[seg["mode"] or 0, [c for p in seg["points"] for c in p[:2]]] for seg in parse_routes(sb[0x48EA52A4])]
    lv = sb.get(0x73DACF23, b"")   # facility connection levels: 112-byte records from +106 (u32 code, u16 index, u16 level)
    # per facility: code, connection level, six material stocks (stored 96 bytes before the code; tools/review_facilities.py)
    levels = [list(struct.unpack_from("<I2xH", lv, o)) + [list(struct.unpack_from("<12I", lv, o - 96)[0::2])]
              for o in range(106, min(len(lv) - 7, 106 + 49 * 112), 112)]
    import hashlib
    n = struct.unpack_from("<I", payload, 0x1FC)[0]
    dg = bytearray(hashlib.md5(payload[0x200:0x200 + n]).digest()); dg[0] ^= 0x06
    verified = bytes(dg) == payload[0x1EC:0x1FC]   # the save's own integrity check (same as the viewer's)
    st = sb.get(0x202659D5, b"")   # likes: +4 from NPCs, +12 from other porters, +44 given (FINDINGS "Test session 2026-10-01")
    likes = list(struct.unpack_from("<I", st, o)[0] for o in (4, 12, 44)) if len(st) >= 48 else None
    from review_apas import parse_apas   # section 69049449: APAS enhancements the player has, [hash, developed]
    apas_recs = parse_apas(sb.get(0x69049449, b""), APAS)[0] if APAS else []
    apas = [[int(r["hash"], 16), int(r["developed"])] for r in apas_recs if r["points"] > 0]
    ck = sb.get(0x3926C2C4, b"")   # in-game clock: +4 f32 hour of day, +8 u32 day (same rule as the viewer)
    clock = [struct.unpack_from("<I", ck, 8)[0], struct.unpack_from("<f", ck, 4)[0]] if len(ck) >= 12 else None
    sample = dict(name=Path(path).name.split("_")[-1], version=s.version, playtime=s.playtime, meta=text[:6],
                  missions=missions, recipes=flags, routes=routes, levels=levels, likes=likes, apas=apas, clock=clock, cargo=cargo_of(path), verified=verified, thumb="data:image/png;base64," + base64.b64encode(thumb).decode())
    return sample, missions


sample, missions = read_sample(SAMPLE) if SAMPLE else (None, [])
if WRITE_EXAMPLE and sample:
    Path(WRITE_EXAMPLE).write_text(json.dumps(dict(sample, thumb=None), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("example written:", WRITE_EXAMPLE)
example = json.load(open(EXAMPLE, encoding="utf-8")) if EXAMPLE else None
observed = set(json.load(open(ROOT / "catalog/unlock_observed.json")))   # keys with the unlock bit in any corpus save
tracked = sorted({f"{r[5]}|{r[6] or ''}" for r in recipes if r[5] and r[0] in observed})
g8fac = json.load(open(ROOT / "catalog/game8_facility_pages.json", encoding="utf-8"))   # verified Game8 prepper pages
wiki = json.load(open(ROOT / "catalog/wiki_pages.json", encoding="utf-8"))   # exact wiki article titles (catalog/build_wiki_links.py)
def fac_icon(code):
    """The facility's own map icon from the game (private build, --icons), as a 32 px PNG data URI; None without it."""
    f = ICONS / "facilities" / f"{code}.png" if ICONS else None
    if not f or not f.exists():
        return None
    from io import BytesIO
    from PIL import Image
    im = Image.open(f).convert("RGBA"); im.thumbnail((32, 32), Image.LANCZOS)
    b = BytesIO(); im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def read_map(d):
    meta = json.load(open(d / "map.json", encoding="utf-8"))
    names = {"aus": "Australia", "mex": "Mexico"}
    # colour maps (tools/build_map_colour.py: the game's per-voxel colours over the relief) when built, else the relief
    pic = lambda rid: d / f"{rid}_colour.jpg" if (d / f"{rid}_colour.jpg").exists() else d / f"{rid}.jpg"
    regions = {rid: dict(name=names.get(rid, rid), area=m["area"], size=m["size"], x0=m["x0"], y0=m["y0"],
                         img="data:image/jpeg;base64," + base64.b64encode(pic(rid).read_bytes()).decode())
               for rid, m in meta.items()}
    fac = [[int(r["code"]), r["name"], r["type"], r["area"], float(r["x"]), float(r["y"]), fac_icon(r["code"])]
           for r in csv.DictReader(open(ROOT / "catalog/facilities_game.csv", encoding="utf-8"))]
    return dict(regions=regions, facilities=fac)


map_data = read_map(MAP) if MAP else None
# without the game's map images (public build): our own simplified voxel terrain + facility positions (facts)
vmap = json.load(open(ROOT / "catalog/voxel_map.json", encoding="utf-8")) if not MAP and (ROOT / "catalog/voxel_map.json").exists() else None
vfac = json.load(open(ROOT / "catalog/facility_positions.json", encoding="utf-8")) if vmap else []


def read_links():
    """Which order or facility level unlocks each catalogue item (catalog/unlocks_game.csv, from the game's catalogue).
    -> {key: [mission ids, facility code or 0, connection level or 0]}; only items with a known source."""
    out = {}
    for r in csv.DictReader(open(ROOT / "catalog/unlocks_game.csv", encoding="utf-8-sig")):
        mids = [int(x) for x in r["mission_ids"].split() if x.isdigit() and int(x)]
        lvl = int(r["connection_level"]) if r["connection_level"].isdigit() else 0
        fac = int(r["terminal_id"]) if r["terminal_id"].lstrip("-").isdigit() and int(r["terminal_id"]) > 0 and lvl else 0
        if mids or fac:
            out[int(r["key"], 16)] = [mids, fac, lvl]
    return out


def read_icons(d):
    """Small WebP thumbnails of the items' own pictures, keyed by catalogue key (only real pictures, no type icons)."""
    from io import BytesIO
    from PIL import Image
    out = {}
    for r in csv.DictReader(open(ROOT / "catalog/icons_game.csv", encoding="utf-8-sig")):
        if r["category"] != "items" or not r["item_namecode"] or "/items/" not in r["file"] or r["placeholder"] == "1":
            continue
        f = ROOT / r["file"]
        if not f.exists():
            continue
        im = Image.open(f).convert("RGBA"); im.thumbnail((128, 80))
        b = BytesIO(); im.save(b, "WEBP", quality=72)
        out[int(r["item_namecode"], 16)] = "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()
    return out


links = read_links()
icons = read_icons(ICONS) if ICONS else {}
# APAS enhancement icons (private build only, like the item pictures): hash -> data URI
apas_icons = {}
if ICONS:
    from PIL import Image
    from io import BytesIO
    for r in APAS:
        if r.get("icon") and (ROOT / r["icon"]).exists():
            im = Image.open(ROOT / r["icon"]).convert("RGBA"); im.thumbnail((80, 80))
            b = BytesIO(); im.save(b, "WEBP", quality=80)
            apas_icons[int(r["hash"], 16)] = "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()
out = json.dumps(dict(orders=orders, recipes=recipes, about=ABOUT, tracked=tracked, g8fac=g8fac, wiki=wiki, sample=sample, example=example, map=map_data, links=links, icons=icons, vmap=vmap, vfac=vfac, generic=json.load(open(ROOT / "catalog/generic_icons.json", encoding="utf-8")), apas=apas_cat, apas_icons=apas_icons, bags=bags, lockers=lockers), ensure_ascii=False, separators=(",", ":"))
OUT.write_text(out, encoding="utf-8")
print(f"orders {len(orders)}, recipes {len(recipes)} (" + ", ".join(f"{k}={sum(x[4].startswith(k) for x in recipes)}" for k in ("e", "g", "x")) + "), "
      f"sample missions {len(missions)}, bytes {len(out):,}")

