///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module mux (
    input logic [1:0] selector,
    output logic [7:0] out
);
    always_comb begin
        case (selector)
            2'b00: out = 8'd10;
            2'b01: out = 8'd20;
            2'b10: out = 8'd30;
            2'b11: out = 8'd40;
        endcase
    end
endmodule
