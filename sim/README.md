# CY7C67200 HPI fake target simulation

This is a minimal fake HPI target for testing host/bridge logic without hardware.

With Icarus Verilog:

```bash
iverilog -g2012 -o cy7c67200_hpi_model_tb.vvp sim/cy7c67200_hpi_model.v sim/cy7c67200_hpi_model_tb.v
vvp cy7c67200_hpi_model_tb.vvp
```

Expected:

```text
PASS cy7c67200_hpi_model_tb
```

This model does not emulate USB, BIOS, or CY16 instruction execution. It only validates HPI address/data/mailbox/status behavior.
