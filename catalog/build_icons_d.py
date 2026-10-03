"""Style-D ("Clean UI") unlock icons for the viewer: catalog/generic_icons.json.

Replaces the game-icons.net set of catalog/build_generic_icons.py. Every icon follows one spec: 24x24 grid, 2px round
stroke, no fill, outline glyphs (like the game's own menus). Base library: Tabler Icons (MIT); the rest is drawn for
Peko-Check on the same grid. The game's item pictures (private, assets_private/icons) were looked at only as a shape
reference for the drawings (silhouette and proportions); nothing is traced or copied and no game picture is included.

  python -B catalog/build_icons_d.py     # writes catalog/generic_icons.json + assets/icons-generic/CREDITS.md
                                         # (+ design/icon-themes/d-full-preview.html in the research checkout)

Output: {"icons": {kind: "<svg ...>"}, "map": {catalogue key: kind}, "tint": {kind: family colour}}.
Kinds without a "tint" entry are neutral (Other / Features / Hot springs / Collectibles).
Assignment: RULES_KEY -> RULES_NAME (regex on "name | subrig" inside a category) -> RULES_CAT -> "misc".
Hidden unlocks (cat None) get no icon.
"""
import collections, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "catalog" / "unlock_items.json"
OUT = ROOT / "catalog" / "generic_icons.json"
CREDITS = ROOT / "assets" / "icons-generic" / "CREDITS.md"
PREVIEW = ROOT / "design" / "icon-themes" / "d-full-preview.html"

# family -> (tint name in the JSON, colour on dark, colour on light) ; preview only uses the colours
FAMILIES = {
    "weapons": ("orange", "#f08a4b", "#b4440f", "Weapons"),
    "equipment": ("cyan", "#5cc8ff", "#1a6f93", "Equipment"),
    "vehicles": ("teal", "#3fd0b8", "#11766a", "Vehicles"),
    "cosmetic": ("violet", "#b49cff", "#6a4fc0", "Outfits, patches & holograms"),
    "structure": ("gold", "#e3b23c", "#8a6206", "Structures"),
    "music": ("rose", "#f27fa5", "#a8385f", "Music"),
    "apas": ("green", "#7cc68c", "#2e6b3c", "APAS"),
    "other": (None, "#a9b6c2", "#56636f", "Other (neutral)"),
}

# kind -> (family, title, source, markup). source: "custom" = drawn for Peko-Check; "tabler:<name>" = Tabler Icons
# outline (coordinates rounded to 0.1); "tabler:<name>+" = Tabler, modified. Markup: <path d>/<circle> only.
T, C = "tabler:", "custom"
GRENADE = ('<path d="M9 9h6a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-6a2 2 0 0 1 -2 -2v-8a2 2 0 0 1 2 -2z"/><path d="M10 9v-3h4v3"/>'
           '<path d="M14 6.5h3v5.5"/><circle cx="8" cy="4.5" r="1.5"/>')  # shared body; each grenade kind adds an emblem
