# Processamento do experimento HDL

## Ambiente Linux e caminho dos dados

A raiz dos dados e resolvida em `scripts/caminhos.py`, a partir da localizacao
deste repositorio (independente da pasta atual do terminal). Por padrao usa
`../HDL-Experiment-Data`, que neste computador corresponde a
`/home/gaber/dev/easy_academico/hdl/HDL-Experiment-Data`.
As subpastas `coletas`, `data`, `recuperados`, `telas` e `graficos` mantem sua estrutura.
Para outra localizacao, defina `HDL_DATA_ROOT`; os argumentos de caminho de cada
script continuam tendo precedencia. No PowerShell, o processamento tambem aceita
`-DemoDirectory`.

Prepare o Python uma vez, na raiz deste repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Para reprocessar no Linux, inclusive participantes com recuperacao especial:

```bash
python scripts/processa_participante.py 01
python scripts/processa_participante.py 00
```

`--only-split` gera somente os recortes e resumos. O separador Python conserva
as regras do PowerShell: primeiros cinco gaps >= 5 s, quatro tarefas, sem
remover coordenadas negativas. O reprocessamento atualiza os derivados do
participante; os arquivos originais em `coletas` sao a entrada.
Os graficos sao salvos sem exigir uma janela grafica (backend Agg).
O script `inicia_experimento.ps1` continua especifico da coleta Windows/Tobii.

## Processar um participante no Windows

```powershell
.\processa_participante.ps1 00
```

P00, P03, P09, P11, P15, P17, P21 e P25 usam os tratamentos em `scripts/participantes_com_problema/`. Os demais usam o separador por gaps. Consulte o README dessa pasta para as estimativas temporais e limitacoes das recuperacoes.

Para corrigir a posicao vertical dos olhos, altere somente o numero do participante em `DESLOCAMENTO_Y_PIXELS`, no arquivo `scripts/main_script_adap.py`. Valor positivo move as fixacoes para baixo na imagem; negativo move para cima. O valor vale para as quatro tarefas. Depois, execute novamente `processa_participante.ps1` para cada participante alterado: os CSVs de fixacoes e os graficos individuais sao recalculados. Os agregados usam esses CSVs quando forem gerados novamente, sem deslocamento adicional.

## Gerar resultados agregados

```bash
python scripts/gera_desempenho_tarefas.py
python scripts/gera_heatmaps_agregados.py --dpi 300
python scripts/gera_heatmaps_agregados_aoi.py --dpi 300
```

Resultados em `HDL-Experiment-Data/graficos/agregados/`, nas subpastas
`execution_time`, `attempts`, `heatmaps` e `heatmaps_aoi1`. Para cada caso,
comparam **With Atom** e **Without Atom**, incluindo todos os participantes.
Tempo e tentativas têm quatro comparativos de violinos por caso e um
comparativo geral com a soma das quatro tarefas de cada participante. Os heatmaps
mostram totais no título e escala numérica; a modalidade AOI usa somente as
fixações dentro da região de interesse. Consulte [scripts/README_AGREGADOS.md](scripts/README_AGREGADOS.md).

## Organizacao

- `lambda/` e `omega/`: aplicacoes das duas condicoes.
- `config/`: condicoes e limites das regioes de interesse.
- `scripts/`: processamento, graficos e utilitarios.
- `scripts/participantes_com_problema/`: recuperacoes necessarias ao fluxo atual.
- `tests/`: verificacoes da selecao de dados para os agregadores.
- `output/`: documentos auxiliares gerados.

As coletas e os resultados ficam em `HDL-Experiment-Data`, fora deste repositorio. `tmp/` e reservada a trabalho temporario e ignorada pelo Git; nao e necessaria ao processamento. Os diagnosticos pontuais do primeiro dia foram arquivados fora do repositorio em `HDL-Experiment-Data/arquivo_diagnosticos/limpeza_repositorio`.

## Verificar a selecao das fontes

```powershell
python -m unittest discover -s tests
```

Use uma instalacao Python com numpy, pandas, scipy, matplotlib, seaborn e Pillow para executar os geradores. O parametro `-PythonExecutable` do processamento permite selecionar a instalacao.
