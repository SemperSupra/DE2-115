import re
import os

def extract_lcp(input_path, output_path):
    print(f"Extracting LCP data from {input_path}...")
    
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Match the array content: static unsigned char de2_bios[2691] = { ... };
    match = re.search(r'unsigned\s+char\s+de2_bios\s*\[\s*\d*\s*\]\s*=\s*\{([^}]+)\}', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find de2_bios array in the input file.")
    
    # Extract hex values
    hex_values = re.findall(r'0x[0-9a-fA-F]+', match.group(1))
    data = [int(v, 16) for v in hex_values]
    
    # Generate the header file
    with open(output_path, 'w') as f:
        f.write("/* Automatically generated LCP firmware blob */\n")
        f.write("#ifndef LCP_BLOB_H\n")
        f.write("#define LCP_BLOB_H\n\n")
        f.write(f"#define LCP_DATA_SIZE {len(data)}\n\n")
        f.write("static const uint8_t de2_bios[] = {\n")
        for i, val in enumerate(data):
            f.write(f"0x{val:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n")
        f.write("\n};\n\n")
        f.write("#endif // LCP_BLOB_H\n")
    
    print(f"Successfully wrote {len(data)} bytes to {output_path}")

if __name__ == "__main__":
    src = "Downloads/cy7c67300/Source/coprocessor/de_app/de2_bios.h"
    dst = "firmware/src/lcp_blob.h"
    extract_lcp(src, dst)
