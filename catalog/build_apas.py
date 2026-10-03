"""APAS enhancement catalogue from the game's own data: catalog/apas_game.json.

One row per DSApasEnhancementResource (52). The save's APAS list (section 69049449, see tools/review_apas.py) refers
to an enhancement by hash = CRC32C(EnhancementId) with init 0, no final xor and the top bit cleared, the same masked
Decima hash as the catalogue picture names (tools/odradek/build_icons.py name_hash).

Input: the JSON closure that tools/odradek/build_icons.py exports to decoded/icons_work/json (git-ignored cache;
rebuild it with that script). Names are the game's English text (LocalizedTextResource.Texts[0]).
  python -B catalog/build_apas.py
Needs the private research checkout (game export); the public repo ships the output.
"""
import csv, glob, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
J = ROOT / "decoded/icons_work/json"
OUT = ROOT / "catalog/apas_game.json"
ICONS = ROOT / "assets_private/icons/apas"   # private: game art (each enhancement's IconTexture, 256x256 white glyph)


def crc32c(b):
    c = 0
    for x in b:
        c ^= x
        for _ in range(8):
            c = (c >> 1) ^ (0x82F63B78 if c & 1 else 0)
    return c


def name_hash(s):
    return crc32c(s.encode()) & 0x7FFFFFFF


def ref(s):
    m = re.match(r"<(?:streaming )?ref to (\d+):(\d+)>", s or "")
    return f"{m.group(1)}_{m.group(2)}" if m else None


def text(r):
    files = glob.glob(str(J / f"*_{r}.json")) if r else []
    if not files:
        return ""
    t = (json.load(open(files[0], encoding="utf-8")).get("Texts") or [{}])[0].get("Text") or ""
    t = re.sub(r"<letter case=default>(.*?)</letter>", r"\1", t, flags=re.S)
    return re.sub(r"<[^>]+>", "", t).strip()


def main():
    # unlock-catalogue entries that share the enhancement's Name ref (build_icons.py links APAS icons this way)
    link = {}
    for r in csv.DictReader(open(ROOT / "catalog/icons_game.csv", encoding="utf-8-sig")):
        if r["source_type"] == "DSApasEnhancementResource" and r["item_namecode"]:
            link.setdefault(r["source_id"], []).append(r["item_namecode"])
    rows = []
    ICONS.mkdir(parents=True, exist_ok=True)
    for f in sorted(glob.glob(str(J / "DSApasEnhancementResource_*.json"))):
        o = json.load(open(f, encoding="utf-8"))
        obj = re.search(r"_(\d+)_(\d+)\.json$", f)
        eid = o["EnhancementId"]
        tex = ref(o.get("IconTexture"))
        png = ROOT / "decoded/icons_work/png" / f"{tex}.png" if tex else None
        icon = ""
        if png and png.exists():
            icon = f"assets_private/icons/apas/{tex}.png"
            shutil.copyfile(png, ROOT / icon)
        m = re.search(r"_(\d{4})_(\d+)$", eid)
        rows.append(dict(
            id=eid, hash=format(name_hash(eid), "08x"), no=int(m.group(1)), step=int(m.group(2)),
            name=text(ref(o.get("Name"))), info=text(ref(o.get("InfoText"))),
            points=o.get("EnhancementPoint", 0), category=o.get("EnhancementCategory", ""),
            unlock_keys=link.get(f"{obj.group(1)}:{obj.group(2)}", []), icon=icon, object=f"{obj.group(1)}:{obj.group(2)}"))
    rows.sort(key=lambda r: (r["no"], r["step"]))
    OUT.write_text("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n", encoding="utf-8")
    print(f"apas_game.json: {len(rows)} enhancements, {sum(bool(r['name']) for r in rows)} named, "
          f"{len({r['hash'] for r in rows})} distinct hashes")


if __name__ == "__main__":
    main()
