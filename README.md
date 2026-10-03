<p align="center"><img src="assets/logo.svg" width="128" height="128" alt=""></p>

<h1 align="center">Peko-Check <sup>Lv1</sup></h1>

<p align="center"><b>See your Death Stranding 2 progress straight from your save: every order, every unlock, every route.</b><br>
<i>"Commencing peko-check at once!"</i></p>

<p align="center">
  <a href="https://github.com/binsento-netizen/ds2-peko-check/actions/workflows/check.yml"><img src="https://github.com/binsento-netizen/ds2-peko-check/actions/workflows/check.yml/badge.svg" alt="publication check"></a>
  <img src="https://img.shields.io/badge/Death%20Stranding%202-PC%201.10.89-f08a2c" alt="Death Stranding 2 PC 1.10.89">
  <img src="https://img.shields.io/badge/runs%20in-your%20browser-1f7a55" alt="runs in your browser">
  <img src="https://img.shields.io/badge/your%20save-never%20uploaded-1f7a55" alt="your save is never uploaded">
  <img src="https://img.shields.io/badge/saves-read--only-5fc9f2" alt="read-only">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-5fc9f2" alt="MIT licence"></a>
  <img src="https://img.shields.io/badge/fan%20project-unofficial-8aa3b2" alt="unofficial fan project">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/screenshots/overview-dark.png">
    <img src="assets/screenshots/overview.png" width="820" alt="Peko-Check showing a save: order totals, likes, unlocks, and a facility with its connection level, material stock and rewards">
  </picture>
</p>

Open a save and Peko-Check shows which orders are done, in progress, available or still locked; how far each
facility's connection level has come and what each level unlocks; which weapons, gear and vehicle parts you have;
and the routes you travelled. Compare two saves to see exactly what changed in between.

**Your save never leaves your computer.** The page decodes it in your browser and uploads nothing. The tools only
read saves; they never write to them.

## Quick start

1. Open the viewer: `viewer/index.html` in any modern browser (a hosted copy will follow).
2. Click **Open save** and pick a file from
   ```
   Documents\DEATH STRANDING 2 - ON THE BEACH\<your Steam ID>\
   ```
   Any `autosave`, `checkpointsave` or `manualsave` works; `profile.dat` only holds settings.
3. Browse the tabs. To see what one play session changed, open the later save, then **Compare with…** the earlier
   one (or drop both files at once).

## Features

- **Main orders as a story timeline**, episode by episode: which order you are on, what is done and what is still
  locked, and what each order unlocks.
- **Standard orders per facility**, with the facility's connection level (stars), its material stock and the rewards
  of every level, ticked once you have them.
- **Unlocks** (weapons, gear, outfits, vehicles and vehicle parts) by category, with "unlocked by" links that jump
  to the order or facility level that gives them, and back. Collab and event items and firmware updates are tagged.
- **Routes**: the map's "previous routes", split into on foot and by vehicle (see [Map](#map)).
- **Cargo**: what Sam has equipped and in the backpack, and what is in your **private locker at each facility**,
  with material totals (partly used stacks included).
- **APAS**: every enhancement, marked developed, available or not yet available.
- **Likes**: from NPCs, from other porters, and given. The save card also shows the **in-game day and time**.
- **Save check**: every save is verified against its own built-in checksum, so a damaged or wrong file is caught.
- **Compare two saves**: orders that changed state, new unlocks, new route segments and a byte diff of every save
  section, with a copyable text report.
- **Light and dark look**, following your system setting.
- Order numbers and names come from the **game's own mission data**, so they match what you see in-game.
- Guide links per order: Game8 walkthroughs for main orders, otherwise Game8 or the Death Stranding Wiki.

<p align="center">
  <img src="assets/screenshots/weapons.png" width="49%" alt="Weapon unlocks with item pictures, unlocked and locked state, and the order or facility level that unlocks each">
  <img src="assets/screenshots/standard-orders.png" width="49%" alt="Standard orders for Ciudad Nudo del Norte: connection level, material stock, level rewards and each order's state">
</p>
<p align="center"><sub>Shown with the item pictures and mini-maps of the private build. The public version shows the same lists without game art.</sub></p>

## Map

