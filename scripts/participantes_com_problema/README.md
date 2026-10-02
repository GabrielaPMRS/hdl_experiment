# Participantes com problema

O comando habitual continua sendo `./processa_participante.ps1 00` (ou 03/09/11/15/17/21/25).
O despachante chama o arquivo Pxx.py correspondente nesta pasta. Outros IDs seguem o fluxo original de cinco gaps >=5 s, sem mudancas no separador ou no gerador principal.

- P00: pausa inicial sem gap; estimativa pelos horarios do JSON corrige o deslocamento das quatro tarefas.
- P03: pausas fragmentadas e perdas internas; recortes por horarios, graficos PROVISORIOS. Especialmente T04 nao deve ser considerada recuperada em qualidade apenas porque existe uma imagem.
- P09: gaps internos em T05 e T02 foram confundidos com transicoes; recortes por horarios preservam as perdas existentes.
- P11: pausa inicial fragmentada (4,855 s); recortes por horarios.
- P15: pausa inicial de 4,523 s; recortes por horarios. Nenhuma tarefa possui gap interno acima de 1 s.
- P17: pausa inicial sem gap e pausas posteriores fragmentadas; recortes por horarios. Nenhuma tarefa possui gap interno acima de 1 s.
- P21: pausa inicial sem gap e primeira transicao com gap de 3,023 s; recortes por horarios. Nenhuma tarefa possui gap interno acima de 1 s.
- P25: nenhum gap acima de 1 s no registro ocular, embora as quatro tarefas tenham amostras quase continuas. Recortes por horarios do JSON e pausas nominais.

Os arquivos individuais registram o motivo e os SHA256 dos dois arquivos auditados. A infraestrutura compartilhada em _recuperacao.py evita duplicar leitura, exportacao e desenho. Atualmente os oito casos usam a mesma estimativa temporal, mas as entradas podem evoluir separadamente. As quatro pausas nominais sao 7,4 s; os limites nao sao timestamps medidos por tarefa. O detector de fixacoes original e mantido, inclusive suas limitacoes em lacunas temporais.

Saidas especiais: `Documents/demo/recuperados/data/Pxx` e `Documents/demo/recuperados/graficos/Pxx`. Coletas, data e graficos do fluxo normal sao preservados. Reexecutar atualiza somente as saidas especiais. MinimumGapSeconds nao se aplica aos oito tratamentos especiais.

Se python nao estiver no PATH, use o parametro existente -PythonExecutable com o caminho de uma instalacao que possua numpy, pandas, scipy, matplotlib, seaborn e Pillow. A recuperacao usa Agg localmente; o fluxo normal preserva TkAgg e exige Tk funcional.

Execucao direta: `python scripts/participantes_com_problema/P00.py --demo-dir CAMINHO_DEMO`. Para verificar somente os recortes, acrescente `--only-split`; para testes isolados, `--output-dir CAMINHO_SAIDA`.

No P09, nenhuma lacuna acima de 1 s foi incluida em uma fixacao nos CSVs recuperados. T04 e T01 nao possuem gaps internos acima de 1 s.

