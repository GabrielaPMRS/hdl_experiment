"""Selecao unica das fontes normais e recuperadas para os agregadores."""
import csv
import re
from pathlib import Path
import pandas as pd

RECUPERADOS = frozenset({'P00', 'P03', 'P09', 'P11'})
TAREFAS = {'T01', 'T02', 'T04', 'T05'}


def seleciona_fontes(data_dir, recovered_dir=None):
    data_dir = Path(data_dir)
    recovered_dir = Path(recovered_dir) if recovered_dir is not None else data_dir.parent / 'recuperados' / 'data'
    def inventario(raiz):
        pastas = {}
        for pasta in raiz.glob('P*'):
            if not pasta.is_dir() or not re.fullmatch(r'P\d+', pasta.name):
                continue
            nome = f'P{int(pasta.name[1:]):02d}'
            if nome != pasta.name:
                raise ValueError(f'Nome nao canonico de participante: {pasta}; esperado {nome}')
            pastas[nome] = pasta
        return pastas
    normais, recuperadas = inventario(data_dir), inventario(recovered_dir)
    nomes = sorted(set(normais) | set(recuperadas))
    if not nomes:
        raise ValueError(f'Nenhum participante encontrado em {data_dir} ou {recovered_dir}')
    fontes = []
    for nome in nomes:
        especial = nome in RECUPERADOS
        pasta = (recovered_dir if especial else data_dir) / nome
        resumo_path = pasta / 'resumo_tarefas.csv'
        if not resumo_path.is_file():
            raise FileNotFoundError(f'Fonte obrigatoria ausente: {resumo_path}. Nao sera usada outra versao.')
        resumo = pd.read_csv(resumo_path)
        required = {'Participante', 'TarefaReal', 'PosicaoExecucao', 'VersaoExperimento'}
        if not required.issubset(resumo.columns):
            raise ValueError(f'Resumo incompleto: {resumo_path}')
        versao = 'lambda' if int(nome[1:]) % 2 == 0 else 'omega'
        if (len(resumo) != 4 or set(resumo.TarefaReal) != TAREFAS
                or set(resumo.PosicaoExecucao) != {1, 2, 3, 4}
                or set(resumo.Participante) != {nome}
                or set(resumo.VersaoExperimento.str.lower()) != {versao}):
            raise ValueError(f'Mapeamento inconsistente: {resumo_path}')
        for tarefa in sorted(TAREFAS):
            arquivo = pasta / f'Fixations {nome} {tarefa}.csv'
            if not arquivo.is_file():
                raise FileNotFoundError(f'Fixacoes obrigatorias ausentes: {arquivo}')
            if not {'x', 'y', 'duracao'}.issubset(pd.read_csv(arquivo, nrows=0).columns):
                raise ValueError(f'Colunas de fixacao ausentes: {arquivo}')
        fontes.append((pasta.resolve(), versao))
    return fontes


def salva_fontes(fontes, output_dir):
    caminho = Path(output_dir) / 'fontes_utilizadas.csv'
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Participante', 'Versao', 'Origem', 'Pasta', 'Resumo'])
        for pasta, versao in fontes:
            writer.writerow([pasta.name, versao,
                             'recuperado' if pasta.name in RECUPERADOS else 'normal',
                             str(pasta), str(pasta / 'resumo_tarefas.csv')])
