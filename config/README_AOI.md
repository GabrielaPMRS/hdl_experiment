# Telas e AOIs por versão

As tarefas continuam identificadas como `T01` a `T06`. A versão do
experimento diferencia os dois estímulos do mesmo caso:

- `lambda/T01`: caso 1 com átomo;
- `omega/T01`: caso 1 sem átomo.

Os novos prints devem ser salvos em:

```text
Documents/demo/telas/lambda/T01.png ... T06.png
Documents/demo/telas/omega/T01.png  ... T06.png
```

No arquivo `aoi_por_versao.json`, preencha cada entrada da seguinte forma:

```json
{
  "codigo": [pixel_da_base, pixel_do_topo],
  "linhasCodigo": [pixel_da_linha_1, 0],
  "aoi1": [pixel_da_base, pixel_do_topo],
  "linhasAoi1": [pixel_da_linha_1, 0],
  "aoi2": [pixel_da_base, pixel_do_topo]
}
```

Enquanto as coordenadas estiverem como `null`, elas ainda não estão prontas
para serem usadas na análise.
