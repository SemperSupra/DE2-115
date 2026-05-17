import sys

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    search = """    wire       hpi_access = active & ~debug_latched;
    wire [5:0] effective_access_cycles ="""
    
    # We want a 1 cycle delay for RD/WR strobes.
    # CS goes low when hpi_access goes high.
    # We can define hpi_strobe = hpi_access & (count >= 6'd1) & (count < effective_access_cycles - 6'd1)
    # Wait, the current logic is:
    # count == effective_access_cycles - 6'd1 -> STATE_ACK (which transitions to STATE_TURNAROUND)
    # active is 1 in STATE_WAIT.
    # So hpi_access is 1 in STATE_WAIT.
    
    # If we want a setup and hold time for CS relative to RD/WR:
    # CS_N goes low when hpi_access = 1.
    # RD_N/WR_N goes low when hpi_strobe = 1.
    # hpi_strobe = hpi_access & (count >= 1) & (count < effective_access_cycles - 1)
    
    replace = """    wire       hpi_access = active & ~debug_latched;
    wire       hpi_strobe = hpi_access & (count >= 6'd1) & (count < (effective_access_cycles - 6'd1));
    wire [5:0] effective_access_cycles ="""

    if search in content:
        content = content.replace(search, replace)
    else:
        print("Search block not found in", filepath)
        return
        
    search2 = """        .iRD_N((hpi_access & ~latched_we) ? 1'b0 : 1'b1),
        .iWR_N((hpi_access &  latched_we) ? 1'b0 : 1'b1),
        .iCS_N(~hpi_access),"""
    
    replace2 = """        .iRD_N((hpi_strobe & ~latched_we) ? 1'b0 : 1'b1),
        .iWR_N((hpi_strobe &  latched_we) ? 1'b0 : 1'b1),
        .iCS_N(~hpi_access),"""
        
    if search2 in content:
        content = content.replace(search2, replace2)
    else:
        print("Search block 2 not found in", filepath)
        return
        
    with open(filepath, 'w') as f:
        f.write(content)

patch_file("./cy7c67200_wb_bridge.v")
patch_file("./rtl/cy7c67200_wb_bridge.v")
print("Patched files successfully.")
