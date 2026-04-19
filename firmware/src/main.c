#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>

#include "font.h"

// --- Constants ---
#define VGA_TEXT_BASE 0x83000000u
#define VGA_COLS 80
#define VGA_ROWS 30
#define VGA_TEXT ((volatile uint32_t *)VGA_TEXT_BASE)

#define CY_BASE 0x82000000u
#define CY_HPI_DATA    (*(volatile uint32_t *)(CY_BASE + 0x000))
#define CY_HPI_MAILBOX (*(volatile uint32_t *)(CY_BASE + 0x004))
#define CY_HPI_ADDRESS (*(volatile uint32_t *)(CY_BASE + 0x008))
#define CY_HPI_STATUS  (*(volatile uint32_t *)(CY_BASE + 0x00C))
#define CY_BRIDGE_CFG0 (*(volatile uint32_t *)(CY_BASE + 0x100))

// --- MDIO ---
#define MDC (1u << CSR_ETHPHY_MDIO_W_MDC_OFFSET)
#define MDO (1u << CSR_ETHPHY_MDIO_W_W_OFFSET)
#define OE  (1u << CSR_ETHPHY_MDIO_W_OE_OFFSET)
#define R   (1u << CSR_ETHPHY_MDIO_R_R_OFFSET)

static void mdio_delay(void) {
    for (volatile int i = 0; i < 100; i++);
}

static uint16_t mdio_read(uint8_t phy_addr, uint8_t reg_addr) {
    uint32_t val = 0;
    int i;
    for (i = 0; i < 32; i++) {
        ethphy_mdio_w_write(OE | MDC); mdio_delay();
        ethphy_mdio_w_write(OE); mdio_delay();
    }
    uint32_t cmd = 0x60000000u | ((uint32_t)phy_addr << 23) | ((uint32_t)reg_addr << 18);
    for (i = 0; i < 14; i++) {
        uint32_t bit = (cmd & 0x80000000u) ? MDO : 0;
        ethphy_mdio_w_write(OE | bit | MDC); mdio_delay();
        ethphy_mdio_w_write(OE | bit); mdio_delay();
        cmd <<= 1;
    }
    ethphy_mdio_w_write(MDC); mdio_delay();
    ethphy_mdio_w_write(0); mdio_delay();
    for (i = 0; i < 16; i++) {
        ethphy_mdio_w_write(MDC); mdio_delay();
        uint32_t bit = (ethphy_mdio_r_read() & R) ? 1 : 0;
        ethphy_mdio_w_write(0); mdio_delay();
        val = (val << 1) | bit;
    }
    return (uint16_t)val;
}

static void mdio_write(uint8_t phy_addr, uint8_t reg_addr, uint16_t data) {
    int i;
    for (i = 0; i < 32; i++) {
        ethphy_mdio_w_write(OE | MDC); mdio_delay();
        ethphy_mdio_w_write(OE); mdio_delay();
    }
    uint32_t cmd = 0x50020000u | ((uint32_t)phy_addr << 23) | ((uint32_t)reg_addr << 18) | (uint32_t)data;
    for (i = 0; i < 32; i++) {
        uint32_t bit = (cmd & 0x80000000u) ? MDO : 0;
        ethphy_mdio_w_write(OE | bit | MDC); mdio_delay();
        ethphy_mdio_w_write(OE | bit); mdio_delay();
        cmd <<= 1;
    }
    ethphy_mdio_w_write(0); mdio_delay();
}

// --- VGA ---
static void vga_clear(void) {
    for (int i = 0; i < VGA_COLS * VGA_ROWS; i++) VGA_TEXT[i] = ' ';
}

static void vga_puts_xy(unsigned int row, unsigned int col, const char *str) {
    if (row >= VGA_ROWS) return;
    volatile uint32_t *p = &VGA_TEXT[row * VGA_COLS + col];
    while (*str && col < VGA_COLS) { *p++ = *str++; col++; }
}

static void itoa_hex16(uint16_t value, char *buf) {
    const char *hex_chars = "0123456789ABCDEF";
    buf[0] = hex_chars[(value >> 12) & 0xF];
    buf[1] = hex_chars[(value >> 8) & 0xF];
    buf[2] = hex_chars[(value >> 4) & 0xF];
    buf[3] = hex_chars[value & 0xF];
    buf[4] = '\0';
}

