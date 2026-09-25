"""Infraestrutura compartilhada; cada entrada autoriza uma coleta especifica."""
import argparse
import csv
import hashlib
import json
import runpy
import sys
from datetime import datetime, timedelta
from pathlib import Path


def recover(participant, hashes, reason):
    parser = argparse.ArgumentParser(description=reason)
    parser.add_argument('--demo-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--only-split', action='store_true')
    args = parser.parse_args()
    source = args.demo_dir / 'coletas' / participant
    raw = source / f'data{participant}.txt'
    result = source / f'resultado{participant}.json'
    for path, expected in zip((raw, result), hashes):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected.lower():
            raise ValueError(f'Coleta diferente da auditada: {path}. Revise o tratamento antes de continuar.')
    session = json.loads(result.read_text(encoding='utf-8-sig'))
    questions = sorted(session['perguntas'], key=lambda q: q['ordemExecucao'])
    assert session['participanteId'] == participant
    assert [q['ordemExecucao'] for q in questions] == [1, 2, 3, 4]
    assert {q['codigoId'] for q in questions} == {'code-1', 'code-2', 'code-4', 'code-5'}
    start = datetime.fromisoformat(session['iniciadoEm']) - timedelta(hours=3)
    end = datetime.fromisoformat(session['concluidoEm']) - timedelta(hours=3)
    residual = (end-start).total_seconds() - sum(q['segundos'] for q in questions) - 29.6
    if not 0 <= residual <= 0.25:
        raise ValueError('Duracao da sessao fora da reconstrucao auditada.')
    def seconds(text):
        h, m, s, ms = map(int, text.strip().split(':'))
        return h*3600 + m*60 + s + ms/1000
    records = []
    for line in raw.read_text(encoding='utf-8-sig').splitlines():
        x, y, stamp = line.split(',')
        float(x), float(y)
        records.append((seconds(stamp), line))
    output = args.output_dir or args.demo_dir / 'recuperados'
    data = output / 'data' / participant
    data.mkdir(parents=True, exist_ok=True)
    t = start.hour*3600 + start.minute*60 + start.second + start.microsecond/1e6
    summary = []
    for position, question in enumerate(questions, 1):
        t += 7.4
        finish = t + question['segundos']
        segment = [r for r in records if t <= r[0] <= finish]
        if not segment:
            raise ValueError(f'Tarefa sem amostras: {question}')
        name = f'{participant}T{position:02} 1.txt'
        (data / name).write_text('x,y,tempo\n' + '\n'.join(r[1] for r in segment) + '\n', encoding='utf-8')
        gaps = [b[0]-a[0] for a,b in zip(segment, segment[1:])]
        summary.append(dict(Participante=participant, VersaoExperimento=session['versaoExperimento'],
            PosicaoExecucao=position, Arquivo=name, TarefaReal=f"T{int(question['codigoId'].split('-')[-1]):02}",
            SegundosAplicacao=question['segundos'], InicioEstimado=str(timedelta(seconds=t)),
            FimEstimado=str(timedelta(seconds=finish)), Amostras=len(segment),
            MaiorIntervaloSegundos=round(max(gaps, default=0),3),
            Metodo='estimativa_json_pausas_7.4s', ResidualSessaoSegundos=round(residual,3)))
        t = finish
    with (data / 'resumo_tarefas.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    note = (f'{participant}: {reason}\nLimites ESTIMADOS por JSON e pausas nominais de 7,4 s; '
            f'residual total {residual:.3f} s. Nao equivale a validacao da qualidade ocular.\n'
            'Coletas e resultados do fluxo normal preservados. Nao preencheram-se lacunas.\n'
            'Detector original mantido: pode unir fixacoes atraves de perdas temporais; '
            'graficos de tarefas com perdas sao provisorios, sujeitos a revisao.\n')
    (data / 'LEIA-ME.txt').write_text(note, encoding='utf-8')
    print(note, flush=True)
    if not args.only_split:
        # Carrega as mesmas funcoes sem executar main e usa Agg apenas nesta recuperacao.
        script = Path(__file__).resolve().parents[1] / 'main_script_adap.py'
        module = runpy.run_path(str(script), run_name='recovery_plotter')
        module['plt'].switch_backend('Agg')
        sys.argv = [str(script), '--participant', participant, '--data-dir', str(output/'data'),
                    '--images-dir', str(args.demo_dir/'telas'), '--graphs-dir', str(output/'graficos')]
        module['main']()
        graph_dir = output/'graficos'/participant
        (graph_dir/'LEIA-ME.txt').write_text(note, encoding='utf-8')
        print(f'Graficos: {graph_dir}')

