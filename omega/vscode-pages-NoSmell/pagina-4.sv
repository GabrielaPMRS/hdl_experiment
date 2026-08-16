module example (
    input  logic enable,
    output int   out
);
    int result;
    byte in = -5;

    always_comb begin
        result = in + 1;

        if (enable)
            out = result;
        else
            out = in;
    end
endmodule

correct answer: enable=1 -> out=-4
