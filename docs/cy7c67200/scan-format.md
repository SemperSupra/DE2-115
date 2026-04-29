# CY16 SCAN Record Format

The BIOS `SCAN_INT` mechanism consumes records beginning with signature `0xC3B6`.

Common structure:

```text
uint16_le signature = 0xC3B6
uint16_le length
uint8     opcode
uint8[]   data
```

Common opcodes:

| Opcode | Meaning |
|---:|---|
| `0x00` | Write/copy data to memory. Data begins with `uint16_le address`, followed by bytes. |
| `0x04` | Jump to absolute address. Data is `uint16_le address`. |
| `0x05` | Call absolute address. Data is `uint16_le address`. |
| `0x06` | Call software interrupt. Data contains interrupt number. |

For host-parsed SCAN over HPI, the external host can parse COPY records and write bytes/words through HPI, then parse CALL/JUMP records and issue LCP `COMM_CALL_CODE` / `COMM_JUMP2CODE`.
