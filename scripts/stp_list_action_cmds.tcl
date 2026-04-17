load_package project
package require ::quartus::stp

puts "action_cmds_start"
foreach c [lsort [info commands]] {
    if {[string match "set_*" $c] || [string match "start_*" $c] || [string match "run_*" $c] || [string match "read_*" $c] || [string match "write_*" $c] || [string match "create_*" $c] || [string match "open_*" $c] || [string match "close_*" $c]} {
        puts $c
    }
}
puts "action_cmds_end"
