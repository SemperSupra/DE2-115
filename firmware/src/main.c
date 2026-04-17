#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>

#include "font.h"
#include "pcd_asm.h"
#include "lcp_blob.h"

extern void uart_init(void);
extern int sdram_init(void);

// 7-segment patterns (active low for common anode)
static const uint8_t hex_digits[] = {
    0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xf8,
    0x80, 0x90, 0x88, 0x83, 0xc6, 0xa1, 0x86, 0x8e
};

static void make_status_line(char *out, const char *prefix, uint16_t a, uint16_t b);
static uint16_t g_lcp_fail_addr;
static uint16_t g_lcp_fail_expected;
static uint16_t g_lcp_fail_actual;
static uint16_t g_probe_chip_id;
static uint16_t g_probe_revision;
static uint16_t g_probe_pin_flags;
static uint16_t g_hpi_ram_expected;
static uint16_t g_hpi_ram_actual;
static uint32_t g_wr_dbg0;
static uint32_t g_wr_dbg2;
static uint32_t g_wr_dbg3;
static uint32_t g_rd_dbg0;
static uint32_t g_rd_dbg2;
static uint32_t g_rd_dbg3;
static uint32_t g_sweep_cfg0;
static uint32_t g_sweep_cfg1;
static uint32_t g_sweep_cfg2;
static uint32_t g_sweep_cfg3;
static uint32_t g_sweep_index;

static uint16_t hpi_read_reg16(volatile uint32_t *reg) {
    return (uint16_t)(*reg & 0xffffu);
}

// LCD Helpers
#define LCD_ON    (1u << 0)
#define LCD_BLON  (1u << 1)
#define LCD_EN    (1u << 2)
#define LCD_RW    (1u << 3)
#define LCD_RS    (1u << 4)

// CY7C67200 HPI registers (Contiguous 32-bit word offsets to match wb_adr[1:0])
#define CY_BASE 0x82000000u
#define CY_HPI_DATA    (*(volatile uint32_t *)(CY_BASE + 0x000))
#define CY_HPI_MAILBOX (*(volatile uint32_t *)(CY_BASE + 0x004))
#define CY_HPI_ADDRESS (*(volatile uint32_t *)(CY_BASE + 0x008))
#define CY_HPI_STATUS  (*(volatile uint32_t *)(CY_BASE + 0x00C))
#define CY_BRIDGE_CFG0 (*(volatile uint32_t *)(CY_BASE + 0x100))
#define CY_BRIDGE_CFG1 (*(volatile uint32_t *)(CY_BASE + 0x104))
#define CY_BRIDGE_CFG2 (*(volatile uint32_t *)(CY_BASE + 0x108))
#define CY_BRIDGE_CFG3 (*(volatile uint32_t *)(CY_BASE + 0x10c))

#define VGA_TEXT_BASE 0x83000000u
#define VGA_COLS 80
#define VGA_ROWS 30
#define VGA_TEXT ((volatile uint32_t *)VGA_TEXT_BASE)

// CY7C67200 LCP / host constants
#define COMM_ACK               0x0FED
#define COMM_RESET             0xFA50
#define COMM_JUMP2CODE         0xCE00
#define COMM_CALL_CODE         0xCE04
#define COMM_INT_NUM           0x01C2
#define COMM_R0                0x01C4
#define COMM_R1                0x01C6
#define COMM_R2                0x01C8
#define COMM_R3                0x01CA
#define COMM_R4                0x01CC
#define COMM_R5                0x01CE
#define COMM_R6                0x01D0
#define COMM_R7                0x01D2
#define COMM_R8                0x01D4
#define COMM_R9                0x01D6
#define COMM_R10               0x01D8
#define COMM_R11               0x01DA
#define COMM_R12               0x01DC
#define COMM_R13               0x01DE
#define COMM_CODE_ADDR         0x01BC
#define HUSB_SIE1_INIT_INT     0x0072
#define HUSB_RESET_INT         0x0074
#define HPI_IRQ_ROUTING_REG    0x0142
#define HPI_SIE1_MSG_ADR       0x0144
#define HPI_SIE2_MSG_ADR       0x0148
#define HUSB_SIE1_pCurrentTDPtr 0x01B0
#define HUSB_pEOT              0x01B4
#define HOST1_IRQ_EN_REG       0xC08C
#define HOST1_STAT_REG         0xC090
#define HOST2_STAT_REG         0xC0B0
#define USB1_CTL_REG           0xC08A
#define HPI_STATUS_MBX_OUT     (1u << 0)
#define SOFEOP1_TO_CPU_EN      0x0400
#define RESUME1_TO_HPI_EN      0x0040
#define A_CHG_IRQ_EN           0x0010
#define SOF_EOP_IRQ_EN         0x0200
#define A_DP_STAT              0x2000
#define A_DM_STAT              0x1000
#define HPI_STATUS_SIE1MSG     (1u << 4)

static void msleep(unsigned int ms) {
    timer0_en_write(0);
    timer0_reload_write(0);
    timer0_load_write(CONFIG_CLOCK_FREQUENCY / 1000 * ms);
    timer0_en_write(1);
    timer0_update_value_write(1);
    while (timer0_value_read()) {
        timer0_update_value_write(1);
    }
}

typedef struct {
    uint8_t rst_hold_ms;
    uint8_t settle_ms;
    uint8_t force_rst_en;
    uint8_t hpi_rst_n;
    uint8_t access_cycles;
    uint8_t sample_offset;
    uint8_t turnaround_cycles;
} hpi_sweep_cfg_t;

static uint32_t bridge_cfg0_pack(uint8_t force_rst_en, uint8_t hpi_rst_n,
    uint8_t access_cycles, uint8_t sample_offset, uint8_t turnaround_cycles) {
    return ((uint32_t)force_rst_en & 0x1u) |
           (((uint32_t)hpi_rst_n & 0x1u) << 1) |
           (((uint32_t)access_cycles & 0x3fu) << 2) |
           (((uint32_t)sample_offset & 0x3fu) << 8) |
           (((uint32_t)turnaround_cycles & 0x3fu) << 14);
}

static void bridge_apply_cfg(uint8_t force_rst_en, uint8_t hpi_rst_n,
    uint8_t access_cycles, uint8_t sample_offset, uint8_t turnaround_cycles) {
    CY_BRIDGE_CFG0 = bridge_cfg0_pack(
        force_rst_en, hpi_rst_n, access_cycles, sample_offset, turnaround_cycles);
}

