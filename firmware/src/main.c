#include <stdint.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include "pcd_asm.h"
#include "lcp_blob.h"

#define CY_BASE 0x82000000u
#define CY_HPI_STATUS  (*(volatile uint32_t *)(CY_BASE + 0x000)) // A=0
#define CY_HPI_MAILBOX (*(volatile uint32_t *)(CY_BASE + 0x004)) // A=1
#define CY_HPI_ADDRESS (*(volatile uint32_t *)(CY_BASE + 0x008)) // A=2
#define CY_HPI_DATA    (*(volatile uint32_t *)(CY_BASE + 0x00C)) // A=3
#define CY_BRIDGE_CFG0 (*(volatile uint32_t *)(CY_BASE + 0x100))

#define COMM_ACK               0x0FED
#define COMM_RESET             0xFA50
#define COMM_JUMP2CODE         0xCE00
#define COMM_INT_NUM           0x01C2
#define COMM_R0                0x01C4
#define COMM_CODE_ADDR         0x01BC
#define HUSB_SIE1_INIT_INT     0x0072
#define HUSB_RESET_INT         0x0074
#define HPI_IRQ_ROUTING_REG    0x0142
#define HPI_SIE1_MSG_ADR       0x0144
#define HUSB_SIE1_pCurrentTDPtr 0x01B0
#define HUSB_pEOT              0x01B4
#define HOST1_IRQ_EN_REG       0xC08C
#define HOST1_STAT_REG         0xC090
#define SOFEOP1_TO_CPU_EN      0x0400
#define RESUME1_TO_HPI_EN      0x0040
#define A_CHG_IRQ_EN           0x0010
#define SOF_EOP_IRQ_EN         0x0200
#define HPI_STATUS_SIE1MSG     (1u << 4)

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

void msleep(uint32_t ms) {
    for (volatile int i = 0; i < ms * 10000; i++);
}

