# Gráficos para o artigo

Na raiz do repositório, com o ambiente Python ativado:

```bash
python scripts/gera_desempenho_tarefas.py
python scripts/gera_heatmaps_agregados.py --dpi 300
python scripts/gera_heatmaps_agregados_aoi.py --dpi 300
```

Todos usam a raiz de dados definida em `caminhos.py` (repositório irmão
`HDL-Experiment-Data` ou `HDL_DATA_ROOT`). Os quatro casos são T01, T02,
T04 e T05. Cada figura apresenta somente um caso, com as condições
**With Atom** e **Without Atom**, nessa ordem. A correspondência é
lambda = With Atom e omega = Without Atom. Os IDs antigos permanecem
somente na leitura das coletas, configurações e telas, para preservar sua
correspondência. Os rótulos das figuras e as novas tabelas são em inglês.

## Tempo de execução e tentativas

`gera_desempenho_tarefas.py` lê `coletas/Pxx/resultadoPxx.json`.
Usa `codigoId` para identificar o caso, independentemente da ordem sorteada.
O campo `segundos` é o tempo completo de resolução da tarefa registrado
pelo aplicativo, incluindo as tentativas dessa tarefa. Não é tempo de
fixação, tempo na AOI, nem duração da sessão inteira. `tentativas` inclui
a tentativa correta.

Saídas em `graficos/agregados/`:

- `execution_time/tXX_violin.png`: dois violinos dos tempos individuais,
  boxplots e um ponto por participante; eixo vertical logarítmico.
- `execution_time/all_tasks_violin.png`: dois violinos com 13 totais por
  condição. Cada ponto soma o tempo das quatro tarefas de um participante.
- `attempts/tXX_violin.png`: distribuição das tentativas individuais,
  boxplots e pontos, em escala linear com marcações inteiras. Os quatro
  casos compartilham os mesmos limites verticais, de zero até o maior valor
  individual por tarefa, com margem (atualmente 0–13). O comparativo geral
  usa limites próprios para acomodar as somas sem cortes (atualmente 0–26).
- `attempts/all_tasks_violin.png`: dois violinos com a soma das tentativas
  nas quatro tarefas, calculada separadamente para cada participante.

Os títulos informam as somas e o número de participantes. Cada pasta contém
`participant_task_values.csv`, `summary.csv` e `sources.csv`, permitindo
conferir os valores e suas origens. Não há exclusão por quartis ou por tempo;
na coleta atual são 13 participantes por condição em todos os casos.

A densidade dos violinos de tempo é estimada em log10 e os ticks mostram
segundos. Isso mantém a densidade coerente com a escala exibida. As caudas
suavizadas podem ultrapassar os valores observados; os pontos e boxplots
mostram as medições. Tentativas são contagens discretas; sua densidade é
apenas uma visualização suavizada e não significa tentativas fracionárias.
O comparativo geral mantém a unidade de observação no participante: são 13
somas individuais por condição, nunca uma única soma usada como distribuição.
`participant_totals.csv` e `overall_summary.csv` registram essas somas e seu
resumo. Esse gráfico permite comparar a carga total de resolução; sozinho não
isola o efeito de fadiga, que depende também da ordem de execução.

Os scripts `gera_violin_tempo_aoi.py` e `gera_tentativas_agregadas.py` foram
mantidos como entradas de compatibilidade para gerar, respectivamente, o
novo conjunto de tempo completo e o de tentativas. O argumento antigo
`--regiao` foi retirado: o tempo representado agora é sempre o da tarefa inteira.
Use `--coletas-dir`, `--output-dir` e `--dpi` para personalizar a execução.
No comando conjunto, `--output-dir` é a pasta pai dos dois conjuntos.

## Heatmaps

- `heatmaps/`: todas as fixações válidas dentro do painel do código.
- `heatmaps_aoi1/`: somente as fixações válidas dentro da AOI correspondente
  ao átomo (e à região equivalente na condição Without Atom). A densidade
  é calculada exclusivamente com essas fixações e exibida somente nessa
  região, sobre a imagem completa do código. Não há verde ou linhas tracejadas.

Para cada caso é gerada somente uma comparação lado a lado (`comparison_tXX.png` ou `comparison_aoi_tXX.png`). Todas exibem barra
numérica de cores. Cada tarefa e modalidade usa uma escala automática, de zero até o maior
pico entre With Atom e Without Atom. Os dois painéis de cada comparação
compartilham os mesmos limites. A escala pode mudar entre tarefas e entre
código completo/AOI; consulte a barra numérica ao comparar figuras diferentes.

A intensidade representa **densidade acumulada de tempo de fixação em
ms/pixel²**, usando KDE ponderada pela duração, sem divisão pelo número de
participantes. Os títulos mostram o número total de fixações e a soma de
suas durações, em segundos. `n` inclui todos os participantes da condição,
mesmo se algum não tiver fixações válidas na região. Casos sem fixações
produzem mapa vazio; dados insuficientes/colineares usam kernels gaussianos
com desvio de 25 pixels, em vez de excluir participantes.

As coordenadas e limites vêm de `config/aoi_por_versao.json`. Os mapas usam
as fixações já corrigidas pelo processamento individual; não aplicam novo
deslocamento. As fontes recuperadas de P00, P03, P09, P11, P15, P17, P21 e
P25 são selecionadas automaticamente. Os demais usam `data`. As limitações
das recuperações continuam descritas em `participantes_com_problema/README.md`.