ICONS = {
    # ---- weapons (muzzles point right) ----
    "handgun": ("weapons", "Handgun", C,
        '<path d="M4 7h16a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-8l-1.2 6.2a1 1 0 0 1 -1 .8h-2.6a1 1 0 0 1 -1 -1.2l1.2 -5.8h-3.4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1"/>'
        '<path d="M12 11v1a2 2 0 0 1 -2 2h-.6"/><path d="M17 7v-1.5"/>'),
    "shotgun": ("weapons", "Shotgun", C,
        '<path d="M2 8.5h11"/><path d="M13 8.5v-1h3l6 3.5v3h-3l-3 -2.5h-6.5"/><path d="M3 12h3.5"/>'
        '<path d="M6.5 10.5h4.5v3h-4.5z"/><path d="M14 12.5v2"/>'),
    "rifle": ("weapons", "Assault rifle", C,
        '<path d="M2 10.5h4"/><path d="M6 8.5h10l6 2.5v3h-3l-2 -1.5h-11z"/><path d="M10 12.5l1 4.5h2.5l-1 -4.5"/>'
        '<path d="M8 8.5v-2h3v2"/>'),
    "sniper": ("weapons", "Sniper rifle", C,
        '<path d="M2 10.5h7"/><path d="M9 9h7l6 2v3h-3l-2 -1.5h-8z"/><path d="M9.5 4.5h6.5"/><path d="M11 4.5v4.5"/>'
        '<path d="M14.5 4.5v4.5"/><path d="M5.5 10.5l-1.5 5"/><path d="M5.5 10.5l1.5 5"/>'),
    "machine-gun": ("weapons", "Machine gun", C,
        '<path d="M2 11.5h3"/><path d="M5 8.5h11v3.5h-11z"/><path d="M16 10h6"/><path d="M8 12h3.5v3.5h-3.5z"/>'
        '<path d="M13 12l-.5 2.5"/><path d="M19.5 10l-1.5 5.5"/><path d="M19.5 10l1.5 5.5"/>'),
    "grenade-launcher": ("weapons", "Grenade launcher", C,
        '<path d="M2 10.5h3"/><path d="M5 8.5h7v4.5h-7z"/><path d="M12 7.5h4a1.5 1.5 0 0 1 1.5 1.5v4a1.5 1.5 0 0 1 -1.5 1.5h-4z"/>'
        '<path d="M7 13l-1 4.5h2.5l1 -4.5"/><circle cx="20.5" cy="11" r="1.5"/>'),
    "rocket-launcher": ("weapons", "Rocket launcher", C,
        '<path d="M2 7l2 1v5l-2 1z"/><path d="M4 7.5h12v6h-12z"/><path d="M4 10.5h12"/><path d="M16 8.5h2l3 2l-3 2h-2"/>'
        '<path d="M8 13.5l-1 4.5h2.5l1 -4.5"/><path d="M10 7.5v-2h3v2"/>'),
    "cannon": ("weapons", "Tripod cannon", C,
        '<path d="M4 5h9v5h-9z"/><path d="M13 6.5h8v2h-8z"/><path d="M9 10v3"/><path d="M9 13l-5 8"/><path d="M9 13l5 8"/>'
        '<path d="M9 13v8"/>'),
    "bola": ("weapons", "Bola gun", C,
        '<path d="M2 10.5l3 -1v5l-3 -1z"/><path d="M5 8.5h9v5h-9z"/><path d="M14 9.5h2.5v3h-2.5"/>'
        '<path d="M7.5 13.5l-1 4.5h2.5l1 -4.5"/><circle cx="20.5" cy="6.5" r="1.5"/><circle cx="20.5" cy="15.5" r="1.5"/>'
        '<path d="M19.6 7.7c-1.2 2 -1.2 4.6 0 6.6"/>'),
    "sticky-gun": ("weapons", "Sticky gun", C,
        '<path d="M3 8h10v5h-10z"/><path d="M5 13l-1 5h2.5l1.5 -5"/><path d="M6 8v-2h4v2"/>'
        '<path d="M13 10.5c1.5 -2.5 3 2.5 4.5 0s3 -2.5 4.5 0"/>'),
    "sentry": ("weapons", "Floating sentry gun", C,
        '<path d="M3 4h6"/><path d="M15 4h6"/><path d="M6 4v2.5"/><path d="M18 4v2.5"/><path d="M5 6.5h14v4h-14z"/>'
        '<path d="M8 10.5v4h8v-4"/><path d="M16 12.5h5"/><path d="M9 18h6"/><path d="M10.5 21h3"/>'),
    "shield": ("weapons", "Deployable shield", C,
        '<path d="M7 3h10a1 1 0 0 1 1 1v13l-6 4l-6 -4v-13a1 1 0 0 1 1 -1z"/><path d="M6 8.5h12"/><path d="M6 13.5h12"/>'),
    "pizza": ("weapons", "Rubber pizza", T + "pizza",
        '<path d="M12 21.5c-3.04 0 -5.952 -.714 -8.5 -1.983l8.5 -16.517l8.5 16.517a19.09 19.09 0 0 1 -8.5 1.983"/>'
        '<path d="M5.38 15.866a14.94 14.94 0 0 0 6.815 1.634a14.944 14.944 0 0 0 6.502 -1.479"/><path d="M13 11.01v-.01"/>'
        '<path d="M11 14v-.01"/>'),
    "grenade": ("weapons", "Grenade (standard / MP)", C,
        GRENADE + '<path d="M7 14h10"/>'),
    "grenade-blood": ("weapons", "Blood grenade", C,
        GRENADE + '<path d="M12 11.8l1.8 2.6a2.2 2.2 0 1 1 -3.6 0z"/>'),
    "grenade-ex": ("weapons", "EX grenade", C,
        GRENADE + '<path d="M10.3 13l3.4 4"/><path d="M13.7 13l-3.4 4"/>'),
    "grenade-stun": ("weapons", "Stun bomb", C,
        GRENADE + '<path d="M12.8 11.5l-2.3 3.5h3l-2.3 3.5"/>'),
    "grenade-smoke": ("weapons", "Smoke grenade", C,
        GRENADE + '<path d="M10 17.5h4.2a1.6 1.6 0 0 0 .2 -3.2a2.2 2.2 0 0 0 -4.1 -.4a1.8 1.8 0 0 0 -.3 3.6z"/>'),
    "grenade-gas": ("weapons", "Gas grenade", C,
        GRENADE + '<path d="M9.5 13.5c.8 -.8 1.7 .8 2.5 0s1.7 .8 2.5 0"/><path d="M9.5 16.5c.8 -.8 1.7 .8 2.5 0s1.7 .8 2.5 0"/>'),
    "grenade-holo": ("weapons", "Hologrenade", C,
        GRENADE + '<circle cx="12" cy="13" r="1.3"/><path d="M9.8 17.8a2.2 2.2 0 0 1 4.4 0"/>'),
    "dog-mine": ("weapons", "Dog mine", C,
        '<path d="M6 9.5h10v4h-10z"/><path d="M16 10.5l1 -4l2 2.5h2.5v3.5h-5"/><path d="M6 10l-2.5 -4"/>'
        '<path d="M7.5 13.5l-1.5 3l1.5 3.5"/><path d="M14.5 13.5l1.5 3l-1.5 3.5"/>'),
    "melee": ("weapons", "Rod / blade", C,
        '<path d="M4 20l13 -13"/><path d="M17 7l1 -4"/><path d="M17 7l4 -1"/><path d="M5 15.5l3.5 3.5"/>'
        '<path d="M19.5 10.5l1 1"/><path d="M13.5 4.5l-1 -1"/>'),
    "boomerang": ("weapons", "Boomerang", C,
        '<path d="M4 6.5l3.5 -2.5l12.8 11.6a1.6 1.6 0 0 1 -.3 2.6l-1.2 .5l-8.8 -7.7l-3.5 7.2a1.5 1.5 0 0 1 -2.5 .3l-.8 -1z"/>'),
    "airstrike": ("weapons", "Support strike (Magellan)", C,
        '<path d="M12 7a3 3 0 0 1 3 3v6l-3 4l-3 -4v-6a3 3 0 0 1 3 -3z"/><path d="M10 7.5l-1 -4.5h6l-1 4.5"/>'
        '<path d="M5 4v8"/><path d="M19 4v8"/>'),
    "electric-trap": ("weapons", "Electric trap", C,
        '<path d="M7 3v4a4 4 0 0 0 8 0v-4"/><path d="M11 11v10"/><path d="M8 21h6"/><path d="M19 9l-2 3h3l-2 3"/>'),
    "martial-arts": ("weapons", "Karate technique", C,
        '<circle cx="7" cy="4.5" r="2"/><path d="M8 7l2.5 6"/><path d="M10.5 13l-2.5 3.5l1 4.5"/><path d="M10.5 13l9.5 -3.5"/>'
        '<path d="M8.8 9l-4.3 2.5"/><path d="M8.8 9l3.7 -2"/>'),
    # ---- equipment, body gear, backpack ----
    "ladder": ("equipment", "Ladder", T + "ladder",
        '<path d="M8 3v18"/><path d="M16 3v18"/><path d="M8 14h8"/><path d="M8 10h8"/><path d="M8 6h8"/><path d="M8 18h8"/>'),
    "anchor": ("equipment", "Climbing anchor", C,
        '<path d="M9.5 3h5"/><path d="M11 3v11l1 5l1 -5v-11"/><path d="M4 16h4"/><path d="M16 16h4"/>'
        '<path d="M13 5.5c3 0 6 1.5 6.5 4.5s-1.5 3.5 -3 3"/>'),
    "pcc": ("equipment", "PCC (chiral constructor)", C,
        '<path d="M5 6h14a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-8a2 2 0 0 1 2 -2z"/>'
        '<path d="M8.5 9h7v6h-7z"/><path d="M5.5 12h.5"/><path d="M18 12h.5"/><path d="M10 3.5h4"/>'),
    "spray": ("equipment", "Repair spray", T + "spray",
        '<path d="M4 12a2 2 0 0 1 2 -2h4a2 2 0 0 1 2 2v7a2 2 0 0 1 -2 2h-4a2 2 0 0 1 -2 -2l0 -7"/>'
        '<path d="M6 10v-4a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v4"/><path d="M15 7h.01"/><path d="M18 9h.01"/>'
        '<path d="M18 5h.01"/><path d="M21 3h.01"/><path d="M21 7h.01"/><path d="M21 11h.01"/><path d="M10 7h1"/>'),
    "blood-bag": ("equipment", "Blood bag", C,
        '<path d="M6 3h12"/><path d="M9 3v2"/><path d="M15 3v2"/>'
        '<path d="M7 5h10v11a2 2 0 0 1 -2 2h-6a2 2 0 0 1 -2 -2z"/><path d="M12 8.5l1.8 2.6a2.2 2.2 0 1 1 -3.6 0z"/>'
        '<path d="M12 18v3"/>'),
    "floating-carrier": ("equipment", "Floating carrier", C,
        '<path d="M3 10h18v3.5h-18z"/><path d="M12 10v3.5"/><path d="M8 10v-4h8v4"/><path d="M6 17.5h4"/>'
        '<path d="M14 17.5h4"/><path d="M9.5 20.5h5"/>'),
    "coffin-board": ("equipment", "Coffin board", C,
        '<path d="M3 9.5l4 -2.5l14 1.5v5l-14 1.5l-4 -2.5z"/><path d="M11 11h4"/><path d="M13 9.5v3"/>'
        '<path d="M6 18.5h4"/><path d="M14 18.5h4"/><path d="M9.5 21.5h5"/>'),
    "oxygen-mask": ("equipment", "Oxygen mask (helmet)", C,
        '<path d="M5 12a7 7 0 0 1 14 0v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2z"/>'
        '<path d="M8 10h8a1 1 0 0 1 1 1v2a3 3 0 0 1 -3 3h-4a3 3 0 0 1 -3 -3v-2a1 1 0 0 1 1 -1z"/><path d="M9 20v-1.5"/>'
        '<path d="M15 20v-1.5"/>'),
    "canteen": ("equipment", "Canteen", C,
        '<path d="M10 3h4v2.5h-4z"/><path d="M8 5.5h8a2 2 0 0 1 2 2v11.5a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2v-11.5a2 2 0 0 1 2 -2z"/>'
        '<path d="M9 12.5c1 -1 2 -1 3 0s2 1 3 0"/>'),
    "thermal": ("equipment", "Thermal pad", C,
        '<path d="M12 3a4 4 0 0 1 4 4v10a4 4 0 0 1 -8 0v-10a4 4 0 0 1 4 -4z"/><path d="M8 9.5h8"/><path d="M8 14.5h8"/>'
        '<path d="M4.5 9c-1 1 -1 2 0 3s1 2 0 3"/><path d="M19.5 9c-1 1 -1 2 0 3s1 2 0 3"/>'),
    "guidepost": ("equipment", "Guidepost / light", C,
        '<path d="M6 5h12"/><path d="M9 3h6"/><path d="M8 7.5c2.5 1.3 5.5 1.3 8 0"/><path d="M12 5v16"/><path d="M9 21h6"/>'),
    "gloves": ("equipment", "Power gloves", T + "hand-stop+",
        '<path d="M8 13v-7.5a1.5 1.5 0 0 1 3 0v6.5"/><path d="M11 5.5v-2a1.5 1.5 0 1 1 3 0v8.5"/>'
        '<path d="M14 5.5a1.5 1.5 0 0 1 3 0v6.5"/><path d="M17 7.5a1.5 1.5 0 0 1 3 0v8.5a6 6 0 0 1 -6 6h-2h.208a6 6 0 0 1 -5.012 -2.7a69.74 69.74 0 0 1 -.196 -.3c-.312 -.479 -1.407 -2.388 -3.286 -5.728a1.5 1.5 0 0 1 .536 -2.022a1.867 1.867 0 0 1 2.28 .28l1.47 1.47"/>'
        '<path d="M10.5 16h9.5"/>'),
    "boots": ("equipment", "Boots", C,
        '<path d="M7 3h6v8l5.2 1.9a3 3 0 0 1 2 2.8v4.3h-13.2z"/><path d="M7 17h13.2"/><path d="M10 6.5h3"/><path d="M10 9.5h3"/>'),
    "skeleton": ("equipment", "Exoskeleton", C,
        '<path d="M8 10v-5a2 2 0 0 1 2 -2h4a2 2 0 0 1 2 2v5"/><path d="M6.5 10h11"/><path d="M8 10l-1 4.5"/>'
        '<path d="M16 10l1 4.5"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/>'
        '<path d="M7 16.5l1 4.5h-3"/><path d="M17 16.5l-1 4.5h3"/>'),
    "pouch": ("equipment", "Pouch", C,
        '<path d="M6 7h12v12a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2z"/><path d="M6 7l1 5h10l1 -5"/><path d="M12 12v2.5"/>'
        '<path d="M10 7v-3h4v3"/>'),
    "aed": ("equipment", "Auto-resuscitation device", T + "heartbeat",
        '<path d="M19.5 13.572l-7.5 7.428l-2.896 -2.868m-6.117 -8.104a5 5 0 0 1 9.013 -3.022a5 5 0 1 1 7.5 6.572"/>'
        '<path d="M3 13h2l2 3l2 -6l1 3h3"/>'),
    "backpack": ("equipment", "Backpack attachment", T + "backpack",
        '<path d="M5 18v-6a6 6 0 0 1 6 -6h2a6 6 0 0 1 6 6v6a3 3 0 0 1 -3 3h-8a3 3 0 0 1 -3 -3"/>'
        '<path d="M10 6v-1a2 2 0 1 1 4 0v1"/><path d="M9 21v-4a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v4"/><path d="M11 10h2"/>'),
    "stabilizer": ("equipment", "Stabilizer", C,
        '<path d="M9 4h6a3 3 0 0 1 3 3v8a1 1 0 0 1 -1 1h-10a1 1 0 0 1 -1 -1v-8a3 3 0 0 1 3 -3z"/><path d="M6 10h12"/>'
        '<path d="M8.5 16l-1 2.5h3l-1 -2.5"/><path d="M15.5 16l-1 2.5h3l-1 -2.5"/><path d="M9 21v.5"/><path d="M15 21v.5"/>'),
    "battery": ("equipment", "Extra battery", C,
        '<path d="M7 5h10v15a1 1 0 0 1 -1 1h-8a1 1 0 0 1 -1 -1z"/><path d="M9.5 3v2"/><path d="M14.5 3v2"/>'
        '<path d="M12.5 8.5l-2 3.5h3l-2 3.5"/>'),
    "solar": ("equipment", "Solar generator", T + "solar-panel",
        '<path d="M4.28 14h15.44a1 1 0 0 0 .97 -1.243l-1.5 -6a1 1 0 0 0 -.97 -.757h-12.44a1 1 0 0 0 -.97 .757l-1.5 6a1 1 0 0 0 .97 1.243"/>'
        '<path d="M4 10h16"/><path d="M10 6l-1 8"/><path d="M14 6l1 8"/><path d="M12 14v4"/><path d="M7 18h10"/>'),
    "ammo": ("equipment", "Ammo container", C,
        '<path d="M4 12h16v8h-16z"/><path d="M6.5 12v-5a1.5 1.5 0 0 1 3 0v5"/><path d="M10.5 12v-5a1.5 1.5 0 0 1 3 0v5"/>'
        '<path d="M14.5 12v-5a1.5 1.5 0 0 1 3 0v5"/>'),
    "antigravity": ("equipment", "Antigravity device", C,
        '<path d="M5 8a7 3 0 1 0 14 0a7 3 0 1 0 -14 0"/><path d="M5 8v2.5a7 3 0 0 0 14 0v-2.5"/><path d="M7 17.5h4"/>'
        '<path d="M13 17.5h4"/><path d="M9.5 20.5h5"/>'),
    "protector": ("equipment", "Back protector", C,
        '<path d="M7 3h10a2 2 0 0 1 2 2v12a4 4 0 0 1 -4 4h-6a4 4 0 0 1 -4 -4v-12a2 2 0 0 1 2 -2z"/><path d="M5 8.5h14"/>'
        '<path d="M5 13.5h14"/><path d="M12 8.5v5"/>'),
    "shock-absorber": ("equipment", "Shock absorber", C,
        '<path d="M10 3v3"/><path d="M10 18v3"/><path d="M10 6l4 1.5l-8 2l8 2l-8 2l8 2l-4 1.5"/>'
        '<path d="M19.5 4l-2 3.5h3l-2 3.5"/>'),
    "charm": ("equipment", "Backpack charm", C,
        '<path d="M3 3.5h18"/><path d="M3 7h18"/><path d="M10.5 7v3a1.5 1.5 0 0 0 3 0v-3"/><path d="M12 11.5v1.5"/>'
        '<path d="M8.5 19.5h7l-1 -1.5v-2.5a2.5 2.5 0 0 0 -5 0v2.5z"/><path d="M12 21.5v.01"/>'),
    # ---- vehicles ----
    "trike": ("vehicles", "Tri-cruiser", C,
        '<circle cx="18" cy="17" r="3"/><circle cx="6.5" cy="17" r="3"/><path d="M3.8 14.7a3 3 0 0 0 0 4.6"/>'
        '<path d="M4 12l3 -2.5h5l2 -2h3l2 2.5l-2.5 3.5h-11z"/><path d="M15.5 13.5l2.5 3.5"/><path d="M17 7.5l2.5 -1"/>'),
    "truck": ("vehicles", "Off-roader", C,
        '<path d="M3 14v-7a1 1 0 0 1 1 -1h10l5 4h1a1 1 0 0 1 1 1v3z"/><path d="M14 6v4h5"/><circle cx="6.5" cy="17.5" r="2.8"/>'
        '<circle cx="17.5" cy="17.5" r="2.8"/><path d="M9.3 17.5h5.4"/>'),
    "ship": ("vehicles", "DHV Magellan", C,
        '<path d="M2 14l1.5 -4h13l3 3v2l-1.5 2h-14.5z"/><path d="M6 10v-2h6v2"/><path d="M9 8l11 -4.5"/><path d="M19.5 3.7v3"/>'
        '<path d="M19.5 15l3 5"/><path d="M5 17v2.5h8v-2.5"/>'),
    "decal": ("vehicles", "Vehicle decal", T + "sticker",
        '<path d="M20 12l-2 .5a6 6 0 0 1 -6.5 -6.5l.5 -2l8 8"/><path d="M20 12a8 8 0 1 1 -8 -8"/>'),
    "tire": ("vehicles", "Spiked tires", C,
        '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><path d="M12 3v3"/><path d="M12 18v3"/>'
        '<path d="M3 12h3"/><path d="M18 12h3"/><path d="M5.6 5.6l2.1 2.1"/><path d="M16.3 16.3l2.1 2.1"/>'
        '<path d="M5.6 18.4l2.1 -2.1"/><path d="M16.3 7.7l2.1 -2.1"/>'),
    "vehicle-battery": ("vehicles", "Vehicle battery unit", T + "battery-automotive",
        '<path d="M3 7a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2l0 -10"/><path d="M6 5v-2"/>'
        '<path d="M18 3v2"/><path d="M6.5 12h3"/><path d="M14.5 12h3"/><path d="M16 10.5v3"/>'),
    "vehicle-antigravity": ("vehicles", "Vehicle antigravity unit", C,
        '<path d="M3 13v-2l2 -4h10l3 4h2a1 1 0 0 1 1 1v1z"/><path d="M10 7v4"/><path d="M5 17h4"/><path d="M15 17h4"/>'
        '<path d="M9.5 20h5"/>'),
    "vehicle-armor": ("vehicles", "Vehicle armour", C,
        '<path d="M4 6h16l-2 12h-12z"/><path d="M7.5 9h.01"/><path d="M16.5 9h.01"/><path d="M8.5 15h.01"/>'
        '<path d="M15.5 15h.01"/><path d="M9 12h6"/>'),
    "vehicle-defense": ("vehicles", "Electrical defense unit", T + "shield-bolt",
        '<path d="M13.342 20.566c-.436 .17 -.884 .315 -1.342 .434a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3a12 12 0 0 0 8.5 3a12 12 0 0 1 .117 6.34"/>'
        '<path d="M19 16l-2 3h4l-2 3"/>'),
    "vehicle-gun": ("vehicles", "Mounted gun / cannon", C,
        '<path d="M4 6h8v5h-8z"/><path d="M12 7.5h9"/><path d="M12 9.5h6"/><path d="M8 11v4"/><path d="M5 15h6"/>'
        '<path d="M3 19h10"/><path d="M5 15l-1 4"/><path d="M11 15l1 4"/>'),
    "vehicle-launcher": ("vehicles", "Mounted launcher / mortar", C,
        '<path d="M4 12.5l11 -7l2.7 4.2l-11 7z"/><path d="M5.4 14.6l11 -7"/><path d="M10 15v3"/><path d="M5 21l2 -3h8l2 3"/>'),
    "active-defense": ("vehicles", "Active defense system", C,
        '<path d="M6 17a6 6 0 0 1 12 0"/><path d="M4 17h16v3h-16z"/><path d="M12 11v-2"/><path d="M8 6a6 6 0 0 1 8 0"/>'
        '<path d="M5.5 3.5a9.5 9.5 0 0 1 13 0"/>'),
    # ---- outfits, patches, holograms ----
    "hat": ("cosmetic", "Hat / hood / bandana", C,
        '<path d="M4 16v-1a7 7 0 0 1 14 0v1z"/><path d="M15 16h6a1 1 0 0 0 .6 -1.8l-2.6 -1.7"/>'
        '<path d="M11 8c-1.5 2 -2.2 4.6 -2.2 8"/><path d="M11 8v-.01"/>'),
    "glasses": ("cosmetic", "Glasses", T + "sunglasses",
        '<path d="M8 4h-2l-3 10"/><path d="M16 4h2l3 10"/><path d="M10 16h4"/><path d="M21 16.5a3.5 3.5 0 0 1 -7 0v-2.5h7v2.5"/>'
        '<path d="M10 16.5a3.5 3.5 0 0 1 -7 0v-2.5h7v2.5"/><path d="M4 14l4.5 4.5"/><path d="M15 14l4.5 4.5"/>'),
    "mask": ("cosmetic", "Mask", C,
        '<path d="M6 5c4 -2 8 -2 12 0v6.5c0 5 -3 8.5 -6 9.5c-3 -1 -6 -4.5 -6 -9.5z"/><path d="M8.5 10l2.5 1"/>'
        '<path d="M15.5 10l-2.5 1"/><path d="M10 16h4"/>'),
    "suit": ("cosmetic", "Suit (jumpsuit)", C,
        '<path d="M9 3h6l4 2.5l2 6.5l-2.5 1l-1.5 -3.5v11.5h-4l-1 -7l-1 7h-4v-11.5l-1.5 3.5l-2.5 -1l2 -6.5z"/>'
        '<path d="M7 13h10"/><path d="M12 4v9"/>'),
    "bb-pod": ("cosmetic", "BB pod pattern", C,
        '<path d="M12 3c3.5 0 6 2.8 6 6.5v5.5l-2 3h-8l-2 -3v-5.5c0 -3.7 2.5 -6.5 6 -6.5z"/><path d="M9 18v3h6v-3"/>'
        '<circle cx="12" cy="10" r="2"/>'),
    "palette": ("cosmetic", "Colour scheme", T + "palette",
        '<path d="M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.75a1.3 1.3 0 0 1 -1 2.25"/>'
        '<path d="M7.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/><path d="M11.5 7.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/>'
        '<path d="M15.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/>'),
    "patch": ("cosmetic", "Patch", C,
        '<path d="M5 4h14v8a7 7 0 0 1 -14 0z"/><path d="M8 7h8v5a4 4 0 0 1 -8 0z"/>'),
    "hologram": ("cosmetic", "Hologram", C,
        '<path d="M5 19.5a7 2 0 1 0 14 0a7 2 0 1 0 -14 0"/><circle cx="12" cy="6.5" r="2.5"/>'
        '<path d="M7.5 15.5v-1a4 4 0 0 1 4 -4h1a4 4 0 0 1 4 4v1"/><path d="M4 7h.01"/><path d="M20 5h.01"/>'
        '<path d="M19.5 11h.01"/><path d="M4.5 12.5h.01"/>'),
    "character": ("cosmetic", "Character", T + "user",
        '<path d="M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0"/><path d="M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"/>'),
    # ---- structures ----
    "bridge": ("structure", "Bridge", C,
        '<path d="M2 14h20"/><path d="M4 14c3 -8 13 -8 16 0"/><path d="M8 9.5v4.5"/><path d="M12 8v6"/><path d="M16 9.5v4.5"/>'
        '<path d="M5 14v6"/><path d="M19 14v6"/>'),
    "chiral-bridge": ("structure", "Chiral bridge", C,
        '<path d="M3 16c5 -8 13 -8 18 0"/><path d="M6 15c3.5 -4.5 8.5 -4.5 12 0"/><path d="M2 16h3"/><path d="M19 16h3"/>'),
    "postbox": ("structure", "Postbox", C,
        '<path d="M8 5a4 1.5 0 1 0 8 0a4 1.5 0 1 0 -8 0"/><path d="M8 5v13a4 1.5 0 0 0 8 0v-13"/><path d="M10 9.5h4"/>'
        '<path d="M5 21h14"/>'),
    "safe-house": ("structure", "Safe house", T + "home",
        '<path d="M5 12l-2 0l9 -9l9 9l-2 0"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7"/>'
        '<path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6"/>'),
    "shelter": ("structure", "Timefall shelter", T + "umbrella",
        '<path d="M4 12a8 8 0 0 1 16 0l-16 0"/><path d="M12 12v6a2 2 0 0 0 4 0"/>'),
    "watchtower": ("structure", "Watchtower", C,
        '<path d="M7 6l5 -3l5 3"/><path d="M8 6h8v4h-8z"/><path d="M9.5 10l-2.5 11"/><path d="M14.5 10l2.5 11"/>'
        '<path d="M8.6 15.5h6.8"/><path d="M5 21h14"/>'),
    "generator": ("structure", "Generator", C,
        '<path d="M9.5 2h5v20h-5z"/><path d="M12.6 7.5l-1.6 3h2l-1.6 3"/><path d="M9.5 17.5h5"/>'),
    "catapult": ("structure", "Cargo catapult", C,
        '<path d="M5 13.5l10 -8l2.5 3.2l-10 8z"/><path d="M15 5.5l1.5 -1.2l2.5 3.2l-1.5 1.2"/><path d="M9.5 15v6"/>'
        '<path d="M4 21h16"/><path d="M9.5 18l4 3"/>'),
    "zip-line": ("structure", "Zip-line", C,
        '<path d="M6 3v7a2 2 0 0 0 2 2h4a2 2 0 0 0 2 -2v-7"/><path d="M10 12v6"/><path d="M7 18h6v3h-6z"/><path d="M2 4.5l20 5"/>'),
    "transponder": ("structure", "Transponder", T + "antenna",
        '<path d="M20 4v8"/><path d="M16 4.5v7"/><path d="M12 5v16"/><path d="M8 5.5v5"/><path d="M4 6v4"/><path d="M20 8h-16"/>'),
    "jump-ramp": ("structure", "Jump ramp", C,
        '<path d="M3 19h18v-10c-7 0 -13 4 -18 10z"/><path d="M4 9l3 -4"/><path d="M4 5h3v3"/>'),
    "signboard": ("structure", "Signboard", C,
        '<path d="M5 4h14v9h-14z"/><path d="M12 13v8"/><path d="M9 21h6"/><path d="M8 7h8"/><path d="M8 10h5"/>'),
    "road": ("structure", "Road upgrade", T + "road",
        '<path d="M4 19l4 -14"/><path d="M16 5l4 14"/><path d="M12 8v-2"/><path d="M12 13v-2"/><path d="M12 18v-2"/>'),
    # ---- music / APAS ----
    "music": ("music", "Music", T + "music",
        '<path d="M3 17a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/><path d="M13 17a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/>'
        '<path d="M9 17v-13h10v13"/><path d="M9 8h10"/>'),
    "apas": ("apas", "APAS chip", T + "cpu",
        '<path d="M5 6a1 1 0 0 1 1 -1h12a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-12a1 1 0 0 1 -1 -1l0 -12"/>'
        '<path d="M9 9h6v6h-6l0 -6"/><path d="M3 10h2"/><path d="M3 14h2"/><path d="M10 3v2"/><path d="M14 3v2"/>'
        '<path d="M21 10h-2"/><path d="M21 14h-2"/><path d="M14 21v-2"/><path d="M10 21v-2"/>'),
    # ---- other (neutral) ----
    "rest": ("other", "Rest / private room", T + "bed",
        '<path d="M5 9a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M22 17v-3h-20"/><path d="M2 8v9"/>'
        '<path d="M12 14h10v-2a3 3 0 0 0 -3 -3h-7v5"/>'),
    "feature": ("other", "New feature", T + "sparkles",
        '<path d="M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6"/>'),
    "camera": ("other", "Camera", T + "camera",
        '<path d="M5 7h1a2 2 0 0 0 2 -2a1 1 0 0 1 1 -1h6a1 1 0 0 1 1 1a2 2 0 0 0 2 2h1a2 2 0 0 1 2 2v9a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-9a2 2 0 0 1 2 -2"/>'
        '<path d="M9 13a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/>'),
    "cryptobiote": ("other", "Cryptobiote", C,
        '<path d="M4 14a4 4 0 0 1 4 -4h8a4 4 0 0 1 4 4v1a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2z"/><path d="M9 10v7"/>'
        '<path d="M13 10v7"/><path d="M7 17v2"/><path d="M11 17v2"/><path d="M15 17v2"/><path d="M17 13.5h.01"/>'),
    "crystal": ("other", "BT crystal", C,
        '<path d="M12 3l3 5l-3 13l-3 -13z"/><path d="M9 8h6"/><path d="M7.5 9.5l-2.5 3l2.5 7"/><path d="M16.5 9.5l2.5 3l-2.5 7"/>'),
    "hot-spring": ("other", "Hot spring", C,
        '<path d="M5 14c-1.3 .9 -2 1.9 -2 3c0 2.2 4 4 9 4s9 -1.8 9 -4c0 -1.1 -.7 -2.1 -2 -3"/>'
        '<path d="M8 16c-1.5 -2 1.5 -3.5 0 -5.5s1.5 -3.5 0 -5.5"/><path d="M12 16c-1.5 -2.2 1.5 -4 0 -6.2s1.5 -4 0 -6.3"/>'
        '<path d="M16 16c-1.5 -2 1.5 -3.5 0 -5.5s1.5 -3.5 0 -5.5"/>'),
    "rope": ("other", "Strand (rope)", C,
        '<path d="M3.5 15.1a9 3.5 -20 1 1 16.9 -6.2a9 3.5 -20 1 1 -16.9 6.2"/><path d="M5.4 14.4a7 1.5 -20 1 1 13.2 -4.8a7 1.5 -20 1 1 -13.2 4.8"/>'
        '<path d="M9.4 9.1l2.4 6.8"/><path d="M12.2 8.1l2.4 6.8"/><path d="M16 15c1 2.5 3 4.5 5.5 5.5"/>'),
    "misc": ("other", "Other", T + "box",
        '<path d="M12 3l8 4.5l0 9l-8 4.5l-8 -4.5l0 -9l8 -4.5"/><path d="M12 12l8 -4.5"/><path d="M12 12l0 9"/>'
        '<path d="M12 12l-8 -4.5"/>'),
}

