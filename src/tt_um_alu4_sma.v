// TinyTapeout wrapper — maps tt_um 8-bit IO to internal 4-bit ALU
// Pin mapping:
//   ui_in[3:0]  = A[3:0]
//   ui_in[7:4]  = B[3:0]
//   uio_in[3:0] = S[3:0]  (function select)
//   uio_in[4]   = M        (mode)
//   uio_in[5]   = CIN      (carry-in)
//   uo_out[3:0] = F[3:0]
//   uo_out[4]   = COUT
//   uo_out[5]   = P
//   uo_out[6]   = G
`default_nettype none

module tt_um_alu4_sma (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    wire [3:0] F;
    wire       COUT, P, G;

    alu_4bit core (
        .A   (ui_in[3:0]),
        .B   (ui_in[7:4]),
        .S   (uio_in[3:0]),
        .M   (uio_in[4]),
        .CIN (uio_in[5]),
        .F   (F),
        .COUT(COUT),
        .P   (P),
        .G   (G)
    );

    assign uo_out  = {1'b0, G, P, COUT, F};
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    wire _unused = &{ena, clk, rst_n, uio_in[7:6]};
endmodule
