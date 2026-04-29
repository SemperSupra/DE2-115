# CY7C67200 / CY16 Bring-up Notes for DE2-115

This directory captures practical device facts used by the DE2-115 CY7C67200 HPI bring-up.

Current project rule:

> Do not debug USB class behavior until HPI register readback and RAM write/read pass.

Suggested bring-up order:

1. FPGA HPI bridge sanity.
2. CY reset release and identity-register reads.
3. CY internal RAM write/read through HPI.
4. Errata cleanup of SIE message registers.
5. SCAN COPY records.
6. LCP CALL/JUMP.
7. BIOS software interrupt execution.
8. Host SIE initialization.
9. USB bus traffic and HID/KVM2USB enumeration.
