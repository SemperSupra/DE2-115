#!/usr/bin/env python3
"""Create simple CY16 SCAN-wrapped images.

Clean-room host tool for COPY + CALL/JUMP records.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SIG = 0xC3B6
OP_COPY = 0x00
OP_JUMP = 0x04
OP_CALL = 0x05


def u16le(v: int) -> bytes:
    return bytes((v & 0xFF, (v >> 8) & 0xFF))


def record(op: int, payload: bytes) -> bytes:
    return u16le(SIG) + u16le(len(payload)) + bytes([op]) + payload


def copy_record(addr: int, data: bytes) -> bytes:
    return record(OP_COPY, u16le(addr) + data)


def call_record(addr: int) -> bytes:
    return record(OP_CALL, u16le(addr))


def jump_record(addr: int) -> bytes:
    return record(OP_JUMP, u16le(addr))


def wrap(input_path: Path, output_path: Path, base: int, call_address: int | None, jump: bool) -> None:
    data = input_path.read_bytes()
    if base < 0 or base > 0xFFFF:
        raise SystemExit("base address must fit in 16 bits")
    if call_address is None:
        call_address = base
    if call_address < 0 or call_address > 0xFFFF:
        raise SystemExit("call/jump address must fit in 16 bits")

    out = bytearray()
    # Dummy alignment COPY record: address only, no bytes copied.
    out += copy_record(base, b"")

    pos = 0
    while pos < len(data):
        chunk = data[pos:pos + 0xFF00]
        out += copy_record((base + pos) & 0xFFFF, chunk)
        pos += len(chunk)

    out += jump_record(call_address) if jump else call_record(call_address)
    out += b"\x00\x00"

    output_path.write_bytes(out)
    print(f"inpath = {input_path}")
    print(f"outpath = {output_path}")
    print(f"base_address = 0x{base:04x}")
    print(f"{'jump' if jump else 'call'}_address = 0x{call_address:04x}")
    print(f"in_file_size = {len(data)}")
    print(f"out_file_size = {len(out)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("base_address", type=lambda s: int(s, 0))
    ap.add_argument("--call-address", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--jump", action="store_true", help="emit JUMP instead of CALL for final control record")
    args = ap.parse_args()

    wrap(args.input, args.output, args.base_address, args.call_address, args.jump)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
