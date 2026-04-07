#!/bin/bash
set -e

# Target configuration
TARGET_PATH="$(pwd)/de2_115_vga_target.py"
GATEWARE_DIR="$(pwd)/build/terasic_de2_115/gateware"
FIRMWARE_BIN="$(pwd)/firmware/src/demo.bin"

echo "--- Stage 1: Generating Software Headers ---"
python3 $TARGET_PATH

# Check if firmware exists. If not, we might be in the first pass of a two-pass build.
if [ -f "$FIRMWARE_BIN" ]; then
    echo "--- Stage 2: Integrating Firmware into ROM ---"
    python3 $TARGET_PATH --with-firmware $FIRMWARE_BIN
else
    echo "Info: Firmware binary not found. Skipping integration for now."
    echo "You should build the firmware and then re-run this script."
fi

echo "--- Copying VexRiscv CPU Verilog ---"
VEXRISCV_VERILOG=$(find /pythondata-cpu-vexriscv -name VexRiscv.v | head -n 1)
if [ -z "$VEXRISCV_VERILOG" ]; then
    echo "Error: VexRiscv.v not found in /pythondata-cpu-vexriscv"
    exit 1
fi

cp $VEXRISCV_VERILOG $GATEWARE_DIR/

echo "--- Build Complete ---"
echo "Bitstream location: build/terasic_de2_115/gateware/terasic_de2_115.sof"
