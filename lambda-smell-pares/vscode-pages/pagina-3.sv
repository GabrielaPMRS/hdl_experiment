///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module testbench;

    function int maxx(int a, int b);
        int max = a;
        if (b > max)
            max = b;
        return max;
    endfunction

    initial begin
        int r1, r2, r3;

        r1 = maxx(3, 7);
        r2 = maxx(1, 2);
        r3 = maxx(0, 0);
    end

endmodule
