load_package project
package require ::quartus::stp

set hws [get_hardware_names]
set hw [lindex $hws 0]
set devs [get_device_names -hardware_name $hw]
set dev [lindex $devs 0]

if {[catch {start_insystem_source_probe -hardware_name $hw -device_name $dev} rerr]} {
    puts "start_failed=$rerr"
}

puts "polling_active..."
set count 0
while {$count < 1000} {
    set pdata [read_probe_data -instance_index 0 -value_in_hex]
    # Bit 147 is 'active' (based on my v4 decode)
    # val >> 147 & 1
    # Hex string is 38 chars. Bit 147 is in the 2nd char from the left?
    # Bits 151..148 are 1st char. Bits 147..144 are 2nd char.
    set char2 [string index $pdata 1]
    set val2 [expr "0x$char2"]
    if {$val2 & 0x8} {
        puts "ACTIVE_CAPTURE: $pdata"
        # Decode some fields
        # State is bits 143..141. (Part of 2nd and 3rd char?)
        # state: bits 143, 142, 141.
        # val2 & 0x7 is bits 146, 145, 144.
        # So state is in the NEXT char.
        set char3 [string index $pdata 2]
        puts "  Char2=$char2 Char3=$char3"
    }
    incr count
}

end_insystem_source_probe
qexit -success
