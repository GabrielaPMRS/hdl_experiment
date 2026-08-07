///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module mux (
    input logic [1:0] selector,
    output logic [7:0] out
);
    always_comb begin
        case (selector)
            0: out = 8'd10;
            01: out = 8'd20;
            10: out = 8'd30;
            2: out = 8'd40;
        endcase
    end
endmodule