static void display_hex32(uint32_t val) {
    hex0_out_write(hex_digits[(val >> 28) & 0xf]);
    hex1_out_write(hex_digits[(val >> 24) & 0xf]);
    hex2_out_write(hex_digits[(val >> 20) & 0xf]);
    hex3_out_write(hex_digits[(val >> 16) & 0xf]);
    hex4_out_write(hex_digits[(val >> 12) & 0xf]);
    hex5_out_write(hex_digits[(val >> 8) & 0xf]);
    hex6_out_write(hex_digits[(val >> 4) & 0xf]);
    hex7_out_write(hex_digits[val & 0xf]);
}

static void lcd_write_cmd(uint8_t cmd) {
    uint32_t val = LCD_ON | LCD_BLON | ((uint32_t)cmd << 5);
    lcd_out_write(val);
    lcd_out_write(val | LCD_EN);
    lcd_out_write(val);
    msleep(2);
}

static void lcd_write_data(uint8_t data) {
    uint32_t val = LCD_ON | LCD_BLON | LCD_RS | ((uint32_t)data << 5);
    lcd_out_write(val);
    lcd_out_write(val | LCD_EN);
    lcd_out_write(val);
    msleep(2);
}

static void lcd_init(void) {
    lcd_out_write(LCD_ON | LCD_BLON);
    msleep(100);
    lcd_write_cmd(0x38);
    msleep(10);
    lcd_write_cmd(0x38);
    msleep(2);
    lcd_write_cmd(0x38);
    msleep(2);
    lcd_write_cmd(0x38);
    lcd_write_cmd(0x08);
    lcd_write_cmd(0x01);
    msleep(10);
    lcd_write_cmd(0x06);
    lcd_write_cmd(0x0C);
}

static void lcd_set_cursor(int row, int col) {
    uint8_t addr = (row == 0) ? 0x00 : 0x40;
    lcd_write_cmd(0x80 | (addr + col));
}

static void lcd_print(const char *str) {
    while (*str) {
        lcd_write_data((uint8_t)*str++);
    }
}

static void lcd_print_padded(const char *line0, const char *line1) {
    char buf[17];
    int i = 0;

    lcd_set_cursor(0, 0);
    memset(buf, ' ', 16);
    for (i = 0; i < 16 && line0[i]; ++i) {
        buf[i] = line0[i];
    }
    buf[16] = '\0';
    lcd_print(buf);

    lcd_set_cursor(1, 0);
    memset(buf, ' ', 16);
    for (i = 0; i < 16 && line1[i]; ++i) {
        buf[i] = line1[i];
    }
    buf[16] = '\0';
    lcd_print(buf);
}

static void itoa_hex32(uint32_t n, char *s) {
    static const char hex[] = "0123456789ABCDEF";
    int i;
    for (i = 0; i < 8; ++i) {
        s[7 - i] = hex[(n >> (i * 4)) & 0xf];
    }
    s[8] = '\0';
}

