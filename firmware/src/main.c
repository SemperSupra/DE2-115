#include <stdint.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include "pcd_asm.h"
#include "lcp_blob.h"

#define CY_BASE 0x82000000u
#define CY_HPI_DATA    (*(volatile uint32_t *)(CY_BASE + 0x000)) // A=0
#define CY_HPI_MAILBOX (*(volatile uint32_t *)(CY_BASE + 0x004)) // A=1
#define CY_HPI_ADDRESS (*(volatile uint32_t *)(CY_BASE + 0x008)) // A=2
#define CY_HPI_STATUS  (*(volatile uint32_t *)(CY_BASE + 0x00C)) // A=3
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

#define HPI_CFG(force_rst, rst_n, access, sample, turnaround) \
    (((force_rst) ? 1u : 0u) | (((rst_n) ? 1u : 0u) << 1) | \
     (((uint32_t)(access) & 0x3fu) << 2) | \
     (((uint32_t)(sample) & 0x3fu) << 8) | \
     (((uint32_t)(turnaround) & 0x3fu) << 14))
#define HPI_ACCESS_CYCLES      63
#define HPI_SAMPLE_OFFSET      8
#define HPI_TURNAROUND_CYCLES  8

#ifndef DE2_ETH_SPEED_MODE
#define DE2_ETH_SPEED_MODE 0
#endif

#define ETH_SPEED_AUTO_10_100 0
#define ETH_SPEED_100_ONLY   100
#define ETH_SPEED_10_ONLY    10

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

    // Keep the current FPGA RGMII shim in its stable MII-style 10/100 path.
    // Disable 1000BASE-T advertisement and constrain copper autonegotiation
    // to the selected low-speed mode.
    mdio_write(phy_addr, 9, 0x0000);
#if DE2_ETH_SPEED_MODE == ETH_SPEED_100_ONLY
    mdio_write(phy_addr, 4, 0x0181); // 100BASE-TX full/half, selector=IEEE 802.3.
#elif DE2_ETH_SPEED_MODE == ETH_SPEED_10_ONLY
    mdio_write(phy_addr, 4, 0x0061); // 10BASE-T full/half, selector=IEEE 802.3.
#else
    mdio_write(phy_addr, 4, 0x01E1); // 10/100 full/half, selector=IEEE 802.3.
#endif
    mdio_write(phy_addr, 0, 0x1200); // Enable/restart autonegotiation.
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

static void usb_write(uint16_t addr, uint16_t data) {
    CY_HPI_ADDRESS = addr;
    CY_HPI_DATA = data;
}

static uint16_t usb_read(uint16_t addr) {
    CY_HPI_ADDRESS = addr;
    return (uint16_t)(CY_HPI_DATA & 0xFFFF);
}

static void hpi_dump_debug(const char *label) {
    uart_puts(label);
    uart_puts(" cfg=");
    uart_puthex32(CY_BRIDGE_CFG0);
    uart_puts(" ctrl=");
    uart_puthex32(*(volatile uint32_t *)(CY_BASE + 0x104));
    uart_puts(" sample=");
    uart_puthex32(*(volatile uint32_t *)(CY_BASE + 0x108));
    uart_puts(" cy=");
    uart_puthex32(*(volatile uint32_t *)(CY_BASE + 0x10C));
    uart_puts("\n");
}

static void uart_putmac(volatile uint8_t *p) {
    for (int i = 0; i < 6; i++) {
        if (i) uart_puts(":");
        uart_puthex8(p[i]);
    }
}

static void uart_putip(volatile uint8_t *p) {
    for (int i = 0; i < 4; i++) {
        if (i) uart_puts(".");
        uint8_t v = p[i];
        char tmp[4];
        tmp[0] = '0' + (v / 100);
        tmp[1] = '0' + ((v / 10) % 10);
        tmp[2] = '0' + (v % 10);
        tmp[3] = 0;
        if (v >= 100) {
            uart_puts(tmp);
        } else if (v >= 10) {
            uart_puts(&tmp[1]);
        } else {
            uart_puts(&tmp[2]);
        }
    }
}

