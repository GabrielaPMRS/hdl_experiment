# Processamento do experimento HDL

## Processar um participante

```powershell
.\processa_participante.ps1 00
```

P00, P03, P09 e P11 usam os tratamentos em `scripts/participantes_com_problema/`. Os demais usam o separador por gaps. Consulte o README dessa pasta para as estimativas temporais e limitacoes das recuperacoes.

## Gerar resultados agregados

```powershell
python scripts/gera_heatmaps_agregados.py
python scripts/gera_violin_tempo_aoi.py
python scripts/gera_violin_tempo_aoi.py --regiao aoi1
python scripts/gera_tentativas_agregadas.py
```

Resultados em `Documents/demo/graficos/agregados/`, nas subpastas `heatmaps`, `tempos` e `tentativas`. Os agregadores oculares selecionam automaticamente os recuperados de P00, P03, P09 e P11. Tentativas sao lidas dos JSONs originais. Consulte [scripts/README_AGREGADOS.md](scripts/README_AGREGADOS.md).

## Organizacao

- `lambda/` e `omega/`: aplicacoes das duas condicoes.
- `config/`: condicoes e limites das regioes de interesse.
- `scripts/`: processamento, graficos e utilitarios.
- `scripts/participantes_com_problema/`: recuperacoes necessarias ao fluxo atual.
- `tests/`: verificacoes da selecao de dados para os agregadores.
- `output/`: documentos auxiliares gerados.

As coletas e os resultados ficam em `Documents/demo`, fora deste repositorio. `tmp/` e reservada a trabalho temporario e ignorada pelo Git; nao e necessaria ao processamento. Os diagnosticos pontuais do primeiro dia foram arquivados fora do repositorio em `Documents/demo/arquivo_diagnosticos/limpeza_repositorio`.

## Verificar a selecao das fontes

```powershell
python -m unittest discover -s tests
```

Use uma instalacao Python com numpy, pandas, scipy, matplotlib, seaborn e Pillow para executar os geradores. O parametro `-PythonExecutable` do processamento permite selecionar a instalacao.
