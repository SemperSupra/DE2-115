#include <stdint.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include "pcd_asm.h"
#include "lcp_blob.h"
#include "cy7c67200_regs.h"
#include "cy7c67200_hpi.h"
#include "cy7c67200_lcp.h"
#include "cy7c67200_scan.h"
#include "cy7c67200_bringup.h"

#define CY_BASE 0x82000000u

#ifndef DE2_ETH_SPEED_MODE
#define DE2_ETH_SPEED_MODE 0
#endif

#define ETH_SPEED_AUTO_10_100 0
#define ETH_SPEED_100_ONLY   100
#define ETH_SPEED_10_ONLY    10

#ifndef DE2_RUN_SDRAM_TEST
#define DE2_RUN_SDRAM_TEST 0
#endif

#define BOARDTEST_SDRAM_WORDS 1024

// --- MDIO ---
#define MDC (1u << CSR_ETHPHY_MDIO_W_MDC_OFFSET)
#define MDO (1u << CSR_ETHPHY_MDIO_W_W_OFFSET)
#define OE  (1u << CSR_ETHPHY_MDIO_W_OE_OFFSET)
#define R   (1u << CSR_ETHPHY_MDIO_R_R_OFFSET)

static void msleep(uint32_t ms);

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

static void eth_configure_low_speed_phy(uint8_t phy_addr) {
    uint16_t reg20 = mdio_read(phy_addr, 20);

    mdio_write(phy_addr, 20, reg20 | 0x0082u);
    mdio_write(phy_addr, 0, 0x8000); // Soft reset to apply RGMII delay config.
    msleep(100);

    mdio_write(phy_addr, 9, 0x0000);
#if DE2_ETH_SPEED_MODE == ETH_SPEED_100_ONLY
    mdio_write(phy_addr, 4, 0x0181); 
#elif DE2_ETH_SPEED_MODE == ETH_SPEED_10_ONLY
    mdio_write(phy_addr, 4, 0x0061); 
#else
    mdio_write(phy_addr, 4, 0x01E1); 
#endif
    mdio_write(phy_addr, 0, 0x1200); 
}

static void msleep(uint32_t ms) {
    for (volatile int i = 0; i < ms * 10000; i++);
}

static void uart_puts(const char *s) {
    while (*s) {
        while (uart_txfull_read());
        uart_rxtx_write(*s++);
    }
}

static void itoa_hex16(uint16_t value, char *buf) {
    const char *hex_chars = "0123456789ABCDEF";
    buf[0] = hex_chars[(value >> 12) & 0xF];
    buf[1] = hex_chars[(value >> 8) & 0xF];
    buf[2] = hex_chars[(value >> 4) & 0xF];
    buf[3] = hex_chars[value & 0xF];
    buf[4] = '\0';
}

static void uart_puthex16(uint16_t value) {
    char hex[5];
    itoa_hex16(value, hex);
    uart_puts(hex);
}

static void uart_puthex8(uint8_t value) {
    const char *hex_chars = "0123456789ABCDEF";
    while (uart_txfull_read());
    uart_rxtx_write(hex_chars[(value >> 4) & 0xF]);
    while (uart_txfull_read());
    uart_rxtx_write(hex_chars[value & 0xF]);
}

static void uart_puthex32(uint32_t value) {
    uart_puthex16((uint16_t)(value >> 16));
    uart_puthex16((uint16_t)value);
}

static void boardtest_set_hex_digit(int index, uint32_t value) {
    switch (index) {
#ifdef CSR_HEX0_OUT_ADDR
    case 0: hex0_out_write(value); break;
#endif
#ifdef CSR_HEX1_OUT_ADDR
    case 1: hex1_out_write(value); break;
#endif
#ifdef CSR_HEX2_OUT_ADDR
    case 2: hex2_out_write(value); break;
#endif
#ifdef CSR_HEX3_OUT_ADDR
    case 3: hex3_out_write(value); break;
#endif
#ifdef CSR_HEX4_OUT_ADDR
    case 4: hex4_out_write(value); break;
#endif
#ifdef CSR_HEX5_OUT_ADDR
    case 5: hex5_out_write(value); break;
#endif
#ifdef CSR_HEX6_OUT_ADDR
    case 6: hex6_out_write(value); break;
#endif
#ifdef CSR_HEX7_OUT_ADDR
    case 7: hex7_out_write(value); break;
#endif
    default: break;
    }
}

