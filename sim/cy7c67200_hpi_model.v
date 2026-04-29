`timescale 1ns/1ps

module cy7c67200_hpi_model (
    input  wire        clk,
    input  wire        rst,
    inout  wire [15:0] hpi_data,
    input  wire [1:0]  hpi_addr,
    input  wire        hpi_cs_n,
    input  wire        hpi_rd_n,
    input  wire        hpi_wr_n,
    input  wire        hpi_rst_n,
    output reg         hpi_int
);
    reg [15:0] mem [0:32767];
    reg [15:0] addr_latch;
    reg [15:0] mailbox;
    reg [15:0] status;
    reg [15:0] data_out;
    reg        drive;

    assign hpi_data = drive ? data_out : 16'hzzzz;

    integer i;

    initial begin
        for (i = 0; i < 32768; i = i + 1) mem[i] = 16'h0000;
        mem[16'hc004 >> 1] = 16'h00a1;
        mem[16'hc008 >> 1] = 16'h0000;
        mem[16'hc00a >> 1] = 16'h0001;
        addr_latch = 0;
        mailbox = 0;
        status = 0;
        data_out = 0;
        drive = 0;
        hpi_int = 0;
    end

    always @(negedge hpi_rst_n or posedge rst) begin
        if (rst || !hpi_rst_n) begin
            addr_latch <= 16'h0000;
            mailbox <= 16'h0000;
            status <= 16'h0000;
            hpi_int <= 1'b0;
            mem[16'hc004 >> 1] <= 16'h00a1;
            mem[16'hc008 >> 1] <= 16'h0000;
            mem[16'hc00a >> 1] <= 16'h0001;
        end
    end

    always @(*) begin
        drive = 1'b0;
        data_out = 16'h0000;
        if (!hpi_cs_n && !hpi_rd_n && hpi_wr_n && hpi_rst_n) begin
            drive = 1'b1;
            case (hpi_addr)
                2'b00: data_out = mem[addr_latch[15:1]];
                2'b01: data_out = mailbox;
                2'b10: data_out = addr_latch;
                2'b11: data_out = status;
            endcase
        end
    end

    always @(posedge hpi_wr_n) begin
        if (!hpi_cs_n && hpi_rst_n) begin
            case (hpi_addr)
                2'b00: begin
                    mem[addr_latch[15:1]] <= hpi_data;
                    addr_latch <= addr_latch + 16'd2;
                end
                2'b01: begin
                    mailbox <= hpi_data;
                    status[0] <= 1'b1;
                    hpi_int <= 1'b1;
                end
                2'b10: addr_latch <= hpi_data;
                2'b11: status <= hpi_data;
            endcase
        end
    end

    always @(posedge hpi_rd_n) begin
        if (!hpi_cs_n && hpi_rst_n) begin
            if (hpi_addr == 2'b00) begin
                addr_latch <= addr_latch + 16'd2;
            end
            if (hpi_addr == 2'b01) begin
                status[0] <= 1'b0;
                hpi_int <= 1'b0;
            end
        end
    end
endmodule
