# CY7C67200 HPI and LCP Notes

## HPI logical registers

The external HPI bus exposes four logical ports selected by `HPI_ADDR[1:0]`:

| A[1:0] | Register |
|---:|---|
| `0` | DATA |
| `1` | MAILBOX |
| `2` | ADDRESS |
| `3` | STATUS |

Expected access pattern:

```text
write ADDRESS = target CY address
write/read DATA
DATA auto-increments target address for block operations
```

## LCP command constants

| Symbol | Value |
|---|---:|
| `COMM_JUMP2CODE` | `0xCE00` |
| `COMM_EXEC_INT` | `0xCE01` |
| `COMM_READ_CTRL_REG` | `0xCE02` |
| `COMM_WRITE_CTRL_REG` | `0xCE03` |
| `COMM_CALL_CODE` | `0xCE04` |
| `COMM_ACK` | `0x0FED` |
| `COMM_NAK` | `0xDEAD` |
| `COMM_RESET` | `0xFA50` |

## LCP shared memory addresses

| Symbol | Address |
|---|---:|
| `COMM_CODE_ADDR` | `0x01BC` |
| `COMM_INT_NUM` | `0x01C2` |
| `COMM_R0` | `0x01C4` |
| `CY_SIE1MSG_REG` | `0x0144` |
| `CY_SIE2MSG_REG` | `0x0148` |
