module vga_text_console (
    input              sys_clk,
    input              sys_rst,

    input      [13:0]  wb_adr,
    input      [31:0]  wb_dat_w,
    output reg [31:0]  wb_dat_r,
    input              wb_cyc,
    input              wb_stb,
    input              wb_we,
    output reg         wb_ack,

    input              vga_clk,
    output reg  [7:0]  vga_r,
    output reg  [7:0]  vga_g,
    output reg  [7:0]  vga_b,
    output             vga_blank_n,
    output             vga_hsync_n,
    output             vga_vsync_n
);
    localparam H_ACTIVE = 640;
    localparam H_FP     = 16;
    localparam H_SYNC   = 96;
    localparam H_BP     = 48;
    localparam H_TOTAL  = H_ACTIVE + H_FP + H_SYNC + H_BP;

    localparam V_ACTIVE = 480;
    localparam V_FP     = 10;
    localparam V_SYNC   = 2;
    localparam V_BP     = 33;
    localparam V_TOTAL  = V_ACTIVE + V_FP + V_SYNC + V_BP;

    reg [7:0] text_ram [0:2399];
    integer i;

    initial begin
        for (i = 0; i < 2400; i = i + 1)
            text_ram[i] = 8'h20;
    end

    wire wb_access = wb_cyc & wb_stb;
    wire [11:0] wb_cell = wb_adr[11:0];

    always @(posedge sys_clk) begin
        if (sys_rst) begin
            wb_ack <= 1'b0;
        end else begin
            wb_ack <= wb_access & ~wb_ack;
            if (wb_access & wb_we & ~wb_ack & (wb_cell < 2400))
                text_ram[wb_cell] <= wb_dat_w[7:0];
            if (wb_cell < 2400)
                wb_dat_r <= {24'h000000, text_ram[wb_cell]};
            else
                wb_dat_r <= 32'h00000000;
        end
    end

    reg [10:0] h_cnt = 0;
    reg [10:0] v_cnt = 0;

    always @(posedge vga_clk) begin
        if (h_cnt == H_TOTAL - 1) begin
            h_cnt <= 0;
            if (v_cnt == V_TOTAL - 1)
                v_cnt <= 0;
            else
                v_cnt <= v_cnt + 1'b1;
        end else begin
            h_cnt <= h_cnt + 1'b1;
        end
    end

    wire display_on = (h_cnt < H_ACTIVE) && (v_cnt < V_ACTIVE);
    wire h_sync_active = (h_cnt >= H_ACTIVE + H_FP) && (h_cnt < H_ACTIVE + H_FP + H_SYNC);
    wire v_sync_active = (v_cnt >= V_ACTIVE + V_FP) && (v_cnt < V_ACTIVE + V_FP + V_SYNC);

    assign vga_blank_n = vga_hsync_n & vga_vsync_n;
    assign vga_hsync_n = ~h_sync_active;
    assign vga_vsync_n = ~v_sync_active;

    wire [6:0] text_col = h_cnt[9:3];
    wire [4:0] text_row = v_cnt[8:4];
    wire [11:0] text_index = {text_row, 6'b0} + {text_row, 4'b0} + text_col;
    wire [11:0] safe_text_index = display_on ? text_index : 12'd0;
    wire [7:0] text_char = text_ram[safe_text_index];
    wire [7:0] glyph_bits = font_row(text_char, v_cnt[3:0]);
    wire glyph_pixel = glyph_bits[7 - h_cnt[2:0]];
    wire header_row = text_row == 0 || text_row == 1;
    wire border_pixel = (h_cnt < 8) || (h_cnt >= H_ACTIVE - 8) ||
                        (v_cnt < 8) || (v_cnt >= V_ACTIVE - 8);

    always @(posedge vga_clk) begin
        if (!display_on) begin
            vga_r <= 8'h00;
            vga_g <= 8'h00;
            vga_b <= 8'h00;
        end else if (border_pixel) begin
            vga_r <= 8'hff;
            vga_g <= 8'hff;
            vga_b <= 8'hff;
        end else if (glyph_pixel) begin
            vga_r <= header_row ? 8'hff : 8'hc0;
            vga_g <= 8'hff;
            vga_b <= header_row ? 8'hff : 8'hc0;
        end else begin
            vga_r <= h_cnt[7] ? 8'h10 : 8'h00;
            vga_g <= header_row ? 8'h20 : 8'h08;
            vga_b <= v_cnt[7] ? 8'h20 : 8'h08;
        end
    end

    function [7:0] font_row;
        input [7:0] ch;
        input [3:0] row;
        reg [2:0] r;
        begin
            r = row[3:1];
            font_row = 8'h00;
            case (ch)
            8'h20: font_row = 8'h00;
            8'h2d: font_row = (r == 3) ? 8'h7c : 8'h00;
            8'h2f: begin case (r) 0: font_row=8'h04; 1: font_row=8'h08; 2: font_row=8'h10; 3: font_row=8'h20; 4: font_row=8'h40; default: font_row=8'h00; endcase end
            8'h3a: font_row = (r == 2 || r == 5) ? 8'h18 : 8'h00;
            8'h5f: font_row = (r == 7) ? 8'h7e : 8'h00;
            8'h7c: font_row = 8'h18;
            8'h30: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h6e; 3: font_row=8'h76; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h31: begin case (r) 0: font_row=8'h18; 1: font_row=8'h38; 2: font_row=8'h18; 3: font_row=8'h18; 4: font_row=8'h18; 5: font_row=8'h18; 6: font_row=8'h7e; default: font_row=8'h00; endcase end
            8'h32: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h06; 3: font_row=8'h1c; 4: font_row=8'h30; 5: font_row=8'h60; 6: font_row=8'h7e; default: font_row=8'h00; endcase end
            8'h33: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h06; 3: font_row=8'h1c; 4: font_row=8'h06; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h34: begin case (r) 0: font_row=8'h0c; 1: font_row=8'h1c; 2: font_row=8'h3c; 3: font_row=8'h6c; 4: font_row=8'h7e; 5: font_row=8'h0c; 6: font_row=8'h0c; default: font_row=8'h00; endcase end
            8'h35: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h60; 2: font_row=8'h7c; 3: font_row=8'h06; 4: font_row=8'h06; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h36: begin case (r) 0: font_row=8'h1c; 1: font_row=8'h30; 2: font_row=8'h60; 3: font_row=8'h7c; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h37: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h06; 2: font_row=8'h0c; 3: font_row=8'h18; 4: font_row=8'h30; 5: font_row=8'h30; 6: font_row=8'h30; default: font_row=8'h00; endcase end
            8'h38: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h3c; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h39: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h3e; 4: font_row=8'h06; 5: font_row=8'h0c; 6: font_row=8'h38; default: font_row=8'h00; endcase end
            8'h41, 8'h61: begin case (r) 0: font_row=8'h18; 1: font_row=8'h3c; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h7e; 5: font_row=8'h66; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h42, 8'h62: begin case (r) 0: font_row=8'h7c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h7c; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h7c; default: font_row=8'h00; endcase end
            8'h43, 8'h63: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h60; 3: font_row=8'h60; 4: font_row=8'h60; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h44, 8'h64: begin case (r) 0: font_row=8'h78; 1: font_row=8'h6c; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h66; 5: font_row=8'h6c; 6: font_row=8'h78; default: font_row=8'h00; endcase end
            8'h45, 8'h65: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h60; 2: font_row=8'h60; 3: font_row=8'h7c; 4: font_row=8'h60; 5: font_row=8'h60; 6: font_row=8'h7e; default: font_row=8'h00; endcase end
            8'h46, 8'h66: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h60; 2: font_row=8'h60; 3: font_row=8'h7c; 4: font_row=8'h60; 5: font_row=8'h60; 6: font_row=8'h60; default: font_row=8'h00; endcase end
            8'h47, 8'h67: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h60; 3: font_row=8'h6e; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h48, 8'h68: begin case (r) 0: font_row=8'h66; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h7e; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h49, 8'h69: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h18; 2: font_row=8'h18; 3: font_row=8'h18; 4: font_row=8'h18; 5: font_row=8'h18; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h4a, 8'h6a: begin case (r) 0: font_row=8'h1e; 1: font_row=8'h0c; 2: font_row=8'h0c; 3: font_row=8'h0c; 4: font_row=8'h0c; 5: font_row=8'h6c; 6: font_row=8'h38; default: font_row=8'h00; endcase end
            8'h4b, 8'h6b: begin case (r) 0: font_row=8'h66; 1: font_row=8'h6c; 2: font_row=8'h78; 3: font_row=8'h70; 4: font_row=8'h78; 5: font_row=8'h6c; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h4c, 8'h6c: begin case (r) 0: font_row=8'h60; 1: font_row=8'h60; 2: font_row=8'h60; 3: font_row=8'h60; 4: font_row=8'h60; 5: font_row=8'h60; 6: font_row=8'h7e; default: font_row=8'h00; endcase end
            8'h4d, 8'h6d: begin case (r) 0: font_row=8'h63; 1: font_row=8'h77; 2: font_row=8'h7f; 3: font_row=8'h6b; 4: font_row=8'h63; 5: font_row=8'h63; 6: font_row=8'h63; default: font_row=8'h00; endcase end
            8'h4e, 8'h6e: begin case (r) 0: font_row=8'h66; 1: font_row=8'h76; 2: font_row=8'h7e; 3: font_row=8'h7e; 4: font_row=8'h6e; 5: font_row=8'h66; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h4f, 8'h6f: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h50, 8'h70: begin case (r) 0: font_row=8'h7c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h7c; 4: font_row=8'h60; 5: font_row=8'h60; 6: font_row=8'h60; default: font_row=8'h00; endcase end
            8'h51, 8'h71: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h6e; 5: font_row=8'h3c; 6: font_row=8'h0e; default: font_row=8'h00; endcase end
            8'h52, 8'h72: begin case (r) 0: font_row=8'h7c; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h7c; 4: font_row=8'h78; 5: font_row=8'h6c; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h53, 8'h73: begin case (r) 0: font_row=8'h3c; 1: font_row=8'h66; 2: font_row=8'h60; 3: font_row=8'h3c; 4: font_row=8'h06; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h54, 8'h74: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h18; 2: font_row=8'h18; 3: font_row=8'h18; 4: font_row=8'h18; 5: font_row=8'h18; 6: font_row=8'h18; default: font_row=8'h00; endcase end
            8'h55, 8'h75: begin case (r) 0: font_row=8'h66; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h66; 5: font_row=8'h66; 6: font_row=8'h3c; default: font_row=8'h00; endcase end
            8'h56, 8'h76: begin case (r) 0: font_row=8'h66; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h66; 4: font_row=8'h66; 5: font_row=8'h3c; 6: font_row=8'h18; default: font_row=8'h00; endcase end
            8'h57, 8'h77: begin case (r) 0: font_row=8'h63; 1: font_row=8'h63; 2: font_row=8'h63; 3: font_row=8'h6b; 4: font_row=8'h7f; 5: font_row=8'h77; 6: font_row=8'h63; default: font_row=8'h00; endcase end
            8'h58, 8'h78: begin case (r) 0: font_row=8'h66; 1: font_row=8'h66; 2: font_row=8'h3c; 3: font_row=8'h18; 4: font_row=8'h3c; 5: font_row=8'h66; 6: font_row=8'h66; default: font_row=8'h00; endcase end
            8'h59, 8'h79: begin case (r) 0: font_row=8'h66; 1: font_row=8'h66; 2: font_row=8'h66; 3: font_row=8'h3c; 4: font_row=8'h18; 5: font_row=8'h18; 6: font_row=8'h18; default: font_row=8'h00; endcase end
            8'h5a, 8'h7a: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h06; 2: font_row=8'h0c; 3: font_row=8'h18; 4: font_row=8'h30; 5: font_row=8'h60; 6: font_row=8'h7e; default: font_row=8'h00; endcase end
            default: begin case (r) 0: font_row=8'h7e; 1: font_row=8'h42; 2: font_row=8'h5a; 3: font_row=8'h5a; 4: font_row=8'h42; 5: font_row=8'h7e; default: font_row=8'h00; endcase end
            endcase
        end
    endfunction
endmodule
