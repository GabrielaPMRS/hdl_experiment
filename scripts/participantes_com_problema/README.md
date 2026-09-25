# Participantes com problema

O comando habitual continua sendo `./processa_participante.ps1 00` (ou 03/09/11).
O despachante chama P00.py, P03.py, P09.py ou P11.py nesta pasta. Outros IDs seguem o fluxo original de cinco gaps >=5 s, sem mudancas no separador ou no gerador principal.

- P00: pausa inicial sem gap; estimativa pelos horarios do JSON corrige o deslocamento das quatro tarefas.
- P03: pausas fragmentadas e perdas internas; recortes por horarios, graficos PROVISORIOS. Especialmente T04 nao deve ser considerada recuperada em qualidade apenas porque existe uma imagem.
- P11: pausa inicial fragmentada (4,855 s); recortes por horarios.

Os arquivos individuais registram o motivo e os SHA256 dos dois arquivos auditados. A infraestrutura compartilhada em _recuperacao.py evita duplicar leitura, exportacao e desenho. Atualmente os quatro casos usam a mesma estimativa temporal, mas as entradas podem evoluir separadamente. As quatro pausas nominais sao 7,4 s; os limites nao sao timestamps medidos por tarefa. O detector de fixacoes original e mantido, inclusive suas limitacoes em lacunas temporais.

Saidas especiais: `Documents/demo/recuperados/data/Pxx` e `Documents/demo/recuperados/graficos/Pxx`. Coletas, data e graficos do fluxo normal sao preservados. Reexecutar atualiza somente as saidas especiais. MinimumGapSeconds nao se aplica aos quatro tratamentos especiais.

Se python nao estiver no PATH, use o parametro existente -PythonExecutable com o caminho de uma instalacao que possua numpy, pandas, scipy, matplotlib, seaborn e Pillow. A recuperacao usa Agg localmente; o fluxo normal preserva TkAgg e exige Tk funcional.

Execucao direta: `python scripts/participantes_com_problema/P00.py --demo-dir CAMINHO_DEMO`. Para verificar somente os recortes, acrescente `--only-split`; para testes isolados, `--output-dir CAMINHO_SAIDA`.

P09 integrado: gaps internos de 8,796 s e 7,496 s em T05, e 9,255 s em T02 confundiam o separador. Recortes reconstruidos pelo JSON, residual de 0,145 s. Nenhuma dessas lacunas acima de 1 s foi incluida em uma fixacao nos CSVs recuperados. T04 e T01 sem gaps internos acima de 1 s.

