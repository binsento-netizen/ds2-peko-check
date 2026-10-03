"""Map internal mission IDs (from saves) to order numbers and names. Writes mission_catalog.json/.csv.

Everything comes from the game's own data, via catalog/missions_game.csv (exported from the game files with Odradek;
the export script is not part of the public repo). No community guide is read.
  * Number: position in the game's DSMissionContentsDataResource lists (standard No. = 200 + index, main = index + 1,
    sub = 100 + index). Name: the game's English MissionName.
  * From: the order's StartConstruction (facility); story orders without one: the game's OrderPerson
    (e.g. "Drawbridge"); neither: "N/A".
  * To: collect / recover / eliminate / destroy orders: the target (enemy base or BT area name from the game, or
    "Near <place>" built from the game's "Near {0}" text and the named place nearest to the order's marker);
    all other orders: the GoalConstruction (facility); none: "N/A".
  * Cargo: size classes and counts of the game's cargo items ("XL×2, L×1"), "None" without cargo.
  * Episode (main orders): the game's EpisodeId.
The one main order outside the game's numbered lists (570, "Deliver the Present for Lou") gets No. 49 and the episode
after the last numbered one by inference (confidence "high" instead of "verified").
Check: the mission id -> number pairs seen in save metadata (ANCHORS) must all agree.
"""
import collections, csv, json

GAME = [r for r in csv.DictReader(open("catalog/missions_game.csv", encoding="utf-8-sig")) if r["order_no"]]
# (mission id -> order number) pairs seen in save metadata
ANCHORS = {10: 1, 20: 2, 30: 3, 40: 4, 50: 5, 60: 6, 70: 7, 80: 8, 90: 9, 100: 10, 130: 11, 135: 12, 160: 13, 170: 14,
           190: 16, 230: 18, 240: 19, 245: 20, 250: 21, 260: 22, 270: 23, 280: 24, 290: 25, 300: 26, 305: 27, 310: 28,
           320: 29, 360: 32, 370: 33, 390: 34, 410: 35, 415: 36, 420: 37, 430: 38, 460: 41, 500: 42, 510: 43, 520: 44,
           550: 47, 560: 48, 220070: 402, 295: 105}
# save mission type per kind (the numbers the viewer gets from ids_by_type.json); kept as "gtype" for standard orders
KIND_TYPE = {"delivery": 3, "collect": 4, "elimination": 17, "recover_from_enemies": 18, "destroy_cargo": 19}

last_episode = max(int(g["episode"]) for g in GAME if g["section"] == "Main" and g["episode"])
cat = {}
for g in GAME:
    no = int(g["order_no"])
    verified = g["no_source"] == "game list index"
    r = dict(no=no, section=g["section"])
    if g["section"] == "Main":
        r["Episode"] = g["episode"] or ("" if verified else str(last_episode + 1))
    r["Order"] = g["name"]
    r["From"] = g["client"] or g["order_person"] or "N/A"
    r["To"] = g["target"] or g["dest"] or "N/A"
    r["Cargo"] = g["cargo"] or "None"
    if g["section"] == "Standard":
        r["gtype"] = KIND_TYPE[g["kind"]]
    r["confidence"] = "verified" if verified else "high"
    cat[int(g["mission_id"])] = r

bad = [(k, v, cat.get(k, {}).get("no")) for k, v in ANCHORS.items() if cat.get(k, {}).get("no") != v]
assert not bad, f"save metadata disagrees: {bad}"
assert len({v["no"] for v in cat.values()}) == len(cat), "duplicate order numbers"
print("catalogue:", len(cat), dict(collections.Counter(v["section"] + "/" + v["confidence"] for v in cat.values())))
json.dump({str(k): v for k, v in sorted(cat.items())}, open("catalog/mission_catalog.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
with open("catalog/mission_catalog.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["mission_id", "order_no", "section", "episode", "order", "from", "to", "cargo", "confidence"])
    for k, v in sorted(cat.items(), key=lambda kv: kv[1]["no"]):
        w.writerow([k, v["no"], v["section"], v.get("Episode", ""), v["Order"], v["From"], v["To"], v["Cargo"], v["confidence"]])
