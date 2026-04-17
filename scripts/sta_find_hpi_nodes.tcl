load_package report
load_package project

project_open de2_115_vga_platform -revision de2_115_vga_platform
create_timing_netlist
read_sdc
update_timing_netlist

proc print_matches {label pattern} {
    puts "${label}_start"
    foreach_in_collection n [get_names -filter "*${pattern}*"] {
        puts [get_name_info -info full_path $n]
    }
    puts "${label}_end"
}

print_matches STP_PROBE stp_hpi_bridge_probe
print_matches CLK_SYS sys_clk
print_matches CLK_CRG crg
print_matches USB_CS usb_otg_cs_n
print_matches USB_RD usb_otg_rd_n
print_matches USB_WR usb_otg_wr_n
print_matches USB_ADDR usb_otg_addr
print_matches USB_DATA usb_otg_data
print_matches USB_RST usb_otg_rst_n

delete_timing_netlist
project_close
