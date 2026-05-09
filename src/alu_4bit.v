// 4-bit ALU slice modelled after 74181 — combinational logic and arithmetic operations
module alu_4bit (
    input  wire [3:0] A,
    input  wire [3:0] B,
    input  wire [3:0] S,      // function select
    input  wire       M,      // mode: 0=arithmetic, 1=logic
    input  wire       CIN,    // carry-in
    output reg  [3:0] F,      // result
    output reg        COUT,   // carry-out
    output wire       P,      // group propagate
    output wire       G       // group generate
);
    wire [3:0] p_i = A | B;
    wire [3:0] g_i = A & B;
    assign P = &p_i;
    assign G = |(g_i & {p_i[2:0], 1'b1});

    always @(*) begin
        if (M) begin
            // Logic mode — bitwise operations selected by S[1:0]
            case (S[1:0])
                2'b00: F = ~A;
                2'b01: F = ~(A | B);
                2'b10: F = (~A) & B;
                2'b11: F = 4'b0000;
            endcase
            COUT = 1'b0;
        end else begin
            // Arithmetic mode
            case (S[1:0])
                2'b00: {COUT, F} = {1'b0, A} + {1'b0, CIN};
                2'b01: {COUT, F} = {1'b0, A} + {1'b0, B} + {4'b0, CIN};
                2'b10: {COUT, F} = {1'b0, A} - {1'b0, B} - {4'b0, ~CIN};
                2'b11: {COUT, F} = {1'b0, A} - 5'd1 + {4'b0, CIN};
            endcase
        end
    end
endmodule
