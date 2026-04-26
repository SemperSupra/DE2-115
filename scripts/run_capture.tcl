load_package project
package require ::quartus::stp

if {[llength $argv] < 2} {
    puts "usage: quartus_stp.exe -t scripts/run_capture.tcl <session.stp> <output.csv> ?signal_set? ?trigger? ?instance? ?data_log?"
    qexit -error
}

set session_path [file normalize [lindex $argv 0]]
set output_path [file normalize [lindex $argv 1]]
set data_log_name [expr {[llength $argv] > 2 ? [lindex $argv 2] : "log_1"}]
set wait_ms [expr {[info exists ::env(SIGNALTAP_WAIT_MS)] ? $::env(SIGNALTAP_WAIT_MS) : 10000}]

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

file mkdir [file dirname $output_path]

puts "session=$session_path"
puts "output=$output_path"
puts "hardware=$hw"
puts "device=$dev"
puts "data_log=$data_log_name"

open_session -name $session_path
run -check -hardware_name $hw -device_name $dev -data_log $data_log_name

puts "waiting_ms=$wait_ms"
after $wait_ms

export_data_log -data_log $data_log_name -filename $output_path -format csv
close_session
qexit -success
