puts "core_load_package=[info commands load_package]"
if {[llength [info commands load_package]] > 0} {
    catch {load_package flow} flow_res
    puts "load_flow=$flow_res"
    catch {load_package project} proj_res
    puts "load_project=$proj_res"
    catch {load_package signaltap} stp_res
    puts "load_signaltap=$stp_res"
}

catch {package require ::quartus::project} proj_pkg
puts "pkg_project=$proj_pkg"
catch {package require ::quartus::flow} flow_pkg
puts "pkg_flow=$flow_pkg"
catch {package require ::quartus::stp} stp_pkg
puts "pkg_stp=$stp_pkg"

puts "stp_commands_start"
foreach c [lsort [info commands ::quartus::stp::*]] {
    puts $c
}
puts "stp_commands_end"

puts "global_matches_start"
foreach c [lsort [info commands *]] {
    if {[string match "*hardware*" $c] || [string match "*signal*" $c] || [string match "*stp*" $c] || [string match "*instance*" $c] || [string match "*trigger*" $c] || [string match "*acq*" $c]} {
        puts $c
    }
}
puts "global_matches_end"
