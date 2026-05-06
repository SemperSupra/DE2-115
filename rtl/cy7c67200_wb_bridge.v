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
    input  wire        hpi_int0,
    input  wire        hpi_int1,
    input  wire        hpi_dreq,
    input  wire [1:0]  diag_in,
    output wire [191:0] dbg_probe
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
    
    reg        cfg_force_rst_en = 1'b1;
    reg        cfg_hpi_rst_n = 1'b0;
    reg [5:0]  cfg_access_cycles = ACCESS_CYCLES_DEFAULT;
    reg [5:0]  cfg_sample_offset = SAMPLE_OFFSET_DEFAULT;
    reg [5:0]  cfg_turnaround_cycles = TURNAROUND_CYCLES_DEFAULT;
    reg        manual_force_en = 1'b0;
    reg [1:0]  manual_addr = 2'd0;
    reg        manual_rd_n = 1'b1;
    reg        manual_wr_n = 1'b1;
    reg        manual_cs_n = 1'b1;
    reg [15:0] manual_data = 16'd0;

    wire       wb_access = wb_cyc & wb_stb;
    // LiteX passes the absolute Wishbone word address. Decode only the local
    // low bits inside the 64 KiB USB window.
    wire [13:0] local_adr = wb_adr[13:0];
    // Map HPI registers to contiguous words (offsets 0, 1, 2, 3).
    // Map debug registers to anything above local word address 0x3F.
    wire       debug_access = wb_access & (local_adr[13:6] != 8'd0);
    wire [1:0] bus_hpi_addr = local_adr[1:0];
    wire [2:0] debug_index = local_adr[2:0];
    wire       hpi_access = active & ~debug_latched;
    wire [1:0] cy_if_addr = manual_force_en ? manual_addr : latched_adr[1:0];
    wire       cy_if_rd_n = manual_force_en ? manual_rd_n : ((hpi_access & ~latched_we) ? 1'b0 : 1'b1);
    wire       cy_if_wr_n = manual_force_en ? manual_wr_n : ((hpi_access &  latched_we) ? 1'b0 : 1'b1);
    wire       cy_if_cs_n = manual_force_en ? manual_cs_n : ~hpi_access;
    wire [15:0] cy_if_write_data = manual_force_en ? manual_data : write_data;
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
    wire [3:0] diag_source;

    CY7C67200_IF cy_if (
        .iDATA({16'h0000, cy_if_write_data}),
        .oDATA(cy_o_data),
        .iADDR(cy_if_addr),
        .iRD_N(cy_if_rd_n),
        .iWR_N(cy_if_wr_n),
        .iCS_N(cy_if_cs_n),
        .iRST_N(cy_i_rst_n),
        .iFPGA_RST(rst),
        .iCLK(clk),
        .oINT(cy_o_int),
        .HPI_DATA(hpi_data),
        .HPI_ADDR(hpi_addr),
        .HPI_RD_N(hpi_rd_n),
        .HPI_WR_N(hpi_wr_n),
        .HPI_CS_N(hpi_cs_n),
        .HPI_RST_N(hpi_rst_n),
        .HPI_INT(hpi_int1)
    );

    wire [2:0] diag_capture_mode = diag_source[3:1];
    wire [5:0] diag_capture_count =
        latched_we ? 6'd10 : sample_threshold;
    wire       diag_capture_match =
        (diag_capture_mode == 3'd0) |
        ((diag_capture_mode == 3'd1) & ~latched_we & (hpi_addr == 2'd0)) |
        ((diag_capture_mode == 3'd2) &  latched_we & (hpi_addr == 2'd0)) |
        ((diag_capture_mode == 3'd3) & ~latched_we & (hpi_addr == 2'd3)) |
        ((diag_capture_mode == 3'd4) &  latched_we & (hpi_addr == 2'd2)) |
        ((diag_capture_mode == 3'd5) & ~latched_we & (hpi_addr == 2'd1)) |
        ((diag_capture_mode == 3'd6) &  latched_we & (hpi_addr == 2'd1)) |
        ((diag_capture_mode == 3'd7) &  latched_we & (hpi_addr == 2'd3));

    reg [191:0] diag_probe_reg = 192'd0;
    reg         diag_captured = 1'b0;

    wire [191:0] diag_probe_live = {
        1'b0, cy_o_int, cfg_turnaround_cycles, cfg_access_cycles, cfg_sample_offset,
        effective_access_cycles, sample_threshold,
        diag_captured, diag_capture_match, diag_source, diag_in, hpi_int0, hpi_int1, hpi_dreq,
        hpi_access, rst, hpi_rst_n, wb_access, debug_access, active, debug_latched, latched_we, wb_we,
        hpi_cs_n, hpi_rd_n, hpi_wr_n, hpi_addr, state, count, wb_ack,
        local_adr, write_data, read_data, sample_data, last_sample_data,
        cy_o_data[15:0], hpi_data, wb_dat_w[15:0]
    };

    always @(posedge clk) begin
        if (active && !diag_captured && diag_capture_match && count == diag_capture_count) begin
            diag_probe_reg <= diag_probe_live | (192'd1 << 159);
            diag_captured <= 1'b1;
        end
        if (diag_source[0]) begin
            diag_captured <= 1'b0;
        end
    end

    wire [191:0] diag_probe_mux = diag_captured ? diag_probe_reg : diag_probe_live;

    altsource_probe #(
        .sld_auto_instance_index("YES"),
        .sld_instance_index(0),
        .instance_id("HPI0"),
        .probe_width(192),
        .source_width(4),
        .source_initial_value("0")
    ) hpi_probe (
        .probe(diag_probe_mux),
        .source(diag_source)
    );

    assign dbg_probe = diag_probe_mux;

`ifdef HPI_PIN_SIGNALTAP
    wire [68:0] hpi_stp_data = {
        1'b0, cy_o_int, hpi_int0, hpi_int1, hpi_dreq, rst, hpi_rst_n,
        hpi_access, active, latched_we, wb_we, hpi_cs_n, hpi_rd_n, hpi_wr_n,
        hpi_addr, state, count, write_data, cy_o_data[15:0], hpi_data
    };

    sld_signaltap #(
        .SLD_DATA_BITS(69),
        .SLD_TRIGGER_BITS(1),
        .SLD_STORAGE_QUALIFIER_BITS(1),
        .SLD_SAMPLE_DEPTH(256),
        .SLD_MEM_ADDRESS_BITS(8),
        .SLD_DATA_BIT_CNTR_BITS(7),
        .SLD_TRIGGER_LEVEL(1),
        .SLD_TRIGGER_LEVEL_PIPELINE(1),
        .SLD_RAM_BLOCK_TYPE("M4K"),
        .SLD_SECTION_ID("hpi_pin_signaltap"),
        .SLD_NODE_INFO(0),
        .SLD_NODE_CRC_BITS(32),
        .SLD_NODE_CRC_LOWORD(16'h6720),
        .SLD_NODE_CRC_HIWORD(16'h2026)
    ) hpi_pin_signaltap (
        .acq_clk(clk),
        .acq_data_in(hpi_stp_data),
        .acq_trigger_in({~hpi_rd_n}),
        .acq_storage_qualifier_in({1'b1}),
        .storage_enable(1'b1),
        .trigger_in(1'b0)
    );
`endif

    always @(*) begin
        if (debug_access) begin
            case (debug_index)
            3'd0: wb_dat_r = {12'd0, cfg_turnaround_cycles, cfg_sample_offset, cfg_access_cycles, cfg_hpi_rst_n, cfg_force_rst_en};
            3'd1: wb_dat_r = last_ctrl;
            3'd2: wb_dat_r = {16'h0000, last_sample_data};
            3'd3: wb_dat_r = {16'h0000, last_cy_data};
            3'd4: wb_dat_r = {24'd0, manual_addr, manual_cs_n, manual_wr_n, manual_rd_n, manual_force_en};
            3'd5: wb_dat_r = {16'h0000, manual_data};
            3'd6: wb_dat_r = {16'h0000, hpi_data};
            3'd7: wb_dat_r = {16'h0000, cy_o_data[15:0]};
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
            cfg_force_rst_en <= 1'b1;
            cfg_hpi_rst_n <= 1'b0;
            cfg_access_cycles <= ACCESS_CYCLES_DEFAULT;
            cfg_sample_offset <= SAMPLE_OFFSET_DEFAULT;
            cfg_turnaround_cycles <= TURNAROUND_CYCLES_DEFAULT;
            manual_force_en <= 1'b0;
            manual_addr <= 2'd0;
            manual_rd_n <= 1'b1;
            manual_wr_n <= 1'b1;
            manual_cs_n <= 1'b1;
            manual_data <= 16'd0;
        end else begin
            case (state)
            STATE_IDLE: begin
                count  <= 6'd0;
                active <= 1'b0;
                if (debug_access) begin
                    wb_ack <= 1'b1;
                    if (wb_we) begin
                        case (debug_index)
                        3'd0: begin
                            cfg_force_rst_en   <= wb_dat_w[0];
                            cfg_hpi_rst_n      <= wb_dat_w[1];
                            cfg_access_cycles  <= wb_dat_w[7:2];
                            cfg_sample_offset  <= wb_dat_w[13:8];
                            cfg_turnaround_cycles <= wb_dat_w[19:14];
                        end
                        3'd4: begin
                            manual_force_en <= wb_dat_w[0];
                            manual_rd_n     <= wb_dat_w[1];
                            manual_wr_n     <= wb_dat_w[2];
                            manual_cs_n     <= wb_dat_w[3];
                            manual_addr     <= wb_dat_w[5:4];
                        end
                        3'd5: begin
                            manual_data <= wb_dat_w[15:0];
                        end
                        default: begin
                        end
                        endcase
                    end
                end else if (wb_access) begin
                    latched_adr   <= {28'd0, bus_hpi_addr};
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
