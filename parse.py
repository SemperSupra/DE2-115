import sys
import re

with open("tb.vcd", "r") as f:
    text = f.read()

mapping = {}
for line in text.split("\n"):
    if line.startswith("$var"):
        parts = line.split()
        if len(parts) >= 5:
            sym = parts[3]
            name = parts[4]
            mapping[sym] = name

print("Mapping:", {k:v for k,v in mapping.items() if v in ['clk', 'hpi_rd_n', 'hpi_cs_n', 'hpi_strobe', 'hpi_access', 'state', 'count', 'active']})

time = 0
events = []
for line in text.split("\n"):
    if line.startswith("#"):
        time = int(line[1:])
    elif len(line) >= 2 and line[0] in "01xz":
        sym = line[1:].strip()
        if sym in mapping and mapping[sym] in ['hpi_rd_n', 'hpi_cs_n', 'hpi_strobe', 'hpi_access', 'state', 'count', 'active']:
            events.append(f"{time}: {mapping[sym]} = {line[0]}")
    elif line.startswith("b"):
        parts = line.split()
        if len(parts) == 2:
            sym = parts[1]
            if sym in mapping and mapping[sym] in ['hpi_rd_n', 'hpi_cs_n', 'hpi_strobe', 'hpi_access', 'state', 'count', 'active']:
                events.append(f"{time}: {mapping[sym]} = {parts[0][1:]}")

for e in events[:50]:
    print(e)
