"""DS2 save-state reader for the decoded payload (see ds2_decode.py). Read-only.

Layout follows the Decima save format as documented by Nukem9's HZDCoreEditor (Decima.SaveGameSystem.cs /
Decima.SaveState.cs, Horizon Zero Dawn; format knowledge only, no code copied), adapted to what DS2 contains:

payload header (same as HZD)
  0x000  char[32] version string "v1.10.89.0"
  0x020  u32 gameVersion, u8 saveVersion, u8 flags, u16 worldIdHash, u8 coop
  0x02C  u32 gameStateBlockLength + 256-byte block
  0x130  i32 unknown, i32 saveType (1 = manual), 4x GGUUID, f64 playTimeSeconds (@0x178)
  0x1EC  16-byte MD5 of the data block, first byte XOR 0x06, u32 dataLength (@0x1FC)
  0x200  data block (dataLength bytes)

data block
  [sections ...]                 custom per-system binary, variable-length ints
  @raw_off   string pool (8 KiB blocks), wide strings, GUID pool (256 tables)   -- as in HZD
  directory  magic 05a00e53 ffffeeee, vint count, count x (vint id32, vint offset, vint version)
  trailer    u32 type_off, u32 raw_off (last 8 bytes)
Section ids and versions are identical across all saves; versions look like date stamps (20250303).
Unlike HZD there is no RTTI class/member table, so section contents are not self-describing.
"""
import struct
import sys

DIR_MAGIC = bytes.fromhex("05a00e53ffffeeee")


class R:
    def __init__(self, b, pos=0):
        self.b, self.pos = b, pos

    def s8(self):
        v = struct.unpack_from("<b", self.b, self.pos)[0]; self.pos += 1; return v

    def i16(self):
        v = struct.unpack_from("<h", self.b, self.pos)[0]; self.pos += 2; return v

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.pos)[0]; self.pos += 4; return v

    def raw(self, n):
        v = self.b[self.pos:self.pos + n]; self.pos += n; return v

    def vint(self):
        """Decima variable-length int: 0x80 -> i32 follows, 0x81 -> i16 follows, else signed byte."""
        v = self.s8()
        return self.i32() if v == -128 else self.i16() if v == -127 else v

    def voff(self):
        v = self.vint()
        if v < 0 or v > len(self.b) - self.pos:
            raise ValueError(f"bad count {v} at {self.pos:#x}")
        return v


class SaveState:
    def __init__(self, payload):
        self.version = payload[:32].split(b"\0")[0].decode()
        self.save_type = struct.unpack_from("<i", payload, 0x134)[0]
        self.playtime = struct.unpack_from("<d", payload, 0x178)[0]
        n = struct.unpack_from("<I", payload, 0x1FC)[0]
        self.data = d = payload[0x200:0x200 + n]
        self.type_off, self.raw_off = struct.unpack_from("<II", d, n - 8)

        r = R(d, self.raw_off)
        self.strings = []
        for _ in range(r.voff()):
            count, size = r.i32(), r.i32()
            blocks = [r.raw(size) for _ in range(count)]
            r.raw(r.i32() * 8)
            self.strings.append((size, blocks))
        self.wide = [r.raw(r.voff() * 2).decode("utf-16-le", "replace") for _ in range(r.voff())]
        self.guids = [[r.raw(16) for _ in range(r.voff())] for _ in range(256)]

        if d[r.pos:r.pos + 8] != DIR_MAGIC:
            raise ValueError(f"section directory magic not found at {r.pos:#x}")
        r.pos += 8
        self.sections = [(r.vint() & 0xFFFFFFFF, r.vint(), r.vint()) for _ in range(r.voff())]
        if r.pos != n - 8:
            raise ValueError("directory does not end at trailer")

    def section_bytes(self):
        """{id: bytes} using directory order by offset; last section ends at type_off."""
        order = sorted(self.sections, key=lambda s: s[1])
        out = {}
        for i, (sid, off, ver) in enumerate(order):
            end = order[i + 1][1] if i + 1 < len(order) else self.type_off
            out[sid] = self.data[off:end]
        return out

    def all_strings(self):
        return [x.decode("utf-8", "replace") for _, bl in self.strings for x in b"".join(bl).split(b"\0") if x]


if __name__ == "__main__":
    from ds2lib import load
    for path in sys.argv[1:]:
        s = SaveState(load(path)[1])
        print(f"{path[-40:]}: {s.version} type {s.save_type} playtime {s.playtime / 3600:.2f} h, "
              f"{len(s.sections)} sections, {len(s.all_strings())} strings, {sum(map(len, s.guids))} guids")
