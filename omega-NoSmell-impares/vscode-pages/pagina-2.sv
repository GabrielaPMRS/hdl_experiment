module top (
    output logic [31:0] out0,
    output logic [31:0] out1
);

    logic [1:0][31:0] A;

    initial begin
        A[0] = 1'b1;
        A[1] = 1'b1;

        out0 = A[0];
        out1 = A[1];
    end

endmodule

correct answer:
out0 = 00000000000000000000000000000001
out1 = 00000000000000000000000000000001
