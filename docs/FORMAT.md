# Death Stranding 2 PC save format

What is known so far, as implemented in `tools/` (Python) and `viewer/template.html` (JavaScript). Verified on
saves from game versions 1.0.45, 1.1.53 and 1.10.89. All integers are little-endian. Nothing here writes saves.

## 1. Container (`*.dat`)

| Offset | Content |
|---|---|
| `0x00` | 24-byte fixed header (starts `49 f6 0e c1`) |
| `0x18` | `u32` random key seed |
| `0x1c` | `u32` (0 or 1) |
| `0x20` | body, XORed with a 16-byte key `K` that restarts at the start of every part |

**Key.** `K = MurmurHash3_x64_128(seed = 42, data = seed_u32 || M[4:16])`, with the Death Stranding 1 key material
`M = 46 3F BB BC 7B 6F 57 ED 9B 41 7D 36 E3 26 12 BC` (the same scheme as DS1, see mi5hmash's resigner). Shortcut:
the first 16 body bytes are plaintext zeros except byte 2 (the chunk count), so `K = body[0:16]` with
`K[2] ^= count`, where `count = body[0x12] ^ body[0x02]`.

**Body.** 16-byte key block, then `u32 sizes[count]`, then the chunks back to back:

- chunk 0: LZ4 block, 1,312 bytes of metadata (order in progress, objective, episode/area IDs, save type)
- chunk 1: PNG thumbnail
- the rest: LZ4 blocks of 256 KiB each (a chunk of exactly 256 KiB is stored uncompressed). Concatenated they form
  the 16 MiB payload.

## 2. Payload

| Offset | Content |
|---|---|
| `0x000` | version string, e.g. `v1.10.89.0` |
| `0x134` | `i32` save type |
| `0x178` | `f64` play time in seconds |
| `0x1EC` | MD5 of the data block, first byte XOR `0x06` |
| `0x1FC` | `u32` data length |
| `0x200` | data block |

The data block follows the Decima save layout known from Horizon Zero Dawn (Nukem9's HZDCoreEditor): sections,
then at `raw_off` a string pool, wide strings and 256 GUID tables, then the **section directory**: magic
`05 a0 0e 53 ff ff ee ee`, a count (222), and per section `(vint id, vint offset, vint version)`. The last 8 bytes
of the data block are `u32 type_off, u32 raw_off`. Section IDs and versions are the same in every save; offsets
and sizes vary.

`vint`: one signed byte; `0x80` means an `i32` follows, `0x81` means an `i16` follows.

## 3. Decoded sections

### `4afa625b`: mission records (orders)

`u32` marker `0x1FD6B79B`, `u32` count, then records of `84 + L` bytes:

| Offset | Content |
|---|---|
| `+4` | open state: 1 Displayable (listed at a terminal), 2 NotSelectable (accepted), 4 NotDisplayable |
| `+5` | order state: 1 NotStarted, 2 NotCompleted (in progress), 4 Completed |
| `+6` | `u16` state: 10 Available, 20 Progress, 30 Failed, 40 Success, 90 Missing, 100 Consign |
| `+0xC` | `u32` mission ID |
| `+0x10` | `u32`, low 6 bits = mission type (3 delivery, 4 recover lost cargo, 17 elimination, 18 recover stolen cargo, 19 destroy) |
| `+0x4E` | `u32` L (variable tail length) |

Standard order IDs are `facility_code * 1000 + suffix` (codes 102-108 Mexico, 202-237 Australia). The suffix
range follows the type: `0xx` delivery, `05x`/`06x` recovery, `1xx`/`2xx` elimination, `3xx` destroy, `4xx`
recovery from enemies. IDs from `0x10000000` are temporary records that appear and disappear between saves.
`catalog/mission_catalog.json` maps IDs to order numbers.

### `3ef4dc4d`: unlock catalogue

`u32` marker `0x8b3f7cc3`, `vint` count (903), `vint`, then `count` records `(u32 key, u32 flags)`. Bit `0x8000`
= unlocked, `flags & 0xfff` = catalogue index. The bit is used for weapons, gear, outfits and vehicle parts; other
kinds (structures, holograms, music, colours) keep their state elsewhere.

### `48ea52a4`: route history

33-byte header (marker `0x7cf9113d`), then segments of 6-byte points `(i16 x, i16 y, i16 z)`, about one point per
10 m of travel. Each segment ends in a trailer `02 00 <u16 mode> 00×8 <u32 n> n×6-byte points … 00 00 ff ff`.
Mode 200 is most likely a vehicle and 100 on foot (strong hypothesis). The history survives saving and quitting
and is cleared when a main order is completed (and on some other events not yet identified). The newest segment
keeps growing while you travel.

### More decoded sections

Hashes below are the game's masked name hash: CRC32C (init 0, no final xor) of the resource's name, with the top
bit cleared.

| Section | Content |
|---|---|
| `73dacf23` | Facilities: 49 records of 112 bytes from `+106`: `u32` facility code, `u16` index, `u16` connection level 0-5. The six material stocks (`u32`, 8 bytes apart: Chiral Crystals, Resins, Metals, Ceramics, Chemicals, Special Alloys) start 96 bytes before the code. |
| `202659d5` | Likes: `u32` at `+4` from NPCs, `+12` from other porters, `+44` given. |
| `69049449` | Chiral bandwidth: `vint` at `+4` = the sum over facilities of [0, 20, 35, 50, 65, 95][level]. Then the APAS list: per enhancement the player has access to, `u32` hash of its id, `u8` developed (1) / available (0), more bytes not decoded; then a `u8` count and the hashes of the developed ones. |
| `0aa0d44e` | Cargo: a pool of 464-byte item slots (from `+253`): `+7` container kind, `+48` 12-byte container id (`w0 w1 w2`), `+60` baggage name code, `+172` `f32` remaining amount of a material stack. Kind `0x00` = equipped, `0x34` = backpack, `0x1f` with `w2 = 36a83550` = a private locker, whose `w0` identifies the facility. |
| `3926c2c4` | In-game clock: `f32` hour of the day at `+4` (6.0 = 06:00), `u32` day number at `+8`. |
| `129ec9ee` | Signs (lead): a count near the start, then records of about 72-78 bytes with the sign type's hash and its `f64 x, y, z` (world metres) 36, 28 and 20 bytes before the hash. Whose sign it is is not known yet. |

## 4. Leads (not confirmed)

| Section | Observation |
|---|---|
| `0b8cfaf0` | 606 objective/progress records |
| `5cef9b34` | story table |
| `6727b031` | 24 bytes of clocks: `+16` grows about 29.97 per second of play; the other fields are open |
| `01b35e1e` | changes when a facility is connected (`u32 @32` 0→3) |
| `2cf918ee` | a counter `@624` (with an `f64` timestamp `@616`) that steps at certain main orders |
| `4d4b4d42` | active order markers (`f32 x, y, z` records) |

The viewer's **Compare with…** mode lists every section whose bytes differ between two saves; a save pair around
a single in-game action is the fastest way to find where something is stored.
