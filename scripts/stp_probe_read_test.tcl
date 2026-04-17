load_package project
package require ::quartus::stp

set hws [get_hardware_names]
if {[llength $hws] == 0} {
    puts "no_hardware"
    qexit -error
}
set hw [lindex $hws 0]
set devs [get_device_names -hardware_name $hw]
if {[llength $devs] == 0} {
    puts "no_devices"
    qexit -error
}
set dev [lindex $devs 0]
puts "hw=$hw"
puts "dev=$dev"

if {[catch {start_insystem_source_probe -hardware_name $hw -device_name $dev} start_err]} {
    puts "start_insystem_source_probe_failed=$start_err"
    qexit -error
}
puts "start_insystem_source_probe_ok"

if {[catch {set inst_info [get_insystem_source_probe_instance_info -hardware_name $hw -device_name $dev]} info_err]} {
    puts "get_instances_failed=$info_err"
    qexit -error
}
puts "instances=$inst_info"

set inst_id [lindex $inst_info 0]
puts "selected_instance=$inst_id"

if {[catch {set pdata [read_probe_data -instance_index $inst_id -value_in_hex -hardware_name $hw -device_name $dev]} rerr]} {
    puts "read_probe_data_failed=$rerr"
    qexit -error
}
puts "probe_data=$pdata"
qexit -success
