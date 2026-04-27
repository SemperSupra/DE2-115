#!/usr/bin/env python3
import argparse


FIELDS = [
    ("wb_dat_w_low", 0, 16),
    ("hpi_data", 16, 16),
    ("cy_o_data", 32, 16),
    ("last_sample_data", 48, 16),
    ("sample_data", 64, 16),
    ("read_data", 80, 16),
    ("write_data", 96, 16),
    ("local_adr", 112, 14),
    ("wb_ack", 126, 1),
    ("count", 127, 6),
    ("state", 133, 2),
    ("hpi_addr", 135, 2),
    ("hpi_wr_n", 137, 1),
    ("hpi_rd_n", 138, 1),
    ("hpi_cs_n", 139, 1),
    ("wb_we", 140, 1),
    ("latched_we", 141, 1),
    ("debug_latched", 142, 1),
    ("active", 143, 1),
    ("debug_access", 144, 1),
    ("wb_access", 145, 1),
    ("hpi_rst_n", 146, 1),
    ("rst", 147, 1),
    ("hpi_access", 148, 1),
    ("hpi_dreq", 149, 1),
    ("hpi_int1", 150, 1),
    ("hpi_int0", 151, 1),
    ("diag_in", 152, 2),
    ("diag_source", 154, 4),
    ("diag_capture_match", 158, 1),
    ("diag_captured", 159, 1),
    ("sample_threshold", 160, 6),
    ("effective_access_cycles", 166, 6),
    ("cfg_sample_offset", 172, 6),
    ("cfg_access_cycles", 178, 6),
    ("cfg_turnaround_cycles", 184, 6),
    ("cy_o_int", 190, 1),
]


def bits(value, start, width):
    return (value >> start) & ((1 << width) - 1)


def main():
    parser = argparse.ArgumentParser(description="Decode the 192-bit HPI0 source/probe value.")
    parser.add_argument("hex_value", help="Probe value from quartus_stp read_source_probe.tcl")
    args = parser.parse_args()

    value = int(args.hex_value.strip().replace("_", ""), 16)
    for name, start, width in FIELDS:
        field = bits(value, start, width)
        if width == 1:
            print(f"{name:<24} {field}")
        else:
            hex_width = (width + 3) // 4
            print(f"{name:<24} 0x{field:0{hex_width}x}")


if __name__ == "__main__":
    main()
