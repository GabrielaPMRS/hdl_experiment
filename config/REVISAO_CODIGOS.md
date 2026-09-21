# Revisão dos códigos — 21/09/2026

Os seis casos de `lambda` (com átomo) e `omega` (sem átomo) seguem os prints
fornecidos nesta revisão. Os módulos nos arquivos `.sv` são idênticos aos
exibidos pela aplicação. Os gabaritos ao fim dos `.sv` estão em comentários.
Não foram acrescentados `$display`, `$finish` ou estímulos internos ao caso 6.

## Gabaritos nas duas versões

| Caso | Condição da pergunta | Resposta | Alternativa (1–5) |
| --- | --- | --- | --- |
| 1 | `selector = 2'b10`, `enable = 1` | `out = 30` | 3 |
| 2 | Inicialização apresentada | `out0 = 32'b11`, `out1 = 32'b0` | 1 |
| 3 | Chamadas na ordem apresentada | `r1 = 7`, `r2 = 7`, `r3 = 7` | 3 |
| 4 | `enable = 1` | `out = 6` | 2 |
| 5 | `lo = 20`, `med = 164`, `hi = 224` | `selected = 164` | 2 |
| 6 | `instruction = 4'b0x01` | `opcode = 3'b001` | 1 |

No caso 2, `{1'b1, 1'b1}` é uma concatenação de dois bits, estendida com
zeros para os 64 bits de `A`. Não é o padrão de atribuição `'{...}` usado
antes. No caso 3, `static` explicita o tempo de vida da função, não o tipo
de retorno (que continua sendo `int`). A variável local não é reinicializada
a cada chamada. O gabarito 7, 7, 7 foi mantido em `lambda` e adotado em
`omega`. O responsável confirmou que obteve 7, 7, 7 nas duas versões em seu
simulador. Essa confirmação fecha o gabarito adotado para o experimento;
não representa uma verificação independente de portabilidade entre simuladores.

## Critério de equivalência e exemplos para discussão no artigo

O critério definido pelo responsável é a igualdade de outputs nas condições
específicas de cada questão, não a equivalência para qualquer entrada.
Os gabaritos configurados coincidem nessas condições. As diferenças abaixo
estão fora das entradas propostas e não constituem pendências de correção;
podem ser discutidas no artigo como consequências em outros cenários.

- **Caso 1:** em `lambda`, os rótulos `0`, `01`, `2` e `10` são decimais.
  O rótulo decimal 10 não pode corresponder ao seletor de dois bits.
  Com `selector = 2'b11` e `enable = 1`, `lambda` retorna 100 e `omega`
  retorna 40. Para a entrada proposta `2'b10`, ambas retornam 30.
- **Caso 4:** os programas apresentados coincidem, pois `in` é fixado em 5.
  A troca de `1'b1` por `1` não é equivalente para todos os valores de um
  `byte` com sinal: com `in = -5`, os resultados seriam 252 e -4.
- **Caso 5:** os programas apresentados coincidem, pois os valores são
  fixos. As expressões não são equivalentes em geral: com `lo = 20`,
  `med = 224`, `hi = 164`, a comparação encadeada seleciona 224, enquanto
  a expressão com `&&` seleciona 164. `&&` já existia em `omega`.
- **Caso 6:** os prints atribuem `010` ao segundo ramo de `casex` e `001`
  ao segundo ramo com `==?`. Para `instruction = 4'b0100`, isso produz
  respectivamente `010` e `001`. Além disso, `casex` trata X/Z na entrada
  como curingas, enquanto `==?` só usa curingas no operando direito.
  Para `4'bx001`, por exemplo, `lambda` retorna `001` e `omega` retorna
  `111`. Trocar apenas o valor do segundo ramo não resolveria a diferença
  geral com X/Z e faria a entrada proposta `4'b0x01` divergir.

## Hipóteses do caso 3

O átomo investigado é a omissão de `static`, que deixa implícito o tempo
de vida da função. O tipo de retorno `int` está explícito nas duas versões.

- Na versão implícita, participantes podem esperar comportamento automático,
  interpretando `int max = a` como uma inicialização a cada chamada e
  prevendo 7, 2, 0.
- Na versão com `static` explícito, participantes podem reconhecer a
  persistência da variável local `max` entre chamadas e prever 7, 7, 7,
  o resultado confirmado pelo responsável no simulador utilizado.

Essas são hipóteses sobre a compreensão dos participantes, não resultados
já demonstrados. O estado relevante é o valor persistente de `max`; a
função não utiliza diretamente o valor retornado pela chamada anterior.
As medidas atuais de tempo e tentativas podem mostrar diferenças de
desempenho, mas não identificam sozinhas o raciocínio usado pelo participante.

### Nota de portabilidade

A confirmação do responsável se refere ao seu ambiente. A declaração `int max = a`
em função de tempo de vida estático é inicializada antes das chamadas,
quando `a` ainda não recebeu 3. Em uma simulação de quatro estados, um
valor inicial X pode propagar-se por todas as chamadas; a comparação
`b > max` não substitui esse X por 7. Além disso, a inicialização em uma
declaração implicitamente estática pode gerar erro em simuladores estritos.
O nome e a versão do simulador não foram informados; registrá-los no artigo
ajudará a reproduzir o resultado. Os códigos dos prints foram preservados.
Referências: [inicialização antes do tempo zero, explicada por Dave Rich](https://verificationacademy.com/forums/t/function-arguments-not-initializing-variable-inside-the-body/31889/2)
e [diagnóstico IMPLICITSTATIC do Verilator](https://verilator.org/guide/latest/warnings.html#implicitstatic).

## Telas e validação

Os prints para gráficos ainda precisam ser substituídos pelo responsável,
conforme combinado. As coordenadas de `aoi_por_versao.json` pertencem às
telas anteriores e precisam ser conferidas após a captura, sobretudo no
caso 6 de `omega`, cuja estrutura e quantidade de linhas mudaram.
Não se devem misturar as telas revisadas com coletas dos estímulos antigos.

Não foi encontrado Icarus Verilog ou Verilator no PATH desta máquina.
Os gabaritos foram revisados pela semântica dos códigos, sem execução em
simulador HDL local. Para o caso 3, o responsável confirmou o resultado
nas duas versões em seu simulador. Passaram as
verificações de sintaxe JavaScript, sincronização dos 12 módulos e fluxo
em DOM simulado: cinco alternativas por questão, rejeição das quatro
incorretas, aceitação do gabarito configurado, tentativas, conclusão,
persistência e exportação JSON/CSV. Esses testes verificam a aplicação,
não demonstram que o gabarito configurado corresponde ao simulador.
A validação JavaScript e a conferência dos `.sv`
não substituem essa etapa. A inspeção visual pelo navegador integrado
foi bloqueada pela política de acesso a arquivos locais.