static char vga_sanitize_char(char ch) {
    if (ch >= 'a' && ch <= 'z') {
        return (char)(ch - ('a' - 'A'));
    }
    if ((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') ||
        ch == ' ' || ch == ':' || ch == '-' || ch == '/' ||
        ch == '_' || ch == '|') {
        return ch;
    }
    return ' ';
}

static void vga_putc_xy(unsigned int row, unsigned int col, char ch) {
    if (row < VGA_ROWS && col < VGA_COLS) {
        VGA_TEXT[row * VGA_COLS + col] = (uint32_t)(uint8_t)vga_sanitize_char(ch);
    }
}

static void vga_clear_line(unsigned int row) {
    unsigned int col;
    for (col = 0; col < VGA_COLS; ++col) {
        vga_putc_xy(row, col, ' ');
    }
}

static void vga_clear(void) {
    unsigned int row;
    for (row = 0; row < VGA_ROWS; ++row) {
        vga_clear_line(row);
    }
}

static void vga_puts_xy(unsigned int row, unsigned int col, const char *str) {
    while (*str && row < VGA_ROWS && col < VGA_COLS) {
        vga_putc_xy(row, col++, *str++);
    }
}

static void vga_put_hex32_xy(unsigned int row, unsigned int col, uint32_t value) {
    char hex[9];
    itoa_hex32(value, hex);
    vga_puts_xy(row, col, hex);
}

static void vga_put_hex16_xy(unsigned int row, unsigned int col, uint16_t value) {
    char hex[9];
    itoa_hex32(value, hex);
    vga_puts_xy(row, col, hex + 4);
}

static void vga_status(uint32_t code, const char *line0, const char *line1) {
    static unsigned int log_row = 28;

    vga_clear_line(0);
    vga_clear_line(1);
    vga_clear_line(2);
    vga_clear_line(3);
    vga_puts_xy(0, 0, "DE2-115 VGA USB HPI DEBUG");
    vga_puts_xy(1, 0, "STATUS:");
    vga_put_hex32_xy(1, 8, code);
    vga_puts_xy(2, 0, line0);
    vga_puts_xy(3, 0, line1);

    if (log_row >= 30) {
        log_row = 28;
    }
    vga_clear_line(log_row);
    vga_put_hex32_xy(log_row, 0, code);
    vga_puts_xy(log_row, 10, line0);
    vga_puts_xy(log_row, 38, line1);
    ++log_row;
}

static void mdio_delay(void) {
    for (volatile int i = 0; i < 50; i++);
}

static uint16_t mdio_read(uint8_t phy_addr, uint8_t reg_addr) {
    uint32_t val;
    int i;
    const uint32_t OE = (1u << CSR_ETHPHY_MDIO_W_OE_OFFSET);
    const uint32_t W  = (1u << CSR_ETHPHY_MDIO_W_W_OFFSET);
    const uint32_t MDC = (1u << CSR_ETHPHY_MDIO_W_MDC_OFFSET);
    const uint32_t R   = (1u << CSR_ETHPHY_MDIO_R_R_OFFSET);

    // Send preamble (32 ones)
    for (i = 0; i < 32; i++) {
        ethphy_mdio_w_write(OE | W);
        mdio_delay();
        ethphy_mdio_w_write(OE | W | MDC);
        mdio_delay();
    }

    // Send start (01)
    for (i = 0; i < 2; i++) {
        val = (0x1u >> (1 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send opcode (10 for read)
    for (i = 0; i < 2; i++) {
        val = (0x2u >> (1 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send PHY address (5 bits)
    for (i = 0; i < 5; i++) {
        val = (phy_addr >> (4 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send register address (5 bits)
    for (i = 0; i < 5; i++) {
        val = (reg_addr >> (4 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Turnaround (Z0)
    // Bit 1: Host releases MDIO (High-Z)
    ethphy_mdio_w_write(0);
    mdio_delay();
    ethphy_mdio_w_write(MDC);
    mdio_delay();
    // Bit 2: PHY drives 0.
    ethphy_mdio_w_write(0);
    mdio_delay();
    ethphy_mdio_w_write(MDC);
    mdio_delay();

    // Read data (16 bits)
    val = 0;
    for (i = 0; i < 16; i++) {
        ethphy_mdio_w_write(MDC); // MDC=1
        mdio_delay();
        uint32_t bit = (ethphy_mdio_r_read() & R) ? 1 : 0;
        ethphy_mdio_w_write(0); // MDC=0
        mdio_delay();
        val = (val << 1) | bit;
    }

    return (uint16_t)val;
}

static void mdio_write(uint8_t phy_addr, uint8_t reg_addr, uint16_t data) {
    uint32_t val;
    int i;
    const uint32_t OE = (1u << CSR_ETHPHY_MDIO_W_OE_OFFSET);
    const uint32_t W  = (1u << CSR_ETHPHY_MDIO_W_W_OFFSET);
    const uint32_t MDC = (1u << CSR_ETHPHY_MDIO_W_MDC_OFFSET);

    // Send preamble
    for (i = 0; i < 32; i++) {
        ethphy_mdio_w_write(OE | W);
        mdio_delay();
        ethphy_mdio_w_write(OE | W | MDC);
        mdio_delay();
    }

    // Send start (01)
    for (i = 0; i < 2; i++) {
        val = (0x1u >> (1 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send opcode (01 for write)
    for (i = 0; i < 2; i++) {
        val = (0x1u >> (1 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send PHY address
    for (i = 0; i < 5; i++) {
        val = (phy_addr >> (4 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send register address
    for (i = 0; i < 5; i++) {
        val = (reg_addr >> (4 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Turnaround (10)
    for (i = 0; i < 2; i++) {
        val = (0x2u >> (1 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }

    // Send data
    for (i = 0; i < 16; i++) {
        val = (data >> (15 - i)) & 0x1u;
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET));
        mdio_delay();
        ethphy_mdio_w_write(OE | (val << CSR_ETHPHY_MDIO_W_W_OFFSET) | MDC);
        mdio_delay();
    }
}

static void phy_soft_reset(uint8_t addr) {
    uint16_t bmcr = mdio_read(addr, 0);
    mdio_write(addr, 0, bmcr | 0x8000);
    msleep(100);
}

static void phy_init_rgmii(uint8_t addr) {
    // 1. Configure Mode to RGMII-to-Copper (Reg 27 bits 3:0 = 0b1011)
    uint16_t mscr = mdio_read(addr, 27);
    mscr = (mscr & ~0xf) | 0xb;
    mdio_write(addr, 27, mscr);
    
    // 2. Enable RGMII TX/RX delays and in-band status
    uint16_t ext_ctrl = mdio_read(addr, 20);
    ext_ctrl |= 0x000b; // Bit 3=1 (reserved), Bit 1=1 (RX Delay), Bit 0=1 (TX Delay)
    ext_ctrl |= 0x0004; // Bit 2=1 (In-band status enable)
    mdio_write(addr, 20, ext_ctrl);
    
    // 3. Soft reset to apply changes
    phy_soft_reset(addr);
    msleep(100);
}

static void phy_force_100m(uint8_t addr) {
    // Disable Gigabit Advertisement (Reg 9)
    mdio_write(addr, 9, 0x0000); 
    // 100BT Advertisement (Reg 4): 100FDX only
    mdio_write(addr, 4, 0x0101);
    // Force 100Mbps + Full Duplex + Disable Auto-neg (Reg 0)
    // Bit 13=1 (100M), Bit 12=0 (Auto-neg Disable), Bit 8=1 (Full Duplex)
    mdio_write(addr, 0, 0x2100);
    msleep(100);
}

static void usb_strapping_hpi(void) {
    vga_puts_xy(1, 60, "USB STRAPPING...");
    // 1. Force Reset
    CY_BRIDGE_CFG0 = 0x0001; // RST_N=0, FORCE=1
    msleep(200);
    // 2. Strapping pins should be set by gateware (DREQ=0, DACK#=1)
    // 3. Release Reset
    CY_BRIDGE_CFG0 = 0x0003; // RST_N=1, FORCE=1
    msleep(500);
    vga_puts_xy(1, 60, "USB STRAP DONE ");
}

static void vga_mdio_debug(uint8_t addr, uint8_t reg) {
    uint32_t raw_bits = 0;
    const uint32_t OE = (1u << CSR_ETHPHY_MDIO_W_OE_OFFSET);
    const uint32_t W  = (1u << CSR_ETHPHY_MDIO_W_W_OFFSET);
    const uint32_t MDC = (1u << CSR_ETHPHY_MDIO_W_MDC_OFFSET);
    const uint32_t R   = (1u << CSR_ETHPHY_MDIO_R_R_OFFSET);

    // Send preamble, start, opcode, addr, reg (Standard MDIO frame)
    // ... (omitting full manual frame for brevity, will use existing helper)
    
    vga_puts_xy(24, 0, "MDIO RAW:");
    // Dump raw bits sampled at high frequency or varied offsets
    for (int i = 0; i < 32; i++) {
        ethphy_mdio_w_write(0);
        mdio_delay();
        uint32_t b0 = (ethphy_mdio_r_read() & R) ? 1 : 0;
        ethphy_mdio_w_write(MDC);
        mdio_delay();
        uint32_t b1 = (ethphy_mdio_r_read() & R) ? 1 : 0;
        // Output bits to see where the transition occurs
        vga_putc_xy(24, 10 + i, b0 ? '1' : '0');
        vga_putc_xy(25, 10 + i, b1 ? '1' : '0');
    }
}

static void vga_eth_diag(void) {
    int start_row = 18;
    
    // Scan for PHYs
    uint8_t found_phys[32];
    int num_phys = 0;
    for (int i = 0; i < 32; i++) {
        uint16_t id1 = mdio_read(i, 2);
        if (id1 != 0x0000 && id1 != 0xFFFF) {
            found_phys[num_phys++] = i;
        }
    }

    vga_clear_line(start_row - 1);
    vga_puts_xy(start_row - 1, 0, "PHYS FOUND:");
    for (int i = 0; i < num_phys; i++) {
        vga_put_hex16_xy(start_row - 1, 12 + i*5, found_phys[i]);
    }
    
    // In-band status
    uint32_t inband = ethphy_rx_inband_status_read();
    vga_puts_xy(start_row - 1, 30, "INBAND:");
    vga_put_hex32_xy(start_row - 1, 38, inband);

    uint8_t addr = 16;
    if (num_phys > 0) addr = found_phys[0];
    
    vga_clear_line(start_row);
    vga_puts_xy(start_row, 0, "PHY ");
    vga_put_hex16_xy(start_row, 4, addr);
    vga_puts_xy(start_row, 7, " FULL DUMP:");

    for (int reg = 0; reg < 32; reg++) {
        uint16_t val = mdio_read(addr, reg);
        int col = (reg % 4) * 20;
        int row = start_row + 1 + (reg / 4);
        if (reg % 4 == 0) vga_clear_line(row);
        
        vga_put_hex16_xy(row, col, (uint16_t)reg);
        vga_puts_xy(row, col + 2, ":");
        vga_put_hex16_xy(row, col + 3, val);
    }
}

static void vga_hpi_diag_table(uint32_t page,
    uint16_t direct_data, uint16_t direct_mailbox,
    uint16_t direct_address, uint16_t direct_status,
    uint16_t ram0, uint16_t ram1,
    uint16_t rev, uint16_t pin,
    uint32_t dbg0, uint32_t dbg1, uint32_t dbg2, uint32_t dbg3,
    uint32_t cfg0, uint32_t cfg1, uint32_t cfg2, uint32_t cfg3,
    uint32_t sweep_index) {
    unsigned int row;

    for (row = 5; row < 18; ++row) {
        vga_clear_line(row);
    }

    vga_puts_xy(5, 0, "HPI FAIL DIAG PAGE");
    vga_put_hex32_xy(5, 20, page);
    vga_puts_xy(5, 32, "SWEEP:");
    vga_put_hex32_xy(5, 39, sweep_index);

    vga_puts_xy(6, 0, "CFG0:");
    vga_put_hex32_xy(6, 6, cfg0);
    vga_puts_xy(6, 20, "CFG1:");
    vga_put_hex32_xy(6, 26, cfg1);
    vga_puts_xy(6, 40, "CFG2:");
    vga_put_hex32_xy(6, 46, cfg2);
    vga_puts_xy(6, 60, "CFG3:");
    vga_put_hex32_xy(6, 66, cfg3);

    vga_puts_xy(7, 0, "DIRECT DATA:");
    vga_put_hex16_xy(7, 14, direct_data);
    vga_puts_xy(7, 24, "MAILBOX:");
    vga_put_hex16_xy(7, 33, direct_mailbox);
    vga_puts_xy(7, 44, "ADDRESS:");
    vga_put_hex16_xy(7, 53, direct_address);
    vga_puts_xy(7, 64, "STATUS:");
    vga_put_hex16_xy(7, 72, direct_status);

    vga_puts_xy(9, 0, "RAM 2100 EXP 55AA ACT");
    vga_put_hex16_xy(9, 24, ram0);
    vga_puts_xy(10, 0, "RAM 2100 EXP AA55 ACT");
    vga_put_hex16_xy(10, 24, ram1);

    vga_puts_xy(12, 0, "REV C004:");
    vga_put_hex16_xy(12, 10, rev);
    vga_puts_xy(12, 24, "PIN C008:");
    vga_put_hex16_xy(12, 34, pin);

    vga_puts_xy(14, 0, "FAIL EXP:");
    vga_put_hex16_xy(14, 10, g_hpi_ram_expected);
    vga_puts_xy(14, 20, "ACT:");
    vga_put_hex16_xy(14, 25, g_hpi_ram_actual);
    vga_puts_xy(14, 36, "CHIP:");
    vga_put_hex16_xy(14, 42, g_probe_chip_id);
    vga_puts_xy(14, 52, "REV:");
    vga_put_hex16_xy(14, 57, g_probe_revision);

    vga_puts_xy(15, 0, "DBG0:");
    vga_put_hex32_xy(15, 6, dbg0);
    vga_puts_xy(15, 20, "DBG1:");
    vga_put_hex32_xy(15, 26, dbg1);
    vga_puts_xy(15, 40, "DBG2:");
    vga_put_hex32_xy(15, 46, dbg2);
    vga_puts_xy(15, 60, "DBG3:");
    vga_put_hex32_xy(15, 66, dbg3);

    vga_puts_xy(16, 0, "WR0:");
    vga_put_hex32_xy(16, 4, g_wr_dbg0);
    vga_puts_xy(16, 16, "WR2:");
    vga_put_hex32_xy(16, 20, g_wr_dbg2);
    vga_puts_xy(16, 32, "WR3:");
    vga_put_hex32_xy(16, 36, g_wr_dbg3);

    vga_puts_xy(17, 0, "RD0:");
    vga_put_hex32_xy(17, 4, g_rd_dbg0);
    vga_puts_xy(17, 16, "RD2:");
    vga_put_hex32_xy(17, 20, g_rd_dbg2);
    vga_puts_xy(17, 32, "RD3:");
    vga_put_hex32_xy(17, 36, g_rd_dbg3);
}

static void show_status(uint32_t code, const char *line0, const char *line1) {
    display_hex32(code);
    lcd_print_padded(line0, line1);
    vga_status(code, line0, line1);
    printf("[STATUS] %08lx %s | %s\n",
        (unsigned long)code,
        line0,
        line1);
}

static void show_runtime_status(uint32_t ticks, uint32_t switches, uint32_t ep_seen_mask) {
    uint32_t code = 0xC0DE0000u;

    code |= (switches & 0xffu) << 8;
    code |= ep_seen_mask & 0xffu;
    if (ticks & 0x20u) {
        code ^= 0x0000F000u;
    }
    display_hex32(code);
    vga_clear_line(4);
    vga_puts_xy(4, 0, "RUN TICKS:");
    vga_put_hex32_xy(4, 11, ticks);
    vga_puts_xy(4, 24, "SW:");
    vga_put_hex32_xy(4, 28, switches);
    vga_puts_xy(4, 42, "EP:");
    vga_put_hex32_xy(4, 46, ep_seen_mask);
}

static void show_mismatch_status(uint16_t address, uint16_t expected, uint16_t actual) {
    char line0[17];
    char line1[17];

    make_status_line(line0, "ADDR ", address, expected);
    make_status_line(line1, "ACT  ", actual, 0);
    show_status(((uint32_t)address << 16) | actual, line0, line1);
}

static void make_status_line(char *out, const char *prefix, uint16_t a, uint16_t b) {
    char a_hex[9];
    char b_hex[9];
    int i;

    itoa_hex32(a, a_hex);
    itoa_hex32(b, b_hex);
    memset(out, ' ', 16);
    for (i = 0; i < 16 && prefix[i]; ++i) {
        out[i] = prefix[i];
    }
    out[5] = a_hex[4];
    out[6] = a_hex[5];
    out[7] = a_hex[6];
    out[8] = a_hex[7];
    out[10] = b_hex[4];
    out[11] = b_hex[5];
    out[12] = b_hex[6];
    out[13] = b_hex[7];
    out[16] = '\0';
}

static void UsbWrite(uint16_t address, uint16_t data) {
    CY_HPI_ADDRESS = address;
    CY_HPI_DATA = data;
}

static uint16_t UsbRead(uint16_t address) {
    CY_HPI_ADDRESS = address;
    return (uint16_t)(CY_HPI_DATA & 0xffffu);
}

static void usb_write_words(uint16_t address, const uint8_t *data, unsigned int byte_length) {
    unsigned int i;

    for (i = 0; i < byte_length; i += 2) {
        uint16_t word = data[i];
        if (i + 1 < byte_length) {
            word |= (uint16_t)data[i + 1] << 8;
        }
        UsbWrite((uint16_t)(address + i), word);
    }
}

static int usb_verify_words(uint16_t address, const uint8_t *data, unsigned int byte_length,
    uint16_t *fail_addr, uint16_t *expected_out, uint16_t *actual_out) {
    unsigned int i;

    for (i = 0; i < byte_length; i += 2) {
        uint16_t expected = data[i];
        uint16_t actual;

        if (i + 1 < byte_length) {
            expected |= (uint16_t)data[i + 1] << 8;
        }
        actual = UsbRead((uint16_t)(address + i));
        if (actual != expected) {
            *fail_addr = (uint16_t)(address + i);
            *expected_out = expected;
            *actual_out = actual;
            return 0;
        }
    }
    return 1;
}

static uint16_t image_u16(const uint8_t *data, unsigned int offset) {
    return (uint16_t)(data[offset] | ((uint16_t)data[offset + 1] << 8));
}

static void usb_soft_reset(void) {
    CY_HPI_MAILBOX = COMM_RESET;
    msleep(100);
    msleep(500);

    (void)CY_HPI_MAILBOX;
    (void)CY_HPI_STATUS;

    (void)UsbRead(HPI_SIE1_MSG_ADR);
    UsbWrite(HPI_SIE1_MSG_ADR, 0);
    (void)UsbRead(HPI_SIE2_MSG_ADR);
    UsbWrite(HPI_SIE2_MSG_ADR, 0);
    UsbWrite(HOST1_STAT_REG, 0xffff);
    UsbWrite(HOST2_STAT_REG, 0xffff);
}

static void usb_clear_bug(void) {
    uint16_t tmp;

    (void)CY_HPI_MAILBOX;
    (void)CY_HPI_STATUS;

    tmp = UsbRead(HPI_SIE1_MSG_ADR);
    (void)tmp;
    UsbWrite(HPI_SIE1_MSG_ADR, 0);
    tmp = UsbRead(HPI_SIE2_MSG_ADR);
    (void)tmp;
    UsbWrite(HPI_SIE2_MSG_ADR, 0);

    UsbWrite(HOST1_STAT_REG, 0xffff);
    UsbWrite(HOST2_STAT_REG, 0xffff);
}

static int usb_probe_chip(void) {
    g_probe_chip_id = UsbRead(0xC004);
    g_probe_revision = UsbRead(0xC002);
    g_probe_pin_flags = UsbRead(0xC008);

    /* 0xC004 is HW_REV_REG, not a part ID. Terasic's CY7C67200 header
     * documents first silicon as 0x0101; later revisions increment.
     */
    return g_probe_chip_id >= 0x0101 && g_probe_chip_id < 0x0200;
}

static int usb_probe_ram(void) {
    const uint16_t test_addr = 0x2100;
    const uint16_t pattern0 = 0x55aa;
    const uint16_t pattern1 = 0xaa55;

    UsbWrite(test_addr, pattern0);
    g_hpi_ram_expected = pattern0;
    g_hpi_ram_actual = UsbRead(test_addr);
    if (g_hpi_ram_actual != pattern0) {
        return 0;
    }

    UsbWrite(test_addr, pattern1);
    g_hpi_ram_expected = pattern1;
    g_hpi_ram_actual = UsbRead(test_addr);
    return g_hpi_ram_actual == pattern1;
}

static const hpi_sweep_cfg_t g_hpi_sweep_cfgs[] = {
    {  2,   5, 1, 1, 32, 2,  4},
    {  2,  20, 1, 1, 32, 4,  8},
    {  5,  20, 1, 1, 48, 4,  8},
    {  5,  50, 1, 1, 63, 4,  8},
    { 10,  20, 1, 1, 63, 8,  8},
    { 20,  50, 1, 1, 63, 8, 16},
    { 20, 100, 1, 1, 48, 8, 16},
    { 50, 100, 1, 1, 32, 8, 16},
    {100, 100, 1, 1, 63, 2, 16},
    { 20, 150, 0, 1, 63, 4,  8},
    { 20, 150, 0, 1, 48, 8, 16},
    { 50, 200, 0, 1, 32, 4, 16}
};

static void hpi_diag_fail_loop(void) {
    uint32_t page = 0;

    while (1) {
        char line0[17];
        char line1[17];
        uint16_t direct_data;
        uint16_t direct_mailbox;
        uint16_t direct_address;
        uint16_t direct_status;
        uint16_t ram0;
        uint16_t ram1;
        uint16_t rev;
        uint16_t pin;
        uint32_t dbg0;
        uint32_t dbg1;
        uint32_t dbg2;
        uint32_t dbg3;
        const hpi_sweep_cfg_t *cfg =
            &g_hpi_sweep_cfgs[page % (sizeof(g_hpi_sweep_cfgs) / sizeof(g_hpi_sweep_cfgs[0]))];

        bridge_apply_cfg(1, 0, cfg->access_cycles, cfg->sample_offset, cfg->turnaround_cycles);
        vga_puts_xy(1, 60, "RST ON ");
        msleep(cfg->rst_hold_ms);
        bridge_apply_cfg(cfg->force_rst_en, cfg->hpi_rst_n,
            cfg->access_cycles, cfg->sample_offset, cfg->turnaround_cycles);
        vga_puts_xy(1, 60, "RST OFF");
        msleep(cfg->settle_ms);

        g_sweep_cfg0 = CY_BRIDGE_CFG0;
        g_sweep_cfg1 = CY_BRIDGE_CFG1;
        g_sweep_cfg2 = CY_BRIDGE_CFG2;
        g_sweep_cfg3 = CY_BRIDGE_CFG3;
        g_sweep_index = page % (sizeof(g_hpi_sweep_cfgs) / sizeof(g_hpi_sweep_cfgs[0]));

        CY_HPI_ADDRESS = 0x2100;
        CY_HPI_DATA = 0x55aa;
        g_wr_dbg0 = CY_BRIDGE_CFG0;
        g_wr_dbg2 = CY_BRIDGE_CFG2;
        g_wr_dbg3 = CY_BRIDGE_CFG3;
        CY_HPI_ADDRESS = 0x2100;
        ram0 = hpi_read_reg16(&CY_HPI_DATA);
        g_rd_dbg0 = CY_BRIDGE_CFG0;
        g_rd_dbg2 = CY_BRIDGE_CFG2;
        g_rd_dbg3 = CY_BRIDGE_CFG3;

        CY_HPI_ADDRESS = 0x2100;
        CY_HPI_DATA = 0xaa55;
        CY_HPI_ADDRESS = 0x2100;
        ram1 = hpi_read_reg16(&CY_HPI_DATA);

        CY_HPI_ADDRESS = 0xC004;
        rev = hpi_read_reg16(&CY_HPI_DATA);
        CY_HPI_ADDRESS = 0xC008;
        pin = hpi_read_reg16(&CY_HPI_DATA);

        direct_data = hpi_read_reg16(&CY_HPI_DATA);
        direct_mailbox = hpi_read_reg16(&CY_HPI_MAILBOX);
        direct_address = hpi_read_reg16(&CY_HPI_ADDRESS);
        direct_status = hpi_read_reg16(&CY_HPI_STATUS);
        dbg0 = CY_BRIDGE_CFG0;
        dbg1 = CY_BRIDGE_CFG1;
        dbg2 = CY_BRIDGE_CFG2;
        dbg3 = CY_BRIDGE_CFG3;

        vga_hpi_diag_table(page, direct_data, direct_mailbox,
            direct_address, direct_status, ram0, ram1, rev, pin,
            dbg0, dbg1, dbg2, dbg3,
            g_sweep_cfg0, g_sweep_cfg1, g_sweep_cfg2, g_sweep_cfg3, g_sweep_index);

        vga_eth_diag();

        switch (page & 7u) {
        case 0:
            make_status_line(line0, "DATA ", direct_data, direct_mailbox);
            make_status_line(line1, "ADDR ", direct_address, direct_status);
            show_status(0xD0000000u | direct_data, line0, line1);
            break;
        case 1:
            make_status_line(line0, "RAM0 ", 0x55aa, ram0);
            make_status_line(line1, "RAM1 ", 0xaa55, ram1);
            show_status(0xD0010000u | ram0, line0, line1);
            break;
        case 2:
            make_status_line(line0, "REV  ", 0xC004, rev);
            make_status_line(line1, "PIN  ", 0xC008, pin);
            show_status(0xD0020000u | rev, line0, line1);
            break;
        case 3:
            CY_HPI_MAILBOX = COMM_RESET;
            msleep(100);
            make_status_line(line0, "MBXR ", COMM_RESET, hpi_read_reg16(&CY_HPI_MAILBOX));
            make_status_line(line1, "STAT ", hpi_read_reg16(&CY_HPI_STATUS), 0);
            show_status(0xD0030000u | hpi_read_reg16(&CY_HPI_STATUS), line0, line1);
            break;
        case 4:
            CY_HPI_ADDRESS = 0x0000;
            make_status_line(line0, "A000 ", 0x0000, hpi_read_reg16(&CY_HPI_DATA));
            CY_HPI_ADDRESS = 0x0002;
            make_status_line(line1, "A002 ", 0x0002, hpi_read_reg16(&CY_HPI_DATA));
            show_status(0xD0040000u | hpi_read_reg16(&CY_HPI_DATA), line0, line1);
            break;
        case 5:
            CY_HPI_ADDRESS = 0xC090;
            make_status_line(line0, "H1ST ", 0xC090, hpi_read_reg16(&CY_HPI_DATA));
            CY_HPI_ADDRESS = 0xC0B0;
            make_status_line(line1, "H2ST ", 0xC0B0, hpi_read_reg16(&CY_HPI_DATA));
            show_status(0xD0050000u | hpi_read_reg16(&CY_HPI_DATA), line0, line1);
            break;
        case 6:
            make_status_line(line0, "FAIL ", g_hpi_ram_expected, g_hpi_ram_actual);
            make_status_line(line1, "CHIP ", g_probe_chip_id, g_probe_revision);
            show_status(0xD0060000u | g_hpi_ram_actual, line0, line1);
            break;
        default:
            make_status_line(line0, "PIN  ", g_probe_pin_flags, direct_status);
            make_status_line(line1, "PAGE ", (uint16_t)page, 0);
            show_status(0xD0070000u | (page & 0xffffu), line0, line1);
            break;
        }

        leds_g_out_write(1u << (page % 9u));
        leds_r_out_write(1u << (page % 18u));
        ++page;
        msleep(1000);
    }
}

static int wait_for_mailbox_ack(unsigned int timeout) {
    while (timeout-- > 0) {
        uint16_t status = (uint16_t)(CY_HPI_STATUS & 0xffffu);
        if (status & HPI_STATUS_MBX_OUT) {
            if ((CY_HPI_MAILBOX & 0xffffu) == COMM_ACK) {
                return 1;
            }
        }
    }
    return 0;
}

static int wait_for_mailbox_ack_value(unsigned int timeout, uint16_t *mailbox_value) {
    while (timeout-- > 0) {
        uint16_t status = (uint16_t)(CY_HPI_STATUS & 0xffffu);
        if (status & HPI_STATUS_MBX_OUT) {
            *mailbox_value = (uint16_t)(CY_HPI_MAILBOX & 0xffffu);
            if (*mailbox_value == COMM_ACK) {
                return 1;
            }
            return 1;
        }
    }
    return 0;
}

static int execute_td_sync(uint16_t td_addr) {
    unsigned int timeout = 500000;

    if (CY_HPI_STATUS & HPI_STATUS_SIE1MSG) {
        (void)UsbRead(HPI_SIE1_MSG_ADR);
        UsbWrite(HPI_SIE1_MSG_ADR, 0);
    }

    UsbWrite(HUSB_pEOT, 600);
    UsbWrite(HUSB_SIE1_pCurrentTDPtr, td_addr);

    while (!(CY_HPI_STATUS & HPI_STATUS_SIE1MSG) && timeout-- > 0) {
    }
    if ((CY_HPI_STATUS & HPI_STATUS_SIE1MSG) == 0) {
        return 0xffff;
    }

    (void)UsbRead(HPI_SIE1_MSG_ADR);
    UsbWrite(HPI_SIE1_MSG_ADR, 0);

    CY_HPI_ADDRESS = td_addr + 8;
    return (int)(CY_HPI_DATA & 0xffffu);
}

static void write_td(uint16_t td_addr, uint16_t next_td, uint16_t length,
    uint16_t addr_pid_ep, uint16_t toggle, uint16_t buf_addr) {
    CY_HPI_ADDRESS = td_addr;
    CY_HPI_DATA = next_td;
    CY_HPI_DATA = length;
    CY_HPI_DATA = addr_pid_ep;
    CY_HPI_DATA = toggle;
    CY_HPI_DATA = 0x0013;
    CY_HPI_DATA = buf_addr;
}

static int load_lcp_firmware(void) {
    const uint16_t load_addr = image_u16(pcd_asm, 0x0e);
    const uint16_t total_length = image_u16(pcd_asm, 0x0b);
    const unsigned int payload_length = (unsigned int)(total_length - 2u);
    const uint8_t *payload = &pcd_asm[16];
    uint16_t mailbox_value = 0;
    unsigned int attempt;

    if (PCD_ASM_SIZE < 16 || total_length < 2 || 16u + payload_length > PCD_ASM_SIZE) {
        return 1;
    }

    usb_soft_reset();
    for (attempt = 0; attempt < 10; ++attempt) {
        usb_clear_bug();
        usb_write_words(load_addr, payload, payload_length);
        if (!usb_verify_words(load_addr, payload, payload_length,
            &g_lcp_fail_addr, &g_lcp_fail_expected, &g_lcp_fail_actual)) {
            continue;
        }

        UsbWrite(COMM_CODE_ADDR, load_addr);
        CY_HPI_MAILBOX = COMM_JUMP2CODE;
        if (wait_for_mailbox_ack_value(500000, &mailbox_value) && mailbox_value == COMM_ACK) {
            msleep(100);
            return 0;
        }

        msleep(10);
    }

    if (mailbox_value != 0 && mailbox_value != COMM_ACK) {
        return 4;
    }
    if (!usb_verify_words(load_addr, payload, payload_length,
        &g_lcp_fail_addr, &g_lcp_fail_expected, &g_lcp_fail_actual)) {
        return 3;
    }
    return 2;
}

static int load_de2_bios_image(void) {
    unsigned int pos = 0;
    uint16_t mailbox_value = 0;

    usb_clear_bug();

    while (pos + 2u <= sizeof(de2_bios)) {
        uint16_t tag = image_u16(de2_bios, pos);
        uint16_t record_len;
        uint8_t opcode;
        uint16_t address = 0;
        unsigned int payload_pos;
        unsigned int payload_len;

        if (tag != 0xc3b6) {
            msleep(1000);
            return 0;
        }
        if (pos + 5u > sizeof(de2_bios)) {
            return 1;
        }

        record_len = image_u16(de2_bios, pos + 2u);
        opcode = de2_bios[pos + 4u];
        payload_pos = pos + 5u;
        payload_len = record_len;

        if (opcode == 0x00 || opcode == 0x04 || opcode == 0x05) {
            if (pos + 7u > sizeof(de2_bios) || record_len < 2u) {
                return 1;
            }
            address = image_u16(de2_bios, pos + 5u);
            payload_pos = pos + 7u;
            payload_len = record_len - 2u;
        }

        if (payload_pos + payload_len > sizeof(de2_bios)) {
            return 1;
        }

        switch (opcode) {
        case 0x00:
            usb_write_words(address, &de2_bios[payload_pos], payload_len);
            if (!usb_verify_words(address, &de2_bios[payload_pos], payload_len,
                &g_lcp_fail_addr, &g_lcp_fail_expected, &g_lcp_fail_actual)) {
                return 3;
            }
            break;
        case 0x04:
            UsbWrite(COMM_CODE_ADDR, address);
            CY_HPI_MAILBOX = COMM_JUMP2CODE;
            msleep(1000);
            break;
        case 0x05:
            UsbWrite(COMM_CODE_ADDR, address);
            CY_HPI_MAILBOX = COMM_CALL_CODE;
            if (!wait_for_mailbox_ack_value(500000, &mailbox_value) ||
                mailbox_value != COMM_ACK) {
                return 2;
            }
            break;
        default:
            break;
        }

        pos = payload_pos + payload_len;
    }

    return 1;
}

static int host_init(void) {
    uint16_t msg = 0;
    unsigned int timeout = 5000000;

    UsbWrite(HPI_SIE1_MSG_ADR, 0);
    UsbWrite(HOST1_STAT_REG, 0xffff);
    UsbWrite(HUSB_pEOT, 600);
    UsbWrite(HPI_IRQ_ROUTING_REG, SOFEOP1_TO_CPU_EN | RESUME1_TO_HPI_EN);
    UsbWrite(HOST1_IRQ_EN_REG, A_CHG_IRQ_EN | SOF_EOP_IRQ_EN);

    UsbWrite(COMM_R0, 0x0000);
    UsbWrite(COMM_R1, 0x0000);
    UsbWrite(COMM_R2, 0x0000);
    UsbWrite(COMM_R3, 0x0000);
    UsbWrite(COMM_R4, 0x0000);
    UsbWrite(COMM_R5, 0x0000);
    UsbWrite(COMM_R6, 0x0000);
    UsbWrite(COMM_R7, 0x0000);
    UsbWrite(COMM_R8, 0x0000);
    UsbWrite(COMM_R9, 0x0000);
    UsbWrite(COMM_R10, 0x0000);
    UsbWrite(COMM_R11, 0x0000);
    UsbWrite(COMM_R12, 0x0000);
    UsbWrite(COMM_R13, 0x0000);
    UsbWrite(COMM_INT_NUM, HUSB_SIE1_INIT_INT);
    CY_HPI_MAILBOX = 0xCE01;
    if (!wait_for_mailbox_ack(500000)) {
        return 0;
    }

    UsbWrite(COMM_INT_NUM, HUSB_RESET_INT);
    UsbWrite(COMM_R0, 0x003c);
    CY_HPI_MAILBOX = 0xCE01;
    if (!wait_for_mailbox_ack(500000)) {
        return 0;
    }

    while (timeout-- > 0) {
        if (CY_HPI_STATUS & HPI_STATUS_SIE1MSG) {
            msg = UsbRead(HPI_SIE1_MSG_ADR);
            UsbWrite(HPI_SIE1_MSG_ADR, 0);
            if (msg == 0x1000) {
                break;
            }
        }
    }
    if (msg != 0x1000) {
        return 0;
    }

    msleep(100);
    return 1;
}

static int configure_device(void) {
    int st_addr_setup;
    int st_addr_in;
    int st_cfg_setup;
    int st_cfg_in;
    char line0[17];
    char line1[17];

    CY_HPI_ADDRESS = 0x0514;
    CY_HPI_DATA = 0x0500;
    CY_HPI_DATA = 0x0001;
    CY_HPI_DATA = 0x0000;
    CY_HPI_DATA = 0x0000;
    write_td(0x0500, 0x0000, 8, 0x00D0, 0x0001, 0x0514);
    st_addr_setup = execute_td_sync(0x0500);

    write_td(0x0500, 0x0000, 0, 0x0090, 0x0041, 0x0000);
    st_addr_in = execute_td_sync(0x0500);
    if (st_addr_setup != 0x0003 || st_addr_in != 0x0003) {
        return 0;
    }

    msleep(20);

    CY_HPI_ADDRESS = 0x0514;
    CY_HPI_DATA = 0x0900;
    CY_HPI_DATA = 0x0001;
    CY_HPI_DATA = 0x0000;
    CY_HPI_DATA = 0x0000;
    write_td(0x0500, 0x0000, 8, 0x01D0, 0x0001, 0x0514);
    st_cfg_setup = execute_td_sync(0x0500);

    write_td(0x0500, 0x0000, 0, 0x0190, 0x0041, 0x0000);
    st_cfg_in = execute_td_sync(0x0500);
    if (st_cfg_setup != 0x0003 || st_cfg_in != 0x0003) {
        return 0;
    }

    make_status_line(line0, "ADDR ", (uint16_t)st_addr_setup, (uint16_t)st_addr_in);
    make_status_line(line1, "CFG  ", (uint16_t)st_cfg_setup, (uint16_t)st_cfg_in);
    show_status(0xA0030003, line0, line1);
    return 1;
}

int main(void) {
    uint32_t i = 0;
    int knight_pos = 0;
    int knight_dir = 1;
    uint16_t toggles[6] = {0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001};
    uint16_t last_data[6] = {0, 0, 0, 0, 0, 0};
    uint32_t ep_seen_mask = 0;
    char buf[9];

    uart_init();
    sdram_init();
    vga_clear();
    vga_puts_xy(0, 0, "DE2-115 VGA USB HPI DEBUG");
    vga_puts_xy(1, 0, "BOOTING FIRMWARE");
    lcd_init();

    show_status(0xB0070000, "Booting board", "VGA+USB bringup");
    leds_g_out_write(0x1ff);
    leds_r_out_write(0x3ffff);
    msleep(500);

    vga_puts_xy(1, 40, "ETH INIT...");
    phy_init_rgmii(16);
    phy_init_rgmii(17);
    vga_puts_xy(1, 40, "ETH DONE    ");

    /*
     * Match Terasic's working sequence: command the Cypress boot ROM to reset
     * before treating register reads as meaningful. Some registers can read as
     * erased/floating values before this point, so RAM/BIOS verification is the
     * real HPI health check.
     */
    usb_soft_reset();
    (void)usb_probe_chip();

    usb_strapping_hpi();

    if (!usb_probe_ram()) {
        char line0[17];
        char line1[17];

        vga_puts_xy(1, 60, "BOOT RESETTING...");
        // Force HPI Reset via config register
        CY_BRIDGE_CFG0 = 0x0001; // Force RST_N low
        msleep(100);
        CY_BRIDGE_CFG0 = 0x0003; // Force RST_N high
        msleep(500);

        if (usb_probe_ram()) {
            vga_puts_xy(1, 60, "BOOT RECOVERED ");
        } else {
            make_status_line(line0, "RAM  ", 0x2100, g_hpi_ram_expected);
            make_status_line(line1, "ACT  ", g_hpi_ram_actual, 0);
            show_status(0xE0070000 | (g_probe_chip_id & 0xffffu), line0, line1);
            vga_eth_diag();
            msleep(2000);
            hpi_diag_fail_loop();
        }
    }

    {
        int lcp_status = load_de2_bios_image();
        if (lcp_status != 0) {
            switch (lcp_status) {
            case 1:
                show_status(0xE1010000, "BIOS hdr fail", "image header");
                break;
            case 2:
                show_status(0xE1020000, "BIOS call fail", "mailbox no ack");
                break;
            case 3:
                show_mismatch_status(g_lcp_fail_addr, g_lcp_fail_expected, g_lcp_fail_actual);
                break;
            case 4:
                show_status(0xE1040000, "BIOS bad mbx", "unexpected rsp");
                break;
            default:
                show_status(0xE1FF0000, "BIOS unknown", "check image/HPI");
                break;
            }
            while (1) {
                msleep(250);
                leds_g_out_write(0x155);
                leds_r_out_write(0x15555);
                msleep(250);
                leds_g_out_write(0x0aa);
                leds_r_out_write(0x2aaaa);
            }
        }
    }

    show_status(0xC0010000, "BIOS running", "init host");
    if (!host_init()) {
        show_status(0xE0020000, "Host init fail", "SIE1 no ack");
        while (1) {
            msleep(500);
            leds_g_out_write(0x001);
            leds_r_out_write(0x00001);
            msleep(500);
            leds_g_out_write(0x100);
            leds_r_out_write(0x20000);
        }
    }

    show_status(0xC0020000, "Host active", "cfg device");
    if (!configure_device()) {
        show_status(0xE0030000, "USB cfg fail", "ep0 control");
        while (1) {
            msleep(500);
            leds_g_out_write(0x012);
            leds_r_out_write(0x12012);
            msleep(500);
            leds_g_out_write(0x048);
            leds_r_out_write(0x04804);
        }
    }

    while (1) {
        int ep;
        uint32_t sw;

        msleep(10);

        leds_g_out_write(1u << knight_pos);
        knight_pos += knight_dir;
        if (knight_pos == 8 || knight_pos == 0) {
            knight_dir = -knight_dir;
        }

        sw = switches_in_read();
        leds_r_out_write(sw & 0x3ffffu);

        for (ep = 1; ep <= 5; ++ep) {
            uint16_t addr_pid_ep = (uint16_t)(0x0190 | ep);
            int status;

            write_td(0x0500, 0x0000, 8, addr_pid_ep, toggles[ep], 0x0520);
            status = execute_td_sync(0x0500);

            if (status == 0x0003) {
                uint16_t d0;

                ep_seen_mask |= (1u << ep);
                toggles[ep] ^= 0x0040;
                CY_HPI_ADDRESS = 0x0520;
                d0 = (uint16_t)(CY_HPI_DATA & 0xffffu);
                (void)CY_HPI_DATA;

                if (d0 != 0 && d0 != last_data[ep]) {
                    last_data[ep] = d0;
                    itoa_hex32(d0, buf);
                    lcd_set_cursor(1, 9);
                    lcd_print("E");
                    lcd_write_data((uint8_t)('0' + ep));
                    lcd_print(":");
                    lcd_print(buf + 4);
                }
            }
        }

        // High-frequency HPI read loop for debug capture (Switch 0)
        if (sw & 0x1) {
            vga_puts_xy(1, 60, "READ LOOP ON ");
            for (int k = 0; k < 1000; k++) {
                hpi_read_reg16(&CY_HPI_DATA);
            }
        } else {
            vga_puts_xy(1, 60, "CAPTURE LOOP OFF");
        }

        if ((i % 10u) == 0u) {
            show_runtime_status(i / 10u, sw, ep_seen_mask);
        }

        ++i;
    }
}
