import struct
import sys

def parse_lcp(input_path, output_path):
    print(f"Parsing Linux LCP firmware: {input_path}")
    
    with open(input_path, 'rb') as f:
        data = f.read()
    
    records = []
    offset = 0
    
    while offset < len(data):
        # Scan header: Signature (2), Length (2), Address (2)
        # Signature is 0xC5BE (Big Endian)
        if offset + 6 > len(data):
            break
            
        sig, length, addr = struct.unpack('>HHH', data[offset:offset+6])
        
        if sig != 0xC5BE:
            print(f"Warning: Unknown signature 0x{sig:04x} at offset {offset}")
            # Try to find next 0xC5BE
            next_sig = data.find(b'\xC5\xBE', offset + 1)
            if next_sig == -1:
                break
            offset = next_sig
            continue
            
        payload_size = length * 2 # length is in 16-bit words
        payload = data[offset+6 : offset+6+payload_size]
        
        print(f"Record at 0x{offset:04x}: Addr=0x{addr:04x}, Words={length}")
        
        # Convert payload to 16-bit words (Little Endian for HPI writes)
        words = []
        for i in range(0, len(payload), 2):
            if i + 1 < len(payload):
                word = struct.unpack('<H', payload[i:i+2])[0]
                words.append(word)
        
        records.append({
            'addr': addr,
            'words': words
        })
        
        offset += 6 + payload_size

    # Generate Header
    with open(output_path, 'w') as f:
        f.write("/* Automatically parsed from Linux cy7c67x00.bin */\n")
        f.write("#ifndef LCP_DATA_H\n")
        f.write("#define LCP_DATA_H\n\n")
        f.write("#include <stdint.h>\n\n")
        
        f.write("struct lcp_record {\n")
        f.write("    uint16_t addr;\n")
        f.write("    uint16_t len;\n")
        f.write("    const uint16_t *data;\n")
        f.write("};\n\n")
        
        for i, rec in enumerate(records):
            f.write(f"static const uint16_t lcp_rec_{i}_data[] = {{\n")
            for j, val in enumerate(rec['words']):
                f.write(f"0x{val:04x}, ")
                if (j + 1) % 8 == 0:
                    f.write("\n")
            f.write("\n};\n\n")
            
        f.write(f"#define LCP_RECORD_COUNT {len(records)}\n\n")
        f.write("static const struct lcp_record lcp_records[] = {\n")
        for i, rec in enumerate(records):
            f.write(f"    {{ 0x{rec['addr']:04x}, {len(rec['words'])}, lcp_rec_{i}_data }},\n")
        f.write("};\n\n")
        f.write("#endif\n")
    
    print(f"Successfully wrote {len(records)} records to {output_path}")

if __name__ == "__main__":
    parse_lcp("cy7c67x00.bin", "firmware/src/lcp_data.h")
