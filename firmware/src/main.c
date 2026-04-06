#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <time.h>

#include "font.h"

// 7-segment patterns (active low for common anode)
const uint8_t hex_digits[] = {
    0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xf8,
    0x80, 0x90, 0x88, 0x83, 0xc6, 0xa1, 0x86, 0x8e
};

static void display_hex(uint32_t val) {
    hex1_out_write(hex_digits[(val >> 0) & 0xf]);
    hex2_out_write(hex_digits[(val >> 4) & 0xf]);
    hex3_out_write(hex_digits[(val >> 8) & 0xf]);
    hex4_out_write(hex_digits[(val >> 12) & 0xf]);
    hex5_out_write(hex_digits[(val >> 16) & 0xf]);
    hex6_out_write(hex_digits[(val >> 20) & 0xf]);
    hex7_out_write(hex_digits[(val >> 24) & 0xf]);
}

static void itoa_hex32(uint32_t n, char *s) {
    const char *hex = "0123456789ABCDEF";
    for(int i=0; i<8; i++) {
        s[7-i] = hex[(n >> (i*4)) & 0xF];
    }
    s[8] = '\0';
}

static void msleep(unsigned int ms) {
    timer0_en_write(0);
    timer0_reload_write(0);
    timer0_load_write(CONFIG_CLOCK_FREQUENCY/1000 * ms);
    timer0_en_write(1);
    timer0_update_value_write(1);
    while(timer0_value_read()) timer0_update_value_write(1);
}

// LCD Helpers
#define LCD_ON    (1 << 0)
#define LCD_BLON  (1 << 1)
#define LCD_EN    (1 << 2)
#define LCD_RW    (1 << 3)
#define LCD_RS    (1 << 4)

static void lcd_write_cmd(uint8_t cmd) {
    uint32_t val = LCD_ON | LCD_BLON | (((uint32_t)cmd) << 5);
    lcd_out_write(val);
    lcd_out_write(val | LCD_EN);
    lcd_out_write(val);
    msleep(2);
}

static void lcd_write_data(uint8_t data) {
    uint32_t val = LCD_ON | LCD_BLON | LCD_RS | (((uint32_t)data) << 5);
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
    addr += col;
    lcd_write_cmd(0x80 | addr);
}

static void lcd_print(const char *str) {
    while (*str) {
        lcd_write_data((uint8_t)*str++);
    }
}

extern void uart_init(void);
extern int sdram_init(void);

// CY7C67200 HPI Registers
#define CY_BASE 0x30000000
#define CY_HPI_DATA    (*(volatile uint32_t *)(CY_BASE + 0x00)) // A1=0, A0=0
#define CY_HPI_MAILBOX (*(volatile uint32_t *)(CY_BASE + 0x04)) // A1=0, A0=1
#define CY_HPI_ADDRESS (*(volatile uint32_t *)(CY_BASE + 0x08)) // A1=1, A0=0
#define CY_HPI_STATUS  (*(volatile uint32_t *)(CY_BASE + 0x0C)) // A1=1, A0=1

// CY7C67200 LCP Commands
#define COMM_ACK               0x0FED
#define COMM_RESET             0xFA50
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
#define HUSB_SIE1_INIT_INT     0x0072
#define HUSB_RESET_INT         0x0074
#define HPI_SIE1_MSG_ADR       0x0144
#define HOST1_STAT_REG         0xC090
#define HUSB_pEOT              0x01B4
#define HPI_IRQ_ROUTING_REG    0x0142
#define HOST1_IRQ_EN_REG       0xC08C
#define USB1_CTL_REG           0xC08A
#define SOFEOP1_TO_CPU_EN      0x0400
#define RESUME1_TO_HPI_EN      0x0040
#define A_CHG_IRQ_EN           0x0010
#define SOF_EOP_IRQ_EN         0x0200
#define A_DP_STAT              0x2000
#define A_DM_STAT              0x1000

static void UsbWrite(uint16_t Address, uint16_t Data) {
    CY_HPI_ADDRESS = Address;
    CY_HPI_DATA = Data;
}

