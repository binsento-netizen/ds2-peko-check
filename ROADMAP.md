# Roadmap

How Peko-Check got to where it is, and what is still to do. For how to contribute a test result, see
[How you can help](README.md#how-you-can-help).

## How we got here

The work happened over one week in late September and early October 2026, on a single player's saves, by testing
one game action at a time.

### 1. Opening the file (late September)
- Worked out the save container: an XOR layer with a key derived as in Death Stranding 1 (MurmurHash3 over a seed
  and fixed key material), a chunk table, LZ4 compression and a thumbnail image.
- Parsed the Decima save framework (header, MD5 integrity check, string and GUID pools, a directory of 222 sections),
  building on HZDCoreEditor's work for Horizon Zero Dawn.
- Found the order records and the unlock catalogue, and built a first viewer that decodes saves in the browser.

### 2. Names from the game itself (30 September – 1 October)
- Matched all 474 orders to their in-game numbers and names using the game's own mission lists, read with the Odradek
  extractor. Earlier versions borrowed names from a community guide and a mod dump; both were replaced by game data.
- Decoded the route history ("previous routes"), the facility table (connection levels and material stock), likes
  and chiral bandwidth.
- Rebuilt the in-game map from the game's 3D map data and placed every facility on it.

### 3. Controlled tests (1–2 October)
- Ran save pairs for one action each: a delivery, a structure, a locker deposit, a material withdrawal, fabrication,
  swapping boots, an APAS enhancement, fast travel, the route planner, sleeping, placing a sign and more. A phone
  checklist logged what happened in the game next to each save pair.
- Results: the facility stock layout, fast travel starting a new route segment, the APAS list, the in-game clock,
  and the cargo pool that tells where every item is (equipped, backpack or a facility's private locker).
- Found the hash the game uses for many references (CRC32C with the top bit cleared), which unlocked item pictures,
  APAS ids and sign types in one go.

### 4. The app (1–2 October)
- Story timeline for main orders, standard orders per facility, unlocks with "unlocked by" links, Cargo, APAS,
  Map and a compare mode with a copyable report.
- A game-inspired look (light and dark), chosen from three design directions.
- A public version with a publication check that keeps save data, personal data and game asset files out of the
  repository.

## What is still to do

### Research (help wanted)
- [ ] **Music, holograms, structures and colour schemes:** their unlock state is not in the unlock catalogue. A song
      unlocks through a persistent game flag; how the save stores those flags is open.
- [ ] **Partial stars:** the points needed per level are known; the counter that fills the next star is not.
- [ ] **Signs:** positions and types are read; which signs are your own is not.
- [ ] **Lockers:** confirm the facility of each private locker (three are confirmed in game), and map the lockers of
      facilities that weren't visited in the test saves.
- [ ] **Built structures** and the **route planner:** leads only.
- [ ] **Collectibles** (memory chips and the like).
- [ ] **Auto-pavers:** donations show up as facility stock going down; the paver's own progress seems to be kept on
      the server.
- [ ] **More players and patches:** everything so far comes from one player's saves on game version 1.10.89.0.

### App
- [ ] A hosted copy, so the viewer runs without downloading the repository.
- [ ] Partial stars and music/hologram status in the viewer once the research above is done.
- [ ] A "your signs" map layer.
- [ ] Split the single-file viewer into smaller modules as it grows.
