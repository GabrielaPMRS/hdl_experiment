"""Reprocessamento portavel; mesmas regras do separador PowerShell por gaps."""
import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

from caminhos import raiz_dados

RECUPERADOS = {'P00', 'P03', 'P09', 'P11', 'P15', 'P17', 'P21', 'P25'}


def salva_csv(caminho, linhas):
    with caminho.open('w', encoding='utf-8-sig', newline='') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=linhas[0])
        writer.writeheader()
        writer.writerows(linhas)


def segundos(horario):
    h, m, s, ms = map(int, horario.split(':'))
    return h * 3600 + m * 60 + s + ms / 1000


def separa(raiz, participante, destino, gap_minimo):
    origem = raiz / 'coletas' / participante
    sessao = json.loads((origem / f'resultado{participante}.json').read_text(encoding='utf-8-sig'))
    if isinstance(sessao, list):
        if len(sessao) != 1:
            raise ValueError('O JSON deve conter exatamente uma sessao.')
        sessao = sessao[0]
    perguntas = sorted(sessao['perguntas'], key=lambda q: int(q['ordemExecucao']))
    versao = sessao['versaoExperimento'].lower()
    if len(perguntas) != 4 or versao not in {'lambda', 'omega'}:
        raise ValueError('Sao necessarias quatro tarefas e uma versao valida.')
    resumo = []
    for posicao, pergunta in enumerate(perguntas, 1):
        codigo = re.search(r'(\d+)$', pergunta['codigoId'])
        if int(pergunta['ordemExecucao']) != posicao or codigo is None:
            raise ValueError('Ordem ou codigo de tarefa invalido.')
        resumo.append(dict(Participante=participante, VersaoExperimento=versao,
            PosicaoExecucao=posicao, Arquivo=f'{participante}T{posicao:02} 1.txt',
            TarefaReal=f'T{int(codigo[1]):02}', CodigoId=pergunta['codigoId'],
            SegundosAplicacao=float(pergunta['segundos']), Tentativas=int(pergunta['tentativas']),
            ParticipanteIdJson=sessao['participanteId']))
    if {r['TarefaReal'] for r in resumo} != {'T01', 'T02', 'T04', 'T05'}:
        raise ValueError('Tarefas repetidas, ausentes ou fora do experimento.')
    registros = []
    with (origem / f'data{participante}.txt').open(encoding='utf-8-sig') as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            texto = linha.rstrip('\r\n')
            match = re.fullmatch(r'\s*([^,]+),\s*([^,]+),\s*(\d{2}:\d{2}:\d{2}:\d{3})\s*', texto)
            if match:
                x, y, tempo = match.groups()
                registros.append((numero, texto, float(x), float(y), tempo, segundos(tempo)))
    gaps = []
    for indice in range(1, len(registros)):
        duracao = registros[indice][5] - registros[indice - 1][5]
        if duracao < 0:
            duracao += 86400
        if duracao >= gap_minimo:
            gaps.append((indice, duracao))
    if len(gaps) < 5:
        raise ValueError(f'Encontrados {len(gaps)} gaps; sao necessarios 5.')
    gaps = gaps[:5]
    destino.mkdir(parents=True, exist_ok=True)
    limpeza = []
    for indice, tarefa in enumerate(resumo):
        trecho = registros[gaps[indice][0]:gaps[indice + 1][0]]
        inicio, fim = trecho[0], trecho[-1]
        tarefa.update(InicioEyeTracker=inicio[4], FimEyeTracker=fim[4],
                      SegundosEyeTracker=round((fim[5] - inicio[5]) % 86400, 3))
        (destino / tarefa['Arquivo']).write_text('x,y,tempo\n' + '\n'.join(r[1] for r in trecho) + '\n', encoding='utf-8')
        limpeza.append(dict(File=tarefa['Arquivo'], OriginalRows=len(trecho), WrittenRows=len(trecho),
            NegativeXRows=sum(r[2] < 0 for r in trecho), NegativeYRows=sum(r[3] < 0 for r in trecho),
            XAtOrAbove820Rows=sum(r[2] >= 820 for r in trecho)))
    limites = []
    for indice, duracao in gaps:
        antes, depois = registros[indice - 1], registros[indice]
        limites.append(dict(BeforeLine=antes[0], BeforeTime=antes[4], AfterLine=depois[0],
                            AfterTime=depois[4], GapSeconds=round(duracao, 3)))
    salva_csv(destino / 'resumo_tarefas.csv', resumo)
    salva_csv(destino / 'resumo_limpeza.csv', limpeza)
    salva_csv(destino / 'limites_gaps.csv', limites)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('participante', help='00, 01... ou P00, P01...')
    parser.add_argument('--demo-dir', type=Path, default=raiz_dados())
    parser.add_argument('--minimum-gap-seconds', type=float, default=5.0)
    parser.add_argument('--only-split', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'P?\d+', args.participante):
        parser.error('Participante invalido.')
    if args.minimum_gap_seconds <= 0:
        parser.error('O intervalo minimo deve ser positivo.')
    participante = f'P{int(args.participante.removeprefix("P")):02}'
    raiz = args.demo_dir.expanduser().resolve()
    scripts = Path(__file__).resolve().parent
    if participante in RECUPERADOS:
        comando = [sys.executable, str(scripts / 'participantes_com_problema' / f'{participante}.py'),
                   '--demo-dir', str(raiz)]
        if args.only_split:
            comando.append('--only-split')
        subprocess.run(comando, check=True)
    else:
        separa(raiz, participante, raiz / 'data' / participante, args.minimum_gap_seconds)
        if not args.only_split:
            subprocess.run([sys.executable, str(scripts / 'main_script_adap.py'),
                '--participant', participante, '--data-dir', str(raiz / 'data'),
                '--images-dir', str(raiz / 'telas'), '--graphs-dir', str(raiz / 'graficos')], check=True)
    print(f'Processamento concluido para {participante}.')


if __name__ == '__main__':
    main()
