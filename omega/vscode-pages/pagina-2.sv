///////////////////////////////////////////////////////////////////////////////
// CLIQUE EM "INICIAR PERGUNTA" ANTES DE ANALISAR O CODIGO
///////////////////////////////////////////////////////////////////////////////

module top(output logic [1:0][31:0] A);
    initial begin
        A[0] = 1'b1;
        A[1] = 1'b1;
    end
endmodule

module tb;
...
$display("A[0] = %b", A[0]);
$display("A[1] = %b", A[1]);
...
