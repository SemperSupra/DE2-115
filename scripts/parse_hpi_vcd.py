import sys

def analyze_vcd_simple(filename):
    print(f"Analyzing {filename}...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find the variables
    vars = {}
    for line in lines:
        if line.startswith("$var"):
            parts = line.split()
            # $var wire 2 * usb_otg_addr $end
            code = parts[3]
            name = parts[4]
            vars[code] = name
            print(f"Found signal: {name} ({code})")
        if line.startswith("$enddefinitions"):
            break

    # Look for changes
    for code, name in vars.items():
        changes = []
        pattern_scalar = f"{code}" # 0! or 1!
        pattern_vector = f" {code}" # b00 *
        
        for line in lines:
            line = line.strip()
            if line.endswith(code):
                if line.startswith("b"):
                    changes.append(line.split()[0][1:])
                else:
                    changes.append(line[0])
        
        if len(changes) > 0:
            unique_vals = set(changes)
            print(f"Signal {name}: {len(changes)} changes, unique values: {unique_vals}")
            if "usb_otg_addr" in name or "hpi_addr" in name:
                if len(unique_vals) > 1:
                    print(f">>> Signal {name} IS TOGGLING!")
                else:
                    print(f">>> Signal {name} IS STUCK at {unique_vals}")
            if "bus_dat_r" in name or "hpi_data" in name:
                print(f"First 10 values for {name}: {changes[:10]}")

if __name__ == "__main__":
    fname = sys.argv[1] if len(sys.argv) > 1 else "board_b_capture.vcd"
    analyze_vcd_simple(fname)
