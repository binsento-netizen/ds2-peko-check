"""Helpers: load decoded payload/meta straight from save files (read-only)."""
import re
from pathlib import Path
from ds2_decode import decode, BLOCK, PNG_MAGIC

SAVES = Path(__file__).resolve().parent.parent / "saves"
EPISODES = SAVES / "episode-pack"


def load(path):
    sizes, end, blen, chunks = decode(Path(path).read_bytes())
    meta, payload = None, bytearray()
    for i, (off, s, dec, out) in enumerate(chunks):
        if i == 0:
            meta = out
        elif out is not None:
            payload += out
        elif s == BLOCK:
            payload += dec
    return meta, bytes(payload)


def episode_saves():
    """Episode saves sorted by main order number (Episode 2 Lou has none -> placed after order 7)."""
    def key(p):
        m = re.search(r"Main Order (\d+)", p.name)
        return float(m.group(1)) if m else float(re.search(r"Episode (\d+)", p.name).group(1)) * 3.75
    return sorted(EPISODES.glob("*.dat"), key=key)


def meta_info(meta):
    s = [x.decode("latin1") for x in re.findall(rb"[\x20-\x7e]{4,}", meta)]
    t = next((x for x in s if x.startswith("Order In Progress")), s[0] if s else "")
    mid = next((x for x in s if x.startswith("Mission ID")), "")
    return t, mid