static void boardtest_gpio_banner(void) {
    static const uint8_t raw_digit_pattern[8] = { 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07 };
    uart_puts("BOARDTEST START\n");
    for (int i = 0; i < 8; i++) boardtest_set_hex_digit(i, raw_digit_pattern[i]);
    uart_puts("BOARDTEST END\n");
}

static void eth_dump_debug(const char *label) {
    uart_puts(label);
#ifdef CSR_ETHPHY_RX_INBAND_STATUS_ADDR
    uart_puts(" inband=");
    uart_puthex32(ethphy_rx_inband_status_read());
#endif
    uart_puts("\n");
#ifdef CSR_ETHMAC_SRAM_WRITER_EV_PENDING_ADDR
    ethmac_sram_writer_ev_pending_write(1);
#endif
}

int main(void) {
    cy_hpi_ctx_t cy_ctx;
    cy_bringup_blobs_t cy_blobs = {
        .scan_image = pcd_asm,
        .scan_image_len = sizeof(pcd_asm),
        .lcp_probe_call_addr = 0x0000 
    };

    uart_puts("USB KVM MODULAR TEST START\n");
    boardtest_gpio_banner();
    
    eth_configure_low_speed_phy(16);
    eth_configure_low_speed_phy(17);
    msleep(500);
    eth_dump_debug("ETHDBG boot");

    cy_hpi_init(&cy_ctx, CY_BASE, uart_puts, uart_puthex16, uart_puthex32, msleep);
    
    cy_bringup_result_t res = cy_bringup_run(&cy_ctx, &cy_blobs, CY_BRINGUP_STOP_ON_FAILURE);
    if (res != CY_BRINGUP_OK) {
        uart_puts("CY_BRINGUP_FAILURE code=");
        uart_puthex16((uint16_t)res);
        uart_puts("\n");
        uint32_t cfg = *cy_hpi_reg32(&cy_ctx, CY_HPI_CFG0_OFFSET);
        uint32_t ctrl = *cy_hpi_reg32(&cy_ctx, CY_HPI_DBG_CTRL_OFFSET);
        uint32_t smp = *cy_hpi_reg32(&cy_ctx, CY_HPI_DBG_SAMPLE_OFFSET);
        uint32_t cy = *cy_hpi_reg32(&cy_ctx, CY_HPI_DBG_CY_OFFSET);
        uart_puts("DBG: cfg="); uart_puthex32(cfg);
        uart_puts(" ctrl="); uart_puthex32(ctrl);
        uart_puts(" smp="); uart_puthex32(smp);
        uart_puts(" cy="); uart_puthex32(cy);
        uart_puts("\n");
        while(1);
    }

    // Initialize BIOS parts not covered by minimal LCP bring-up
    cy_hpi_write_block(&cy_ctx, 0xE000, de2_bios, sizeof(de2_bios));
    uart_puts("BIOS_FULL_LOAD_OK\n");

    // Host SIE1 Init
    cy_hpi_write16(&cy_ctx, CY_SIE1MSG_REG, 0);
    cy_hpi_write16(&cy_ctx, CY_HOST1_STAT_REG, 0xffff);
    cy_hpi_write16(&cy_ctx, CY_HUSB_EOT, 600);
    cy_hpi_write16(&cy_ctx, CY_HPI_IRQ_ROUTING_REG, 0x0400 | 0x0040); // SOFEOP1_TO_CPU | RESUME1_TO_HPI
    cy_hpi_write16(&cy_ctx, CY_HOST1_IRQ_EN_REG, 0x0010 | 0x0200);   // A_CHG | SOF_EOP

    cy_lcp_exec_int_r0(&cy_ctx, 0x0072, 0, 1000000, "SIE1_INIT");
    cy_lcp_exec_int_r0(&cy_ctx, 0x0074, 0x003c, 1000000, "USB_RESET");
    uart_puts("USB_HOST_READY\n");

    uint16_t msg = 0;
    uint32_t tick = 0;
    while (msg != 0x1000) {
        if (cy_hpi_status_read(&cy_ctx) & CY_HPI_STATUS_SIE1MSG) {
            msg = cy_hpi_read16(&cy_ctx, CY_SIE1MSG_REG);
            cy_hpi_write16(&cy_ctx, CY_SIE1MSG_REG, 0);
            if (msg != 0) {
                uart_puts("MSG: "); uart_puthex16(msg); uart_puts("\n");
            }
        }
        if ((tick % 100000) == 0) {
            leds_g_out_write(1 << ((tick / 100000) % 8));
        }
        tick++;
    }
    uart_puts("CONNECTED\n");

    while (1) {
        msleep(100);
        leds_r_out_write(tick++);
    }

    return 0;
}
