# Third-party notices

Peko-Check is a fan project. It is not affiliated with, endorsed by or sponsored by Kojima Productions,
Sony Interactive Entertainment, hololive production or COVER Corporation. *Death Stranding* and
*Death Stranding 2: On the Beach* are trademarks of their respective owners. The name nods to a line of the game's
Data Scientist ("Commencing peko-check at once!"); the project uses no likeness, artwork or logo of her or hololive. Game names and text shown by the viewer belong to their owners and are used only to label what a
player's own save contains.

The MIT licence in `LICENSE` covers the code and documentation written for this project. It does not cover the
material below.

## Game data

Order numbers, names, clients, destinations and cargo (`catalog/missions_game.csv`, `catalog/mission_catalog.*`) and
the unlock catalogue (`catalog/unlock_items.json`, `catalog/unlocks_game.csv`) were read from a local installation
of the game with [ShadelessFox/odradek](https://github.com/ShadelessFox/odradek) (GPL-3.0; used as a tool, none of
its code is included). The names and text in these files are the game's own and belong to their owners. Item and
APAS names (`catalog/baggage_names.json`, `catalog/apas_game.json`) are the game's own too. The facility positions
and the blocky map (`catalog/facility_positions.json`, `catalog/voxel_map.json`) are simplified from the game's map
data. No game images, models or other assets are included.

## Used as a reference (format knowledge only, no code copied)

| Source | Licence | What it gave us |
|---|---|---|
| [Nukem9/HZDCoreEditor](https://github.com/Nukem9/HZDCoreEditor) | No licence file | The Decima save framework (payload header, string/GUID pools, section directory), originally for Horizon Zero Dawn. |
| [mi5hmash/DeathStrandingSaveDataResigner](https://github.com/mi5hmash/DeathStrandingSaveDataResigner) | MIT | The container's XOR key derivation (MurmurHash3 of the seed in the file header), shared with Death Stranding 1. |
| [ShadelessFox/odradek](https://github.com/ShadelessFox/odradek) | GPL-3.0 | DS2 type dump and asset reader, used to research the save format and to read the game data above. |

## Item icons

The item icons in the viewer are from [game-icons.net](https://game-icons.net) by Delapouite, Lorc, Skoll, Sbed,
Lucas, HeavenlyDog and Lord Berandas, licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
They were recoloured and simplified (background removed, paths rounded). The full list, per icon with its author, is in
[assets/icons-generic/CREDITS.md](assets/icons-generic/CREDITS.md). They are generic icons for each kind of item, not
the game's own pictures.

## Leaflet

`viewer/template.html` contains the stylesheet of [Leaflet](https://leafletjs.com) 1.9.4, which is only used by
builds that include the game's own map image; `viewer/build_page.py` leaves it out of the published page.

> BSD 2-Clause License. Copyright (c) 2010-2023, Volodymyr Agafonkin. Copyright (c) 2010-2011, CloudMade.
> All rights reserved.
>
> Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
> following conditions are met:
>
> 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the
>    following disclaimer.
> 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
>    following disclaimer in the documentation and/or other materials provided with the distribution.
>
> THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
> INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
> DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
> SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
> SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
> WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
> USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

## Guide links

| Source | What we use |
|---|---|
| [Game8](https://game8.co/games/Death-Stranding-2-On-the-Beach) and the [Death Stranding Wiki (Fandom)](https://deathstranding.fandom.com/) | Linked from the viewer as guides (page IDs in `catalog/game8_*_pages.json`, wiki titles in `catalog/wiki_pages.json`). Nothing is copied from them. |
