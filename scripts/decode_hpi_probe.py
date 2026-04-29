
import sys

def decode_hpi_probe(hex_str):
    # Ensure it's 192 bits (48 hex chars)
    hex_str = hex_str.strip().replace(" ", "")
    if len(hex_str) < 48:
        hex_str = hex_str.zfill(48)
    
    val = int(hex_str, 16)
    
    def get_bits(v, pos, width):
        return (v >> pos) & ((1 << width) - 1)

    # Layout from cy7c67200_wb_bridge.v:
    # 191: 1'b0
    # 190: cy_o_int
    # 184-189: cfg_turnaround_cycles (6)
    # 178-183: cfg_access_cycles (6)
    # 172-177: cfg_sample_offset (6)
    # 166-171: effective_access_cycles (6)
    # 160-165: sample_threshold (6)
    # 159: diag_captured
    # 158: diag_capture_match
    # 154-157: diag_source (4)
    # 152-153: diag_in (2)
    # 151: hpi_int0
    # 150: hpi_int1
    # 149: hpi_int2 (dreq)
    # 148: hpi_access
    # 147: rst
    # 146: hpi_rst_n
    # 145: wb_access
    # 144: debug_access
    # 143: active
    # 142: debug_latched
    # 141: latched_we
    # 140: wb_we
    # 139: hpi_cs_n
    # 138: hpi_rd_n
    # 137: hpi_wr_n
    # 135-136: hpi_addr (2)
    # 133-134: state (2)
    # 127-132: count (6)
    # 126: wb_ack
    # 112-125: local_adr (14)
    # 96-111: write_data (16)
    # 80-95: read_data (16)
    # 64-79: sample_data (16)
    # 48-63: last_sample_data (16)
    # 32-47: cy_o_data (16)
    # 16-31: hpi_data (16)
    # 0-15: wb_dat_w (16)

    fields = {
        "cy_o_int": get_bits(val, 190, 1),
        "cfg_turnaround": get_bits(val, 184, 6),
        "cfg_access": get_bits(val, 178, 6),
        "cfg_sample_offset": get_bits(val, 172, 6),
        "eff_access": get_bits(val, 166, 6),
        "sample_thresh": get_bits(val, 160, 6),
        "captured": get_bits(val, 159, 1),
        "match": get_bits(val, 158, 1),
        "diag_src": get_bits(val, 154, 4),
        "diag_in": get_bits(val, 152, 2),
        "hpi_int0": get_bits(val, 151, 1),
        "hpi_int1": get_bits(val, 150, 1),
        "hpi_dreq": get_bits(val, 149, 1),
        "hpi_access": get_bits(val, 148, 1),
        "rst": get_bits(val, 147, 1),
        "hpi_rst_n": get_bits(val, 146, 1),
        "wb_access": get_bits(val, 145, 1),
        "debug_access": get_bits(val, 144, 1),
        "active": get_bits(val, 143, 1),
        "debug_latched": get_bits(val, 142, 1),
        "latched_we": get_bits(val, 141, 1),
        "wb_we": get_bits(val, 140, 1),
        "hpi_cs_n": get_bits(val, 139, 1),
        "hpi_rd_n": get_bits(val, 138, 1),
        "hpi_wr_n": get_bits(val, 137, 1),
        "hpi_addr": get_bits(val, 135, 2),
        "state": get_bits(val, 133, 2),
        "count": get_bits(val, 127, 6),
        "wb_ack": get_bits(val, 126, 1),
        "local_adr": get_bits(val, 112, 14),
        "write_data": get_bits(val, 96, 16),
        "read_data": get_bits(val, 80, 16),
        "sample_data": get_bits(val, 64, 16),
        "last_sample": get_bits(val, 48, 16),
        "cy_o_data": get_bits(val, 32, 16),
        "hpi_data": get_bits(val, 16, 16),
        "wb_dat_w": get_bits(val, 0, 16),
    }

    for k, v in fields.items():
        print(f"{k:18}: {v:04X} ({v})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        decode_hpi_probe(sys.argv[1])
    else:
        print("Usage: python decode_hpi_probe.py <hex_192bit>")
