module cy7c67200_wb_bridge (
    input  wire        clk,
    input  wire        rst,

    input  wire [29:0] wb_adr,
    input  wire [31:0] wb_dat_w,
    output reg  [31:0] wb_dat_r,
    input  wire        wb_cyc,
    input  wire        wb_stb,
    input  wire        wb_we,
    output reg         wb_ack,

    inout  wire [15:0] hpi_data,
    output wire [1:0]  hpi_addr,
    output wire        hpi_rd_n,
    output wire        hpi_wr_n,
    output wire        hpi_cs_n,
    output wire        hpi_rst_n,
    output wire [159:0] dbg_probe
);

    localparam STATE_IDLE       = 2'd0;
    localparam STATE_WAIT       = 2'd1;
    localparam STATE_ACK        = 2'd2;
    localparam STATE_TURNAROUND = 2'd3;

    localparam ACCESS_CYCLES_DEFAULT     = 6'd63;
    localparam TURNAROUND_CYCLES_DEFAULT = 6'd8;
    localparam SAMPLE_OFFSET_DEFAULT     = 6'd4;

    reg [1:0]  state = STATE_IDLE;
    reg [5:0]  count = 6'd0;
    reg [15:0] read_data = 16'd0;
    reg [15:0] sample_data = 16'd0;
    reg [15:0] write_data = 16'd0;
    reg [29:0] latched_adr = 30'd0;
    reg        latched_we = 1'b0;
    reg        active = 1'b0;
    reg        debug_latched = 1'b0;
    
    reg [31:0] last_ctrl = 32'd0;
    reg [15:0] last_sample_data = 16'd0;
    reg [15:0] last_cy_data = 16'd0;
    
    reg        cfg_force_rst_en = 1'b0;
    reg        cfg_hpi_rst_n = 1'b1;
    reg [5:0]  cfg_access_cycles = ACCESS_CYCLES_DEFAULT;
    reg [5:0]  cfg_sample_offset = SAMPLE_OFFSET_DEFAULT;
    reg [5:0]  cfg_turnaround_cycles = TURNAROUND_CYCLES_DEFAULT;

    wire       wb_access = wb_cyc & wb_stb;
    // Map HPI registers to contiguous words (offsets 0, 1, 2, 3)
    // Map debug registers to anything above word address 0x3F
    wire       debug_access = wb_access & (wb_adr[29:6] != 24'd0);
    wire [1:0] bus_hpi_addr = wb_adr[1:0];
    wire [1:0] debug_index = wb_adr[1:0];
    wire       hpi_access = active & ~debug_latched;
    wire [5:0] effective_access_cycles =
        (cfg_access_cycles == 6'd0) ? 6'd1 : cfg_access_cycles;
    wire [5:0] effective_turnaround_cycles =
        (cfg_turnaround_cycles == 6'd0) ? 6'd1 : cfg_turnaround_cycles;
    wire [5:0] sample_threshold =
        (effective_access_cycles > cfg_sample_offset) ?
        (effective_access_cycles - cfg_sample_offset) : 6'd0;
    wire       cy_i_rst_n = cfg_force_rst_en ? cfg_hpi_rst_n : ~rst;
    wire [31:0] cy_o_data;
    wire        cy_o_int;
    wire [0:0] diag_source;

    assign hpi_cs_n  = ~hpi_access;
    assign hpi_rd_n  = (hpi_access & ~latched_we) ? 1'b0 : 1'b1;
    assign hpi_wr_n  = (hpi_access &  latched_we) ? 1'b0 : 1'b1;
    assign hpi_addr  = latched_adr[1:0];
    assign hpi_rst_n = cy_i_rst_n;

    CY7C67200_IF cy_if (
        .iDATA({16'h0000, write_data}),
        .oDATA(cy_o_data),
        .iADDR(latched_adr[1:0]),
        .iRD_N((hpi_access & ~latched_we) ? 1'b0 : 1'b1),
        .iWR_N((hpi_access &  latched_we) ? 1'b0 : 1'b1),
        .iCS_N(~hpi_access),
        .iRST_N(cy_i_rst_n),
        .iCLK(clk),
        .oINT(cy_o_int),
        .HPI_DATA(hpi_data),
        .HPI_ADDR(),
        .HPI_RD_N(),
        .HPI_WR_N(),
        .HPI_CS_N(),
        .HPI_RST_N(),
        .HPI_INT(1'b0)
    );

    reg [159:0] diag_probe_reg = 160'd0;
    reg         diag_captured = 1'b0;

    always @(posedge clk) begin
        if (active && count == 6'd10 && !diag_captured) begin
            diag_probe_reg <= {
                8'd0, hpi_access, rst, hpi_rst_n, wb_access, debug_access, active, debug_latched, latched_we, wb_we,
                state, count, hpi_cs_n, hpi_rd_n, hpi_wr_n, hpi_addr,
                1'b0, 1'b0, 1'b0, 2'b0,
                wb_ack, 3'b000, latched_adr[9:0], write_data, read_data,
                sample_data, last_sample_data, cy_o_data[15:0], hpi_data, wb_dat_w[15:0]
            };
            diag_captured <= 1'b1;
        end
        if (diag_source[0]) begin
            diag_captured <= 1'b0;
        end
    end

    wire [159:0] diag_probe_mux = diag_captured ? diag_probe_reg : {
        8'd0, hpi_access, rst, hpi_rst_n, wb_access, debug_access, active, debug_latched, latched_we, wb_we,
        state, count, hpi_cs_n, hpi_rd_n, hpi_wr_n, hpi_addr,
        1'b0, 1'b0, 1'b0, 2'b0,
        wb_ack, 3'b000, latched_adr[9:0], write_data, read_data,
        sample_data, last_sample_data, cy_o_data[15:0], hpi_data, wb_dat_w[15:0]
    };

    altsource_probe #(
        .sld_auto_instance_index("YES"),
        .sld_instance_index(0),
        .instance_id("HPI0"),
        .probe_width(160),
        .source_width(1),
        .source_initial_value("0")
    ) hpi_probe (
        .probe(diag_probe_mux),
        .source(diag_source)
    );

    assign dbg_probe = diag_probe_mux;

    always @(*) begin
        if (debug_access) begin
            case (debug_index)
            2'd0: wb_dat_r = {12'd0, cfg_turnaround_cycles, cfg_sample_offset, cfg_access_cycles, cfg_hpi_rst_n, cfg_force_rst_en};
            2'd1: wb_dat_r = last_ctrl;
            2'd2: wb_dat_r = {16'h0000, last_sample_data};
            2'd3: wb_dat_r = {16'h0000, last_cy_data};
            default: wb_dat_r = 32'd0;
            endcase
        end else begin
            wb_dat_r = {16'h0000, read_data};
        end
    end

    always @(posedge clk) begin
        wb_ack <= 1'b0;
        sample_data <= hpi_data;

        if (hpi_access) begin
            last_ctrl <= {4'd0, diag_source[0], rst, hpi_rst_n, active, debug_latched, latched_we,
                state, count, hpi_cs_n, hpi_rd_n, hpi_wr_n, hpi_addr,
                1'b0, 1'b0, 1'b0, 2'b0, 4'd0};
            last_sample_data <= hpi_data;
            last_cy_data <= cy_o_data[15:0];
        end

        if (rst) begin
            state         <= STATE_IDLE;
            count         <= 6'd0;
            read_data     <= 16'd0;
            write_data    <= 16'd0;
            latched_adr   <= 30'd0;
            latched_we    <= 1'b0;
            active        <= 1'b0;
            debug_latched <= 1'b0;
            cfg_force_rst_en <= 1'b0;
            cfg_hpi_rst_n <= 1'b1;
            cfg_access_cycles <= ACCESS_CYCLES_DEFAULT;
            cfg_sample_offset <= SAMPLE_OFFSET_DEFAULT;
            cfg_turnaround_cycles <= TURNAROUND_CYCLES_DEFAULT;
        end else begin
            case (state)
            STATE_IDLE: begin
                count  <= 6'd0;
                active <= 1'b0;
                if (debug_access) begin
                    wb_ack <= 1'b1;
                    if (wb_we) begin
                        case (debug_index)
                        2'd0: begin
                            cfg_force_rst_en   <= wb_dat_w[0];
                            cfg_hpi_rst_n      <= wb_dat_w[1];
                            cfg_access_cycles  <= wb_dat_w[7:2];
                            cfg_sample_offset  <= wb_dat_w[13:8];
                            cfg_turnaround_cycles <= wb_dat_w[19:14];
                        end
                        default: begin
                        end
                        endcase
                    end
                end else if (wb_access) begin
                    latched_adr   <= wb_adr;
                    write_data    <= wb_dat_w[15:0];
                    latched_we    <= wb_we;
                    debug_latched <= 1'b0;
                    active        <= 1'b1;
                    state         <= STATE_WAIT;
                end
            end

            STATE_WAIT: begin
                active <= 1'b1;
                count <= count + 6'd1;
                if (!debug_latched && !latched_we && count >= sample_threshold) begin
                    read_data <= cy_o_data[15:0];
                end
                if (count == effective_access_cycles - 6'd1) begin
                    count <= 6'd0;
                    state <= STATE_ACK;
                end
            end

            STATE_ACK: begin
                wb_ack <= 1'b1;
                active <= 1'b0;
                state  <= STATE_TURNAROUND;
            end

            STATE_TURNAROUND: begin
                active <= 1'b0;
                count <= count + 6'd1;
                if (count == effective_turnaround_cycles - 6'd1 || !wb_access) begin
                    count <= 6'd0;
                    state <= STATE_IDLE;
                end
            end
            endcase
        end
    end
endmodule
