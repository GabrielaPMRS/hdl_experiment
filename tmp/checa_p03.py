import csv,json
from pathlib import Path
base=Path('C:/Users/EASY acadêmico/Documents/demo/recuperados/data/P03')
aoi=json.loads(Path('config/aoi_por_versao.json').read_text(encoding='utf-8-sig'))['omega']
def sec(s):
 h,m,s,ms=map(int,s.strip().split(':'));return h*3600+m*60+s+ms/1000
report=[]
for task in csv.DictReader((base/'resumo_tarefas.csv').open(encoding='utf-8-sig')):
 rows=list(csv.DictReader((base/task['Arquivo']).open(encoding='utf-8-sig')))
 ts=[sec(r['tempo']) for r in rows]; origin=ts[0]
 fixes=list(csv.DictReader((base/f"Fixations P03 {task['TarefaReal']}.csv").open()))
 lo,hi=sorted(aoi[task['TarefaReal']]['codigo'])
 def region(x,y): return 'codigo' if 245<=x<=820 and lo<=y<=hi else 'fora_do_codigo'
 hits=[]
 for i in range(1,len(rows)):
  gap=ts[i]-ts[i-1]
  if gap<=1:continue
  a=(ts[i-1]-origin)*1000;b=(ts[i]-origin)*1000
  overlaps=[]
  for f in fixes:
   overlap=max(0,min(b,float(f['tempofinal']))-max(a,float(f['tempo'])))
   if overlap>0.1: overlaps.append(dict(duracao_ms=f['duracao'],sobreposicao_s=round(overlap/1000,3),regiao=region(float(f['x']),1080-float(f['y']))))
  hits.append(dict(antes=rows[i-1]['tempo'],depois=rows[i]['tempo'],gap_s=round(gap,3),ponto_antes=[float(rows[i-1]['x']),float(rows[i-1]['y'])],ponto_depois=[float(rows[i]['x']),float(rows[i]['y'])],fixacoes_sobrepostas=overlaps))
 outside=sum(region(float(r['x']),float(r['y']))!='codigo' for r in rows)
 report.append(dict(tarefa=task['TarefaReal'],amostras=len(rows),amostras_fora_codigo=outside,gaps_acima_1s=hits))
print(json.dumps(report,indent=2,ensure_ascii=False))
Path('tmp/checagem_p03_gaps.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
