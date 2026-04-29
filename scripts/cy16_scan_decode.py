#!/usr/bin/env python3
"""Decode CY16 / EZ-OTG / EZ-Host SCAN records.

Accepts raw SCAN binaries or C headers containing byte arrays.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SIG = 0xC3B6

OPCODES = {
    0x00: "COPY",
    0x01: "WRITE_VECTOR",
    0x02: "WRITE_ISR",
    0x03: "FIXUP_ISR",
    0x04: "JUMP",
    0x05: "CALL",
    0x06: "CALL_INT",
    0x07: "READ_MEM_USING_INT",
    0x08: "MOVE_DATA_USING_INT",
    0x09: "WRITE_CONFIG",
}


def read_u16le(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def load_any(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw

    nums = []
    for m in re.finditer(r"0x([0-9a-fA-F]{1,2})|\b(\d{1,3})\b", text):
        if m.group(1) is not None:
            v = int(m.group(1), 16)
        else:
            v = int(m.group(2), 10)
        if 0 <= v <= 255:
            nums.append(v)

    if len(nums) >= 5 and (nums[0] | (nums[1] << 8)) == SIG:
        return bytes(nums)
    return raw


def decode(data: bytes, *, strict: bool = False) -> int:
    pos = 0
    recno = 0
    rc = 0

    while pos + 5 <= len(data):
        sig = read_u16le(data, pos)
        if sig != SIG:
            if recno == 0:
                print(f"ERROR offset=0x{pos:04x}: missing SCAN signature, got 0x{sig:04x}", file=sys.stderr)
                return 2
            print(f"STOP offset=0x{pos:04x}: no SCAN signature, got 0x{sig:04x}")
            break

        length = read_u16le(data, pos + 2)
        opcode = data[pos + 4]
        data_pos = pos + 5
        next_pos = data_pos + length
        name = OPCODES.get(opcode, f"UNKNOWN_0x{opcode:02x}")

        print(f"RECORD {recno:04d} offset=0x{pos:04x} sig=0x{sig:04x} length={length} opcode=0x{opcode:02x} {name}")

        if length == 0:
            print("  ERROR: zero-length record")
            rc = 3
            if strict:
                return rc
            break

        if next_pos > len(data):
            print(f"  ERROR: truncated record next=0x{next_pos:04x} file_len=0x{len(data):04x}")
            rc = 4
            if strict:
                return rc
            break

        payload = data[data_pos:next_pos]

        if opcode in (0x00, 0x04, 0x05) and len(payload) >= 2:
            addr = read_u16le(payload, 0)
            print(f"  address=0x{addr:04x}")
            if opcode == 0x00:
                body = payload[2:]
                preview_words = []
                for i in range(0, min(len(body), 16), 2):
                    if i + 1 < len(body):
                        preview_words.append(f"{read_u16le(body, i):04x}")
                    else:
                        preview_words.append(f"{body[i]:02x}")
                print(f"  copy_bytes={len(body)} preview_words={' '.join(preview_words)}")
        elif opcode == 0x06 and len(payload) >= 1:
            print(f"  interrupt={payload[0]}")
        else:
            preview = " ".join(f"{b:02x}" for b in payload[:16])
            print(f"  payload_bytes={len(payload)} preview={preview}")

        if opcode not in OPCODES:
            rc = 5
            if strict:
                return rc

        recno += 1
        pos = next_pos

    print(f"SUMMARY records={recno} final_offset=0x{pos:04x} file_len=0x{len(data):04x}")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    return decode(load_any(args.path), strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
