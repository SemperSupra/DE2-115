load_package project
package require ::quartus::stp

set hws [get_hardware_names]
puts "hardware_names_start"
foreach h $hws { puts $h }
puts "hardware_names_end"

if {[llength $hws] == 0} {
    puts "no_hardware"
    qexit 1
}

set hw [lindex $hws 0]
puts "selected_hardware=$hw"

if {[catch {open_device -hardware_name $hw -device_name "@1:*"} err]} {
    puts "open_device_glob_failed=$err"
    set devs [get_device_names -hardware_name $hw]
    puts "device_names_start"
    foreach d $devs { puts $d }
    puts "device_names_end"
    if {[llength $devs] == 0} {
        puts "no_devices"
        qexit 2
    }
    set dev [lindex $devs 0]
    puts "selected_device=$dev"
    if {[catch {open_device -hardware_name $hw -device_name $dev} err2]} {
        puts "open_device_failed=$err2"
        qexit 3
    }
} else {
    puts "open_device_glob_ok"
}

set info_cmd_result ""
if {[catch {set info_cmd_result [get_insystem_source_probe_instance_info -hardware_name $hw -device_name $dev]} info_err]} {
    puts "get_insystem_source_probe_instance_info_failed=$info_err"
} else {
    puts "isp_instances_start"
    puts $info_cmd_result
    puts "isp_instances_end"
}

close_device
qexit -success
