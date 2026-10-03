r"""Read-only cargo / item location lister (research 2026-10-02).

Section 0aa0d44e is a pool of 464-byte object slots (~9,300). Pool start = the offset s (0..463) whose +60 words
are most often known baggage codes (253 in every save seen so far). Do NOT use the bytes 12 34 17 ac f6 7f at +40:
that is a run-time pointer (it differs per game session; absent in the 10-02 saves). Per slot, from the slot start:

  +0   u32  container runtime index (varies between players/saves; not used for identity)
  +4   u32  (container index << 9) | (container KIND << 24); KIND = byte +7
  +8   u32  mission id of the cargo's order, 0 if none (temporary ids >= 0x10000000, see 4afa625b)
  +12  u32  order flags (05001000 = online order, 07001000 = lost-cargo style; unconfirmed)
  +16  8 B  previous container (+0/+4 layout) or ff..ff
  +48  12 B container id = three u32 words w0 w1 w2 (stable across players; w0 = which container)
  +60  u32  DSGameBaggageListItem.NameCode (catalog/baggage_names.json); ffffffff/0 = empty slot
  +98  u16  position inside the container (shifts down when an item is taken out)
  +112 u32  per-instance counter (ammo / uses?; unconfirmed)
  +172 f32  remaining amount of a raw-material stack (CONFIRMED 2026-10-02: Metals [22], [28], Ceramics [20]
            in the locker photos; full stacks hold the baggage variant's Amount)
  +240 3xf64 last world position (stale for stored items; not a location)

Container kinds (byte +7) and words, with evidence:
  0x00 ffa46565 72b29160 <slot>  Sam: equipped (boots, gloves, skeleton, blood bags, ...)   CONFIRMED (boots swap)
  0x34 fd979c66 72b29160 77ddc563 Sam: backpack                                            CONFIRMED (boots swap,
                                                                                            withdraw, fabricate)
  0x1f <w0> ........ 36a83550     private locker, facility from w0                           CONFIRMED for F1 (deposit)
  0x1f <w0> ........ 4393710a     shared locker (other players' cargo, online orders)       inferred
  0x1f <w0> b770fe15 ........     storage in a structure (postbox etc.; order data gives a structure id)  inferred
  0x1f <w0> 5b215037 36a83550     storage present in every player's save (world / camp stock?)  unknown
  0x0e 00000000 f8e99e53 35f8261c cargo on the vehicle/carrier in use? (held MO27's 4 x Tar Dissolvent XL)  guess
  0x42 8996da15 8996da15 35f8261c same id in every player; 31-216 items (weapons/boots taken from enemies)  unknown
  0x11 560edd28 560edd28 211cb65b same id and the same 3 items (2 Floating Carrier Lv1, Backpack) in every save  unknown
  0x01 / 0x21                     single loose items (in the world?)                         guess
  0xff                            no container (free pool slot with old data; hidden unless --all)

Facility of a locker: w0 -> facility code, from FACILITY_LOCKERS below (built from the order records of shared-locker
cargo: for online orders the record names the container's facility code), plus the same inference on the save itself.
Amounts: a raw-material stack is its own baggage variant (Metals 50/100/200/400/...), so the amount = the baggage's
Amount (CONFIRMED: withdrawing 400 Metals added one 'Metals' item whose baggage Amount is 400).

Example:
  python -B tools/review_cargo.py path/to/manualsave25.dat
  python -B tools/review_cargo.py --json --all <save.dat>
"""
import argparse
import collections
import csv
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SID, STRIDE = 0x0AA0D44E, 464
SAM, BACKPACK, EQUIPPED = "72b29160", "fd979c66", "ffa46565"
PRIVATE, SHARED, STRUCTURE, WORLDSTORE = "36a83550", "4393710a", "b770fe15", "5b215037"

