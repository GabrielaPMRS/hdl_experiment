module example (
    input  logic [3:0] instruction,
    output logic [2:0] opcode
);

    always_comb begin
        if (instruction ==? 4'b00??)
            opcode = 3'b001;

        else if (instruction ==? 4'b0???)
            opcode = 3'b001;

        else
            opcode = 3'b111;
    end
endmodule

// Gabarito: instruction = 4'b0x01 -> opcode = 3'b001
