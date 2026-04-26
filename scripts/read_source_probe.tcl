load_package project
package require ::quartus::stp

set target_id "HPI0"
set mode 0
set wait_ms 1000
set reads 5

if {$argc >= 1} { set target_id [lindex $argv 0] }
if {$argc >= 2} { set mode [lindex $argv 1] }
if {$argc >= 3} { set wait_ms [lindex $argv 2] }
if {$argc >= 4} { set reads [lindex $argv 3] }

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

set inst_info [get_insystem_source_probe_instance_info -hardware_name $hw -device_name $dev]

set inst_index ""
set inst_source_width ""
set inst_probe_width ""
puts "instances=$inst_info"
foreach inst $inst_info {
    if {[llength $inst] < 4} {
        continue
    }
    set idx [lindex $inst 0]
    set source_width [lindex $inst 1]
    set probe_width [lindex $inst 2]
    set instance_id [lindex $inst 3]
    if {$target_id eq $instance_id || $target_id eq $idx} {
        set inst_index $idx
        set inst_source_width $source_width
        set inst_probe_width $probe_width
    }
}

if {$inst_index eq ""} {
    puts "missing_instance=$target_id"
    end_insystem_source_probe
    qexit -error
}

set clear_value [expr {($mode << 1) | 1}]
set arm_value [expr {$mode << 1}]
puts "selected_instance=$inst_index source_width=$inst_source_width probe_width=$inst_probe_width mode=$mode"
puts "clear_value=$clear_value arm_value=$arm_value wait_ms=$wait_ms reads=$reads"

start_insystem_source_probe -hardware_name $hw -device_name $dev
write_source_data -instance_index $inst_index -value [format "%X" $clear_value] -value_in_hex
after 100
write_source_data -instance_index $inst_index -value [format "%X" $arm_value] -value_in_hex
puts "source_data=[read_source_data -instance_index $inst_index -value_in_hex]"
after $wait_ms

for {set i 0} {$i < $reads} {incr i} {
    set pdata [read_probe_data -instance_index $inst_index -value_in_hex]
    puts "probe_data\[$i\]=$pdata"
    after 100
}

end_insystem_source_probe
qexit -success
