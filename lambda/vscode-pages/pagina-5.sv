///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module example;

    int lo, med, hi;
    bit result;

    initial begin
        lo = 20;
        med = 135;
        hi = 347;

        result = lo < med < hi;
    end

endmodule