RULES_KEY = {}
# (category or "*", regex on "name | subrig") -> kind; first match within the category wins
RULES_NAME = [
    ("Weapons", r"\| Magellan$", "airstrike"),  # DHV Magellan support weapons (fireworks, cluster bomb, hunters)
    ("Weapons", r"Handgun|Pistol", "handgun"),
    ("Weapons", r"Sniper", "sniper"),
    ("Weapons", r"Shotgun", "shotgun"),
    ("Weapons", r"Machine Gun", "machine-gun"),
    ("Weapons", r"Assault Rifle", "rifle"),
    ("Weapons", r"Grenade Launcher", "grenade-launcher"),
    ("Weapons", r"(?i)rocket", "rocket-launcher"),
    ("Weapons", r"Cannon", "cannon"),
    ("Weapons", r"Bola", "bola"),
    ("Weapons", r"Sticky Gun", "sticky-gun"),
    ("Weapons", r"Sentry", "sentry"),
    ("Weapons", r"Shield", "shield"),
    ("Weapons", r"Pizza", "pizza"),
    ("Weapons", r"Mine\b", "dog-mine"),
    ("Weapons", r"Electric Trap", "electric-trap"),
    ("Weapons", r"Boomerang", "boomerang"),
    ("Weapons", r"Blood Grenade", "grenade-blood"),
    ("Weapons", r"^EX ", "grenade-ex"),
    ("Weapons", r"Stun Bomb", "grenade-stun"),
    ("Weapons", r"Smoke", "grenade-smoke"),
    ("Weapons", r"Gas Grenade", "grenade-gas"),
    ("Weapons", r"Hologrenade", "grenade-holo"),
    ("Weapons", r"Grenade|Bomb", "grenade"),
    ("Equipment", r"Blood Bag", "blood-bag"),
    ("Equipment", r"Floating Carrier", "floating-carrier"),
    ("Equipment", r"Coffin Board", "coffin-board"),
    ("Equipment", r"Oxygen Mask", "oxygen-mask"),
    ("Equipment", r"Canteen", "canteen"),
    ("Equipment", r"Thermal", "thermal"),
    ("Equipment", r"Spray", "spray"),
    ("Equipment", r"Ladder", "ladder"),
    ("Equipment", r"Climbing Anchor", "anchor"),
    ("Equipment", r"Guidepost", "guidepost"),
    ("Equipment", r"PCC", "pcc"),
    ("Backpack Attachments", r"Ammo", "ammo"),
    ("Backpack Attachments", r"Solar Generator", "solar"),
    ("Backpack Attachments", r"Battery", "battery"),
    ("Backpack Attachments", r"Antigravity", "antigravity"),
    ("Backpack Attachments", r"Protector", "protector"),
    ("Backpack Attachments", r"Electric", "shock-absorber"),
    ("Backpack Attachments", r"Pouch", "pouch"),
    ("Backpack Attachments", r"Resuscitation", "aed"),
    ("Backpack Attachments", r"Stabilizer", "stabilizer"),
    ("Outfits", r"\| Mask\b", "mask"),
    ("Vehicles", r"Tri-Cruiser|\| Moto\b", "trike"),
    ("Vehicles", r"Off-Roader|\| Truck\b", "truck"),
    ("Vehicles", r"Mortar|Rocket Launcher", "vehicle-launcher"),
    ("Vehicles", r"Cannon|Machine Gun", "vehicle-gun"),
    ("Vehicles", r"Active Defense", "active-defense"),
    ("Vehicles", r"Battery", "vehicle-battery"),
    ("Vehicles", r"Antigravity", "vehicle-antigravity"),
    ("Vehicles", r"Electrical", "vehicle-defense"),
    ("Vehicles", r"Armor", "vehicle-armor"),
    ("Vehicles", r"Tires", "tire"),
    ("Structures", r"Chiral Bridge", "chiral-bridge"),
    ("Structures", r"Bridge", "bridge"),
    ("Structures", r"Postbox", "postbox"),
    ("Structures", r"Safe House", "safe-house"),
    ("Structures", r"Shelter", "shelter"),
    ("Structures", r"Watchtower", "watchtower"),
    ("Structures", r"Generator", "generator"),
    ("Structures", r"Catapult", "catapult"),
    ("Structures", r"Zip-Line", "zip-line"),
    ("Structures", r"Transponder", "transponder"),
    ("Structures", r"Jump Ramp", "jump-ramp"),
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
    ("Features", r"Jump Ramp", "jump-ramp"),
    ("Features", r"Road", "road"),
    ("Other", r"Signboard", "signboard"),
    ("Other", r"biote|\| Grb", "cryptobiote"),
    ("Other", r"Strand", "rope"),
    ("Other", r"Harmonica", "music"),
    ("Other", r"Dollman Cam", "camera"),
]
# (category, subcategory or None = any) -> kind
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
    ("Vehicles", None): "truck",
    ("Structures", None): "signboard",
    ("APAS rewards from facilities", None): "apas",
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
    for cat, rx, kind in RULES_NAME:
        if cat in ("*", row["cat"]) and re.search(rx, text):
            return kind
    return RULES_CAT.get((row["cat"], row["sub"])) or RULES_CAT.get((row["cat"], None)) or "misc"


