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

## Organizacao das saidas

Todos os scripts agora usam `Documents/demo/graficos/agregados`:
- `heatmaps/`: mapas Lambda/Omega e comparacoes por tarefa.
- `tempos/`: violin plots e tabelas de tempo de fixacao no codigo ou AOI1.
- `tentativas/`: comparativo de tentativas, contagens por participante/tarefa, resumo por grupo e fontes dos JSONs.

Tentativas: `python scripts/gera_tentativas_agregadas.py`. Le diretamente `coletas/Pxx/resultadoPxx.json`, usando codigoId (nao ordem de execucao). Barras agrupadas mostram a media de tentativas por participante, com valores acima das barras e eixo vertical comum entre tarefas. Contagens incluem a tentativa correta, conforme registradas pelo aplicativo. Esta metrica nao depende de dados oculares recuperados. Para outra origem use `--coletas-dir`; `--output-dir` continua disponivel nos tres scripts.

Os arquivos produzidos anteriormente fora dessas subpastas foram preservados; os novos comandos atualizam as subpastas acima.
