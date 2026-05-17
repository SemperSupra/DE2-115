import sys

with open("tb.vcd", "r") as f:
    text = f.read()

mapping = {}
for line in text.split("\n"):
    if line.startswith("$var"):
        parts = line.split()
        if len(parts) >= 5:
            sym = parts[3]
            name = parts[4]
            if name in ['hpi_rd_n', 'hpi_cs_n', 'hpi_wr_n']:
                mapping[sym] = name

time = 0
events = []
for line in text.split("\n"):
    if line.startswith("#"):
        time = int(line[1:])
    elif len(line) >= 2 and line[0] in "01xz":
        sym = line[1:].strip()
        if sym in mapping:
            events.append(f"{time}: {mapping[sym]} = {line[0]}")

for e in events:
    print(e)
