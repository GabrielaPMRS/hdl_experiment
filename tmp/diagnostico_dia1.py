import json,re,csv
from pathlib import Path
from datetime import datetime,timedelta
base=Path('C:/Users/EASY acadêmico/Documents/demo')
for p in sorted((base/'coletas').iterdir()):
 j=json.loads((p/f'resultado{p.name}.json').read_text(encoding='utf-8-sig'))
 rows=[]
 for line in (p/f'data{p.name}.txt').read_text(encoding='utf-8-sig').splitlines():
  a=line.split(',')
  if len(a)!=3: continue
  h,m,s,ms=map(int,a[2].strip().split(':')); rows.append((h*3600+m*60+s+ms/1000,float(a[0]),float(a[1])))
 start=(datetime.fromisoformat(j['iniciadoEm'])-timedelta(hours=3)); end=(datetime.fromisoformat(j['concluidoEm'])-timedelta(hours=3))
 t=start.hour*3600+start.minute*60+start.second+start.microsecond/1e6
 residual=(end-start).total_seconds()-sum(q['segundos'] for q in j['perguntas'])-29.6
 gaps=[(a[0],b[0],round(b[0]-a[0],3)) for a,b in zip(rows,rows[1:]) if b[0]-a[0]>=1]
 def fmt(t): return str(timedelta(seconds=round(t,3)))
 print(p.name,'gaps>=5',sum(g[2]>=5 for g in gaps),'timer residual',round(residual,3))
 if p.name not in ['P00','P03','P11']: continue
 for q in j['perguntas']:
  t+=7.4; finish=t+q['segundos']; segment=[r for r in rows if t<=r[0]<=finish]
  print('TASK',q['codigoId'],fmt(t),fmt(finish),'rows',len(segment))
  t=finish
 print('GAPS',[(fmt(a),fmt(b),d) for a,b,d in gaps])
