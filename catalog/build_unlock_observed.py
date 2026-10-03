"""Which catalogue entries ever carry the unlock bit (0x8000) in any save of the corpus.

Several kinds of unlocks (structures, holograms, music, colour schemes, ...) are always 0 in section 3ef4dc4d, even in
story-complete saves: their unlock state is stored elsewhere. The viewer uses this list to show 'status not available'
for subcategories where the bit is never observed, instead of a misleading 'Locked'.
Needs a corpus of saves under saves/ (research checkout only); the public repo ships the output.
"""
import glob, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ds2lib import load
from ds2_savestate import R, SaveState

seen, files = set(), sorted(glob.glob(str(ROOT / "saves/**/*.dat"), recursive=True))
if not files:
    sys.exit("no saves under saves/ (research checkout only); catalog/unlock_observed.json left unchanged")
n = 0
for f in files:
    if f.lower().endswith("profile.dat"):
        continue
    c = SaveState(load(f)[1]).section_bytes()[0x3EF4DC4D]
    r = R(c, 4); cnt = r.vint(); r.vint()
    for i in range(cnt):
        key, fl = struct.unpack_from("<II", c, r.pos + 8 * i)
        if fl & 0x8000:
            seen.add(key)
    n += 1
(ROOT / "catalog/unlock_observed.json").write_text(json.dumps(sorted(seen)), encoding="utf-8")
print(f"{n} saves scanned, {len(seen)} catalogue keys ever unlocked")
