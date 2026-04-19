load_package project
package require ::quartus::stp

set hw [lindex [get_hardware_names] 0]
set dev [lindex [get_device_names -hardware_name $hw] 0]

open_session -name "build/terasic_de2_115/gateware/hpi_signaltap.stp"
run -hardware_name $hw -device_name $dev -instance_name auto_signaltap_0 -signal_set signal_set_1 -trigger trigger_1

puts "waiting_for_trigger..."
after 5000

puts "saving_data..."
save_content_from_memory_to_file -instance_name auto_signaltap_0 -signal_set signal_set_1 -trigger trigger_1 -data_log log_1 -filename "capture.txt"

close_session
qexit -success
