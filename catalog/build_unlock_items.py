"""Unlock catalogue for the viewer, from the game's own data: catalog/unlock_items.json.

One row per DSGameCatalogueListItem (903; NameCode = the key in save section 3ef4dc4d), with the exact English name
and the viewer category, so the viewer build needs neither DS2-Mods nor the full game-text dump.
Read-only against the game install. Two steps:

  1. Export (once per game version, ~2 min, ~10 MB of JSON in out/unlocks_export, git-ignored). Needs the ext/
     folder of the main checkout (Odradek + runtime) and the helper classes compiled into tools/odradek/out:
       DS2_EXT=".../ds2-save-viewer/ext" python -B catalog/build_unlock_items.py --export
     FindObjects DSGameCatalogueListItem, then ExportBatch json, following only the refs in FOLLOW
     (catalogue item -> Baggage -> Contents -> LocalizedName / LocalizedUnlockCategoryText, RewardResource -> texts).
  2. Build (pure Python): python -B catalog/build_unlock_items.py  -> catalog/unlock_items.json

Name = DSGameBaggageListItem.LocalizedName (falls back to Contents.LocalizedName when the baggage has no name
resource), LocalizedTextResource.Texts[0] (English), with the <letter case=default> branch kept and the
runtime-filled " [{0}]" suffix dropped. A blank name or the literal placeholder "null" = no name (the viewer shows
"Unnamed entry" and hides the row). Categories: catalog/fabrication_categories.py. See docs/UNLOCKS_GAME.md.
"""
import glob, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "out" / "unlocks_export"
OUT = ROOT / "catalog" / "unlock_items.json"
sys.path.insert(0, str(ROOT / "catalog"))
from fabrication_categories import categorise

FOLLOW = {"Baggage", "RewardResource", "Contents", "LocalizedName", "LocalizedUnlockCategoryText",
          "HoloPersonNameText", "HoloAnimationNameText", "MusicTrackRsource", "TitleText"}
# display order of subcategories inside a category (the viewer lists them in order of first appearance)
SUB_ORDER = ["Attachments", "Charms", "Gloves", "Gear", "Tools", "Vehicles", "Vehicle parts", "DHV Magellan",
             "Vehicle decals", "Color schemes", "Hats & Hoods", "Glasses & Masks", "Suits", "BB Pod patterns",
             "Heavy & special", "Grenades, bombs & traps", "Guns", "Melee", "Support weapons"]
# Four "FIRMWARE UPDATE" entries are listed next to what they upgrade (decided 2026-10-02) and tagged instead of
# being filed under Features with the facility services.
FIRMWARE_HOME = {"64098529": ("APAS enhancements", None),       # Motion Scanner
                 "0532f5de": ("Vehicles", "Vehicle parts"),     # Pickup Off-Roader Improved
                 "42a862c1": ("Melee techniques", None),        # Improved Rubber Pizza
                 "1895a4e5": ("Outfits", "BB Pod patterns")}    # BB Pod Patterns
# Collaboration and event items keep the game's own tabs and get a tag. Evidence: the game's special-item lists
# DSCatalogueSystemSetting.SuitsCamouflageAsus / PSN / MuertosFestItems and the matching ROG / Link names.
TAGS = {"2a1cdc65": "Collab", "62adcdf6": "Collab", "201fd064": "Collab", "412a0a86": "Collab",   # ASUS ROG
        "10c64ef5": "Collab", "09770623": "Collab",                                             # Link (PSN)
        "440c2a1e": "Event", "334f2390": "Event"}                                               # Día de Muertos


