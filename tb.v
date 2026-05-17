
`timescale 1ns/1ps

module tb;
    reg clk;
    reg rst;
    
    reg [29:0] wb_adr;
    reg [31:0] wb_dat_w;
    wire [31:0] wb_dat_r;
    reg wb_cyc;
    reg wb_stb;
    reg wb_we;
    wire wb_ack;

    wire [15:0] hpi_data;
    wire [1:0] hpi_addr;
    wire hpi_rd_n;
    wire hpi_wr_n;
    wire hpi_cs_n;
    wire hpi_rst_n;
    
    assign hpi_data = (hpi_wr_n == 0) ? 16'bz : 16'h1234;

    cy7c67200_wb_bridge dut (
        .clk(clk),
        .rst(rst),
        .wb_adr(wb_adr),
        .wb_dat_w(wb_dat_w),
        .wb_dat_r(wb_dat_r),
        .wb_cyc(wb_cyc),
        .wb_stb(wb_stb),
        .wb_we(wb_we),
        .wb_ack(wb_ack),
        .hpi_data(hpi_data),
        .hpi_addr(hpi_addr),
        .hpi_rd_n(hpi_rd_n),
        .hpi_wr_n(hpi_wr_n),
        .hpi_cs_n(hpi_cs_n),
        .hpi_rst_n(hpi_rst_n),
        .hpi_int0(1'b0),
        .hpi_int1(1'b0),
        .hpi_dreq(1'b0),
        .diag_in(2'b0),
        .dbg_probe()
    );

    always #5 clk = ~clk;
    initial begin
        $dumpfile("tb.vcd");
        $dumpvars(0, tb);
    end

    initial begin
        clk = 0;
        rst = 1;
        wb_adr = 0;
        wb_dat_w = 0;
        wb_cyc = 0;
        wb_stb = 0;
        wb_we = 0;
        
        #20 rst = 0;
        
        // Wait a bit
        #20;
        
        // Perform a read
        wb_adr = 30'h00000000;
        wb_cyc = 1;
        wb_stb = 1;
        wb_we = 0;
        
        wait(wb_ack == 1);
        wb_cyc = 0;
        wb_stb = 0;
        
        #100;
        $display("PASS test_hpi_sim");
        $finish;
    end
    
    // Monitor for setup/hold violations
    always @(negedge hpi_rd_n) begin
        if ($time > 10) begin
        if (hpi_cs_n !== 0) begin
            $display("ERROR: hpi_rd_n fell but hpi_cs_n is not low!");
            $finish;
        end
        end
    end
    always @(posedge hpi_rd_n) begin
        if ($time > 10) begin
        #1;
        if (hpi_cs_n !== 0) begin
            $display("ERROR: hpi_rd_n rose but hpi_cs_n is not low (hold violation)!");
            $finish;
        end
        end
    end
    
    always @(negedge hpi_cs_n) begin
        if ($time > 10) begin
        if (hpi_rd_n !== 1 && hpi_wr_n !== 1) begin
            $display("ERROR: hpi_cs_n fell but read/write strobes are already low!");
            $finish;
        end
        end
    end
    
    always @(posedge hpi_cs_n) begin
        if ($time > 10) begin
        if (hpi_rd_n !== 1 && hpi_wr_n !== 1) begin
            $display("ERROR: hpi_cs_n rose but read/write strobes are still low!");
            $finish;
        end
        end
    end

endmodule
