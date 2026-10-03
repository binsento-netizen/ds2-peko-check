r"""Read-only extractor for the map "previous routes" (section 48ea52a4).

The section stores the travelled routes since the history was last cleared (completing a main order clears it;
it survives saving and quitting) as a list of segments. Format (reverse-engineered 2026-09-30):

  offset 0   : 33-byte header (u32 marker 0x7cf9113d, ...; point stream starts at byte 33)
  per segment: run of 6-byte points, each = little-endian (i16 x, i16 y, i16 z);
               points are sampled about every 10 world units of travel.
  trailer    : b"\x02\x00" + u16 mode (100 or 200) + 8 zero bytes + u32 anchor_count
               + anchor_count * 6-byte points (repeated segment endpoints)
               + b"\x00\x00\xff\xff" + trailing fields.
  The stream is followed by zero padding and a separate metadata block to the fixed
  816 KB body. The number of trailers equals the number of segments (verified: 3 and 11).

Coordinates are raw save units; mapping to a world map (origin/scale/region) is not yet
calibrated. `mode` (100 vs 200) is an unconfirmed per-segment category (NOT step length;
sampling is distance-based). No game/save writes.

Example:
  python -B review_routes.py --work . path\to\saves --summary-only
"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SECTION = 0x48EA52A4
HEADER_MARKER = 0x7CF9113D
POINT_START = 33
TRAILER_HEAD = b"\x02\x00"          # trailer record marker
TRAILER_MODES = (100, 200)           # u16 after the marker
TRAILER_TERM = b"\x00\x00\xff\xff"   # follows the anchor points


def require(cond, msg):
    if not cond:
        raise ValueError(msg)


def find_stream_end(section):
    """The point stream ends where a run of >=64 zero bytes begins."""
    run = 0
    for i in range(POINT_START, len(section)):
        if section[i] == 0:
            run += 1
            if run >= 64:
                return i - 63
        else:
            run = 0
    return len(section)


def parse_routes(section):
    require(len(section) >= POINT_START + 4, "Section too small")
    marker = struct.unpack_from("<I", section, 0)[0]
    require(marker == HEADER_MARKER, f"Unexpected route header 0x{marker:08x}")
    end = find_stream_end(section)

    segments = []
    pos = POINT_START
    while pos < end:
        # find the next trailer marker at a 6-byte-aligned-ish position after some points
        t = pos
        found = -1
        while t < end - 4:
            if section[t:t + 2] == TRAILER_HEAD:
                mode = struct.unpack_from("<H", section, t + 2)[0]
                if mode in TRAILER_MODES and section[t + 4:t + 12] == b"\x00" * 8:
                    found = t
                    break
            t += 1
        if found == -1:
            # trailing points with no closing trailer (rare); take what remains
            body = section[pos:end]
            pts = _points(body)
            if len(pts) >= 2:
                segments.append({"mode": None, "point_count": len(pts), "points": pts})
            break

        mode = struct.unpack_from("<H", section, found + 2)[0]
        anchor = struct.unpack_from("<I", section, found + 12)[0]
        pts = _points(section[pos:found])
        if len(pts) >= 2:
            segments.append({"mode": mode, "point_count": len(pts), "points": pts})
        # advance past trailer: head(4) + zero(8) + anchor u32(4) + anchor*6 + term(4)
        after = found + 16 + anchor * 6
        # tolerate the terminator sitting just after the anchor block
        term_at = section.find(TRAILER_TERM, found + 16, found + 16 + anchor * 6 + 8)
        pos = (term_at + 4) if term_at != -1 else after
    return segments


def _points(body):
    """Decode 6-byte (i16 x, y, z) points, dropping (0,0,0) anchor/padding entries and the segment's count header:
    a leading (0, n, 0) record where n is the number of points that follow (437 of 587 corpus segments have it)."""
    m = len(body) // 6
    out = []
    for i in range(m):
        x, y, z = struct.unpack_from("<hhh", body, i * 6)
        if x == 0 and y == 0 and z == 0:
            continue
        out.append((x, y, z))
    if out and out[0][0] == 0 and out[0][2] == 0 and out[0][1] == len(out) - 1:
        out = out[1:]
    return out


def bbox(segments):
    xs = [p[0] for s in segments for p in s["points"]]
    ys = [p[1] for s in segments for p in s["points"]]
    zs = [p[2] for s in segments for p in s["points"]]
    if not xs:
        return None
    return {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]}


def path_length(segments):
    total = 0.0
    for s in segments:
        pts = s["points"]
        for a, b in zip(pts, pts[1:]):
            d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
            if d < 500:  # skip separator jumps
                total += d
    return total


def inspect(path, decode, block, png, save_state, summary_only):
    import review_missions as rm
    payload, _ = rm.read_payload(path, decode, block, png)
    save = save_state(payload)
    section = save.section_bytes().get(SECTION)
    require(section is not None, "No route section in this save")
    segments = parse_routes(section)
    result = {
        "path": str(path.resolve()),
        "game_version": save.version,
        "playtime_seconds": save.playtime,
        "section_bytes": len(section),
        "segment_count": len(segments),
        "point_count": sum(s["point_count"] for s in segments),
        "modes": sorted({s["mode"] for s in segments if s["mode"] is not None}),
        "bbox": bbox(segments),
        "path_length_units": round(path_length(segments), 1),
    }
    if not summary_only:
        result["segments"] = segments
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", type=Path, default=Path(__file__).parent,
                        help="Directory with ds2_decode.py / ds2_savestate.py / review_missions.py")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.work.resolve()))
    from ds2_decode import decode, BLOCK, PNG_MAGIC
    from ds2_savestate import SaveState

    paths = []
    for item in args.inputs:
        paths.extend(sorted(item.rglob("*.dat")) if item.is_dir() else [item])
    paths = list(dict.fromkeys(
        p.resolve() for p in paths if not p.name.lower().endswith("profile.dat")))

    results, failures = [], []
    for path in paths:
        try:
            if path.stat().st_size == 0:
                continue
            results.append(inspect(path, decode, BLOCK, PNG_MAGIC, SaveState, args.summary_only))
        except Exception as error:
            failures.append({"path": str(path), "error": str(error)})

    report = {"saves_checked": len(results), "failures": failures,
              "saves": [{k: v for k, v in r.items() if k != "segments"} for r in results]
              if args.summary_only else results}
    output = json.dumps(report, indent=2)
    if args.out:
        with args.out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
        print(args.out.resolve())
    else:
        print(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
