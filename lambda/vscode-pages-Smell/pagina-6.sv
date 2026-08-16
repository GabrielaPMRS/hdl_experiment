module example (
    input  logic [3:0] instruction,
    output logic [2:0] opcode
);

    always_comb begin
        casex (instruction)

            4'b0???:
                opcode = 3'b001;

            4'b1000:
                opcode = 3'b010;

            default:
                opcode = 3'b111;

        endcase
    end

endmodule

correct answer:
instruction = 4'bxxxx
opcode = 3'b001
