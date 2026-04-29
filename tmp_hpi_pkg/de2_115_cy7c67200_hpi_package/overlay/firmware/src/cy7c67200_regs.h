#ifndef CY7C67200_REGS_H
#define CY7C67200_REGS_H

#include <stdint.h>

/* CY16 memory-mapped control registers */
#define CY_CPU_FLAGS_REG        0xC000u
#define CY_BANK_REG             0xC002u
#define CY_HW_REV_REG           0xC004u
#define CY_GPIO_CTL_REG         0xC006u
#define CY_CPU_SPEED_REG        0xC008u
#define CY_POWER_CTL_REG        0xC00Au
#define CY_WDT_REG              0xC00Cu
#define CY_IRQ_EN_REG           0xC00Eu
#define CY_TMR0_REG             0xC010u
#define CY_TMR1_REG             0xC012u
#define CY_BKPT_REG             0xC014u
#define CY_XMEM_CTL_REG         0xC03Au
#define CY_USB_DIAG_REG         0xC03Cu
#define CY_MEM_DIAG_REG         0xC03Eu

/* HPI / LCP shared memory areas */
#define CY_HPI_IRQ_ROUTING_REG  0x0142u
#define CY_SIE1MSG_REG          0x0144u
#define CY_SIE2MSG_REG          0x0148u

#define CY_LCP_TABLE            0x019Au
#define CY_LCP_SND_MSG          0x019Cu
#define CY_LCP_SEMA             0x019Eu
#define CY_LCP_CHAIN            0x01A0u
#define CY_LCP_RSP              0x01A2u

#define CY_COMM_PORT_CMD        0x01BAu
#define CY_COMM_PORT_DATA       0x01BCu
#define CY_COMM_MEM_ADDR        0x01BCu
#define CY_COMM_MEM_LEN         0x01BEu
#define CY_COMM_CODE_ADDR       0x01BCu
#define CY_COMM_INT_NUM         0x01C2u
#define CY_COMM_R0              0x01C4u
#define CY_COMM_R1              0x01C6u
#define CY_COMM_R2              0x01C8u
#define CY_COMM_R3              0x01CAu
#define CY_COMM_R4              0x01CCu
#define CY_COMM_R5              0x01CEu
#define CY_COMM_R6              0x01D0u
#define CY_COMM_R7              0x01D2u
#define CY_COMM_R8              0x01D4u
#define CY_COMM_R9              0x01D6u
#define CY_COMM_R10             0x01D8u
#define CY_COMM_R11             0x01DAu
#define CY_COMM_R12             0x01DCu
#define CY_COMM_R13             0x01DEu

/* LCP commands */
#define CY_COMM_JUMP2CODE       0xCE00u
#define CY_COMM_EXEC_INT        0xCE01u
#define CY_COMM_READ_CTRL_REG   0xCE02u
#define CY_COMM_WRITE_CTRL_REG  0xCE03u
#define CY_COMM_CALL_CODE       0xCE04u
#define CY_COMM_READ_XMEM       0xCE05u
#define CY_COMM_WRITE_XMEM      0xCE06u
#define CY_COMM_CONFIG          0xCE07u
#define CY_COMM_READ_MEM        0xCE08u
#define CY_COMM_WRITE_MEM       0xCE09u

#define CY_COMM_ACK             0x0FEDu
#define CY_COMM_NAK             0xDEADu
#define CY_COMM_RESET           0xFA50u

/* BIOS software interrupts used by current project */
#define CY_HUSB_SIE1_INIT_INT   0x0072u
#define CY_HUSB_SIE2_INIT_INT   0x0073u
#define CY_HUSB_RESET_INT       0x0074u

/* Host register addresses used by current project */
#define CY_HOST1_IRQ_EN_REG     0xC08Cu
#define CY_HOST1_STAT_REG       0xC090u
#define CY_USB1_CTL_REG         0xC08Au
#define CY_HOST2_STAT_REG       0xC0B0u
#define CY_USB2_CTL_REG         0xC0AAu

#define CY_HUSB_SIE1_CURRENT_TD_PTR 0x01B0u
#define CY_HUSB_EOT                 0x01B4u

/* HPI status bits as seen by external host */
#define CY_HPI_STATUS_MAILBOX_OUT  (1u << 0)
#define CY_HPI_STATUS_RESET1       (1u << 1)
#define CY_HPI_STATUS_DONE1        (1u << 2)
#define CY_HPI_STATUS_DONE2        (1u << 3)
#define CY_HPI_STATUS_SIE1MSG      (1u << 4)
#define CY_HPI_STATUS_SIE2MSG      (1u << 5)
#define CY_HPI_STATUS_RESUME1      (1u << 6)
#define CY_HPI_STATUS_RESUME2      (1u << 7)
#define CY_HPI_STATUS_MAILBOX_IN   (1u << 8)
#define CY_HPI_STATUS_RESET2       (1u << 9)
#define CY_HPI_STATUS_SOF_EOP1     (1u << 10)
#define CY_HPI_STATUS_SOF_EOP2     (1u << 12)
#define CY_HPI_STATUS_ID           (1u << 14)
#define CY_HPI_STATUS_VBUS         (1u << 15)

/* SCAN */
#define CY_SCAN_SIGNATURE       0xC3B6u
#define CY_SCAN_OPCODE_COPY     0x00u
#define CY_SCAN_OPCODE_JUMP     0x04u
#define CY_SCAN_OPCODE_CALL     0x05u
#define CY_SCAN_OPCODE_INT      0x06u

#endif
