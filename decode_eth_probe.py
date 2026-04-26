import sys


def normalize_hex(line):
    if line.startswith("probe_data"):
        line = line.split("=", 1)[1].strip()
    return line


def decode_eth_probe(hex_str):
    val = int(hex_str, 16)
    data = [(val >> (8*i)) & 0xFF for i in range(16)]
    ctl = (val >> 128) & 0xFFFFFFFF
    ctl_pairs = [(ctl >> (2*i)) & 0x3 for i in range(16)]
    return {
        "data": data,
        "ctl_pairs": ctl_pairs,
        "length": (val >> 160) & 0xFFF,
        "count": (val >> 172) & 0x1F,
        "frames": (val >> 177) & 0xFF,
        "errors": (val >> 185) & 0xF,
        "rx_dv": (val >> 189) & 1,
        "active": (val >> 190) & 1,
        "done": (val >> 191) & 1,
    }


def verdict(data):
    if data[:6] == [0xFF] * 6 and len(data) >= 14 and data[12:14] == [0x08, 0x06]:
        return "arp_broadcast_header"
    if data[:6] == [0xFF] * 6:
        return "broadcast_header"
    if data[:7] == [0x55] * 7 and data[7] == 0xD5:
        return "preamble_ok"
    if 0xD5 in data and all(b == 0x55 for b in data[1:data.index(0xD5)]):
        return "preamble_sfd_seen"
    if data[:4] == [0x55] * 4:
        return "partial_preamble"
    if any(data):
        return "unexpected_first_bytes"
    return "no_frame_captured"


def ethernet_header(data):
    if len(data) < 14:
        return None
    dst = ":".join(f"{b:02X}" for b in data[0:6])
    src = ":".join(f"{b:02X}" for b in data[6:12])
    ethertype = (data[12] << 8) | data[13]
    return dst, src, ethertype


for line in sys.stdin:
    line = line.strip()
    if not line or not (line.startswith("probe_data") or len(line) > 30):
        continue
    try:
        f = decode_eth_probe(normalize_hex(line))
        data_hex = " ".join(f"{b:02X}" for b in f["data"])
        ctl_hex = " ".join(f"{c:02b}" for c in f["ctl_pairs"])
        print(
            f"  Capture: done={f['done']} active={f['active']} rx_dv={f['rx_dv']} "
            f"frames={f['frames']} len={f['length']} stored={f['count']} errors={f['errors']}"
        )
        print(f"  First bytes: {data_hex}")
        print(f"  RX_CTL pairs: {ctl_hex}")
        print(f"  Verdict: {verdict(f['data'])}")
        header = ethernet_header(f["data"])
        if header is not None:
            dst, src, ethertype = header
            print(f"  Ethernet: dst={dst} src={src} ethertype=0x{ethertype:04X}")
    except Exception as e:
        print(f"decode_error: {e}")
