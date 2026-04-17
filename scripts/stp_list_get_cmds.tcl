load_package project
package require ::quartus::stp

puts "get_cmds_start"
foreach c [lsort [info commands get_*]] {
    puts $c
}
puts "get_cmds_end"
