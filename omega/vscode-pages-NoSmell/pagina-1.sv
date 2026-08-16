module mux (
    input  logic [1:0] selector,
    input  logic       enable,
    output logic [7:0] out
);

    logic [7:0] decoded;

    always_comb begin
        case (selector)
            2'b00: decoded = 8'd10;
            2'b01: decoded = 8'd20;
            2'b10: decoded = 8'd30;
            2'b11: decoded = 8'd40;
            default: decoded = 8'd100;
        endcase

        if (enable)
            out = decoded;
        else
            out = 8'd0;
    end

endmodule

selector = 10; enable   = 1;
correct answer: out=30
