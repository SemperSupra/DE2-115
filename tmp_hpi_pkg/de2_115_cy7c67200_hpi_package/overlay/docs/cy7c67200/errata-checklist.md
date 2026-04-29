# CY7C67200 Errata Checklist for DE2-115

Apply these rules during bring-up:

1. After reset deassertion, wait at least about 10 ms, then clear:
   - `CY_SIE1MSG_REG = 0x0144`
   - `CY_SIE2MSG_REG = 0x0148`

2. Do not rely on global SIE interrupt enable bits to independently mask SIE1/SIE2. Use the lower-level SIE interrupt-enable registers when isolating one SIE.

3. Debounce VBUS-valid events in software.

4. If UART debug behaves strangely, remember the UART does not recognize framing errors and GPIO6 direction must be configured correctly when UART RX is enabled.

5. Treat attempted errata cleanup as unproven until HPI readback works.