`sources.csv` registra a origem de cada participante. `summary.csv` informa
totais, quantidade de participantes e máximo da escala compartilhada.
Na análise da AOI, `participant_aoi_fixations.csv` permite conferir também
as fixações dentro e fora da região; os dados fora dela não entram no mapa.

## Tabelas auxiliares e resultados anteriores

`gera_dados_participantes.py` continua disponível para inspeção das tabelas
individuais; seus indicadores exploratórios não filtram os novos gráficos.
Os resultados substituídos da análise anterior estão preservados em
`arquivo_diagnosticos/graficos_anteriores_2026-10-09`, no repositório de dados.

## Equilíbrio de experiência

```bash
python scripts/analisa_equilibrio_experiencia.py
```

Compara os cinco campos de experiência autodeclarada, contando cada
participante uma vez. Salva relatório, frequências, respostas individuais e
figura em `graficos/agregados/experience_balance/`. A análise é descritiva;
não exclui participantes nem altera os gráficos de desempenho.

## Seleção manual de participantes

Edite apenas `config/participantes_analise.json`. O padrão mantém todos:

```json
{
  "incluidos": null
}
```

Para usar os primeiros 12 participantes (P00 até P11, seis por condição):

```json
{
  "incluidos": [
    "P00", "P01", "P02", "P03", "P04", "P05",
    "P06", "P07", "P08", "P09", "P10", "P11"
  ]
}
```

Adicione ou remova IDs dessa lista para formar qualquer seleção manual.
Os IDs pares são With Atom; os ímpares, Without Atom. A lista deve conter
pelo menos uma pessoa de cada condição para produzir os comparativos.
Com uma única pessoa ou valores iguais em um grupo, não há distribuição
variável suficiente para formar um violino; os pontos continuam representando
as medições disponíveis. Uma lista vazia é considerada erro, não “todos”.
IDs inexistentes ou repetidos também geram erro, evitando exclusões silenciosas.

A seleção vale para tempo, tentativas, heatmaps e as análises auxiliares que
usam os mesmos leitores (incluindo a análise de experiência). Os arquivos
originais e o reprocessamento individual não são alterados. As recuperações
especiais continuam sendo usadas para os IDs selecionados que as exigem.
O padrão `null` restaura o comportamento completo sem reverter código.

Para explorar experiência, consulte as respostas individuais em
`HDL-Experiment-Data/graficos/agregados/experience_balance/participant_experience.csv`
ou os JSONs originais em `coletas`. Escolha explicitamente o critério (por
exemplo, hardware ≥3 anos ou software ≥6 anos), e coloque os IDs desejados
na mesma lista. Não há classificação automática de “experiente”.

Depois de editar a lista, regenere os gráficos. Para preservar os resultados
principais, salve este experimento em uma pasta própria:

```bash
source .venv/bin/activate
python scripts/gera_desempenho_tarefas.py --output-dir ../HDL-Experiment-Data/graficos/exploratorios/primeiros_12
python scripts/gera_heatmaps_agregados.py --permitir-grupos-desiguais --output-dir ../HDL-Experiment-Data/graficos/exploratorios/primeiros_12/heatmaps --dpi 300
python scripts/gera_heatmaps_agregados_aoi.py --permitir-grupos-desiguais --output-dir ../HDL-Experiment-Data/graficos/exploratorios/primeiros_12/heatmaps_aoi1 --dpi 300
```

Troque `primeiros_12` pelo nome do experimento, como `hardware` ou `software`.
`sources.csv`, as tabelas e os títulos refletem somente os participantes
selecionados. O argumento `--permitir-grupos-desiguais` permite seleções com
quantidades diferentes entre condições, sem remover ninguém para igualar
grupos. Nesse caso, os heatmaps continuam representando tempo acumulado
absoluto; as quantidades diferentes precisam ser consideradas na interpretação.
Sem `--output-dir`, os comandos atualizam as pastas principais habituais.

## Regenerar todos os comparativos com um comando

Na raiz do repositório:

```bash
.venv/bin/python scripts/gera_graficos.py
```

Usa a seleção atual de `config/participantes_analise.json` e gera os cinco
violinos de tempo, os cinco de tentativas, os quatro heatmaps do código e
os quatro da AOI. Todos são salvos a 300 DPI. Aceita grupos de tamanhos
diferentes e interrompe se algum gerador falhar.

Para guardar uma rodada separada ou alterar a resolução:

```bash
.venv/bin/python scripts/gera_graficos.py --output-dir ../HDL-Experiment-Data/graficos/exploratorios/hardware --dpi 200
```

Sem `--output-dir`, atualiza as quatro pastas de `graficos/agregados`.

## Revisar candidatos a outliers sem excluir dados

```bash
python scripts/analisa_outliers.py
```

Salva `outlier_review/review.md` e duas pastas: `all_participants` (coleta
completa) e `current_selection` (lista atual). `candidates.csv` contém apenas
as sinalizações; `iqr_review.csv` contém todas as observações e limites por
caso × condição. `iqr_review_pooled.csv` permite conferir o efeito de agrupar
as condições por caso. A análise considera somente o tempo completo de execução de cada tarefa
(`ExecutionTimeSeconds`), sem classificar tentativas ou fixações.
A regra usa 1,5 × IQR e marca grupos com IQR zero
ou amostra insuficiente. Não altera a seleção, os dados ou os gráficos.
