load_package project
package require ::quartus::stp

set hws [get_hardware_names]
set hw [lindex $hws 0]
set devs [get_device_names -hardware_name $hw]
set dev [lindex $devs 0]

start_insystem_source_probe -hardware_name $hw -device_name $dev

puts "resetting_capture..."
write_source_data -instance_index 0 -value 1
after 100
write_source_data -instance_index 0 -value 0
after 1000

puts "reading_captured_data..."
for {set i 0} {$i < 5} {incr i} {
    set pdata [read_probe_data -instance_index 0 -value_in_hex]
    puts "probe_data\[$i\]=$pdata"
    after 100
}

end_insystem_source_probe
qexit -success
