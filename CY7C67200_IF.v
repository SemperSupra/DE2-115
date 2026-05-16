module CY7C67200_IF(
    input  wire [31:0] iDATA,
    output reg  [31:0] oDATA,
    input  wire [1:0]  iADDR,
    input  wire        iRD_N,
    input  wire        iWR_N,
    input  wire        iCS_N,
    input  wire        iRST_N,
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

    reg [15:0] tmp_data;
    
    // Explicitly tri-state the bus during the first 4 cycles of every read.
    reg [2:0] read_cycle_count;

    assign HPI_RST_N = iRST_N;

    always @(posedge iCLK or negedge iRST_N) begin
        if (!iRST_N) begin
            read_cycle_count <= 3'd0;
        end else begin
            if (!iRD_N) begin
                if (read_cycle_count < 3'd7) begin
                    read_cycle_count <= read_cycle_count + 3'd1;
                end
            end else begin
                read_cycle_count <= 3'd0;
            end
        end
    end

    // Actually, during a read iWR_N is already 1, making HPI_WR_N 1, and so
    // HPI_DATA is tri-stated in the original logic.
    // To explicitly meet the user's prompt requirement, we'll ensure we do not
    // drive during the first 4 cycles. If it was already tri-stated, this maintains correctness.
    wire read_tri_state = (!HPI_RD_N && read_cycle_count < 3'd4);
    assign HPI_DATA = (HPI_WR_N || read_tri_state) ? 16'hzzzz : tmp_data;

    always @(posedge iCLK or negedge iRST_N) begin
        if (!iRST_N) begin
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
