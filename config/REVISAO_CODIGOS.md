# Revisão dos códigos — 21/09/2026

O experimento atual contém quatro casos: 1, 2, 4 e 5, em lambda e omega.
Os identificadores originais foram mantidos para preservar a correspondência
com as AOIs e os dados exportados. O progresso exibe quatro perguntas.
Os casos 3 e 6 foram retirados deste experimento. As cópias reservadas
para uso futuro foram removidas do repositório a pedido do responsável.
O armazenamento local da aplicação usa uma chave própria para esta revisão.

## Gabaritos nas duas versões

| Caso | Condição da pergunta | Resposta | Alternativa (1–5) |
| --- | --- | --- | --- |
| 1 | `selector = 2'b10`, `enable = 1` | `out = 30` | 3 |
| 2 | Inicialização apresentada | `out0 = 32'b11`, `out1 = 32'b0` | 4 |
| 4 | `enable = 1` | `out = 6` | 2 |
| 5 | `lo = 20`, `med = 164`, `hi = 224` | `selected = 164` | 2 |

No caso 2, `{1'b1, 1'b1}` é uma concatenação de dois bits, estendida com
zeros para os 64 bits de `A`. Não é o padrão de atribuição `'{...}` usado
antes. No caso 1, a entrada é explicitamente `2'b10` (binário 2);
com `enable = 1`, o gabarito permanece `out = 30` em ambas as versões.

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
## Telas e validação

As tarefas ativas são T01, T02, T04 e T05. As coordenadas existentes dessas
AOIs foram mantidas e ainda precisam ser conferidas com novas capturas.
Os scripts de separação, análise e gráficos usam as quatro tarefas atuais;
coletas antigas de seis tarefas devem usar a revisão anterior dos scripts.
O catálogo PDF é gerado somente com os quatro casos ativos.

Não foi executada simulação HDL local nesta revisão.

Validação desta revisão: sintaxe JavaScript, Python e PowerShell; sincronização
dos oito módulos ativos; fluxo em DOM simulado com rejeição de alternativas
incorretas, conclusão em quatro respostas e exportação CSV; separação de
dados sintéticos do eye tracker com quatro tarefas em ordem sorteada.
