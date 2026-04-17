module CY7C67200_IF(
    input  wire [31:0] iDATA,
    output wire [31:0] oDATA,
    input  wire [1:0]  iADDR,
    input  wire        iRD_N,
    input  wire        iWR_N,
    input  wire        iCS_N,
    input  wire        iRST_N,
    input  wire        iCLK,
    output wire        oINT,
    inout  wire [15:0] HPI_DATA,
    output wire [1:0]  HPI_ADDR,
    output wire        HPI_RD_N,
    output wire        HPI_WR_N,
    output wire        HPI_CS_N,
    output wire        HPI_RST_N,
    input  wire        HPI_INT
);

    assign HPI_RST_N = iRST_N;
    assign HPI_CS_N  = iCS_N;
    assign HPI_RD_N  = iRD_N;
    assign HPI_WR_N  = iWR_N;
    assign HPI_ADDR  = iADDR;
    assign oINT      = HPI_INT;
    
    assign HPI_DATA = iWR_N ? 16'hzzzz : iDATA[15:0];
    assign oDATA    = {16'h0000, HPI_DATA};

endmodule