static void eth_dump_debug(const char *label) {
    uint32_t rx_slot = 0;
    uint32_t rx_len = 0;

    uart_puts(label);
#ifdef CSR_ETHPHY_RX_INBAND_STATUS_ADDR
    uart_puts(" inband=");
    uart_puthex32(ethphy_rx_inband_status_read());
#endif
#ifdef CSR_ETHMAC_SRAM_WRITER_SLOT_ADDR
    rx_slot = ethmac_sram_writer_slot_read();
    rx_len = ethmac_sram_writer_length_read();
    uart_puts(" rx_slot=");
    uart_puthex32(rx_slot);
    uart_puts(" rx_len=");
    uart_puthex32(rx_len);
    uart_puts(" rx_err=");
    uart_puthex32(ethmac_sram_writer_errors_read());
    uart_puts(" rx_ev=");
    uart_puthex32(ethmac_sram_writer_ev_status_read());
    uart_puts("/");
    uart_puthex32(ethmac_sram_writer_ev_pending_read());
#endif
#ifdef CSR_ETHMAC_SRAM_READER_READY_ADDR
    uart_puts(" tx_ready=");
    uart_puthex32(ethmac_sram_reader_ready_read());
    uart_puts(" tx_level=");
    uart_puthex32(ethmac_sram_reader_level_read());
    uart_puts(" tx_ev=");
    uart_puthex32(ethmac_sram_reader_ev_status_read());
    uart_puts("/");
    uart_puthex32(ethmac_sram_reader_ev_pending_read());
#endif
#ifdef CSR_ETHMAC_RX_DATAPATH_PREAMBLE_ERRORS_ADDR
    uart_puts(" pre=");
    uart_puthex32(ethmac_rx_datapath_preamble_errors_read());
    uart_puts(" crc=");
    uart_puthex32(ethmac_rx_datapath_crc_errors_read());
#endif
    uart_puts("\n");
#if defined(CSR_ETHMAC_SRAM_WRITER_SLOT_ADDR) && defined(ETHMAC_RX_BASE) && defined(ETHMAC_SLOT_SIZE)
    if (rx_len != 0) {
        volatile uint8_t *rx = (volatile uint8_t *)(ETHMAC_RX_BASE + ((rx_slot & 1u) * ETHMAC_SLOT_SIZE));
        uart_puts("ETHRX head=");
        for (int i = 0; i < 16; i++) {
            if (i) uart_puts(" ");
            uart_puthex8(rx[i]);
        }
        uart_puts("\n");
        uint16_t ethertype = ((uint16_t)rx[12] << 8) | rx[13];
        if ((ethertype == 0x0806) && (rx_len >= 42)) {
            uint16_t op = ((uint16_t)rx[20] << 8) | rx[21];
            uart_puts("ETHARP op=");
            uart_puthex16(op);
            uart_puts(" sha=");
            uart_putmac(&rx[22]);
            uart_puts(" spa=");
            uart_putip(&rx[28]);
            uart_puts(" tha=");
            uart_putmac(&rx[32]);
            uart_puts(" tpa=");
            uart_putip(&rx[38]);
            uart_puts("\n");
        }
    }
#endif
#ifdef CSR_ETHMAC_SRAM_WRITER_EV_PENDING_ADDR
    ethmac_sram_writer_ev_pending_write(1);
#endif
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

static int cy_command(uint16_t int_num, uint16_t r0, const char *name) {
    usb_write(COMM_INT_NUM, int_num);
    usb_write(COMM_R0, r0);
    CY_HPI_MAILBOX = 0xCE01;
    if (wait_ack()) {
        uart_puts(name);
        uart_puts(" ACK\n");
        return 1;
    }
    uart_puts(name);
    uart_puts(" NOACK mb=");
    uart_puthex16((uint16_t)CY_HPI_MAILBOX);
    uart_puts(" st=");
    uart_puthex16((uint16_t)CY_HPI_STATUS);
    uart_puts("\n");
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
    // Bit 7 (0x0080): RGMII TX Timing Control (add delay). Keep this on
    // because the FPGA forwards the negotiated RX-rate clock without a
    // dedicated 90-degree TX phase shift.
    uart_puts("CONFIGURING MDIO DELAYS...\n");
    uart_puts("ETHMODE=");
#if DE2_ETH_SPEED_MODE == ETH_SPEED_100_ONLY
    uart_puts("100\n");
#elif DE2_ETH_SPEED_MODE == ETH_SPEED_10_ONLY
    uart_puts("10\n");
#else
    uart_puts("AUTO10/100\n");
#endif

    eth_configure_low_speed_phy(16);
    eth_configure_low_speed_phy(17);
    msleep(500);
    uart_puts("PHY16 id=");
    uart_puthex16(mdio_read(16, 2));
    uart_puthex16(mdio_read(16, 3));
    uart_puts(" bm=");
    uart_puthex16(mdio_read(16, 1));
    uart_puts(" ps=");
    uart_puthex16(mdio_read(16, 17));
    uart_puts(" rgmii=");
    uart_puthex16(mdio_read(16, 20));
    uart_puts("\n");
    uart_puts("PHY17 id=");
    uart_puthex16(mdio_read(17, 2));
    uart_puthex16(mdio_read(17, 3));
    uart_puts(" bm=");
    uart_puthex16(mdio_read(17, 1));
    uart_puts(" ps=");
    uart_puthex16(mdio_read(17, 17));
    uart_puts(" rgmii=");
    uart_puthex16(mdio_read(17, 20));
    uart_puts("\n");
#ifdef CSR_ETHPHY_RX_INBAND_STATUS_ADDR
    uart_puts("INBAND=");
    uart_puthex32(ethphy_rx_inband_status_read());
    uart_puts("\n");
#endif
    uart_puts("MDIO DELAYS CONFIGURED\n");
    eth_dump_debug("ETHDBG boot");

    // 0. Slow down HPI timing for stability
    // Preserve sample and turnaround fields; zeroing sample_offset prevents
    // the bridge from capturing read data before the access completes.
    CY_BRIDGE_CFG0 = HPI_CFG(1, 0, HPI_ACCESS_CYCLES, HPI_SAMPLE_OFFSET, HPI_TURNAROUND_CYCLES);
    uart_puts("HPI CFG: ");
    uart_puthex32(CY_BRIDGE_CFG0);
    uart_puts("\n");
    uart_puts("HPI TIMING SET\n");

    // 1. HW Reset
    CY_BRIDGE_CFG0 = HPI_CFG(1, 0, HPI_ACCESS_CYCLES, HPI_SAMPLE_OFFSET, HPI_TURNAROUND_CYCLES); msleep(250);
    CY_BRIDGE_CFG0 = HPI_CFG(1, 1, HPI_ACCESS_CYCLES, HPI_SAMPLE_OFFSET, HPI_TURNAROUND_CYCLES); msleep(500); // Release RST and allow BIOS start
    uart_puts("CY rev=");
    uart_puthex16(usb_read(0xC004));
    uart_puts(" cpu=");
    uart_puthex16(usb_read(0xC008));
    uart_puts(" pwr=");
    uart_puthex16(usb_read(0xC00A));
    uart_puts(" mb=");
    uart_puthex16((uint16_t)CY_HPI_MAILBOX);
    uart_puts(" st=");
    uart_puthex16((uint16_t)CY_HPI_STATUS);
    uart_puts("\n");
    
    // 2. Memory Test
    usb_write(0x1000, 0x1234);
    hpi_dump_debug("HPI DBG WR");
    uint16_t mcheck = usb_read(0x1000);
    hpi_dump_debug("HPI DBG RD");
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
    cy_command(HUSB_SIE1_INIT_INT, 0, "SIE1_INIT");
    cy_command(HUSB_RESET_INT, 0x003c, "USB_RESET");
    uart_puts("HOST1 stat=");
    uart_puthex16(usb_read(HOST1_STAT_REG));
    uart_puts(" irq_en=");
    uart_puthex16(usb_read(HOST1_IRQ_EN_REG));
    uart_puts(" route=");
    uart_puthex16(usb_read(HPI_IRQ_ROUTING_REG));
    uart_puts("\n");
    uart_puts("HOST OK\n");

    uart_puts("POLLING...\n");
    uint16_t msg = 0;
    uint32_t conn_tick = 0;
    uint32_t zero_msg_count = 0;
    while (msg != 0x1000) {
        if (CY_HPI_STATUS & HPI_STATUS_SIE1MSG) {
            uint16_t cur_msg = usb_read(HPI_SIE1_MSG_ADR);
            usb_write(HPI_SIE1_MSG_ADR, 0);
            if (cur_msg != 0) {
                msg = cur_msg;
                char mbuf[5]; itoa_hex16(msg, mbuf);
                uart_puts("MSG: "); uart_puts(mbuf); uart_puts("\n");
            } else {
                zero_msg_count++;
            }
        }
        if ((conn_tick % 100000) == 0) {
            uint16_t s1 = usb_read(0xC090); // HOST1_STAT
            uint16_t c1 = usb_read(0xC08A); // USB1_CTL
            uint16_t s2 = usb_read(0xC0B0); // HOST2_STAT
            uint16_t c2 = usb_read(0xC0AA); // USB2_CTL
            
            // Heartbeat on LEDs
            leds_g_out_write(1 << ((conn_tick / 100000) % 8));
            if ((conn_tick % 1000000) == 0) {
                uart_puts("USBSTAT h1=");
                uart_puthex16(s1);
                uart_puts(" c1=");
                uart_puthex16(c1);
                uart_puts(" h2=");
                uart_puthex16(s2);
                uart_puts(" c2=");
                uart_puthex16(c2);
                uart_puts(" hpi=");
                uart_puthex16((uint16_t)CY_HPI_STATUS);
                uart_puts(" zmsg=");
                uart_puthex32(zero_msg_count);
                uart_puts("\n");
                eth_dump_debug("ETHDBG poll");
            }

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
