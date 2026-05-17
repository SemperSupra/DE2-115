#!/usr/bin/env python3
"""Shared CY7C67200 HPI helpers for DE2-115 Etherbone diagnostics."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
BRIDGE_LAST_CTRL = USB_BASE + 0x104
BRIDGE_LAST_SAMPLE = USB_BASE + 0x108
BRIDGE_LAST_CY = USB_BASE + 0x10C

COMM_ACK = 0x0FED
COMM_NAK = 0xDEAD
COMM_RESET = 0xFA50
COMM_EXEC_INT = 0xCE01

CPU_FLAGS_REG = 0xC000
BANK_ADDR_REG = 0xC002
HW_REV_REG = 0xC004
POWER_CONTROL_REG = 0xC00A
HPI_IRQ_ROUTING_REG = 0x0142
HPI_SIE1_MSG_ADR = 0x0144
HPI_SIE2_MSG_ADR = 0x0148


@dataclass(frozen=True)
class PortMap:
    name: str
    data: int
    mailbox: int
    address: int
    status: int

    def offsets(self) -> Tuple[int, int, int, int]:
        return (self.data, self.mailbox, self.address, self.status)


PORT_MAPS: Dict[str, PortMap] = {
    # Datasheet, Linux c67x00, and Terasic Nios demo mapping.
    "canonical": PortMap("canonical", data=0x000, mailbox=0x004, address=0x008, status=0x00C),
    # Legacy local probes that appeared live on checksum 0x033E503E.
    "legacy-data2-addr3": PortMap(
        "legacy-data2-addr3", data=0x008, mailbox=0x004, address=0x00C, status=0x000
    ),
    "legacy-addr2-data3": PortMap(
        "legacy-addr2-data3", data=0x00C, mailbox=0x004, address=0x008, status=0x000
    ),
}


@dataclass(frozen=True)
class TimingProfile:
    name: str
    access_cycles: int
    sample_offset: int
    turnaround_cycles: int


TIMING_PROFILES: Dict[str, TimingProfile] = {
    # At the 50 MHz system clock, 8 cycles gives 160 ns cycle time.
    "spec": TimingProfile("spec", access_cycles=8, sample_offset=3, turnaround_cycles=3),
    # Historical breakthrough profile. This is marginal against the 125 ns datasheet cycle.
    "fast": TimingProfile("fast", access_cycles=6, sample_offset=2, turnaround_cycles=2),
    # Slow profile used by earlier host diagnostics.
    "slow": TimingProfile("slow", access_cycles=63, sample_offset=8, turnaround_cycles=8),
}


def hpi_cfg(force_rst: int, rst_n: int, access: int, sample: int, turnaround: int) -> int:
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )


def parse_csv_names(value: str, allowed: Dict[str, object]) -> List[str]:
    names = [part.strip() for part in value.split(",") if part.strip()]
    unknown = [name for name in names if name not in allowed]
    if unknown:
        raise ValueError(f"unknown value(s): {', '.join(unknown)}")
    return names


class CyHpi:
    def __init__(self, wb, port_map: PortMap, usb_base: int = USB_BASE):
        self.wb = wb
        self.port_map = port_map
        self.usb_base = usb_base

    def _addr(self, offset: int) -> int:
        return self.usb_base + offset

    def write_port(self, offset: int, value: int) -> None:
        self.wb.write(self._addr(offset), value & 0xFFFF)

    def read_port(self, offset: int) -> int:
        return self.wb.read(self._addr(offset)) & 0xFFFF

    def write_addr(self, addr: int) -> None:
        self.write_port(self.port_map.address, addr)

    def write_data(self, value: int) -> None:
        self.write_port(self.port_map.data, value)

    def read_data(self) -> int:
        return self.read_port(self.port_map.data)

    def write_mailbox(self, value: int) -> None:
        self.write_port(self.port_map.mailbox, value)

    def read_mailbox(self) -> int:
        return self.read_port(self.port_map.mailbox)

    def read_status(self) -> int:
        return self.read_port(self.port_map.status)

    def write_mem16(self, addr: int, value: int) -> None:
        self.write_addr(addr)
        self.write_data(value)

    def read_mem16(self, addr: int) -> int:
        self.write_addr(addr)
        return self.read_data()

    def write_words16(self, addr: int, values: Iterable[int]) -> None:
        self.write_addr(addr)
        for value in values:
            self.write_data(value)

    def read_words16(self, addr: int, count: int) -> List[int]:
        self.write_addr(addr)
        return [self.read_data() for _ in range(count)]

    def reset(self, timing: TimingProfile, reset_low_s: float, reset_high_s: float) -> int:
        cfg_low = hpi_cfg(1, 0, timing.access_cycles, timing.sample_offset, timing.turnaround_cycles)
        cfg_high = hpi_cfg(1, 1, timing.access_cycles, timing.sample_offset, timing.turnaround_cycles)
        self.wb.write(BRIDGE_CFG0, cfg_low)
        time.sleep(reset_low_s)
        self.wb.write(BRIDGE_CFG0, cfg_high)
        time.sleep(reset_high_s)
        return cfg_high

    def bridge_snapshot(self) -> Dict[str, int]:
        return {
            "cfg": self.wb.read(BRIDGE_CFG0),
            "last_ctrl": self.wb.read(BRIDGE_LAST_CTRL),
            "last_sample": self.wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF,
            "last_cy": self.wb.read(BRIDGE_LAST_CY) & 0xFFFF,
        }


def classify_block(expected: List[int], actual: List[int]) -> str:
    if actual == expected:
        return "PASS"
    if len(set(actual)) == 1:
        return "ALIAS_OR_ECHO"
    if actual and actual[:-1] == expected[1:]:
        return "OFF_BY_ONE_DUMMY_READ_PATTERN"
    return "FAIL"