static void vga_put_hex16_xy(unsigned int row, unsigned int col, uint16_t val) {
    char buf[5]; itoa_hex16(val, buf); vga_puts_xy(row, col, buf);
}

// --- Utilities ---
void msleep(uint32_t ms) {
    for (volatile int i = 0; i < ms * 1000; i++);
}

void irq_setmask(uint32_t mask) { (void)mask; }
void irq_setie(uint32_t ie) { (void)ie; }

// --- Main ---
int main(void) {
    uint32_t tick = 0;
    vga_clear();
    vga_puts_xy(0, 0, "DE2-115 DEEP DIVE: ETH & USB");
    printf("\n--- DE2-115 DEEP DIVE STARTING ---\n");

    while (1) {
        uint32_t sw = switches_in_read();
        leds_r_out_write(sw);
        leds_g_out_write(1 << (tick % 8));

        if ((tick % 10) == 0) {
            printf("Tick: %d, SW: 0x%08x\n", tick, sw);
        }

        // --- Ethernet Deep Dive ---
        uint8_t eth_addr = (sw & 0x20000) ? 17 : 16;
        vga_puts_xy(2, 0, "ETH PORT:");
        vga_puts_xy(2, 10, (sw & 0x20000) ? "1 (ADDR 17)" : "0 (ADDR 16)");

        if (sw & 0x10000) {
            vga_puts_xy(3, 30, "FORCING COPPER 1000M...");
            mdio_write(eth_addr, 27, 0x000B);
            mdio_write(eth_addr, 0, 0x9140);
            msleep(100);
        } else {
            vga_puts_xy(3, 30, "AUTO-NEG MODE         ");
        }

        uint16_t bmsr2 = mdio_read(eth_addr, 1);
        uint16_t r27 = mdio_read(eth_addr, 27);
        uint16_t r10 = mdio_read(eth_addr, 10);
        
        vga_puts_xy(4, 0, "ETH STATUS:");
        vga_puts_xy(4, 12, (bmsr2 & 0x0004) ? "LINK UP  " : "LINK DOWN");
        vga_puts_xy(4, 25, (r27 & 0x0008) ? "FIBER" : "COPPER");
        vga_puts_xy(4, 35, (r10 & 0x4000) ? "1000M" : "10/100");

        vga_puts_xy(5, 0, "SR1:"); vga_put_hex16_xy(5, 5, bmsr2);
        vga_puts_xy(5, 12, "R27:"); vga_put_hex16_xy(5, 17, r27);
        vga_puts_xy(5, 24, "R10:"); vga_put_hex16_xy(5, 29, r10);
        vga_puts_xy(5, 36, "INB:"); vga_put_hex16_xy(5, 41, (uint16_t)ethphy_rx_inband_status_read());

        // --- USB timing sweep ---
        uint8_t cycles = sw & 0x3F;
        if (cycles < 6) cycles = 6;
        uint8_t offset = (sw >> 6) & 0x3F;
        
        if (sw & 0x8000) {
            CY_BRIDGE_CFG0 = 0x0001;
            vga_puts_xy(8, 20, "USB RESET ACTIVE  ");
        } else {
            CY_BRIDGE_CFG0 = 0x0002 | (cycles << 2) | (offset << 8) | (8 << 14);
            CY_BRIDGE_CFG0 |= 0x0001;
            vga_puts_xy(8, 20, "USB RUNNING       ");
        }

        vga_puts_xy(8, 0, "USB HPI CFG:");
        vga_puts_xy(9, 0, "CYCLES:"); vga_put_hex16_xy(9, 8, cycles);
        vga_puts_xy(9, 15, "OFFSET:"); vga_put_hex16_xy(9, 23, offset);

        CY_HPI_ADDRESS = 0x01B0;
        uint16_t usb_val = (uint16_t)CY_HPI_DATA;
        vga_puts_xy(11, 0, "HPI READ (01B0):");
        vga_put_hex16_xy(11, 17, usb_val);

        vga_puts_xy(13, 0, "TICKS:"); vga_put_hex16_xy(13, 7, (uint16_t)tick);

        msleep(100);
        tick++;
    }
    return 0;
}
