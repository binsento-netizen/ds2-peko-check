<p align="center"><img src="assets/logo.svg" width="128" height="128" alt=""></p>

<h1 align="center">Peko-Check <sup>Lv1</sup></h1>

<p align="center"><b>See your Death Stranding 2 progress straight from your save: every order, every unlock, every locker.</b><br>
<i>"Commencing peko-check at once!"</i></p>

<p align="center">
  <img src="https://img.shields.io/badge/Death%20Stranding%202-PC%20(Steam)%201.10.89-f08a2c" alt="Death Stranding 2, PC (Steam), game version 1.10.89">
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

Open your save and Peko-Check shows which orders you've done and which are still open, how far each facility's
connection has come and what the next level gives you, which weapons and gear you have, what is in your private
locker at every facility, and where you travelled. Compare two saves to see exactly what one play session changed.

**Your save never leaves your computer.** The page reads it in your browser and uploads nothing, and it never
changes your save.

## Quick start

1. Open **[binsento-netizen.github.io/ds2-peko-check](https://binsento-netizen.github.io/ds2-peko-check/)**.
   No install needed. Want to look around first? Click **View an example save**. (You can also download this
   repository and open `viewer/index.html`; it works offline.)
2. Click **Open save** and pick a save file. They are in
   ```
   Documents\DEATH STRANDING 2 - ON THE BEACH\<a long number>\
   ```
   If Windows syncs your Documents folder to Microsoft's cloud storage, the folder is in that synced Documents
   folder instead. The long number is your Steam ID. Any `manualsave`, `autosave` or `checkpointsave` file works.
3. Browse the tabs. To see what a play session changed, open your newest save, click **Compare with…** and pick an
   older one.

Works with the PC (Steam) version of Death Stranding 2. Console saves are not supported.

## What you can see

- **Main orders as a story timeline**, episode by episode: where you are in the story, what's done and what's still
  locked, and what each order unlocks.
- **Standard orders per facility**, with the facility's connection level (stars), its material stock and what every
  level unlocks, ticked once you have it.
- **Unlocks**: weapons, gear, outfits, vehicles and more, by category. Each one links to the order or facility level
  that unlocks it. Collab items, event items and firmware updates are marked.
- **Cargo**: what Sam has equipped and in the backpack, and what is in your **private locker at each facility**,
  including how much of each material.
- **APAS**: every enhancement, marked developed, available to develop, or not available yet.
- **Routes**: the routes the in-game map shows as "previous routes", split into on foot and by vehicle.
- **Likes** from NPCs, from other porters and given, and the **in-game day and time** of the save.
- **Save check**: each save is checked against its own built-in checksum, so a damaged file is spotted.
- **Compare two saves**: which orders changed, what got unlocked and where you travelled in between, with a report
  you can copy (useful for [helping out](#how-you-can-help)).
- Order names and numbers come from the **game's own data**, so they match what you see in the game.
- Guide links for every order (Game8 or the Death Stranding Wiki), and a **light and dark look**.

<p align="center">
  <img src="assets/screenshots/weapons.png" width="49%" alt="Weapon unlocks with item pictures, unlocked and locked state, and the order or facility level that unlocks each">
  <img src="assets/screenshots/standard-orders.png" width="49%" alt="Standard orders for Ciudad Nudo del Norte: connection level, material stock, level rewards and each order's state">
</p>

### About the pictures and the map

The screenshots above and below come from the developer's own copy, which also shows the game's item pictures, a
small map per facility, and a full map. Those images are copyrighted game assets, so they are **not** included here.
The viewer you can open from this page shows the same lists without the pictures, and draws your routes on a plain
background instead of the game's map.

<p align="center"><img src="assets/screenshots/map.png" width="820" alt="The Australia map with facility icons ringed by order progress, routes by vehicle and the layers box"><br>
<sub>The developer's copy: the game's map with facility icons and your routes. The viewer here draws the same routes without the map image.</sub></p>

## What it can read

| Part of the save | Status |
|---|---|
| Orders: done, in progress, available, locked | ✅ All 474 orders, with their in-game numbers |
| Unlocks: weapons, gear, outfits, vehicles and vehicle parts | ✅ Including what unlocks each one |
| Facilities: connection level, material stock | ✅ |
| Cargo: equipped, backpack, private lockers, material amounts | ✅ Which facility a locker belongs to is confirmed in game for 3 facilities so far |
| APAS enhancements | ✅ |
| Route history | ✅ |
| Likes, chiral bandwidth, in-game day and time | ✅ |
| Signs placed in the world | 🟡 Where and which type; not yet whose |
| Progress toward the next star | ❌ Not found yet |
| Music, holograms, structures and colour schemes | ❌ Not found yet |
| Built structures, route planner, auto-paver progress | ❌ Not found yet |

How the file works, for the curious: [docs/FORMAT.md](docs/FORMAT.md).

## How you can help

Everything above was worked out with **save pairs**: save, do exactly one thing in the game, save again, and look
at what changed. The ❌ rows need more of those, and so far all of them came from one player's saves. You don't
need to share your save file for this.

**How to send a result**
1. Make a manual save, do the one thing from the table below and nothing else, then make another manual save.
2. Open the newer save in Peko-Check, click **Compare with…** and pick the older one.
3. In the **Changes** tab, click **Copy report**. Paste it into a [new issue](../../issues/new/choose) together with
   what you did and what the game showed (a photo of the screen helps).

The report contains no personal data. Please don't attach the save files themselves: they contain your Steam ID and
other players' names.

**Wanted**

| Test | What to do | What it solves |
|---|---|---|
| Music or hologram | Save just before and just after a reward that gives one song or hologram, with nothing else happening | Showing which songs and holograms you have |
| New structure | Save before and after reaching a connection level that unlocks a new structure | Same, for structures |
| Star progress | Note how full a facility's next star is, make one delivery there without levelling up, note it again | Showing progress toward the next star |
| Collectible | Save before and after picking up a memory chip or another collectible | Showing collectibles |
| Your own sign | Save, place one sign, save again | Telling your signs apart from other players' |
| Locker check | Compare a locker in the **Cargo** tab with the game's own locker screen at that facility | Confirming which facility each locker belongs to |
| Newer game version | Open a save from a newer patch and tell us if something looks wrong | Keeping it working after updates |

Bug reports and ideas are welcome as [issues](../../issues/new/choose) too. [ROADMAP.md](ROADMAP.md) tells how the
project got here and what's next.

## For developers

```bash
pip install lz4
./setup.sh                                        # enables the publication check hooks
python catalog/build_catalog.py                   # order catalogue from the game data in catalog/
python viewer/build_viewer_data.py --no-sample    # -> viewer/viewer_data.json
python viewer/build_page.py                       # -> viewer/index.html, one self-contained page
python tools/ds2_savestate.py path/to/manualsave0.dat   # list a save's sections
```

The repository never contains save files, personal data, game asset files (map images, icons, item pictures) or
copied third-party text. `tools/public_check.py` enforces that before every commit and push (`setup.sh` turns the
hooks on) and again on GitHub. The only images in the repository are the logo and screenshots of the app.

## Credits

- Game data (orders, unlocks, names): read from the game itself with [ShadelessFox/odradek](https://github.com/ShadelessFox/odradek).
- Decima save framework: [Nukem9/HZDCoreEditor](https://github.com/Nukem9/HZDCoreEditor).
- Save encryption key: [mi5hmash/DeathStrandingSaveDataResigner](https://github.com/mi5hmash/DeathStrandingSaveDataResigner).
- Item icons: [game-icons.net](https://game-icons.net) (CC BY 3.0), see [the icon credits](assets/icons-generic/CREDITS.md).
- Guide links: [Game8](https://game8.co/games/Death-Stranding-2-On-the-Beach) and the [Death Stranding Wiki](https://deathstranding.fandom.com/).

Details and licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Code: MIT, see [LICENSE](LICENSE).

Fan project, not affiliated with or endorsed by Kojima Productions, Sony Interactive Entertainment, hololive
production or COVER Corporation.
