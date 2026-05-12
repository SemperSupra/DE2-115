module altsource_probe #(
    parameter sld_auto_instance_index = "YES",
    parameter sld_instance_index = 0,
    parameter instance_id = "HPI0",
    parameter probe_width = 1,
    parameter source_width = 1,
    parameter source_initial_value = "0"
) (
    input wire [probe_width-1:0] probe,
    output wire [source_width-1:0] source
);
    assign source = 0;
endmodule
