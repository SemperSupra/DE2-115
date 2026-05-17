import sys

with open("test_hpi_sim.py", 'r') as f:
    content = f.read()

# I noticed the simulation stops at #1000. Wait, why #1000?
# `#1000` is probably 1 ns! Wait! `timescale 1ns/1ps` implies #1 is 1ns! 
# So `#1000` is 1000ns. Wait, wb_ack never goes high! 
# The testbench is stuck in `wait(wb_ack == 1)`. Wait, it says:
# "tb.v:94: $finish called at 1000 (1ps)" Wait! "1000 (1ps)" means 1 ns!
# Because #1000 ps = 1 ns!
# Oh! The delay `#20` is 20 ns or 20 ps?
# If `timescale 1ns/1ps`, then `#20` means 20 ns.
# Wait, "1000 (1ps)" means time is 1000, and timescale unit is 1ps! So it's 1ns!
# No, 1000 in timescale 1ns/1ps usually means 1000ns. 
# "tb.v:94: $finish called at 1000 (1ps)". Wait, 1000 * 1ps is 1000ps = 1ns!
# So #1 is 1ps?! 
# If the timescale is `timescale 1ns/1ps`, #1 is 1ns!
# Wait! In test_hpi_sim.py: `timescale 1ns/1ps`
# Ah! I didn't put a backtick before `timescale` properly?
# Wait, in Python:
# """
# `timescale 1ns/1ps
# """
# It's there. 

# The problem: hpi_rd_n goes high at time 0?
# At time 0, everything initializes.
# `always @(posedge hpi_rd_n)` is triggered at time 0 because hpi_rd_n is x, then becomes 1.
# At time 0, hpi_cs_n is also x, then becomes 1.
# Then the #1 delay happens, making the check execute at time 1!
# At time 1, hpi_cs_n is 1. Since hpi_cs_n !== 0 (it is 1), it prints ERROR and finishes!
# This is an initialization glitch in the testbench!

content = content.replace("always @(posedge hpi_rd_n) begin", "always @(posedge hpi_rd_n) begin\n        if ($time > 10) begin")
content = content.replace("always @(negedge hpi_rd_n) begin", "always @(negedge hpi_rd_n) begin\n        if ($time > 10) begin")
content = content.replace("always @(posedge hpi_cs_n) begin", "always @(posedge hpi_cs_n) begin\n        if ($time > 10) begin")
content = content.replace("always @(negedge hpi_cs_n) begin", "always @(negedge hpi_cs_n) begin\n        if ($time > 10) begin")
content = content.replace("            $finish;\n        end\n    end", "            $finish;\n        end\n        end\n    end")

with open("test_hpi_sim.py", 'w') as f:
    f.write(content)

