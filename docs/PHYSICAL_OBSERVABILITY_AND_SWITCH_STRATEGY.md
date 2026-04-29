# Physical Observability and Switch Strategy

## Purpose

The DE2-115 should be made camera-readable and manually controllable. This helps agent-driven bring-up because a human or agent can verify board state even when UART, Ethernet, or USB is broken.

## AgentWebCam usage

Use AgentWebCam to capture:

```text
before programming
after programming
after reset
during GPIO smoke test
during USB test
after error
after switch changes
```

Recommended directory:

```text
artifacts/usb-hpi-runs/YYYYMMDD-HHMMSS/webcam/
  board-before.jpg
  board-after.jpg
  leds.jpg
  sevenseg.jpg
  lcd.jpg
  switch-positions.jpg
  board-run.mp4
```

## LED conventions

Suggested LED mapping:

```text
LED0 = heartbeat
LED1 = UART activity
LED2 = Ethernet/Etherbone activity
LED3 = HPI write observed
LED4 = HPI read observed
LED5 = HPI read nonzero/expected
LED6 = error latched
LED7 = safe mode
```

## 7-seg conventions

Use stable state/error codes:

```text
00 = idle
10 = CY reset low
11 = CY reset high
20 = HPI write address
21 = HPI write data
30 = HPI read address
31 = HPI read data
40 = LCP attempt
50 = SIE host init attempt
E1 = HPI all-zero read
E2 = HPI timeout
E3 = bus ownership / OE unexpected
E4 = Ethernet regression fail
E5 = USB packet evidence missing
```

## LCD conventions

Keep short camera-readable lines:

```text
MODE:HPI_ONLY
PHASE:RD_DATA
READ:0000
ERR:E1
```

or:

```text
ETH:OK UART:OK
USB:HPI FAIL
```

## Toggle switch conventions

Prefer simple, stable, coarse controls.

Recommended map:

```text
SW[2:0]   mode select
SW3       one-shot HPI test enable
SW4       continuous HPI loop enable
SW5       verbose UART logging
SW6       emit LiteScope/SignalTap trigger marker
SW7       extended source/probe snapshot enable
SW[9:8]   HPI test address group
SW[11:10] HPI test pattern
SW12      LCD status enable
SW13      7-seg status enable
SW14      reserved
SW15      force safe mode
SW16      force HPI bridge reset
SW17      force CY reset override
```

Simplified initial map:

```text
SW[2:0] = mode
SW3     = one-shot trigger
SW4     = loop enable
SW5     = verbose logs
SW15    = safe mode
SW16    = bridge reset
SW17    = CY reset
```

## Pushbutton conventions

Use pushbuttons for pulse actions:

```text
KEY0 = one-shot HPI transaction
KEY1 = clear error latch
KEY2 = advance LCD/status page
KEY3 = re-arm capture marker
```

## Agent rule

Agents must record switch positions in every evidence bundle. If visual switch recognition is uncertain, ask the human to state switch positions in the run notes.
