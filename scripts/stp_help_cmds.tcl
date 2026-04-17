load_package project
package require ::quartus::stp

set cmds {
    open_session
    run
    open_device
    get_device_names
    get_insystem_source_probe_instance_info
    read_probe_data
    start_insystem_source_probe
}

foreach c $cmds {
    puts "help_start:$c"
    catch {help $c} out
    puts $out
    puts "help_end:$c"
}