# ---------- path minifier: one <path>, coordinates rounded to STEP (0.1) ----------
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")
ARGS = {"m": 2, "l": 2, "t": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "a": 7, "z": 0}
STEP = 0.1


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)


def snap(v):
    return round(round(v / STEP) * STEP, 6)


def minify_path(d):
    """Round coordinates to STEP, tracking the exact and the rounded pen so relative rounding errors do not add up.
    A dot ("h.01") keeps a 0.1 length so it still renders with round caps."""
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
            sys.exit(f"compact arc flags not supported: {toks[i:i + n]}")
        i += n
        base, base_s = (pen, pen_s) if rel else ([0.0, 0.0], [0.0, 0.0])
        if lc in "hv":
            ax = 0 if lc == "h" else 1
            x = base[ax] + args[0]
            xs = snap(x)
            if xs == pen_s[ax] and args[0] != 0:  # keep dots visible
                xs = round(pen_s[ax] + (STEP if args[0] > 0 else -STEP), 6)
            emit(xs - base_s[ax])
            pen = pen[:]; pen_s = pen_s[:]
            pen[ax], pen_s[ax] = x, xs
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
            cmd = "l" if rel else "L"
    return "".join(out)


def circle_to_path(cx, cy, r):
    cx, cy, r = float(cx), float(cy), float(r)
    return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0"


