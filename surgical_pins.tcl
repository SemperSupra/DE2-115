package require ::quartus::project

project_open de2_115_vga_platform

set_location_assignment PIN_Y2 -to clk50
set_location_assignment PIN_M23 -to buttons0

# UART (Corrected: Manual says TXD is G12, RXD is G9)
set_location_assignment PIN_G12 -to serial_tx
set_location_assignment PIN_G9 -to serial_rx

# Ethernet 1 (RGMII)
set_location_assignment PIN_B15 -to eth_gtx_clocks1_rx
set_location_assignment PIN_C22 -to eth_gtx_clocks1_tx
set_location_assignment PIN_D25 -to rgmii_eth1_mdio
set_location_assignment PIN_D23 -to rgmii_eth1_mdc
set_location_assignment PIN_D22 -to rgmii_eth1_rst_n
set_location_assignment PIN_A22 -to rgmii_eth1_rx_ctl
set_location_assignment PIN_B23 -to rgmii_eth1_rx_data[0]
set_location_assignment PIN_C21 -to rgmii_eth1_rx_data[1]
set_location_assignment PIN_A23 -to rgmii_eth1_rx_data[2]
set_location_assignment PIN_D21 -to rgmii_eth1_rx_data[3]
set_location_assignment PIN_B25 -to rgmii_eth1_tx_ctl
set_location_assignment PIN_C25 -to rgmii_eth1_tx_data[0]
set_location_assignment PIN_A26 -to rgmii_eth1_tx_data[1]
set_location_assignment PIN_B26 -to rgmii_eth1_tx_data[2]
set_location_assignment PIN_C26 -to rgmii_eth1_tx_data[3]

# USB OTG (HPI)
set_location_assignment PIN_H7 -to usb_otg_addr[0]
set_location_assignment PIN_C3 -to usb_otg_addr[1]
set_location_assignment PIN_A3 -to usb_otg_cs_n
set_location_assignment PIN_B3 -to usb_otg_rd_n
set_location_assignment PIN_A4 -to usb_otg_wr_n
set_location_assignment PIN_C5 -to usb_otg_rst_n
set_location_assignment PIN_D5 -to usb_otg_int0
set_location_assignment PIN_E5 -to usb_otg_int1
set_location_assignment PIN_J1 -to usb_otg_dreq
set_location_assignment PIN_J6 -to usb_otg_data[0]
set_location_assignment PIN_K4 -to usb_otg_data[1]
set_location_assignment PIN_J5 -to usb_otg_data[2]
set_location_assignment PIN_K3 -to usb_otg_data[3]
set_location_assignment PIN_J4 -to usb_otg_data[4]
set_location_assignment PIN_J3 -to usb_otg_data[5]
set_location_assignment PIN_J7 -to usb_otg_data[6]
set_location_assignment PIN_H6 -to usb_otg_data[7]
set_location_assignment PIN_H3 -to usb_otg_data[8]
set_location_assignment PIN_H4 -to usb_otg_data[9]
set_location_assignment PIN_G1 -to usb_otg_data[10]
set_location_assignment PIN_G2 -to usb_otg_data[11]
set_location_assignment PIN_G3 -to usb_otg_data[12]
set_location_assignment PIN_F1 -to usb_otg_data[13]
set_location_assignment PIN_F3 -to usb_otg_data[14]
set_location_assignment PIN_G4 -to usb_otg_data[15]

# Force Cyclone IV E
set_global_assignment -name FAMILY "Cyclone IV E"
set_global_assignment -name DEVICE EP4CE115F29C7

export_assignments
project_close