static uint16_t UsbRead(uint16_t Address) {
    CY_HPI_ADDRESS = Address;
    return CY_HPI_DATA & 0xFFFF;
}

static void write_td(uint16_t td_addr, uint16_t next_td, uint16_t length, uint16_t addr_pid_ep, uint16_t toggle, uint16_t buf_addr) {
    CY_HPI_ADDRESS = td_addr;
    CY_HPI_DATA = next_td;
    CY_HPI_DATA = length;
    CY_HPI_DATA = addr_pid_ep;
    CY_HPI_DATA = toggle;
    CY_HPI_DATA = 0x0013; // Control (Enable)
    CY_HPI_DATA = buf_addr;
}

static uint16_t execute_td_sync(uint16_t td_addr) {
    // Clear any pending message
    uint32_t status = CY_HPI_STATUS;
    if (status & (1 << 4)) {
        UsbRead(HPI_SIE1_MSG_ADR);
        UsbWrite(HPI_SIE1_MSG_ADR, 0);
    }
    
    // Execute TD
    UsbWrite(HUSB_pEOT, 600); 
    UsbWrite(0x01B0, td_addr); 
    
    // Wait for TDListDone (0x1000 in SIE1msg)
    int timeout = 500000;
    while (!(CY_HPI_STATUS & (1 << 4)) && timeout > 0) { timeout--; }
    if (timeout > 0) {
        UsbRead(HPI_SIE1_MSG_ADR);
        UsbWrite(HPI_SIE1_MSG_ADR, 0);
    } else {
        return 0xFFFF; // Timeout
    }
    
    // Read status
    CY_HPI_ADDRESS = td_addr + 8; // Word 4
    return CY_HPI_DATA & 0xFFFF;
}

