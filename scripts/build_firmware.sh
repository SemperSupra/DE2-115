#!/bin/bash
set -e

# Firmware configuration
TARGET="terasic_de2_115"
SOFTWARE_DIR="build/$TARGET/software"
FIRMWARE_SRC="firmware/src"

echo "--- Compiling Firmware for $TARGET ---"

if [ ! -d "$SOFTWARE_DIR" ]; then
    echo "Error: Target directory $SOFTWARE_DIR not found. Did you build the SoC first?"
    exit 1
fi

# We use the built-in Makefile logic from LiteX to ensure all CSRs and flags are correct.
# Create a local Makefile that points to the LiteX software headers.
cat <<EOF > $FIRMWARE_SRC/Makefile
BUILD_DIR=../../build/$TARGET

include \$(BUILD_DIR)/software/include/generated/variables.mak
include \$(SOC_DIRECTORY)/software/common.mak

OBJECTS = main.o font_8x16.o
CRT0_FILE = \$(BUILD_DIR)/software/bios/crt0.o

all: demo.bin

%.bin: %.elf
	\$(OBJCOPY) -O binary \$< \$@
	chmod -x \$@

demo.elf: \$(OBJECTS)
	\$(CC) \$(LDFLAGS) -T \$(BIOS_DIRECTORY)/linker.ld -N -o \$@ \$(CRT0_FILE) \$^ \$(PACKAGES:%=-L\$(BUILD_DIR)/software/%) -Wl,--start-group -lc -lbase -lcompiler_rt -lfatfs -llitespi -llitedram -lliteeth -llitesdcard -llitesata -Wl,--end-group
	chmod -x \$@

%.o: %.c
	\$(CC) \$(CFLAGS) -c \$< -o \$@

%.o: %.S
	\$(CC) \$(CFLAGS) -c \$< -o \$@

clean:
	rm -f *.o *.elf *.bin .*~

.PHONY: all clean
EOF

cd $FIRMWARE_SRC
make clean all

echo "--- Firmware Build Complete ---"
echo "Binary location: $FIRMWARE_SRC/demo.bin"
