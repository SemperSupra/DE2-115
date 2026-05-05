#!/bin/bash
set -e

# Target configuration
TARGET_PATH="$(pwd)/de2_115_vga_target.py"
GATEWARE_DIR="$(pwd)/build/terasic_de2_115/gateware"
FIRMWARE_BIN="$(pwd)/firmware/src/demo.bin"
HPI_BRIDGE_SRC="$(pwd)/rtl/cy7c67200_wb_bridge.v"
HPI_BRIDGE_STAGED="$(pwd)/cy7c67200_wb_bridge.v"
CY_IF_SRC="$(pwd)/rtl/CY7C67200_IF.v"
CY_IF_STAGED="$(pwd)/CY7C67200_IF.v"
VGA_TEXT_SRC="$(pwd)/rtl/vga_text_console.v"
VGA_TEXT_STAGED="$(pwd)/vga_text_console.v"

# Stage RTL files to the expected LiteX paths
cp "$HPI_BRIDGE_SRC" "$HPI_BRIDGE_STAGED"
cp "$CY_IF_SRC" "$CY_IF_STAGED"
cp "$VGA_TEXT_SRC" "$VGA_TEXT_STAGED"

ETH_PORT=${1:-1}
SIGNALTAP_FILE=${2:-}
SIGNALTAP_FILE_BASENAME=

echo "--- Stage 1: Generating Software Headers (Port $ETH_PORT) ---"
python3 $TARGET_PATH --eth-port $ETH_PORT

# Check if firmware exists. If not, we might be in the first pass of a two-pass build.
if [ -f "$FIRMWARE_BIN" ]; then
    echo "--- Stage 2: Integrating Firmware into ROM (Port $ETH_PORT) ---"
    python3 $TARGET_PATH --with-firmware $FIRMWARE_BIN --eth-port $ETH_PORT
else
    echo "Info: Firmware binary not found. Skipping integration for now."
    echo "You should build the firmware and then re-run this script."
fi

# Fix paths in QSF for host compilation
sed -i \
    -e 's|/workspace/vga_text_console.v|vga_text_console.v|g' \
    -e 's|/workspace/cy7c67200_wb_bridge.v|cy7c67200_wb_bridge.v|g' \
    -e 's|/workspace/CY7C67200_IF.v|CY7C67200_IF.v|g' \
    -e 's|/workspace/build/terasic_de2_115/gateware/de2_115_vga_platform.v|de2_115_vga_platform.v|g' \
    -e 's|/pythondata-cpu-vexriscv/pythondata_cpu_vexriscv/verilog/VexRiscv.v|VexRiscv.v|g' \
    "$GATEWARE_DIR/de2_115_vga_platform.qsf"

sed -i \
    -e '/^set_global_assignment -name ENABLE_SIGNALTAP /d' \
    -e '/^set_global_assignment -name SIGNALTAP_FILE /d' \
    -e '/^set_global_assignment -name USE_SIGNALTAP_FILE /d' \
    "$GATEWARE_DIR/de2_115_vga_platform.qsf"
if [ -n "$SIGNALTAP_FILE" ]; then
    SIGNALTAP_FILE_BASENAME=$(basename "$SIGNALTAP_FILE")
    cp "$SIGNALTAP_FILE" "$GATEWARE_DIR/$SIGNALTAP_FILE_BASENAME"
    printf '\nset_global_assignment -name ENABLE_SIGNALTAP ON\n' >> "$GATEWARE_DIR/de2_115_vga_platform.qsf"
    printf 'set_global_assignment -name USE_SIGNALTAP_FILE %s\n' "$SIGNALTAP_FILE_BASENAME" >> "$GATEWARE_DIR/de2_115_vga_platform.qsf"
fi

if [ "${DE2_USB_HPI_WEAK_PULLUPS:-0}" = "1" ]; then
    printf '\n# USB HPI read-bus diagnostic: weakly bias DATA high when no device drives it.\n' >> "$GATEWARE_DIR/de2_115_vga_platform.qsf"
    for bit in $(seq 0 15); do
        printf 'set_instance_assignment -name WEAK_PULL_UP_RESISTOR ON -to usb_otg_data[%s]\n' "$bit" >> "$GATEWARE_DIR/de2_115_vga_platform.qsf"
    done
fi

echo "--- Copying VexRiscv CPU Verilog ---"
VEXRISCV_VERILOG=$(find /pythondata-cpu-vexriscv -name VexRiscv.v | head -n 1)
if [ -z "$VEXRISCV_VERILOG" ]; then
    echo "Error: VexRiscv.v not found in /pythondata-cpu-vexriscv"
    exit 1
fi

cp $VEXRISCV_VERILOG $GATEWARE_DIR/
cp "$HPI_BRIDGE_SRC" "$GATEWARE_DIR/"
cp "$CY_IF_SRC" "$GATEWARE_DIR/"
cp "$VGA_TEXT_SRC" "$GATEWARE_DIR/"

echo "--- Staging Quartus host inputs ---"
cp "$GATEWARE_DIR/de2_115_vga_platform.qsf" "$(pwd)/de2_115_vga_platform.qsf"
cp "$GATEWARE_DIR/de2_115_vga_platform.sdc" "$(pwd)/de2_115_vga_platform.sdc"
cp "$GATEWARE_DIR/de2_115_vga_platform.v" "$(pwd)/de2_115_vga_platform.v"
cp "$GATEWARE_DIR/VexRiscv.v" "$(pwd)/VexRiscv.v"
cp "$GATEWARE_DIR"/*.init "$(pwd)/"
if [ -n "$SIGNALTAP_FILE_BASENAME" ]; then
    cp "$GATEWARE_DIR/$SIGNALTAP_FILE_BASENAME" "$(pwd)/$SIGNALTAP_FILE_BASENAME"
fi

echo "--- Build Complete ---"
echo "Quartus project staged at repo root; compile with quartus_sh --flow compile de2_115_vga_platform"
