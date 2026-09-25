"""Compara tentativas registradas no aplicativo, por tarefa e condicao."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

TAREFAS = ('T01', 'T02', 'T04', 'T05')
VERSOES = ('lambda', 'omega')


def carrega_tentativas(coletas_dir):
    linhas, fontes = [], []
    for pasta in sorted(coletas_dir.glob('P*')):
        if not pasta.is_dir() or not re.fullmatch(r'P\d+', pasta.name):
            continue
        arquivo = pasta / f'resultado{pasta.name}.json'
        sessao = json.loads(arquivo.read_text(encoding='utf-8-sig'))
        if isinstance(sessao, list):
            if len(sessao) != 1:
                raise ValueError(f'Esperada uma sessao: {arquivo}')
            sessao = sessao[0]
        versao = sessao['versaoExperimento'].lower()
        esperada = 'lambda' if int(pasta.name[1:]) % 2 == 0 else 'omega'
        perguntas = sessao['perguntas']
        if (sessao['participanteId'] != pasta.name or versao != esperada
                or len(perguntas) != 4
                or {q['codigoId'] for q in perguntas} != {'code-1','code-2','code-4','code-5'}
                or {q['ordemExecucao'] for q in perguntas} != {1,2,3,4}):
            raise ValueError(f'Sessao inconsistente: {arquivo}')
        for pergunta in perguntas:
            tentativas = pergunta['tentativas']
            if type(tentativas) is not int or tentativas < 1:
                raise ValueError(f'Tentativas invalidas: {arquivo}: {pergunta}')
            linhas.append(dict(Participante=pasta.name, Versao=versao,
                Tarefa=f"T{int(pergunta['codigoId'].split('-')[-1]):02}",
                Tentativas=tentativas))
        fontes.append(dict(Participante=pasta.name, Versao=versao, Arquivo=str(arquivo.resolve())))
    if not linhas or {r['Versao'] for r in linhas} != set(VERSOES):
        raise ValueError('Sao necessarias coletas completas dos dois grupos.')
    return pd.DataFrame(linhas), pd.DataFrame(fontes)


def gera_grafico(dados, caminho, dpi):
    fig, ax = plt.subplots(figsize=(10, 6))
    posicoes = np.arange(len(TAREFAS))
    largura = 0.34
    maior_media = 0
    for indice, (versao, cor) in enumerate(zip(VERSOES, ('#cf5f56', '#397faa'))):
        grupo = dados.loc[dados.Versao == versao]
        medias = grupo.groupby('Tarefa').Tentativas.mean().reindex(TAREFAS)
        maior_media = max(maior_media, float(medias.max()))
        n = grupo.Participante.nunique()
        barras = ax.bar(posicoes + (indice - 0.5) * largura, medias,
                        width=largura, color=cor, label=f'{versao.capitalize()} (n={n})', zorder=3)
        ax.bar_label(barras, labels=[f'{valor:.2f}'.replace('.', ',') for valor in medias],
                     padding=5, fontsize=11)
    ax.set_xticks(posicoes, TAREFAS)
    ax.set_xlabel('Tarefa')
    ax.set_ylabel('Média de tentativas por participante')
    ax.set_title('Média de tentativas por tarefa — Lambda e Omega', fontsize=15, pad=16)
    ax.set_ylim(0, max(2, maior_media * 1.22))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis='y', alpha=.2, zorder=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False)
    fig.text(.5, .02, 'As contagens incluem a tentativa correta. Barras representam médias, não totais.',
             ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(caminho, dpi=dpi, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coletas-dir', type=Path, default=Path.home()/'Documents/demo/coletas')
    parser.add_argument('--output-dir', type=Path, default=Path.home()/'Documents/demo/graficos/agregados/tentativas')
    parser.add_argument('--dpi', type=int, default=200)
    args = parser.parse_args()
    dados, fontes = carrega_tentativas(args.coletas_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dados.to_csv(args.output_dir/'tentativas_por_participante_tarefa.csv', index=False, encoding='utf-8-sig')
    fontes.to_csv(args.output_dir/'fontes_utilizadas.csv', index=False, encoding='utf-8-sig')
    resumo = dados.groupby(['Versao','Tarefa']).Tentativas.agg(
        Participantes='count', Media='mean', Mediana='median', Minimo='min', Maximo='max', Total='sum')
    resumo.to_csv(args.output_dir/'resumo_tentativas_por_versao.csv', encoding='utf-8-sig')
    gera_grafico(dados, args.output_dir/'comparacao_tentativas_barras.png', args.dpi)
    print(dados.groupby('Versao').Participante.nunique().to_dict())
    print(f'Resultados: {args.output_dir}')

if __name__ == '__main__':
    main()
