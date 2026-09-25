"""Auditoria e recortes candidatos; preserva coletas e resultados anteriores.
Limites estimados: inicio UTC convertido para UTC-3 + pausas nominais de 7,4 s.
Atrasos de timers nao foram registrados individualmente. Ver residual_sessao_s.
"""
import ast,csv,json
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('C:/Users/EASY acadêmico/Documents/demo')
OUT=BASE/'auditoria_dia1'
OUT.mkdir(exist_ok=True)
source=ast.parse((ROOT/'scripts/main_script_adap.py').read_text(encoding='utf-8-sig'))
namespace={'np':np}
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('remove_missing','fixation_detection')],type_ignores=[]),'<existing fixation functions>','exec'),namespace)
aois=json.loads((ROOT/'config/aoi_por_versao.json').read_text(encoding='utf-8-sig'))
report=[]
def clock(t):
 ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02}:{ms:03}'
for p in sorted((BASE/'coletas').iterdir()):
 j=json.loads((p/f'resultado{p.name}.json').read_text(encoding='utf-8-sig'))
 rows=[]
 for line in (p/f'data{p.name}.txt').read_text(encoding='utf-8-sig').splitlines():
  a=line.split(',')
  if len(a)!=3: continue
  h,m,s,ms=map(int,a[2].strip().split(':')); rows.append((h*3600+m*60+s+ms/1000,float(a[0]),float(a[1]),line))
 start=datetime.fromisoformat(j['iniciadoEm'])-timedelta(hours=3)
 end=datetime.fromisoformat(j['concluidoEm'])-timedelta(hours=3)
 t=start.hour*3600+start.minute*60+start.second+start.microsecond/1e6
 residual=(end-start).total_seconds()-sum(q['segundos'] for q in j['perguntas'])-29.6
 mapping=[]
 for pos,q in enumerate(j['perguntas'],1):
  t+=7.4; finish=t+q['segundos']; segment=[r for r in rows if t<=r[0]<=finish]
  task='T'+q['codigoId'].split('-')[-1].zfill(2)
  ts=np.array([r[0]*1000 for r in segment]); x=np.array([r[1] for r in segment]); y=1080-np.array([r[2] for r in segment])
  _,fix=namespace['fixation_detection'](x,y,ts)
  lo,hi=sorted(aois[j['versaoExperimento']][task]['codigo'])
  codefix=[f for f in fix if 245<=f[3]<=820 and 1080-hi<=f[4]<=1080-lo]
  deltas=[b[0]-a[0] for a,b in zip(segment,segment[1:])]
  # Interrupcoes >1s, nao uma estimativa total de perda de rastreamento.
  longgaps=[d for d in deltas if d>1]
  report.append(dict(participante=p.name,tarefa=task,inicio_estimado=clock(t),fim_estimado=clock(finish),duracao_app_s=q['segundos'],amostras=len(segment),fixacoes_codigo=len(codefix),maior_intervalo_s=round(max(deltas,default=0),3),soma_intervalos_acima_1s=round(sum(longgaps),3),residual_sessao_s=round(residual,3)))
  if p.name in ('P00','P03','P11','P09'):
   dest=OUT/'recortes_estimados'/p.name; dest.mkdir(parents=True,exist_ok=True)
   name=f'{p.name}T{pos:02} 1.txt'
   (dest/name).write_text('x,y,tempo\n'+'\n'.join(r[3] for r in segment)+'\n',encoding='utf-8')
   mapping.append(dict(Participante=p.name,VersaoExperimento=j['versaoExperimento'],PosicaoExecucao=pos,Arquivo=name,TarefaReal=task,SegundosAplicacao=q['segundos'],InicioEstimado=clock(t),FimEstimado=clock(finish),Metodo='estimado_json_pausa_nominal_7.4s'))
   with (dest/f'Fixations {p.name} {task}.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['tempo','tempofinal','duracao','x','y']); w.writerows(fix)
  t=finish
 if mapping:
  with (dest/'resumo_tarefas.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=mapping[0].keys());w.writeheader();w.writerows(mapping)
with (OUT/'auditoria_tarefas.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=report[0].keys());w.writeheader();w.writerows(report)
for row in report:
 if row['participante'] in ('P00','P03','P11','P09'): print(row)
