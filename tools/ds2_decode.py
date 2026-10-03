"""Decode a Death Stranding 2 PC save (.dat). Read-only on input.

File layout (as reverse-engineered 2026-09-28, game v1.10.89.0):
  0x00  24-byte fixed header (magic 49f60ec1 2db5fba9 ..., identical in every file)
  0x18  u32 random key seed: K = MurmurHash3_x64_128(seed 42, seed_u32 || DS1 key material[4:16]) (same scheme as DS1)
  0x1c  u32 (0 or 1)
  0x20  body. Every section is XORed with a 16-byte key K that restarts at each section start.
        body[0x00:0x10] = key block: plaintext zero except byte 2 = chunk count, so K = body[0:16] with K[2] ^= count
        body[0x10:]     = u32 chunk sizes[count]
        then the chunks back to back:
          chunk 0  LZ4 block -> metadata (order in progress, mission/episode id, version)
          chunk 1  stored PNG thumbnail (saves only)
          rest     LZ4 blocks of 256 KiB (a chunk of exactly 256 KiB is stored raw) -> concatenated payload
"""
import argparse
import struct
from pathlib import Path

import lz4.block

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
BLOCK = 256 * 1024


def xor(buf: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % 16] for i, b in enumerate(buf))


def decode(data: bytes):
    body = data[0x20:]
    count = body[0x12] ^ body[0x02]
    key = bytearray(body[0:16])
    key[2] ^= count
    key = bytes(key)
    sizes = list(struct.unpack_from(f"<{count}I", xor(body[0x10:0x10 + 4 * count], key)))
    off = 0x10 + 4 * count
    chunks = []
    for s in sizes:
        dec = xor(body[off:off + s], key)
        try:
            out = lz4.block.decompress(dec, uncompressed_size=1 << 22)
        except Exception:
            out = None  # stored (PNG thumbnail) or unknown
        chunks.append((off, s, dec, out))
        off += s
    return sizes, off, len(body), chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, help="write <stem>/meta.bin, thumb.png, payload.bin, stored_NN.bin")
    a = ap.parse_args()
    for p in a.files:
        sizes, end, blen, chunks = decode(p.read_bytes())
        ok = sum(1 for c in chunks if c[3] is not None)
        total = sum(len(c[3]) for c in chunks[1:] if c[3])
        print(f"{p.name[-40:]}: {len(sizes)} chunks, table end {end:#x} vs body {blen:#x}, lz4 {ok}/{len(sizes)}, payload {total:,} B")
        if not a.out:
            continue
        d = a.out / p.stem[-60:]
        d.mkdir(parents=True, exist_ok=True)
        payload = bytearray()
        for i, (off, s, dec, out) in enumerate(chunks):
            if i == 0 and out:
                (d / "meta.bin").write_bytes(out)
            elif out is not None:
                payload += out
            elif s == BLOCK:
                payload += dec  # block stored uncompressed
            elif dec.startswith(PNG_MAGIC):
                (d / "thumb.png").write_bytes(dec)
            else:
                (d / f"stored_{i:02d}.bin").write_bytes(dec)
                print(f"   chunk {i} stored/unknown, {s} B, head {dec[:16].hex()}")
        (d / "payload.bin").write_bytes(payload)


if __name__ == "__main__":
    main()
