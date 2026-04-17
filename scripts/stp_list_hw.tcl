load_package project
package require ::quartus::stp

set names [get_hardware_names]
puts "hardware_names_start"
foreach n $names { puts $n }
puts "hardware_names_end"
