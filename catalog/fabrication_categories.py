"""Categorise the 903-entry unlock catalogue (DSGameCatalogueListItem) for the viewer, from the game's own fields.

Input: one row of catalog/unlock_items.json (built by catalog/build_unlock_items.py from an Odradek export). The
fields used, all from the game data:
  ui_tab      DSGameCatalogueListItem.UITabType (EDSGameCatalogueListItem_UITabType: Weapon, Equipment, BackPack,
              Vehicle, Magellan, DeliveryMachine, Costume*, BBPod, Dollman, RawMaterial)
  usage       .Usage (All = fabrication, BackPackCustomize, CostumeCustomize, VehicleCustomize, Vehicle, None)
  contents    type of Baggage -> Contents (Commodity, Equipment, Weapon, RawMaterial)
  subrig      Contents.SubRigIconType (EDSUISubRigIconType: the item's icon kind, e.g. Skeleton, BpPatch, Asr, Decal)
  unlock_cat  Contents.LocalizedUnlockCategoryText, English (the game's own unlock heading: "Weapon Data",
              "Structure Data", "FIRMWARE UPDATE", "APAS Enhancement", "Music Data", ...)
  reward      RewardResource.Type (EDSCatalogueRewardItemType: Holo, Sound, Onsen)
  holo_variant  hologram entry X1..X9 in a SortIndex block of ten whose X0 entry is the plain hologram (see below)
Top-level names follow Game8's DS2 categories (Weapons, Skeletons, Boots, Backpack Attachments, Outfits, Vehicles);
the order shown is CAT_ORDER in viewer/template.html.
"""

# EDSUISubRigIconType of weapons -> viewer subcategory
WEAPON_SUB = {
    **dict.fromkeys(["Asr", "Shg", "Hag", "Mag3", "Snpr", "Tri"], "Guns"),
    **dict.fromkeys(["Granade", "Bgdg", "Ewal"], "Grenades, bombs & traps"),
    **dict.fromkeys(["Mrod", "Bboom", "Erai"], "Melee"),
    **dict.fromkeys(["Grl", "Cannon", "Mis", "Blg", "Fsld", "Thm0", "PizzaRubber", "Mag"], "Heavy & special"),
    "Magellan": "Support weapons",   # DHV Magellan support attacks (Golden Hunters, Fireworks, Chiral Cluster Bomb)
}
NOT_WEAPONS = {"Strd", "Urinate", "Dollman"}   # Strand, Urination, Dollman Cam: actions on the weapon wheel
# UITabType of outfit items -> viewer subcategory (the game's Customize Look tabs)
COSTUME_SUB = {"CostumeSuit": "Suits", "Dollman": "Suits", "CostumeCap": "Hats & Hoods", "CostumeHood": "Hats & Hoods",
               "CostumeMask": "Glasses & Masks", "CostumeSunGlasses": "Glasses & Masks", "BBPod": "BB Pod patterns"}
STRUCTURE_ICONS = {"Bridge", "Catapult", "Charger", "Chiralbridge", "Jumpramp", "Post", "Rainproof", "Safetyhouse",
                   "Stopover", "Watchtower", "Zipline"}


def categorise(it):
    """(category, subcategory) for one catalogue item; category None = hide from the list."""
    name, tab, use, con, rig, ucat = it["name"], it["ui_tab"], it["usage"], it["contents"], it["subrig"] or "", it["unlock_cat"] or ""
    if not name:
        return None, None                                   # no English name in the game data
    if con == "RawMaterial":
        return None, None                                   # materials: withdrawable at every facility, not an unlock
    if rig == "BpPatch":
        return "Patches", None
    if rig == "Skeleton":
        return "Skeletons", None
    if rig == "Boots":
        return "Boots", None
    if rig.startswith("BT"):
        return "Collectibles", "BT crystals"
    if rig == "CoHologram":
        return ("Character rewards" if it["holo_variant"] else "Holograms"), None
    if it["reward"] == "Sound" or rig in ("CoMusic", "MpMusic"):
        return "Music", None
    if it["reward"] == "Onsen" or rig in ("CoOnsen", "Hotspringdigger"):
        return "Hot springs", None
    if tab in ("CostumeCap", "CostumeHood", "CostumeMask", "CostumeSunGlasses", "CostumeSuit") or use == "CostumeCustomize":
        return "Outfits", COSTUME_SUB.get(tab, "Suits")
    if use == "BackPackCustomize":
        return "Backpack Attachments", "Charms" if rig == "BpAccessories" else "Attachments"
    if rig == "Decal":
        return "Vehicles", "Vehicle decals"
    if use == "Vehicle":
        return "Vehicles", "Vehicles"
    if use == "VehicleCustomize":
        return "Vehicles", "Vehicle parts"
    if tab == "Magellan" and ucat != "Special Item":
        return "Vehicles", "DHV Magellan"                   # DHV Magellan paint schemes
    if tab in ("Vehicle", "BackPack") and con == "Commodity" and use == "None" and rig == "Invalid":
        return "Outfits", "Color schemes"                   # colour lists (one for vehicles, one for the backpack)
    if ucat == "Structure Data" or rig in STRUCTURE_ICONS:
        return "Structures", "Structures"
    if con == "Weapon" and tab == "DeliveryMachine":
        return "Equipment", "Tools"                         # PCC, ladder, climbing anchor, repair spray, guidepost
    if con == "Weapon" and rig not in NOT_WEAPONS:
        return "Weapons", WEAPON_SUB.get(rig, "Heavy & special")
    if rig == "Gloves":
        return "Equipment", "Gloves"
    if use == "All" or ucat in ("Gear Data", "Item Data") or rig == "Cant":
        return "Equipment", "Gear"                          # blood bags, canteens, floating carriers, coffin board ...
    if ucat == "APAS Enhancement":
        return "APAS enhancements", None
    if rig == "Karate":
        return "Melee techniques", None
    if ucat == "FIRMWARE UPDATE" or rig in ("Camera", "Odra"):
        return "Features", None                             # firmware updates, plus the Instant Camera and Odradek Light
    return "Other", None


ABOUT = {
    "Holograms": "Custom holograms you can show on structures you build: characters, preppers, animals and Ludens Duck colours.",
    "Character rewards": "Extra poses for a character's hologram (Like!, Praise, Greeting, ...), mostly three per person, "
                         "unlocked as your connection level with them rises.",
    "Music": "Tracks for the music player. Many songs have two or three entries in the game's catalogue; they are shown once here.",
    "Hot springs": "Items you can add to hot springs.",
    "Features": "Firmware updates: facility services and game features, for example resting at a facility (one entry per facility).",
    "APAS enhancements": "Enhancements for the APAS.",
    "Melee techniques": "Pizza-Do fighting techniques.",
    "Collectibles": "BT crystals.",
    "Structures": "Structures you can build with the PCC.",
}