# w0 -> facility code. Evidence: online-order cargo in that container whose order record names this code
# (test saves 09-28 .. 10-02; counts in docs). F1 also confirmed by the private-locker deposit test (10-01 ms6->7).
FACILITY_LOCKERS = {
    "dae2d95e": 101, "2e11894d": 102, "2d92e23f": 103, "09aef161": 104, "0a2d9a13": 105, "e25c365b": 107,
    "e1df5d29": 108, "38619c55": 202, "cc92cc46": 203, "cf11a734": 204, "24756d60": 205, "27f60612": 206,
    "ae72d47e": 209, "5a81846d": 210, "5902ef1f": 211, "b1e54e39": 213, "46957558": 215, "62a96606": 216,
    "612a0d74": 217, "7da8f12f": 218, "895ba13c": 219, "8ad8ca4e": 220, "cbdde444": 300,
}
FACILITY_CODES = set(range(101, 109)) | set(range(201, 241)) | {300, 400}


def load_names():
    names = {}
    with (ROOT / "catalog" / "facilities_game.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            names[int(r["code"])] = r["name"]
    names[300] = "DHV Magellan"
    bag = json.loads((ROOT / "catalog" / "baggage_names.json").read_text(encoding="utf-8"))
    return names, bag


def pool_start(b, keys):
    """Slot grid: the offset whose +60 words are most often a known baggage code (empty slots hold ffffffff there,
    but so does a lot of other data, so only real codes are counted)."""
    def score(s):
        return sum(b[o + 60:o + 64].hex() in keys for o in range(s, len(b) - STRIDE + 1, STRIDE))
    return max(range(STRIDE), key=score)


def slots(b, keys):
    s = pool_start(b, keys)
    for i in range((len(b) - s) // STRIDE):
        yield i, b[s + i * STRIDE:s + (i + 1) * STRIDE]


def order_codes(mission):
    """Online-order records (type 5): facility codes after the 00 00 05 0x 00 0a 00 xx 00 header (2nd = container)."""
    h = bytes.fromhex(mission["opaque_variable_hex"])
    m = re.search(rb"\x00\x00\x05[\x00-\x0f]\x00\x0a\x00[\x00-\xff]\x00", h)
    return struct.unpack_from("<III", h, m.end()) if m and m.end() + 12 <= len(h) else None


def location(kind, w0, w1, w2, lockers, fac):
    if kind == 0x00 and w0 == EQUIPPED and w1 == SAM:
        return "Sam: equipped", "confirmed"
    if kind == 0x34 and w1 == SAM:
        return "Sam: backpack", "confirmed"
    if kind == 0x1F:
        code = lockers.get(w0)
        where = fac.get(code, f"facility {code}") if code else None
        if w2 == PRIVATE and w1 not in (STRUCTURE, WORLDSTORE):
            return ((f"Private locker: {where}" if where else f"Private locker: unidentified facility ({w0})"),
                    "confirmed" if w0 in ("27f60612", "24756d60", "46957558") else "inferred")
        if w2 == SHARED and w1 not in (STRUCTURE, WORLDSTORE):
            return (f"Shared locker: {where}" if where else f"Shared locker: unidentified ({w0})"), "inferred"
        if w1 == STRUCTURE:
            return f"Structure storage ({w0}, {w2 == PRIVATE and 'own' or 'online'})", "guess"
        if w1 == WORLDSTORE:
            return f"World storage ({w0}; kind unknown)", "guess"
        return f"Storage {w0} {w1} {w2}", "guess"
    if kind == 0x0E:
        return "Carried by a vehicle or carrier? (kind 0x0e)", "guess"
    if kind in (0x42, 0x11):
        return f"Unidentified store (kind 0x{kind:02x}, {w0})", "guess"
    if kind in (0x01, 0x21):
        return "Loose item (world?)", "guess"
    if kind == 0xFF:
        return "No container", "guess"
    return f"Unknown (kind 0x{kind:02x}, {w0} {w1} {w2})", "guess"


def inspect(path, show_all=False):
    sys.path.insert(0, str(ROOT / "tools"))
    from ds2_decode import decode, BLOCK, PNG_MAGIC
    from ds2_savestate import SaveState
    import review_missions as rm
    fac, bag = load_names()
    payload, _ = rm.read_payload(Path(path), decode, BLOCK, PNG_MAGIC)
    save = SaveState(payload)
    secs = save.section_bytes()
    missions = {m["mission_id"]: m for m in rm.parse_missions(secs[rm.SECTION])[0]}
    items = []
    for i, r in slots(secs[SID], {bytes.fromhex(k)[::-1].hex() for k in bag}):
        key = format(struct.unpack_from("<I", r, 60)[0], "08x")
        if key not in bag:
            continue
        items.append((i, r, key))
    # self-calibration: shared-locker cargo on online orders names its container's facility code
    lockers, votes = dict(FACILITY_LOCKERS), collections.defaultdict(collections.Counter)
    for i, r, key in items:
        m = missions.get(struct.unpack_from("<I", r, 8)[0])
        if r[7] == 0x1F and r[56:60].hex() == SHARED and m and m["mission_type"] == 5:
            c = order_codes(m)
            if c and c[1] in FACILITY_CODES:
                votes[r[48:52].hex()][c[1]] += 1
    for w0, c in votes.items():
        lockers.setdefault(w0, c.most_common(1)[0][0])
    out = []
    for i, r, key in items:
        w0, w1, w2 = (r[o:o + 4].hex() for o in (48, 52, 56))
        loc, sure = location(r[7], w0, w1, w2, lockers, fac)
        if loc == "No container" and not show_all:
            continue
        b = bag[key]
        mid = struct.unpack_from("<I", r, 8)[0]
        out.append({"slot": i, "location": loc, "confidence": sure, "name": b["name"] or f"unnamed {key}",
                    "baggage": key, "type": b["contents_type"],
                    "amount": round(struct.unpack_from("<f", r, 172)[0]) if b["contents_type"] == "RawMaterial" else None,
                    "position": struct.unpack_from("<H", r, 98)[0], "counter": struct.unpack_from("<I", r, 112)[0],
                    "order_mission_id": mid or None, "container": f"{r[7]:02x} {w0} {w1} {w2}"})
    return {"path": str(Path(path).resolve()), "playtime_seconds": save.playtime, "items": out}


def text_report(res):
    lines = [f"{res['path']}  (play time {res['playtime_seconds'] / 3600:.2f} h, {len(res['items'])} items)"]
    by = collections.defaultdict(list)
    for it in res["items"]:
        by[it["location"]].append(it)

    def order(loc):
        for n, p in enumerate(("Sam: equipped", "Sam: backpack", "Private locker", "Shared locker", "Carried")):
            if loc.startswith(p):
                return (n, loc)
        return (9, loc)
    for loc in sorted(by, key=order):
        its = by[loc]
        lines.append(f"\n{loc}  [{len(its)} items; location {its[0]['confidence']}]")
        agg = collections.OrderedDict()
        for it in sorted(its, key=lambda x: x["position"]):
            k = (it["name"], it["type"])
            a = agg.setdefault(k, [0, 0])
            a[0] += 1
            a[1] += it["amount"] or 0
        for (name, typ), (n, amt) in agg.items():
            extra = f"  ({amt} total)" if typ == "RawMaterial" else ""
            lines.append(f"  {n:3d} x {name}{extra}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("save", type=Path)
    ap.add_argument("--json", action="store_true", help="print JSON instead of the grouped text list")
    ap.add_argument("--all", action="store_true", help="also list items with no container (kind 0xff)")
    args = ap.parse_args()
    res = inspect(args.save, args.all)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False) if args.json else text_report(res))


if __name__ == "__main__":
    raise SystemExit(main())
