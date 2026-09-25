# Fontes dos graficos agregados

Execute normalmente:

```powershell
python scripts/gera_heatmaps_agregados.py
python scripts/gera_violin_tempo_aoi.py
```

Ambos usam `fontes_agregados.py`: P00, P03, P09 e P11 sao lidos exclusivamente de `Documents/demo/recuperados/data`; os demais, de `Documents/demo/data`. Cada participante aparece uma vez. As duas pastas sao examinadas, incluindo recuperados sem pasta normal. Pastas de participantes incompletas geram erro; nao ha fallback para dados antigos.

O resumo precisa mapear as quatro tarefas e a condicao correta, e os quatro CSVs de fixacoes devem existir com x, y e duracao. A selecao nao exclui tarefas do P03; esta rodada e preliminar e inclui suas perdas conhecidas.

Cada pasta de resultados recebe `fontes_utilizadas.csv`, com participante, versao, origem e caminhos absolutos. Os calculos e escalas nao foram alterados. A lista de fontes registra entradas, nao certifica a qualidade ocular nem garante contribuicao ao heatmap se nao houver fixacoes validas no codigo.

Para outra localizacao use `--data-dir` e, se necessario, `--recovered-data-dir`. Sem o segundo argumento, recuperados/data e procurada no diretorio pai de data. Saidas podem ser alteradas com `--output-dir`.
