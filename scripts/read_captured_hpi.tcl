load_package project
package require ::quartus::stp

set hws [get_hardware_names]
set hw [lindex $hws 0]
set devs [get_device_names -hardware_name $hw]
set dev [lindex $devs 0]
set mode 0
set wait_ms 1000

if {$argc >= 1} { set mode [lindex $argv 0] }
if {$argc >= 2} { set wait_ms [lindex $argv 1] }

start_insystem_source_probe -hardware_name $hw -device_name $dev

set clear_value [expr {($mode << 1) | 1}]
set arm_value [expr {$mode << 1}]
puts "resetting_capture mode=$mode clear_value=$clear_value arm_value=$arm_value..."
write_source_data -instance_index 0 -value [format "%X" $clear_value] -value_in_hex
after 100
write_source_data -instance_index 0 -value [format "%X" $arm_value] -value_in_hex
puts "source_data=[read_source_data -instance_index 0 -value_in_hex]"
after $wait_ms

puts "reading_captured_data..."
for {set i 0} {$i < 5} {incr i} {
    set pdata [read_probe_data -instance_index 0 -value_in_hex]
    puts "probe_data\[$i\]=$pdata"
    after 100
}

end_insystem_source_probe
qexit -success
