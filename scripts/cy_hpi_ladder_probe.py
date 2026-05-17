#!/usr/bin/env python3
"""CY7C67200 HPI bring-up ladder probe over LiteX Etherbone."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Dict, List, Optional

from litex import RemoteClient

from cy7c67200_hpi import (
    COMM_ACK,
    COMM_NAK,
    COMM_RESET,
    CPU_FLAGS_REG,
    HW_REV_REG,
    POWER_CONTROL_REG,
    PORT_MAPS,
    TIMING_PROFILES,
    CyHpi,
    PortMap,
    TimingProfile,
    classify_block,
    parse_csv_names,
)


TEST_BASE = 0x1000
TEST_WORDS = [0x1357, 0x2468, 0x369C, 0x55AA]


def wait_for_server(host: str, port: int, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    last_error: Optional[BaseException] = None
    while time.time() < deadline:
        try:
            wb = RemoteClient(host=host, port=port)
            wb.open()
            wb.close()
            return
        except Exception as exc:  # pragma: no cover - depends on live server.
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"litex_server did not become ready: {last_error}")


def fmt_words(values: List[int]) -> str:
    return ",".join(f"0x{value:04x}" for value in values)


def run_map_probe(wb, port_map: PortMap, timing: TimingProfile, args) -> Dict[str, object]:
    hpi = CyHpi(wb, port_map)
    cfg = hpi.reset(timing, args.reset_low, args.reset_high)

    hpi.write_words16(TEST_BASE, TEST_WORDS)
    block = hpi.read_words16(TEST_BASE, len(TEST_WORDS))
    block_class = classify_block(TEST_WORDS, block)

    separated_expected = [0xA501, 0x5A02, 0xC303]
    separated_addrs = [TEST_BASE + 0x20, TEST_BASE + 0x40, TEST_BASE + 0x80]
    for addr, value in zip(separated_addrs, separated_expected):
        hpi.write_mem16(addr, value)
    separated_actual = [hpi.read_mem16(addr) for addr in separated_addrs]
    separated_class = classify_block(separated_expected, separated_actual)

    status = hpi.read_status()
    mailbox = hpi.read_mailbox()
    cpu_flags = hpi.read_mem16(CPU_FLAGS_REG)
    hw_rev = hpi.read_mem16(HW_REV_REG)
    power = hpi.read_mem16(POWER_CONTROL_REG)
    snap = hpi.bridge_snapshot()

    rung1_pass = block_class == "PASS" and separated_class == "PASS"
    print(
        "CY_HPI_MAP_RESULT "
        f"timing={timing.name} map={port_map.name} cfg=0x{cfg:08x} "
        f"block={block_class} block_read={fmt_words(block)} "
        f"separated={separated_class} separated_read={fmt_words(separated_actual)} "
        f"status=0x{status:04x} mailbox=0x{mailbox:04x} "
        f"cpu_flags=0x{cpu_flags:04x} hw_rev=0x{hw_rev:04x} power=0x{power:04x} "
        f"bridge_ctrl=0x{snap['last_ctrl']:08x} bridge_sample=0x{snap['last_sample']:04x} "
        f"bridge_cy=0x{snap['last_cy']:04x}"
    )

    return {
        "timing": timing.name,
        "map": port_map.name,
        "cfg": cfg,
        "block_expected": TEST_WORDS,
        "block_actual": block,
        "block_class": block_class,
        "separated_expected": separated_expected,
        "separated_actual": separated_actual,
        "separated_class": separated_class,
        "status": status,
        "mailbox": mailbox,
        "cpu_flags": cpu_flags,
        "hw_rev": hw_rev,
        "power": power,
        "bridge": snap,
        "rung1_pass": rung1_pass,
    }


def run_mailbox_reset(wb, port_map: PortMap, timing: TimingProfile, args) -> Dict[str, object]:
    hpi = CyHpi(wb, port_map)
    cfg = hpi.reset(timing, args.reset_low, args.reset_high)
    hpi.write_mailbox(COMM_RESET)

    deadline = time.time() + args.mailbox_timeout
    observed: List[Dict[str, int]] = []
    last_pair = None
    ack = False
    nak = False
    while time.time() < deadline:
        mailbox = hpi.read_mailbox()
        status = hpi.read_status()
        pair = (mailbox, status)
        if pair != last_pair:
            observed.append({"mailbox": mailbox, "status": status})
            last_pair = pair
            print(
                "CY_HPI_MAILBOX_POLL "
                f"map={port_map.name} timing={timing.name} "
                f"mailbox=0x{mailbox:04x} status=0x{status:04x}"
            )
        if mailbox == COMM_ACK:
            ack = True
            break
        if mailbox == COMM_NAK:
            nak = True
            break
        time.sleep(args.poll_interval)

    result = "PASS" if ack else ("NAK" if nak else "TIMEOUT")
    print(
        "CY_HPI_RUNG2_RESULT "
        f"timing={timing.name} map={port_map.name} cfg=0x{cfg:08x} result={result}"
    )
    return {
        "timing": timing.name,
        "map": port_map.name,
        "cfg": cfg,
        "result": result,
        "observed": observed,
    }


def run_probe(args) -> Dict[str, object]:
    map_names = parse_csv_names(args.maps, PORT_MAPS)
    timing_names = parse_csv_names(args.timings, TIMING_PROFILES)
    results: List[Dict[str, object]] = []

    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        print(
            "CY_HPI_LADDER_START "
            f"maps={','.join(map_names)} timings={','.join(timing_names)} "
            "dummy_reads=0 canonical_required=true"
        )
        for timing_name in timing_names:
            timing = TIMING_PROFILES[timing_name]
            for map_name in map_names:
                results.append(run_map_probe(wb, PORT_MAPS[map_name], timing, args))

        canonical_passes = [
            item
            for item in results
            if item["map"] == "canonical" and item["rung1_pass"]
        ]
        if canonical_passes:
            best = canonical_passes[0]
            print(f"CY_HPI_RUNG1_PASS timing={best['timing']} map=canonical")
        else:
            print("CY_HPI_RUNG1_FAIL map=canonical")

        mailbox_result = None
        if args.attempt_mailbox and canonical_passes:
            best_timing = TIMING_PROFILES[str(canonical_passes[0]["timing"])]
            mailbox_result = run_mailbox_reset(wb, PORT_MAPS["canonical"], best_timing, args)
        elif args.attempt_mailbox:
            print("CY_HPI_RUNG2_SKIPPED reason=canonical_rung1_failed")

        return {
            "maps": map_names,
            "timings": timing_names,
            "rung1_pass": bool(canonical_passes),
            "results": results,
            "mailbox": mailbox_result,
        }
    finally:
        wb.close()


def start_server(args):
    cmd = [
        "litex_server",
        "--udp",
        "--udp-ip",
        args.board_ip,
        "--udp-port",
        str(args.board_udp_port),
        "--bind-ip",
        args.host,
        "--bind-port",
        str(args.port),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a canonical CY7C67200 HPI ladder probe. The memory tests use "
            "single HPI DATA reads and block auto-increment; no dummy read is used."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1235)
    parser.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--board-ip", default="192.168.178.50")
    parser.add_argument("--board-udp-port", type=int, default=1234)
    parser.add_argument("--server-start-timeout", type=float, default=8.0)
    parser.add_argument(
        "--maps",
        default="canonical,legacy-data2-addr3,legacy-addr2-data3",
        help=f"comma-separated maps: {', '.join(PORT_MAPS)}",
    )
    parser.add_argument(
        "--timings",
        default="spec,fast",
        help=f"comma-separated timing profiles: {', '.join(TIMING_PROFILES)}",
    )
    parser.add_argument("--reset-low", type=float, default=0.10)
    parser.add_argument("--reset-high", type=float, default=0.50)
    parser.add_argument("--attempt-mailbox", action="store_true")
    parser.add_argument("--mailbox-timeout", type=float, default=3.0)
    parser.add_argument("--poll-interval", type=float, default=0.05)
    parser.add_argument("--json-out")
    parser.add_argument("--fail-on-rung1", action="store_true")
    parser.add_argument("--fail-on-rung2", action="store_true")
    args = parser.parse_args()

    server = None
    try:
        if args.start_server:
            server = start_server(args)
            wait_for_server(args.host, args.port, args.server_start_timeout)
        result = run_probe(args)
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
                f.write("\n")
        if args.fail_on_rung1 and not result["rung1_pass"]:
            raise SystemExit(1)
        if args.fail_on_rung2 and args.attempt_mailbox:
            mailbox = result.get("mailbox")
            if not mailbox or mailbox.get("result") != "PASS":
                raise SystemExit(1)
    finally:
        if server is not None:
            server.terminate()
            try:
                out, _ = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                out, _ = server.communicate(timeout=3)
            if out:
                sys.stdout.write(out)


if __name__ == "__main__":
    main()
