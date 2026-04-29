`timescale 1ns/1ps

module cy7c67200_hpi_model_tb;
    reg clk = 0;
    reg rst = 1;
    wire [15:0] hpi_data;
    reg [15:0] hpi_data_drv;
    reg hpi_data_oe;
    reg [1:0] hpi_addr;
    reg hpi_cs_n;
    reg hpi_rd_n;
    reg hpi_wr_n;
    reg hpi_rst_n;
    wire hpi_int;

    assign hpi_data = hpi_data_oe ? hpi_data_drv : 16'hzzzz;

    cy7c67200_hpi_model dut (
        .clk(clk),
        .rst(rst),
        .hpi_data(hpi_data),
        .hpi_addr(hpi_addr),
        .hpi_cs_n(hpi_cs_n),
        .hpi_rd_n(hpi_rd_n),
        .hpi_wr_n(hpi_wr_n),
        .hpi_rst_n(hpi_rst_n),
        .hpi_int(hpi_int)
    );

    always #5 clk = ~clk;

    task hpi_write;
        input [1:0] a;
        input [15:0] d;
        begin
            hpi_addr = a;
            hpi_data_drv = d;
            hpi_data_oe = 1;
            hpi_cs_n = 0;
            hpi_wr_n = 0;
            #20;
            hpi_wr_n = 1;
            #20;
            hpi_cs_n = 1;
            hpi_data_oe = 0;
            #20;
        end
    endtask

    task hpi_read;
        input [1:0] a;
        output [15:0] d;
        begin
            hpi_addr = a;
            hpi_data_oe = 0;
            hpi_cs_n = 0;
            hpi_rd_n = 0;
            #20;
            d = hpi_data;
            hpi_rd_n = 1;
            #20;
            hpi_cs_n = 1;
            #20;
        end
    endtask

    reg [15:0] r;

    initial begin
        hpi_data_drv = 0;
        hpi_data_oe = 0;
        hpi_addr = 0;
        hpi_cs_n = 1;
        hpi_rd_n = 1;
        hpi_wr_n = 1;
        hpi_rst_n = 0;

        #50 rst = 0;
        #50 hpi_rst_n = 1;

        hpi_write(2, 16'h1000);
        hpi_write(0, 16'h1234);

        hpi_write(2, 16'h1000);
        hpi_read(0, r);
        if (r !== 16'h1234) begin
            $display("FAIL ram readback got=%h", r);
            $finish;
        end

        hpi_write(2, 16'hc004);
        hpi_read(0, r);
        if (r !== 16'h00a1) begin
            $display("FAIL hwrev got=%h", r);
            $finish;
        end

        hpi_write(1, 16'hce04);
        hpi_read(3, r);
        if ((r & 16'h0001) == 0) begin
            $display("FAIL mailbox status got=%h", r);
            $finish;
        end

        $display("PASS cy7c67200_hpi_model_tb");
        $finish;
    end
endmodule
