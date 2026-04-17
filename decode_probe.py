import sys

def decode_probe_v6(hex_str):
    if hex_str.startswith("probe_data"):
        hex_str = hex_str.split("=")[1].strip()
    val = int(hex_str, 16)
    res = {}
    res["wb_dat_w"] = (val >> 0) & 0xFFFF
    res["hpi_data"] = (val >> 16) & 0xFFFF
    res["cy_o_data"] = (val >> 32) & 0xFFFF
    res["last_sample_data"] = (val >> 48) & 0xFFFF
    res["sample_data"] = (val >> 64) & 0xFFFF
    res["read_data"] = (val >> 80) & 0xFFFF
    res["write_data"] = (val >> 96) & 0xFFFF
    res["latched_adr"] = (val >> 112) & 0x3FF
    res["wb_ack"] = (val >> 125) & 1
    res["hpi_addr"] = (val >> 131) & 3
    res["hpi_wr_n"] = (val >> 133) & 1
    res["hpi_rd_n"] = (val >> 134) & 1
    res["hpi_cs_n"] = (val >> 135) & 1
    res["count"] = (val >> 136) & 0x3F
    res["state"] = (val >> 142) & 7
    res["wb_we"] = (val >> 144) & 1
    res["latched_we"] = (val >> 145) & 1
    res["debug_latched"] = (val >> 146) & 1
    res["active"] = (val >> 147) & 1
    res["debug_access"] = (val >> 148) & 1
    res["wb_access"] = (val >> 149) & 1
    res["hpi_rst_n"] = (val >> 150) & 1
    res["rst"] = (val >> 151) & 1
    res["hpi_access"] = (val >> 152) & 1
    return res

for line in sys.stdin:
    line = line.strip()
    if not line or not (line.startswith("probe_data") or len(line) > 30):
        continue
    try:
        f = decode_probe_v6(line)
        print(f"  RST: {f['rst']} HPI_RST_N: {f['hpi_rst_n']} WB_ACC: {f['wb_access']} ACT: {f['active']} HA: {f['hpi_access']} DA: {f['debug_access']}")
        print(f"  HPI Pins: CS_N={f['hpi_cs_n']} RD_N={f['hpi_rd_n']} WR_N={f['hpi_wr_n']} ADDR={f['hpi_addr']} DATA={f['hpi_data']:04X}")
        print(f"  State: {f['state']} Count: {f['count']} WB_DAT_W: {f['wb_dat_w']:04X} ADR: {f['latched_adr']:03X}")
        print(f"  Data: read={f['read_data']:04X} write={f['write_data']:04X} cy_o={f['cy_o_data']:04X}")
    except:
        pass

