import sys


HPI_MODES = {
    0: "any",
    1: "read_data",
    2: "write_data",
    3: "read_status",
    4: "write_address",
    5: "read_mailbox",
    6: "write_mailbox",
    7: "write_status",
}


def normalize_hex(line):
    if line.startswith("probe_data"):
        line = line.split("=", 1)[1].strip()
    return line


def decode_probe_v7(hex_str):
    val = int(hex_str, 16)
    return {
        "wb_dat_w": (val >> 0) & 0xFFFF,
        "hpi_data": (val >> 16) & 0xFFFF,
        "cy_o_data": (val >> 32) & 0xFFFF,
        "last_sample_data": (val >> 48) & 0xFFFF,
        "sample_data": (val >> 64) & 0xFFFF,
        "read_data": (val >> 80) & 0xFFFF,
        "write_data": (val >> 96) & 0xFFFF,
        "local_adr": (val >> 112) & 0x3FFF,
        "wb_ack": (val >> 126) & 1,
        "count": (val >> 127) & 0x3F,
        "state": (val >> 133) & 0x3,
        "hpi_addr": (val >> 135) & 0x3,
        "hpi_wr_n": (val >> 137) & 1,
        "hpi_rd_n": (val >> 138) & 1,
        "hpi_cs_n": (val >> 139) & 1,
        "wb_we": (val >> 140) & 1,
        "latched_we": (val >> 141) & 1,
        "debug_latched": (val >> 142) & 1,
        "active": (val >> 143) & 1,
        "debug_access": (val >> 144) & 1,
        "wb_access": (val >> 145) & 1,
        "hpi_rst_n": (val >> 146) & 1,
        "rst": (val >> 147) & 1,
        "hpi_access": (val >> 148) & 1,
        "hpi_dreq": (val >> 149) & 1,
        "hpi_int1": (val >> 150) & 1,
        "hpi_int0": (val >> 151) & 1,
        "diag_in": (val >> 152) & 0x3,
        "diag_source": (val >> 154) & 0xF,
        "capture_match": (val >> 158) & 1,
        "captured": (val >> 159) & 1,
        "sample_threshold": (val >> 160) & 0x3F,
        "effective_access": (val >> 166) & 0x3F,
        "cfg_sample_offset": (val >> 172) & 0x3F,
        "cfg_access": (val >> 178) & 0x3F,
        "cfg_turnaround": (val >> 184) & 0x3F,
        "cy_o_int": (val >> 190) & 1,
    }


def decode_probe_v6(hex_str):
    val = int(hex_str, 16)
    return {
        "wb_dat_w": (val >> 0) & 0xFFFF,
        "hpi_data": (val >> 16) & 0xFFFF,
        "cy_o_data": (val >> 32) & 0xFFFF,
        "last_sample_data": (val >> 48) & 0xFFFF,
        "sample_data": (val >> 64) & 0xFFFF,
        "read_data": (val >> 80) & 0xFFFF,
        "write_data": (val >> 96) & 0xFFFF,
        "local_adr": (val >> 112) & 0x3FF,
        "wb_ack": (val >> 125) & 1,
        "hpi_addr": (val >> 131) & 3,
        "hpi_wr_n": (val >> 133) & 1,
        "hpi_rd_n": (val >> 134) & 1,
        "hpi_cs_n": (val >> 135) & 1,
        "count": (val >> 136) & 0x3F,
        "state": (val >> 142) & 7,
        "wb_we": (val >> 144) & 1,
        "latched_we": (val >> 145) & 1,
        "debug_latched": (val >> 146) & 1,
        "active": (val >> 147) & 1,
        "debug_access": (val >> 148) & 1,
        "wb_access": (val >> 149) & 1,
        "hpi_rst_n": (val >> 150) & 1,
        "rst": (val >> 151) & 1,
        "hpi_access": (val >> 152) & 1,
    }


def print_v7(f):
    mode = (f["diag_source"] >> 1) & 0x7
    print(
        f"  Capture: captured={f['captured']} match={f['capture_match']} "
        f"source=0x{f['diag_source']:X} mode={HPI_MODES.get(mode, 'unknown')}"
    )
    print(
        f"  Reset/sideband: rst={f['rst']} hpi_rst_n={f['hpi_rst_n']} "
        f"int0={f['hpi_int0']} int1={f['hpi_int1']} dreq={f['hpi_dreq']} cy_o_int={f['cy_o_int']}"
    )
    print(
        f"  HPI pins: cs_n={f['hpi_cs_n']} rd_n={f['hpi_rd_n']} "
        f"wr_n={f['hpi_wr_n']} addr={f['hpi_addr']} data={f['hpi_data']:04X}"
    )
    print(
        f"  Bus/FSM: wb_access={f['wb_access']} debug_access={f['debug_access']} "
        f"active={f['active']} state={f['state']} count={f['count']} "
        f"wb_we={f['wb_we']} latched_we={f['latched_we']} local_adr=0x{f['local_adr']:04X}"
    )
    print(
        f"  Data: wb_dat_w={f['wb_dat_w']:04X} write={f['write_data']:04X} "
        f"read={f['read_data']:04X} sample={f['sample_data']:04X} "
        f"last_sample={f['last_sample_data']:04X} cy_o={f['cy_o_data']:04X}"
    )
    print(
        f"  Timing: access={f['cfg_access']} sample_offset={f['cfg_sample_offset']} "
        f"threshold={f['sample_threshold']} turnaround={f['cfg_turnaround']}"
    )


def print_v6(f):
    print(
        f"  RST: {f['rst']} HPI_RST_N: {f['hpi_rst_n']} "
        f"WB_ACC: {f['wb_access']} ACT: {f['active']} HA: {f['hpi_access']} DA: {f['debug_access']}"
    )
    print(
        f"  HPI Pins: CS_N={f['hpi_cs_n']} RD_N={f['hpi_rd_n']} "
        f"WR_N={f['hpi_wr_n']} ADDR={f['hpi_addr']} DATA={f['hpi_data']:04X}"
    )
    print(
        f"  State: {f['state']} Count: {f['count']} "
        f"WB_DAT_W: {f['wb_dat_w']:04X} ADR: {f['local_adr']:03X}"
    )
    print(f"  Data: read={f['read_data']:04X} write={f['write_data']:04X} cy_o={f['cy_o_data']:04X}")


for line in sys.stdin:
    line = line.strip()
    if not line or not (line.startswith("probe_data") or len(line) > 30):
        continue
    try:
        hex_str = normalize_hex(line)
        if len(hex_str) > 40:
            print_v7(decode_probe_v7(hex_str))
        else:
            print_v6(decode_probe_v6(hex_str))
    except Exception as e:
        print(f"decode_error: {e}")
