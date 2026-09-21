module top (
    output logic [31:0] out0,
    output logic [31:0] out1
);

    logic [1:0][31:0] A;

    initial begin
        A[0] = 2'b11;
        A[1] = 2'b00;

        out0 = A[0];
        out1 = A[1];
    end

endmodule

// Gabarito: out0 = 00000000000000000000000000000011; out1 = 00000000000000000000000000000000
