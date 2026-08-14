///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module testbench;

    logic [3:0] instruction;
    logic [2:0] opcode;

    always_comb begin
        case (instruction) inside

            4'b0???:
                opcode = 3'b001;

            4'b1000:
                opcode = 3'b010;

            default:
                opcode = 3'b111;

        endcase
    end
endmodule
