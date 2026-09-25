"""Gera violin plots e resumos do tempo de fixacao em uma regiao.

A regiao e lida de ``config/aoi_por_versao.json`` e pode ser o painel completo
do codigo (padrao) ou a AOI1. O tempo e a soma das duracoes das fixacoes cujo
ponto representativo esta dentro da regiao selecionada.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from fontes_agregados import seleciona_fontes, salva_fontes


VERSOES = ("lambda", "omega")
TAREFAS = tuple(f"T{numero:02d}" for numero in (1, 2, 4, 5))
REGIOES = ("codigo", "aoi1")
ALTURA_TELA = 1080.0
X_MIN_CODIGO = 245.0
X_MAX_CODIGO = 820.0


def carrega_configuracao(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)
    for versao in VERSOES:
        for tarefa in TAREFAS:
            for regiao in REGIOES:
                try:
                    limites = configuracao[versao][tarefa][regiao]
                except KeyError as erro:
                    raise ValueError(
                        f"Regiao {regiao} ausente: {versao}/{tarefa}"
                    ) from erro
                if (
                    not isinstance(limites, list)
                    or len(limites) != 2
                    or None in limites
                ):
                    raise ValueError(
                        f"Regiao {regiao} incompleta: {versao}/{tarefa}"
                    )
    return configuracao


def limites_regiao(configuracao: dict, versao: str, tarefa: str, regiao: str):
    """Converte os limites medidos desde o topo para o eixo Y dos graficos."""
    limites = configuracao[versao][tarefa][regiao]
    topo, base = min(limites), max(limites)
    y_min = ALTURA_TELA - base
    y_max = ALTURA_TELA - topo
    return X_MIN_CODIGO, X_MAX_CODIGO, y_min, y_max


def descobre_participantes(data_dir: Path, recovered_dir=None):
    return seleciona_fontes(data_dir, recovered_dir)


def calcula_tempos(
    data_dir: Path, configuracao: dict, regiao: str, participantes=None
) -> pd.DataFrame:
    linhas = []
    if participantes is None:
        participantes = descobre_participantes(data_dir)
    if not participantes:
        raise ValueError(f"Nenhum participante processado encontrado em {data_dir}")

    for pasta, versao in participantes:
        for tarefa in TAREFAS:
            caminho = pasta / f"Fixations {pasta.name} {tarefa}.csv"
            if not caminho.is_file():
                raise FileNotFoundError(f"Fixacoes ausentes: {caminho}")
            dados = pd.read_csv(caminho)
            colunas = {"x", "y", "duracao"}
            if not colunas.issubset(dados.columns):
                raise ValueError(f"Colunas {sorted(colunas)} ausentes em {caminho}")

            x_min, x_max, y_min, y_max = limites_regiao(
                configuracao, versao, tarefa, regiao
            )
            fixacoes_regiao = dados.loc[
                dados.x.between(x_min, x_max, inclusive="both")
                & dados.y.between(y_min, y_max, inclusive="both")
                & (dados.duracao > 0),
                ["duracao"],
            ].dropna()
            duracao_ms = float(fixacoes_regiao.duracao.sum())
            linhas.append(
                {
                    "Participante": pasta.name,
                    "Versao": versao,
                    "Tarefa": tarefa,
                    "Regiao": regiao,
                    "NumFixacoesRegiao": len(fixacoes_regiao),
                    "TempoFixacaoRegiaoSegundos": duracao_ms / 1000.0,
                }
            )

    return pd.DataFrame(linhas)


def salva_resumos(dados: pd.DataFrame, output_dir: Path, regiao: str):
    detalhado = output_dir / f"tempos_{regiao}_por_participante_tarefa.csv"
    dados.to_csv(detalhado, index=False, encoding="utf-8-sig", float_format="%.3f")

    tempos = dados.pivot(
        index=["Participante", "Versao"],
        columns="Tarefa",
        values="TempoFixacaoRegiaoSegundos",
    ).reset_index()
    tempos.columns.name = None
    tempos["TotalSegundos"] = tempos[list(TAREFAS)].sum(axis=1)
    tempos["MediaPorTarefaSegundos"] = tempos[list(TAREFAS)].mean(axis=1)
    tempos.to_csv(
        output_dir / f"resumo_tempos_{regiao}_por_participante.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.3f",
    )

    por_versao = (
        dados.groupby(["Versao", "Tarefa"])["TempoFixacaoRegiaoSegundos"]
        .agg(
            Participantes="count",
            MediaSegundos="mean",
            MedianaSegundos="median",
            DesvioPadraoSegundos="std",
            MinimoSegundos="min",
            MaximoSegundos="max",
        )
        .reset_index()
    )
    por_versao.to_csv(
        output_dir / f"resumo_tempos_{regiao}_por_versao.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.3f",
    )


def gera_grafico(dados: pd.DataFrame, caminho: Path, dpi: int, regiao: str):
    sns.set_theme(style="whitegrid")
    paleta = {"lambda": "#ef9a8f", "omega": "#8ebad3"}
    fig, eixos = plt.subplots(2, 2, figsize=(12, 10), sharey=False)

    for eixo, tarefa in zip(eixos.flat, TAREFAS):
        dados_tarefa = dados.loc[dados.Tarefa == tarefa]
        sns.violinplot(
            data=dados_tarefa,
            x="Versao",
            y="TempoFixacaoRegiaoSegundos",
            hue="Versao",
            order=list(VERSOES),
            hue_order=list(VERSOES),
            palette=paleta,
            inner=None,
            cut=0,
            linewidth=1,
            legend=False,
            ax=eixo,
        )
        sns.stripplot(
            data=dados_tarefa,
            x="Versao",
            y="TempoFixacaoRegiaoSegundos",
            order=list(VERSOES),
            color="black",
            size=6,
            jitter=0.08,
            ax=eixo,
        )
        eixo.set_title(tarefa)
        eixo.set_xlabel("")
        rotulo_regiao = "codigo" if regiao == "codigo" else "AOI1"
        eixo.set_ylabel(f"Tempo de fixacao no {rotulo_regiao} (s)")
        eixo.set_xticks([0, 1])
        eixo.set_xticklabels(["Lambda", "Omega"])

    titulo_regiao = "regiao do codigo" if regiao == "codigo" else "AOI1"
    fig.suptitle(f"Tempo de fixacao na {titulo_regiao} por tarefa", fontsize=16)
    fig.tight_layout()
    fig.savefig(caminho, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path, default=Path.home() / "Documents/demo/data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / "Documents/demo/graficos/agregados/tempos",
    )
    parser.add_argument(
        "--aoi-config", type=Path, default=raiz / "config/aoi_por_versao.json"
    )
    parser.add_argument(
        "--regiao",
        choices=REGIOES,
        default="codigo",
        help="Regiao usada no calculo: codigo (padrao) ou aoi1",
    )
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--recovered-data-dir", type=Path, help="Padrao: pasta recuperados/data ao lado de data")
    args = parser.parse_args()

    configuracao = carrega_configuracao(args.aoi_config)
    fontes = descobre_participantes(args.data_dir, args.recovered_data_dir)
    dados = calcula_tempos(args.data_dir, configuracao, args.regiao, participantes=fontes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    salva_fontes(fontes, args.output_dir)
    salva_resumos(dados, args.output_dir, args.regiao)
    gera_grafico(
        dados,
        args.output_dir / f"violin_tempo_fixacao_{args.regiao}.png",
        args.dpi,
        args.regiao,
    )
    quantidades = dados.groupby("Versao").Participante.nunique().to_dict()
    print(f"Participantes por versao: {quantidades}")
    print(f"Resultados salvos em: {args.output_dir}")


if __name__ == "__main__":
    main()