def to_d(markup):
    parts = []
    for tag, attrs in re.findall(r"<(path|circle)\s+([^>]*?)/?>", markup):
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        parts.append(a["d"] if tag == "path" else circle_to_path(a["cx"], a["cy"], a["r"]))
    left = re.sub(r"<(path|circle)\s+[^>]*?/?>", "", markup).strip()
    if left:
        sys.exit(f"unsupported markup: {left[:60]}")
    return "".join(minify_path(p) for p in parts)


SVG_HEAD = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
            "stroke-linecap='round' stroke-linejoin='round'>")


def svg_of(kind):
    return f"{SVG_HEAD}<path d='{to_d(ICONS[kind][3])}'/></svg>"


# ---------- outputs ----------
MIT = """MIT License

Copyright (c) 2020-2026 Paweł Kuna

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


def write_credits(used):
    tab = sorted(k for k in used if ICONS[k][2].startswith(T))
    own = sorted(k for k in used if ICONS[k][2] == C)
    lines = [
        "# Unlock icons: credits", "",
        "The viewer shows one outline icon per kind of unlock (stored in `catalog/generic_icons.json`, built by",
        "`catalog/build_icons_d.py`). Style: 24×24 grid, 2px round stroke, no fill, coloured by the viewer via `currentColor`.", "",
        "The game's own item pictures are copyrighted and are **not included**. While drawing, they were looked at privately",
        "only as a shape reference (overall silhouette and proportions, e.g. that the Tri-Cruiser is a low three-wheeler);",
        "nothing was traced, and no details, logos, decals or colours were copied.", "",
        f"## Tabler Icons ({len(tab)} icons)", "",
        "From [Tabler Icons](https://github.com/tabler/tabler-icons) (outline set), MIT License,",
        "Copyright (c) 2020-2026 Paweł Kuna. Change made to all of them: path coordinates rounded to 0.1 and merged into one",
        "path; marked “modified” where the drawing itself was changed.", "",
        "| Kind | Tabler icon | Note |", "|---|---|---|",
    ]
    for k in tab:
        src = ICONS[k][2][len(T):]
        mod = src.endswith("+")
        name = src.rstrip("+")
        lines.append(f"| `{k}` | [{name}](https://tabler.io/icons/icon/{name}) | "
                     f"{'modified (knuckle line added)' if mod else 'as published'} |")
    lines += ["", "Licence text (applies to the icons listed above):", "", "```", MIT, "```", "",
              f"## Drawn for Peko-Check ({len(own)} icons)", "",
              "Drawn for this project on the same grid and stroke, offered under the same MIT terms as the repository:", "",
              ", ".join(f"`{k}`" for k in own) + ".", ""]
    CREDITS.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_preview(rows, mapping, icons, tint):
    by_kind = collections.defaultdict(list)
    for r in rows:
        k = mapping.get(r["key"])
        if k and r["name"] not in by_kind[k]:
            by_kind[k].append(r["name"])
    count = collections.Counter(mapping.values())
    order = [k for f in FAMILIES for k in ICONS if ICONS[k][0] == f and k in icons]

    def card(k):
        fam = ICONS[k][0]
        _, cd, cl, _ = FAMILIES[fam]
        ex = "".join(f"<li>{html.escape(n)}</li>" for n in by_kind[k][:3])
        return (f'<figure style="--c:{cd};--cl:{cl}"><div class="ic">{icons[k]}</div>'
                f'<figcaption><b>{k}</b><i>{count[k]} · {html.escape(ICONS[k][1])}</i><ul>{ex}</ul></figcaption></figure>')

    sections = []
    for f, (tn, cd, cl, label) in FAMILIES.items():
        ks = [k for k in order if ICONS[k][0] == f]
        if ks:
            sections.append(f'<h2 style="--c:{cd};--cl:{cl}">{html.escape(label)} <small>{tn or "no tint"} · {len(ks)}</small></h2>'
                            f'<div class="grid">{"".join(card(k) for k in ks)}</div>')
    body = "".join(sections)
    strip = "".join(f'<span style="--c:{FAMILIES[ICONS[k][0]][1]};--cl:{FAMILIES[ICONS[k][0]][2]}">{icons[k]}</span>' for k in order)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Unlock Icons D</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#0b1724;--panel:#10202f;--fg:#dbe6ef;--mute:#8fa3b4;--line:#1f3346}}
body{{margin:0;background:#18222d;color:var(--fg);font:13px system-ui,sans-serif;padding:16px}}
h1{{font-size:18px;margin:0 0 4px}} p{{margin:0 0 10px;color:var(--mute)}}
.theme{{padding:12px 14px;border-radius:8px;margin-bottom:16px;background:var(--bg)}}
.theme.light{{--bg:#f3f0e8;--panel:#fffdf8;--fg:#1c2b3a;--mute:#5d6b78;--line:#d9d2c4;color:var(--fg)}}
figure,h2,.strip span{{--k:var(--c)}} .theme.light figure,.theme.light h2,.theme.light .strip span{{--k:var(--cl)}}
h2{{font-size:13px;margin:14px 0 6px;color:var(--k);letter-spacing:.08em;text-transform:uppercase}} h2 small{{color:var(--mute);letter-spacing:0;text-transform:none}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}}
figure{{margin:0;display:flex;gap:10px;align-items:flex-start;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:8px}}
.ic{{flex:none;width:60px;height:46px;display:grid;place-items:center;border:1.5px solid var(--k);border-radius:4px;color:var(--fg);
  box-shadow:inset 0 0 0 3px color-mix(in srgb,var(--k) 14%,transparent)}}
.ic svg{{width:30px;height:30px;stroke-width:1.5}}
figcaption{{min-width:0;font-size:11px;line-height:1.35}} figcaption b{{display:block;font-size:12px;color:var(--k)}}
figcaption i{{display:block;font-style:normal;color:var(--mute)}} ul{{margin:2px 0 0;padding-left:14px;color:var(--fg)}}
li{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.strip{{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 4px}} .strip span{{color:var(--k)}} .strip svg{{width:24px;height:24px;display:block}}
.strip.big svg{{width:24px;height:24px;stroke-width:2}}
</style></head><body>
<h1>Unlock icons, style D ({len(icons)} kinds)</h1>
<p>Built by catalog/build_icons_d.py. {len(mapping)} visible unlocks mapped. Frame colour = tint family. Viewer size (30 px, stroke 1.5) in the cards; strip below = 24 px at stroke 2.</p>
<div class="theme dark"><div class="strip">{strip}</div>{body}</div>
<div class="theme light"><div class="strip">{strip}</div>{body}</div>
</body></html>
"""
    PREVIEW.write_text(page, encoding="utf-8", newline="\n")


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    mapping, cov = {}, collections.defaultdict(collections.Counter)
    for r in rows:
        if not r["cat"]:
            continue
        kind = assign(r)
        if kind not in ICONS:
            sys.exit(f"rule gives unknown kind {kind!r} for {r['key']} {r['name']}")
        mapping[r["key"]] = kind
        cov[(r["cat"], r["sub"])][kind] += 1
    used = [k for k in ICONS if k in set(mapping.values())]
    icons = {k: svg_of(k) for k in used}
    tint = {k: FAMILIES[ICONS[k][0]][0] for k in used if FAMILIES[ICONS[k][0]][0]}
    OUT.write_text(json.dumps({"icons": icons, "map": dict(sorted(mapping.items())), "tint": tint},
                              ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    write_credits(used)
    if PREVIEW.parent.is_dir():  # research checkout only
        write_preview(rows, mapping, icons, tint)

    visible = sum(1 for r in rows if r["cat"])
    unmapped = [r["name"] for r in rows if r["cat"] and r["key"] not in mapping]
    print(f"{len(mapping)}/{visible} visible unlocks mapped ({len(rows) - visible} hidden skipped); "
          f"{len(icons)} kinds used of {len(ICONS)}; {OUT.name} {OUT.stat().st_size / 1024:.1f} KB")
    if unmapped:
        print("  UNMAPPED:", unmapped)
    unused = [k for k in ICONS if k not in icons]
    if unused:
        print("  unused kinds:", ", ".join(unused))
    for (cat, sub), c in sorted(cov.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        print(f"  {cat}{' / ' + sub if sub else ''}: {sum(c.values())} -> "
              + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    if "misc" in icons:
        print("  misc fallback:", ", ".join(sorted({r["name"] for r in rows if mapping.get(r["key"]) == "misc"})))


if __name__ == "__main__":
    main()
