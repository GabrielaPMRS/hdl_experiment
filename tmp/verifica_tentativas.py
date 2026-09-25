from pathlib import Path
import csv,json
for name in ('gera_heatmaps_agregados.py','gera_violin_tempo_aoi.py'):
 p=Path('scripts')/name
 p.write_text(p.read_text(encoding='utf-8-sig').rstrip()+'\n',encoding='utf-8')
b=Path('C:/Users/EASY acadêmico/Documents/demo')
rows=list(csv.DictReader((b/'graficos/agregados/tentativas/tentativas_por_participante_tarefa.csv').open(encoding='utf-8-sig')))
assert len(rows)==48 and len({(r['Participante'],r['Tarefa']) for r in rows})==48
for r in rows:
 j=json.loads((b/'coletas'/r['Participante']/f"resultado{r['Participante']}.json").read_text(encoding='utf-8-sig'))
 q=next(q for q in j['perguntas'] if int(q['codigoId'].split('-')[-1])==int(r['Tarefa'][1:]))
 assert int(r['Tentativas'])==q['tentativas']
assert len(list((b/'graficos/agregados/heatmaps').glob('*.png')))==12
assert len(list((b/'graficos/agregados/tempos').glob('*.png')))==2
print('Validado: 48 contagens correspondem aos JSONs; 12 heatmaps e 2 violin plots.')