The save keeps the routes you travelled since your last main order (the map's "previous routes"), one point roughly
every 10 metres, marked as on foot or by vehicle. Peko-Check draws them as lines on a plain background, with the
oldest and latest point marked.

The game's own map image, facility icons and item pictures are copyrighted game assets, so they are not part of this
repository and the viewer here shows none of them. Order and facility names are text from the game's data.

<p align="center"><img src="assets/screenshots/map.png" width="820" alt="The Australia map with facility icons ringed by order progress, routes by vehicle and the layers box"><br>
<sub>The map view of the private build, drawn from the game's own 3D map data with facility icons and your routes. The public version draws the same routes on a plain background.</sub></p>

## What it can read

| Area | State |
|---|---|
| File container (XOR key, chunk table, LZ4, metadata, thumbnail) | Solved |
| Save framework (header, MD5, string/GUID pools, 222-section directory) | Solved |
| Orders: done / in progress / available / locked | Solved; all 474 orders matched to their number from the game's mission lists |
| Unlocks: weapons, gear, outfits, vehicle parts | Solved; what unlocks each item (order or facility level) from the game's catalogue |
| Facility connection levels, material stock, chiral bandwidth | Solved |
| Likes (from NPCs, from other porters, given) | Solved |
| Route history (the map's "previous routes") | Solved; fast travel starts a new segment |
| Cargo: equipped, backpack, private lockers per facility, material amounts | Solved; locker-to-facility link confirmed in game for 3 facilities, the rest inferred |
| APAS enhancements (developed / available) | Solved |
| In-game day and time of day | Solved |
| Signs placed in the world | Partly (positions and types; whose sign is open) |
| Partial stars (connection points toward the next level) | Open (thresholds known, counter not found) |
| Music, hologram, structure and colour unlock state | Open (not in the unlock catalogue; leads) |
| Built structures, route planner, auto-paver progress | Open (paver progress seems to live on the server) |

The file format is documented in [docs/FORMAT.md](docs/FORMAT.md).

## How you can help

Most of what Peko-Check knows came from **save pairs**: save, do exactly one thing in the game, save again, and
compare. The pieces still missing need more of those, ideally from players other than the original tester. You
don't need to share your save file: the **Compare with…** report contains no personal data and is enough for most
questions.

**How to send a result**
1. Make a manual save, do the one action below and nothing else, make another manual save.
2. Open the later save in Peko-Check, click **Compare with…** and pick the earlier one.
3. Click **Copy report** and paste it into a [new issue](../../issues/new/choose), with what you did and what the game
   showed (a photo of the screen helps).

Please don't attach `.dat` files to public issues: a save contains your Steam ID and other players' names.

**Wanted**

| Test | What to do | Why |
|---|---|---|
| Music or hologram | Save right before and after a reward that gives one song or hologram, with nothing else happening | Find where music and hologram unlocks are stored |
| Structure unlock | Save before and after a connection level that unlocks a new structure type | Same, for structures |
| Star fill | Note how full a facility's next star is, make one delivery there without levelling up, note it again | Find the connection points behind the partial stars |
| Collectible | Save before and after picking up a memory chip or another collectible | Collectibles for the map |
| Your own sign | Place one sign, save, then check the report | Tell your own signs apart from other players' |
| Private lockers | Open the Cargo tab and compare one locker with the game's locker screen | Confirm which facility each locker belongs to, especially in eastern Australia |
| Mexico map | Compare the Map tab's Mexico with the in-game map | Only the central strip has colour data; is the rest grey in the game too? |
| Other game versions | Open a save from a newer patch | Check nothing moved |

Bug reports and ideas are welcome as issues too. See [ROADMAP.md](ROADMAP.md) for where the project came from and
what is next.

## Build it yourself

```bash
pip install lz4
./setup.sh                                        # enables the publication check hooks
python catalog/build_catalog.py                   # mission id -> order number/name catalogue (from the repo root)
python viewer/build_viewer_data.py --no-sample    # catalogue + labels -> viewer/viewer_data.json
python viewer/build_page.py                       # -> viewer/index.html, one self-contained page
python tools/ds2_savestate.py path/to/manualsave0.dat   # print a save's sections
```

## Privacy and publication check

The repository never contains save files, personal data, game assets or copied third-party text.
`tools/public_check.py` enforces that as a pre-commit and pre-push hook (`setup.sh` enables them, or
`git config core.hooksPath .githooks`) and in CI on every push and pull request. The only images allowed are this
project's own logo and screenshots of its own interface.

## Credits

- Game data (orders, unlocks, names): read from the game itself with [ShadelessFox/odradek](https://github.com/ShadelessFox/odradek).
- Decima save framework: [Nukem9/HZDCoreEditor](https://github.com/Nukem9/HZDCoreEditor).
- Container key derivation: [mi5hmash/DeathStrandingSaveDataResigner](https://github.com/mi5hmash/DeathStrandingSaveDataResigner).
- Guide links: [Game8](https://game8.co/games/Death-Stranding-2-On-the-Beach) and the [Death Stranding Wiki](https://deathstranding.fandom.com/).

Details and licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Code: MIT, see [LICENSE](LICENSE).

Fan project, not affiliated with or endorsed by Kojima Productions, Sony Interactive Entertainment, hololive
production or COVER Corporation.
