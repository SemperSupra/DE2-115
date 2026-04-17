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
    puts "no_device"
    qexit -error
}
set dev [lindex $devs 0]

puts "hw=$hw"
puts "dev=$dev"

if {[catch {start_insystem_source_probe -hardware_name $hw -device_name $dev} rerr]} {
    puts "start_failed=$rerr"
}

puts "reading_probe..."
for {set i 0} {$i < 5} {incr i} {
    if {[catch {set pdata [read_probe_data -instance_index 0 -value_in_hex]} rerr]} {
        puts "read_failed=$rerr"
    } else {
        puts "probe_data\[$i\]=$pdata"
    }
    after 100
}

end_insystem_source_probe
qexit -success