# ---------------------------------------------------------------- export (Odradek)
def odradek(*args):
    res = subprocess.run(["sh", str(ROOT / "tools/odradek/run_out.sh"), *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return [l for l in res.stdout.splitlines() if not re.search(r" (DEBUG|INFO|WARN) ", l)]


def ref(s):
    m = re.match(r"<(?:streaming )?ref to (\d+:\d+)>", s) if isinstance(s, str) else None
    return m.group(1) if m else None


def load():
    objs, types = {}, {}
    for f in glob.glob(str(EXP / "j" / "*.json")):
        m = re.match(r"(.+)_(\d+)_(\d+)$", Path(f).stem)
        k = f"{m.group(2)}:{m.group(3)}"
        objs[k] = json.load(open(f, encoding="utf-8"))
        types[k] = m.group(1)
    return objs, types


def export():
    if not os.environ.get("DS2_EXT"):
        sys.exit("set DS2_EXT to the ext/ folder of the main checkout")
    (EXP / "j").mkdir(parents=True, exist_ok=True)
    lines = odradek("FindObjects", "DSGameCatalogueListItem")
    print(lines[-1] if lines else "FindObjects: no output")
    objs = load()[0]
    ids = {l.split()[1] for l in lines if l.startswith("DSGameCatalogueListItem ")} - set(objs)
    n = 1
    while ids:   # one ExportBatch per ref level; only objects not yet dumped
        idfile = EXP / f"ids{n}.txt"
        idfile.write_text("\n".join(sorted(ids)) + "\n")
        print(f"pass {n}: {len(ids)} objects", [l for l in odradek("ExportBatch", "json", str(EXP / "j"), str(idfile))
                                               if l.startswith(("DONE", "FAIL"))][-2:])
        objs = load()[0]
        ids = {ref(v) for o in objs.values() for f, v in o.items() if f in FOLLOW and ref(v)} - set(objs)
        n += 1


# ---------------------------------------------------------------- build
def clean(text):
    """Keep the case=default branch of <letter case=...> markup, drop other tags and the ' [{0}]' runtime suffix."""
    if text is None:
        return None
    text = re.sub(r"<letter case=default>(.*?)</letter>", r"\1", text, flags=re.S)
    text = re.sub(r"<letter case=[^>]*>.*?</letter>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s*\[\{0\}\]$", "", text).strip()


def build():
    objs, types = load()
    if not objs:
        sys.exit(f"no export in {EXP}; run with --export first")

    def txt(r):
        o = objs.get(r)
        return clean(o["Texts"][0]["Text"]) if o and o.get("Texts") else None

    items = []
    for k, t in types.items():
        if t != "DSGameCatalogueListItem":
            continue
        o = objs[k]
        bag = objs.get(ref(o["Baggage"])) or {}
        con_id = ref(bag.get("Contents"))
        con = objs.get(con_id) or {}
        rw = objs.get(ref(o.get("RewardResource"))) or {}
        if ref(bag.get("LocalizedName")):
            name, how = txt(ref(bag["LocalizedName"])), "baggage"
        else:
            name, how = txt(ref(con.get("LocalizedName"))), "contents"
        if not name or name == "null":
            name, how = "", ""
        items.append(dict(
            key=format(o["NameCode"] & 0xFFFFFFFF, "08x"), name=name, name_from=how,
            ui_tab=o.get("UITabType", ""), usage=o.get("Usage", ""),
            contents=types.get(con_id, "").replace("DSGame", "").replace("ListItem", ""),
            subrig=con.get("SubRigIconType"), unlock_cat=txt(ref(con.get("LocalizedUnlockCategoryText"))),
            reward=rw.get("Type"), pose=txt(ref(rw.get("HoloAnimationNameText"))),
            sort_index=o.get("SortIndex"), unlock_reason=o.get("UnlockReason", ""), object=k))
    # Holograms come in SortIndex blocks of ten per person: X0 = the plain custom hologram (no reward resource),
    # X1..X4 = extra poses rewarded by connection level. Ludens Duck colours (10100-10107) have no plain X0 entry.
    plain = {it["sort_index"] for it in items if it["subrig"] == "CoHologram" and not it["reward"]}
    for it in items:
        s = it["sort_index"]
        it["holo_variant"] = it["subrig"] == "CoHologram" and s % 10 != 0 and s - s % 10 in plain
        it["cat"], it["sub"] = categorise(it)
        it["tag"] = TAGS.get(it["key"], "")
        if it["key"] in FIRMWARE_HOME:
            it["cat"], it["sub"] = FIRMWARE_HOME[it["key"]]
            it["tag"] = "Firmware update"
    cats =["Weapons", "Skeletons", "Boots", "Equipment", "Backpack Attachments", "Patches", "Outfits", "Vehicles",
            "Structures", "APAS enhancements", "Melee techniques", "Holograms", "Character rewards", "Music",
            "Hot springs", "Collectibles", "Features", "Other"]
    items.sort(key=lambda it: (cats.index(it["cat"]) if it["cat"] else 99,
                               SUB_ORDER.index(it["sub"]) if it["sub"] in SUB_ORDER else -1, it["sort_index"], it["key"]))
    OUT.write_text("[\n" + ",\n".join(json.dumps(it, ensure_ascii=False) for it in items) + "\n]\n", encoding="utf-8")
    named = sum(bool(it["name"]) for it in items)
    print(f"unlock_items.json: {len(items)} items, {named} named, {len(items) - named} without a name; "
          f"shown {sum(bool(it['cat']) for it in items)}")


if __name__ == "__main__":
    if "--export" in sys.argv:
        export()
    build()
