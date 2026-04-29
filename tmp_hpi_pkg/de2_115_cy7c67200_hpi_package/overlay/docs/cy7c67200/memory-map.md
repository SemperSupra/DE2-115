# CY16 / CY7C67200 Memory Map Summary

Important regions for the DE2-115 bring-up:

| Range | Purpose |
|---:|---|
| `0x0000-0x007F` | Hardware interrupt vectors |
| `0x0080-0x00FF` | Software interrupt vectors |
| `0x0100-0x011F` | Primary register bank |
| `0x0120-0x013F` | Swap register bank |
| `0x0140-0x0148` | HPI interrupt/mailbox area |
| `0x014A-0x01FF` | LCP command processor variables |
| `0x0200-0x02FF` | USB registers |
| `0x0310-0x03FF` | BIOS stack |
| `0x04A4-0x3FFF` | Internal RAM user code/data |
| `0xC000-0xC0FF` | Memory-mapped control registers |
| `0xE000-0xFFFF` | Internal BIOS ROM |

Useful control registers:

| Address | Symbol |
|---:|---|
| `0xC000` | `CY_CPU_FLAGS_REG` |
| `0xC002` | `CY_BANK_REG` |
| `0xC004` | `CY_HW_REV_REG` |
| `0xC008` | `CY_CPU_SPEED_REG` |
| `0xC00A` | `CY_POWER_CTL_REG` |
| `0xC00E` | `CY_IRQ_EN_REG` |
| `0xC014` | `CY_BKPT_REG` |
| `0xC03A` | `CY_XMEM_CTL_REG` |
