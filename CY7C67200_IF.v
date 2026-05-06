module CY7C67200_IF(
    input  wire [31:0] iDATA,
    output reg  [31:0] oDATA,
    input  wire [1:0]  iADDR,
    input  wire        iRD_N,
    input  wire        iWR_N,
    input  wire        iCS_N,
    input  wire        iRST_N,
    input  wire        iFPGA_RST,
    input  wire        iCLK,
    output reg         oINT,
    inout  wire [15:0] HPI_DATA,
    output reg  [1:0]  HPI_ADDR,
    output reg         HPI_RD_N,
    output reg         HPI_WR_N,
    output reg         HPI_CS_N,
    output wire        HPI_RST_N,
    input  wire        HPI_INT
);

    reg [15:0] tmp_data = 16'd0;

    assign HPI_RST_N = iRST_N;
    assign HPI_DATA = HPI_WR_N ? 16'hzzzz : tmp_data;

    always @(posedge iCLK) begin
        if (iFPGA_RST) begin
            tmp_data <= 16'd0;
            HPI_ADDR <= 2'd0;
            HPI_RD_N <= 1'b1;
            HPI_WR_N <= 1'b1;
            HPI_CS_N <= 1'b1;
            oDATA    <= 32'd0;
            oINT     <= 1'b0;
        end else begin
            oDATA    <= {16'h0000, HPI_DATA};
            oINT     <= HPI_INT;
            tmp_data <= iDATA[15:0];
            HPI_ADDR <= iADDR;
            HPI_RD_N <= iRD_N;
            HPI_WR_N <= iWR_N;
            HPI_CS_N <= iCS_N;
        end
    end

endmodule
