# Roadmap

How Peko-Check got to where it is, and what is still to do. For how to contribute a test result, see
[How you can help](README.md#how-you-can-help).

## How we got here

The work happened over one week in late September and early October 2026, on a single player's saves, by testing
one game action at a time.

### 1. Opening the file (late September)
- Unlocked the save file itself: it is scrambled and compressed the same way as Death Stranding 1's saves
  (an XOR key derived with MurmurHash3, LZ4-compressed chunks, plus a thumbnail picture).
- Read its inner structure, the save format of the game's Decima engine (a checksum and 222 numbered sections),
  building on HZDCoreEditor's work for Horizon Zero Dawn.
- Found where orders and unlocks are stored, and built a first viewer that reads saves in the browser.

### 2. Names from the game itself (30 September – 1 October)
- Matched all 474 orders to their in-game numbers and names using the game's own mission lists, read with the Odradek
  extractor. Earlier versions borrowed names from a community guide and a mod dump; both were replaced by game data.
- Decoded the route history ("previous routes"), the facility table (connection levels and material stock), likes
  and chiral bandwidth.
- Rebuilt the in-game map from the game's 3D map data and placed every facility on it.

### 3. Controlled tests (1–2 October)
- Ran save pairs for one action each: a delivery, a structure, a locker deposit, a material withdrawal, fabrication,
  swapping boots, an APAS enhancement, fast travel, the route planner, sleeping, placing a sign and more.
- Results: the facility stock layout, fast travel starting a new route segment, the APAS list, the in-game clock,
  and the cargo pool that tells where every item is (equipped, backpack or a facility's private locker).
- Found the hash the game uses for many references (CRC32C with the top bit cleared), which linked items, APAS ids
  and sign types to the game's data in one go.

### 4. The app (1–2 October)
- Story timeline for main orders, standard orders per facility, unlocks with "unlocked by" links, Cargo, APAS,
  Map and a compare mode with a copyable report.
- A game-inspired look (light and dark).
- A public version with a publication check that keeps save data, personal data and game asset files out of the
  repository.

### 5. Public release (3 October)
- A hosted copy on GitHub Pages, so the viewer runs without downloading the repository.
- An example save to look around without your own.
- Generic item icons with level and weapon-type badges, instead of the game's own pictures.
- A blocky map of our own (voxel terrain simplified from the game's map) with facilities and your routes.
- The in-game day and time on the save card.
- The highway and monorail on the map, showing which sections you've built (read from the save; it matches the
  game's statistics screen).
- Spoiler protection: orders, items and rewards you haven't reached are blurred until you choose to see them.
- Tabs that show your totals at a glance, and a new set of item icons drawn in the style of the game's menus.

## What is still to do

### Research (help wanted)
- [ ] **Music, holograms, structures and colour schemes:** their unlock state is not in the unlock catalogue. A song
      unlocks through a persistent game flag; how the save stores those flags is open. The viewer works them out
      from orders and connection levels for now.
- [ ] **Partial stars:** the points needed per level are known; the counter that fills the next star is not.
- [ ] **Signs:** positions and types are read; which signs are your own is not.
- [ ] **Lockers:** confirm the facility of each private locker (three are confirmed in game), and map the lockers of
      facilities that weren't visited in the test saves.
- [ ] **Built structures** and the **route planner:** leads only.
- [ ] **Collectibles** (memory chips and the like).
- [ ] **Auto-pavers:** finished sections are read from the save; donations to an unfinished paver only show up as
      facility stock going down, and the paver's own progress seems to be kept on the server.
- [ ] **More players and patches:** everything so far comes from one player's saves, mostly on 1.10.89.0 (older
      1.0.45 and 1.1.53 saves also open).

### App
- [ ] Partial stars and music/hologram status in the viewer once the research above is done.
- [ ] A "your signs" map layer.
- [ ] Split the single-file viewer into smaller modules as it grows.
