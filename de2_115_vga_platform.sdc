create_clock -name clk50 -period 20.0 [get_ports {clk50}]

# Ethernet RX Clock (from PHY ENET1_RX_CLK / B15)
create_clock -name eth_rx_clk -period 8.0 [get_ports {eth_gtx_clocks1_rx}]

# Ethernet TX Clock (to PHY ENET1_GTX_CLK / C23)
# Shift the generated clock by 90 degrees (2ns for 125MHz/8ns period) to fix hold timing
create_generated_clock -name eth_tx_clk -source [get_ports {eth_gtx_clocks1_rx}] -phase 90 [get_ports {eth_gtx_clocks1_tx}]

derive_pll_clocks -use_net_name
derive_clock_uncertainty

# --- RGMII Constraints (Standard Marvell 88E1111 for DE2-115) ---
# Relaxed constraints to allow fitter more room, phase shift handles the bulk of the delay
set_output_delay -clock eth_tx_clk -max 1.5 [get_ports {rgmii_eth1_tx_data[*] rgmii_eth1_tx_ctl}]
set_output_delay -clock eth_tx_clk -min -1.5 [get_ports {rgmii_eth1_tx_data[*] rgmii_eth1_tx_ctl}]
set_output_delay -clock eth_tx_clk -max 1.5 [get_ports {rgmii_eth1_tx_data[*] rgmii_eth1_tx_ctl}] -add_delay -clock_fall
set_output_delay -clock eth_tx_clk -min -1.5 [get_ports {rgmii_eth1_tx_data[*] rgmii_eth1_tx_ctl}] -add_delay -clock_fall

set_input_delay -clock eth_rx_clk -max 1.5 [get_ports {rgmii_eth1_rx_data[*] rgmii_eth1_rx_ctl}]
set_input_delay -clock eth_rx_clk -min -1.5 [get_ports {rgmii_eth1_rx_data[*] rgmii_eth1_rx_ctl}]
set_input_delay -clock eth_rx_clk -max 1.5 [get_ports {rgmii_eth1_rx_data[*] rgmii_eth1_rx_ctl}] -add_delay -clock_fall
set_input_delay -clock eth_rx_clk -min -1.5 [get_ports {rgmii_eth1_rx_data[*] rgmii_eth1_rx_ctl}] -add_delay -clock_fall

# --- False paths between system and ethernet domains ---
set_false_path -from [get_clocks {sys_clk}] -to [get_clocks {eth_rx_clk}]
set_false_path -from [get_clocks {sys_clk}] -to [get_clocks {eth_tx_clk}]
set_false_path -from [get_clocks {eth_rx_clk}] -to [get_clocks {sys_clk}]
set_false_path -from [get_clocks {eth_tx_clk}] -to [get_clocks {sys_clk}]

# False path between RX and TX (standard for RGMII loopback)
set_false_path -from [get_clocks {eth_rx_clk}] -to [get_clocks {eth_tx_clk}]
set_false_path -from [get_clocks {eth_tx_clk}] -to [get_clocks {eth_rx_clk}]