int main(void) {
    uint32_t i = 0;
    int knight_pos = 0;
    int knight_dir = 1;
    
    display_hex(0x8888888);

    uart_init();
    sdram_init();

    lcd_init();
    lcd_set_cursor(0, 0);
    lcd_print("Initializing USB");
    
    CY_HPI_MAILBOX = COMM_RESET;
    msleep(100);
    UsbRead(HPI_SIE1_MSG_ADR);
    UsbWrite(HPI_SIE1_MSG_ADR, 0);
    UsbWrite(HOST1_STAT_REG, 0xFFFF);
    UsbWrite(HUSB_pEOT, 600);
    UsbWrite(HPI_IRQ_ROUTING_REG, SOFEOP1_TO_CPU_EN | RESUME1_TO_HPI_EN);
    UsbWrite(HOST1_IRQ_EN_REG, A_CHG_IRQ_EN | SOF_EOP_IRQ_EN);

    UsbWrite(COMM_R0,0); UsbWrite(COMM_R1,0); UsbWrite(COMM_R2,0);
    UsbWrite(COMM_R3,0); UsbWrite(COMM_R4,0); UsbWrite(COMM_R5,0);
    UsbWrite(COMM_INT_NUM, HUSB_SIE1_INIT_INT);
    CY_HPI_MAILBOX = 0xCE01;
    int t1 = 500000; while (!(CY_HPI_STATUS & 0xFFFF) && t1 > 0) { t1--; }
    if (t1 == 0) { lcd_set_cursor(1, 0); lcd_print("Err: t1_1"); return 0; }
    
    int t2 = 500000; while ((CY_HPI_MAILBOX & 0xFFFF) != COMM_ACK && t2 > 0) { t2--; }
    if (t2 == 0) { lcd_set_cursor(1, 0); lcd_print("Err: t1_2"); return 0; }

    UsbWrite(COMM_INT_NUM, HUSB_RESET_INT);
    UsbWrite(COMM_R0,0x003c); // Reset Host 1 port
    CY_HPI_MAILBOX = 0xCE01;
    int t3 = 500000; while ((CY_HPI_MAILBOX & 0xFFFF) != COMM_ACK && t3 > 0) { t3--; }
    if (t3 == 0) { lcd_set_cursor(1, 0); lcd_print("Err: t2"); return 0; }
    
    lcd_set_cursor(0, 0);
    lcd_print("Wait for Insert ");
    
    uint16_t msg = 0;
    int t4 = 5000000; while (msg != 0x1000 && t4 > 0) { t4--;
        if (CY_HPI_STATUS & (1 << 4)) {
            msg = UsbRead(HPI_SIE1_MSG_ADR);
            UsbWrite(HPI_SIE1_MSG_ADR, 0);
        }
    }
    if (t4 == 0) { lcd_set_cursor(1, 0); lcd_print("Err: t3"); return 0; }
    
    msleep(100); // Wait for port to stabilize
    
    // 1. SET_ADDRESS = 1
    CY_HPI_ADDRESS = 0x0514;
    CY_HPI_DATA = 0x0500; // bmRequestType=0, bRequest=5 (SET_ADDRESS)
    CY_HPI_DATA = 0x0001; // wValue=1
    CY_HPI_DATA = 0x0000;
    CY_HPI_DATA = 0x0000;
    write_td(0x0500, 0x0000, 8, 0x00D0, 0x0001, 0x0514); // Addr 0, SETUP
    uint16_t st_addr_setup = execute_td_sync(0x0500);
    
    write_td(0x0500, 0x0000, 0, 0x0090, 0x0041, 0x0000); // Addr 0, IN
    uint16_t st_addr_in = execute_td_sync(0x0500);

    msleep(20);

    // 2. SET_CONFIGURATION = 1 (to Address 1)
    CY_HPI_ADDRESS = 0x0514;
    CY_HPI_DATA = 0x0900; // bmRequestType=0, bRequest=9 (SET_CONFIGURATION)
    CY_HPI_DATA = 0x0001; // wValue=1
    CY_HPI_DATA = 0x0000;
    CY_HPI_DATA = 0x0000;
    write_td(0x0500, 0x0000, 8, 0x01D0, 0x0001, 0x0514); // Addr 1, SETUP
    uint16_t st_cfg_setup = execute_td_sync(0x0500);
    
    write_td(0x0500, 0x0000, 0, 0x0190, 0x0041, 0x0000); // Addr 1, IN
    uint16_t st_cfg_in = execute_td_sync(0x0500);
    
    lcd_set_cursor(0, 0);
    char buf[16];
    itoa_hex32((st_addr_setup << 16) | st_addr_in, buf);
    lcd_print("A:"); lcd_print(buf); lcd_print(" ");
    
    lcd_set_cursor(1, 0);
    itoa_hex32((st_cfg_setup << 16) | st_cfg_in, buf);
    lcd_print("C:"); lcd_print(buf); lcd_print(" ");

    uint16_t toggles[6] = {0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001};
    uint16_t last_data[6] = {0, 0, 0, 0, 0, 0};

    while (1) {
        msleep(10);

        leds_g_out_write(1 << knight_pos);
        knight_pos += knight_dir;
        if (knight_pos == 7 || knight_pos == 0) knight_dir = -knight_dir;

        uint32_t sw = switches_in_read();
        leds_r_out_write(sw);

        for (int ep = 1; ep <= 5; ep++) {
            uint16_t addr_pid_ep = 0x0190 | ep; // Addr 1, PID 9, EP n
            write_td(0x0500, 0x0000, 8, addr_pid_ep, toggles[ep], 0x0520);
            uint16_t status = execute_td_sync(0x0500);
            
            if (status == 0x0003) { // ACK
                toggles[ep] ^= 0x0040; // Flip DATA0/1 toggle
                
                CY_HPI_ADDRESS = 0x0520;
                uint16_t d0 = CY_HPI_DATA & 0xFFFF;
                (void)CY_HPI_DATA;
                
                if (d0 != 0 && d0 != last_data[ep]) {
                    last_data[ep] = d0;
                    
                    lcd_set_cursor(1, 9);
                    lcd_print("E");
                    char ep_buf[2] = {'0'+ep, 0};
                    lcd_print(ep_buf);
                    lcd_print(":");
                    itoa_hex32(d0, buf);
                    lcd_print(buf + 4);
                }
            }
        }

        if (i % 10 == 0) {
            uint32_t uptime = i / 10;
            display_hex(uptime);
        }
        
        i++;
    }

    return 0;
}
