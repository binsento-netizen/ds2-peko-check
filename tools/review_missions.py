"""Read-only DS2 mission-table review/extractor. Requires lz4 and tools/ds2_decode.py + ds2_savestate.py (pass their folder as --work).

Example:
  python -B review_missions.py --work path/to/tools save.dat --out missions.json
  python -B review_missions.py --work path/to/tools saves_dir extra_dir --summary-only

Record boundaries verified on 93 saves (63,821 records). Enum labels are
matched to the DS2 RTTI type dump; repeat-order history/ranks remain unverified.
No game/save writes. Output is optional and refuses to overwrite an existing file.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
SECTION = 0x4AFA625B
MARKER = bytes.fromhex("9bb7d61f")
OPEN = {0: "None", 1: "Displayable", 2: "NotSelectable", 4: "NotDisplayable"}
ORDER = {0: "None", 1: "NotStarted", 2: "NotCompleted", 4: "Completed"}
STATE = {0: "Invalid", 10: "Available", 20: "Progress", 30: "Failed",
         40: "Success", 90: "Missing", 100: "Consign"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_payload(path, decode, block, png):
    data = path.read_bytes()
    if path.suffix.lower() == ".bin":
        return data, None
    require(len(data) >= 0x34, "Short container")
    require(data[:8] == bytes.fromhex("49f60ec12db5fba9"), "Unknown container magic")
    sizes, end, body_length, chunks = decode(data)
    require(end == body_length, "Chunk table does not cover body exactly")
    require(len(chunks) >= 3, "Not a gameplay save")
    require(chunks[0][3] is not None and len(chunks[0][3]) == 1312, "Unknown metadata")
    require(chunks[1][2].startswith(png), "Missing thumbnail")
    parts = []
    for _, size, decoded, expanded in chunks[2:]:
        require(len(decoded) == size, "Truncated chunk")
        value = decoded if size == block else expanded
        require(value is not None and len(value) == block, "Invalid gameplay block")
        parts.append(value)
    return b"".join(parts), chunks[0][3]


def parse_missions(section):
    require(len(section) >= 20 and section[:4] == MARKER, "Unknown mission marker")
    count = struct.unpack_from("<I", section, 4)[0]
    require(count <= (len(section) - 20) // 84, "Implausible mission count")
    pos = 8
    records = []
    seen = set()
    for index in range(count):
        require(pos + 84 <= len(section) - 12, "Truncated mission header")
        header, opened, ordered, state, flags, mid, packed = struct.unpack_from("<IBBHIII", section, pos)
        length = struct.unpack_from("<I", section, pos + 78)[0]
        end = pos + 84 + length
        require(header == 1 and end <= len(section) - 12, "Invalid mission frame")
        require(opened in OPEN and ordered in ORDER and state in STATE, "Unknown mission enum")
        identity = (packed << 32) | mid
        require(identity not in seen, "Duplicate full mission identity")
        seen.add(identity)
        records.append({
            "index": index, "section_offset": pos,
            "mission_id": mid, "mission_id_raw_hex": f"{identity:016x}",
            "mission_type": packed & 0x3f, "packed_upper32": packed,
            "open_state": opened, "open_state_label": OPEN[opened],
            "order_state": ordered, "order_state_label": ORDER[ordered],
            "state": state, "state_label": STATE[state], "unknown_u32_at_8": flags,
            "unknown_header_20_78_hex": section[pos + 20:pos + 78].hex(),
            "unknown_u16_at_82": struct.unpack_from("<H", section, pos + 82)[0],
            "variable_length": length,
            "opaque_variable_hex": section[pos + 84:end].hex(),
        })
        pos = end
    require(pos + 12 == len(section), "Mission walk did not reach 12-byte trailer")
    return records, list(struct.unpack_from("<III", section, pos))


def inspect(path, decode, block, png, save_state, summary_only):
    payload, metadata = read_payload(path, decode, block, png)
    require(len(payload) >= 512, "Short payload")
    size = struct.unpack_from("<I", payload, 508)[0]
    require(8 <= size <= len(payload) - 512, "Invalid declared data length")
    data = payload[512:512 + size]
    digest = bytearray(hashlib.md5(data).digest())
    digest[0] ^= 6
    require(bytes(digest) == payload[492:508], "Data digest mismatch (observed XOR-06 convention)")
    require(not payload[512 + size:].strip(b"\0"), "Nonzero bytes after declared data")
    save = save_state(payload)
    require(len({sid for sid, _, _ in save.sections}) == len(save.sections), "Duplicate section ID")
    require(all(0 <= off < save.type_off <= save.raw_off < size - 8 for _, off, _ in save.sections), "Invalid section offsets")
    entries = [entry for entry in save.sections if entry[0] == SECTION]
    require(len(entries) == 1 and entries[0][2] == 6, "Unsupported mission section version")
    records, tail = parse_missions(save.section_bytes()[SECTION])
    result = {
        "path": str(path.resolve()), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "game_version": save.version, "playtime_seconds": save.playtime,
        "payload_bytes": len(payload), "declared_data_bytes": size,
        "mission_section_id": f"{SECTION:08x}", "mission_section_version": entries[0][2],
        "mission_section_payload_offset": 512 + entries[0][1],
        "mission_count": len(records), "unknown_trailer_u32": tail,
        "order_state_counts": dict(Counter(r["order_state_label"] for r in records)),
        "state_counts": dict(Counter(r["state_label"] for r in records)),
        "completed_available_count": sum(r["order_state"] == 4 and r["state"] == 10 for r in records),
    }
    if metadata is not None:
        import re
        match = re.search(rb"Mission ID\.(\d+)", metadata)
        result["metadata_mission_id"] = int(match[1]) if match else None
        result["metadata_matching_records"] = [
            {key: r[key] for key in ("mission_id_raw_hex", "order_state_label", "state_label")}
            for r in records if r["mission_id"] == result["metadata_mission_id"]
        ]
    if not summary_only:
        result["missions"] = records
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True, help="Directory containing ds2_decode.py and ds2_savestate.py")
    parser.add_argument("inputs", nargs="+", type=Path, help="Raw .dat, decoded payload.bin, or raw-save directories")
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.work.resolve()))
    from ds2_decode import decode, BLOCK, PNG_MAGIC
    from ds2_savestate import SaveState
    paths = []
    for item in args.inputs:
        paths.extend(sorted(item.rglob("*.dat")) if item.is_dir() else [item])
    paths = list(dict.fromkeys(p.resolve() for p in paths if not p.name.lower().endswith("profile.dat")))
    results, failures = [], []
    for path in paths:
        try:
            results.append(inspect(path, decode, BLOCK, PNG_MAGIC, SaveState, args.summary_only))
        except Exception as error:
            failures.append({"path": str(path), "error": str(error)})
    report = {"saves_checked": len(paths), "saves_passed": len(results),
              "records_checked": sum(r["mission_count"] for r in results),
              "failures": failures, "saves": results}
    output = json.dumps(report, indent=2)
    if args.out:
        with args.out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "saves"}))
        print(args.out.resolve())
    else:
        print(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
