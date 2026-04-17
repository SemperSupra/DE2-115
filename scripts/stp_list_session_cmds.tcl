load_package project
package require ::quartus::stp

puts "session_cmds_start"
foreach c [lsort [info commands *session*]] {
    puts $c
}
foreach c [lsort [info commands *save*]] {
    puts $c
}
puts "session_cmds_end"