void uart_puts(const char *s) {
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

static void usb_write(uint16_t addr, uint16_t data) {
    CY_HPI_ADDRESS = addr;
    CY_HPI_DATA = data;
}

static uint16_t usb_read(uint16_t addr) {
    CY_HPI_ADDRESS = addr;
    return (uint16_t)(CY_HPI_DATA & 0xFFFF);
}

static int wait_ack(void) {
    int timeout = 1000000;
    while (timeout--) {
        if (CY_HPI_STATUS & 1) {
            if ((CY_HPI_MAILBOX & 0xFFFF) == COMM_ACK) return 1;
        }
    }
    return 0;
}

static void usb_write_block(uint16_t addr, const uint8_t *data, uint16_t len) {
    for (uint16_t i=0; i<len; i+=2) {
        uint16_t w = data[i] | (data[i+1] << 8);
        usb_write(addr + i, w);
    }
}

static void write_td(uint16_t td_addr, uint16_t next_td, uint16_t length,
    uint16_t addr_pid_ep, uint16_t toggle, uint16_t buf_addr) {
    CY_HPI_ADDRESS = td_addr;
    CY_HPI_DATA = next_td;
    CY_HPI_DATA = length;
    CY_HPI_DATA = addr_pid_ep;
    CY_HPI_DATA = toggle;
    CY_HPI_DATA = 0x0013; // Enable
    CY_HPI_DATA = buf_addr;
}

static int execute_td_sync(uint16_t td_addr) {
    int timeout = 100000;
    if (CY_HPI_STATUS & HPI_STATUS_SIE1MSG) { usb_read(HPI_SIE1_MSG_ADR); usb_write(HPI_SIE1_MSG_ADR, 0); }
    usb_write(HUSB_pEOT, 600);
    usb_write(HUSB_SIE1_pCurrentTDPtr, td_addr);
    while (!(CY_HPI_STATUS & HPI_STATUS_SIE1MSG) && timeout-- > 0);
    if (timeout <= 0) return 0xFFFF;
    usb_read(HPI_SIE1_MSG_ADR);
    usb_write(HPI_SIE1_MSG_ADR, 0);
    CY_HPI_ADDRESS = td_addr + 8; // Offset to status
    return (int)(CY_HPI_DATA & 0xFFFF);
}

int main(void) {
    char hex[5];
    uart_puts("USB KVM TEST START\n");
    
    // Configure Marvell 88E1111 PHYs (Addresses 16 and 17) for internal RGMII delays
    // Register 20: Extended PHY Specific Control Register
    // Bit 1 (0x0002): RGMII RX Timing Control (add delay)
    // Bit 7 (0x0080): RGMII TX Timing Control (add delay)
    uart_puts("CONFIGURING MDIO DELAYS...\n");
    uint16_t reg20_16 = mdio_read(16, 20);
    mdio_write(16, 20, reg20_16 | 0x0082);
    mdio_write(16, 0, 0x8000); // Soft reset to apply

    uint16_t reg20_17 = mdio_read(17, 20);
    mdio_write(17, 20, reg20_17 | 0x0082);
    mdio_write(17, 0, 0x8000); // Soft reset to apply
    msleep(100);
    uart_puts("MDIO DELAYS CONFIGURED\n");

    // 0. Slow down HPI timing for stability
    // Bits 2-7: access_cycles. Let's use 20 (0x14)
    // Bit 0: force_rst_en = 0
    CY_BRIDGE_CFG0 = (0x14 << 2); 
    uart_puts("HPI TIMING SET\n");

    // 1. HW Reset
    CY_BRIDGE_CFG0 |= 0x0001; msleep(100);
    CY_BRIDGE_CFG0 |= 0x0002; msleep(200); // Release RST
    
    // 2. Memory Test
    usb_write(0x1000, 0x1234);
    uint16_t mcheck = usb_read(0x1000);
    itoa_hex16(mcheck, hex);
    uart_puts("MEM CHECK: "); uart_puts(hex);
    if (mcheck == 0x1234) uart_puts(" OK\n"); else uart_puts(" FAIL\n");

    // 2. Load LCP
    uart_puts("LCP... ");
    uint32_t lcp_pos = 0;
    while (lcp_pos < sizeof(pcd_asm)) {
        uint16_t tag = pcd_asm[lcp_pos] | (pcd_asm[lcp_pos+1] << 8);
        if (tag != 0xc3b6) break;
        uint16_t rlen = pcd_asm[lcp_pos+2] | (pcd_asm[lcp_pos+3] << 8);
        uint8_t op = pcd_asm[lcp_pos+4];
        uint16_t addr = pcd_asm[lcp_pos+5] | (pcd_asm[lcp_pos+6] << 8);
        if (op == 0x00) usb_write_block(addr, &pcd_asm[lcp_pos+7], rlen-2);
        else if (op == 0x04) { usb_write(COMM_CODE_ADDR, addr); CY_HPI_MAILBOX = COMM_JUMP2CODE; msleep(50); }
        lcp_pos += rlen + 5;
    }
    if (wait_ack()) uart_puts("OK\n"); else uart_puts("FAIL\n");

    // 3. Load BIOS
    uint32_t pos = 0;
    while (pos < sizeof(de2_bios)) {
        uint16_t tag = de2_bios[pos] | (de2_bios[pos+1] << 8);
        if (tag != 0xc3b6) break;
        uint16_t rlen = de2_bios[pos+2] | (de2_bios[pos+3] << 8);
        uint8_t op = de2_bios[pos+4];
        uint16_t addr = de2_bios[pos+5] | (de2_bios[pos+6] << 8);
        if (op == 0x00) usb_write_block(addr, &de2_bios[pos+7], rlen-2);
        else if (op == 0x04) { usb_write(COMM_CODE_ADDR, addr); CY_HPI_MAILBOX = COMM_JUMP2CODE; msleep(50); }
        pos += rlen + 5;
    }
    uart_puts("BIOS OK\n");

    // 4. Init Host SIE1
    usb_write(HPI_SIE1_MSG_ADR, 0); usb_write(HOST1_STAT_REG, 0xffff); usb_write(HUSB_pEOT, 600);
    usb_write(HPI_IRQ_ROUTING_REG, SOFEOP1_TO_CPU_EN | RESUME1_TO_HPI_EN);
    usb_write(HOST1_IRQ_EN_REG, A_CHG_IRQ_EN | SOF_EOP_IRQ_EN);
    usb_write(COMM_INT_NUM, HUSB_SIE1_INIT_INT); CY_HPI_MAILBOX = 0xCE01; wait_ack();
    usb_write(COMM_INT_NUM, HUSB_RESET_INT); usb_write(COMM_R0, 0x003c); CY_HPI_MAILBOX = 0xCE01; wait_ack();
    uart_puts("HOST OK\n");

    uart_puts("POLLING...\n");
    uint16_t msg = 0;
    uint32_t conn_tick = 0;
    while (msg != 0x1000) {
        if (CY_HPI_STATUS & HPI_STATUS_SIE1MSG) {
            msg = usb_read(HPI_SIE1_MSG_ADR);
            usb_write(HPI_SIE1_MSG_ADR, 0);
            char mbuf[5]; itoa_hex16(msg, mbuf);
            uart_puts("MSG: "); uart_puts(mbuf); uart_puts("\n");
        }
        if ((conn_tick % 100000) == 0) {
            uint16_t s1 = usb_read(0xC090); // HOST1_STAT
            uint16_t c1 = usb_read(0xC08A); // USB1_CTL
            uint16_t s2 = usb_read(0xC0B0); // HOST2_STAT
            uint16_t c2 = usb_read(0xC0AA); // USB2_CTL
            
            // Heartbeat on LEDs
            leds_g_out_write(1 << ((conn_tick / 100000) % 8));

            // Clear status bits
            usb_write(0xC090, s1);
            usb_write(0xC0B0, s2);
        }
        conn_tick++;
    }
    uart_puts("CONNECTED\n");

    // Address = 1, Config = 1
    usb_write(0x0514, 0x0500); usb_write(0x0516, 0x0001); usb_write(0x0518, 0x0000); usb_write(0x051A, 0x0000);
    write_td(0x0500, 0x0000, 8, 0x00D0, 0x0001, 0x0514); execute_td_sync(0x0500);
    write_td(0x0500, 0x0000, 0, 0x0090, 0x0041, 0x0000); execute_td_sync(0x0500);
    msleep(20);
    usb_write(0x0514, 0x0900); usb_write(0x0516, 0x0001); usb_write(0x0518, 0x0000); usb_write(0x051A, 0x0000);
    write_td(0x0500, 0x0000, 8, 0x01D0, 0x0001, 0x0514); execute_td_sync(0x0500);
    write_td(0x0500, 0x0000, 0, 0x0190, 0x0041, 0x0000); execute_td_sync(0x0500);
    uart_puts("ENUM OK\n");

    uint16_t toggles[6] = {0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001};
    while (1) {
        for (int ep = 1; ep <= 3; ep++) {
            write_td(0x0500, 0x0000, 8, 0x0190 | ep, toggles[ep], 0x0520);
            if (execute_td_sync(0x0500) == 0x0003) {
                toggles[ep] ^= 0x0040;
                CY_HPI_ADDRESS = 0x0520;
                uint16_t d0 = CY_HPI_DATA & 0xFFFF;
                uint16_t d1 = CY_HPI_DATA & 0xFFFF;
                uart_puts("EP"); itoa_hex16(ep, hex); uart_puts(hex); uart_puts(": ");
                itoa_hex16(d0, hex); uart_puts(hex); uart_puts(" ");
                itoa_hex16(d1, hex); uart_puts(hex); uart_puts("\n");
                if (ep == 1 && d1 != 0) { uart_puts("KBD: "); itoa_hex16(d1, hex); uart_puts("\n"); }
            }
        }
        msleep(10);
    }
    return 0;
}
