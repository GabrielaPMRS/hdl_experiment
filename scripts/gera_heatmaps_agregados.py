"""Gera heatmaps agregados das fixacoes dos grupos Lambda e Omega.

O script usa os arquivos ``Fixations Pxx Txx.csv`` produzidos por
``main_script_adap.py`` e confirma a condicao em ``resumo_tarefas.csv``.
Para cada tarefa, sao gerados os dois mapas individuais e uma comparacao
lado a lado. A escala de cores e identica entre Lambda e Omega.
"""

from __future__ import annotations

from caminhos import raiz_dados
import argparse
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as st
from fontes_agregados import seleciona_fontes, salva_fontes
from plot_common import LABELS, HEAT_CMAP, case_label, heat_scale


VERSOES = ("lambda", "omega")
TAREFAS = tuple(f"T{numero:02d}" for numero in (1, 2, 4, 5))
LARGURA_TELA = 1920
ALTURA_TELA = 1080


def numero_participante(nome: str) -> int:
    correspondencia = re.fullmatch(r"P(\d+)", nome, flags=re.IGNORECASE)
    if not correspondencia:
        raise ValueError(f"Nome de participante invalido: {nome}")
    return int(correspondencia.group(1))


def versao_esperada(participante: str) -> str:
    return "lambda" if numero_participante(participante) % 2 == 0 else "omega"


def descobre_participantes(data_dir: Path, recovered_dir=None) -> dict[str, list[Path]]:
    grupos = {versao: [] for versao in VERSOES}
    for pasta, versao in seleciona_fontes(data_dir, recovered_dir):
        grupos[versao].append(pasta)
    return grupos


def carrega_limites_codigo(aoi_config: Path, versao: str, tarefa: str):
    with aoi_config.open(encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)
    try:
        codigo = configuracao[versao][tarefa]["codigo"]
    except KeyError as erro:
        raise ValueError(f"AOI ausente para {versao}/{tarefa}") from erro
    if not isinstance(codigo, list) or len(codigo) != 2 or None in codigo:
        raise ValueError(f"Limite do codigo incompleto para {versao}/{tarefa}")
    topo, base = min(codigo), max(codigo)
    return 245.0, 820.0, ALTURA_TELA - base, ALTURA_TELA - topo


def agrega_fixacoes(pastas: list[Path], tarefa: str, limites):
    quadros = []
    usados = []
    xmin, xmax, ymin, ymax = limites
    for pasta in pastas:
        caminho = pasta / f"Fixations {pasta.name} {tarefa}.csv"
        if not caminho.is_file():
            raise FileNotFoundError(f"Fixacoes ausentes: {caminho}")
        dados = pd.read_csv(caminho)
        colunas = {"x", "y", "duracao"}
        if not colunas.issubset(dados.columns):
            raise ValueError(f"Colunas {sorted(colunas)} ausentes em {caminho}")
        dados = dados.loc[
            dados.x.between(xmin, xmax, inclusive="both")
            & dados.y.between(ymin, ymax, inclusive="both")
            & (dados.duracao > 0),
            ["x", "y", "duracao"],
        ].dropna()
        if not dados.empty:
            quadros.append(dados)
            usados.append(pasta.name)
    if not quadros:
        return pd.DataFrame(columns=["x", "y", "duracao"]), usados
    return pd.concat(quadros, ignore_index=True), usados


def calcula_mapa(dados: pd.DataFrame, limites, largura: int, altura: int):
    xmin, xmax, ymin, ymax = limites
    xx, yy = np.mgrid[
        xmin:xmax:complex(0, largura),
        ymin:ymax:complex(0, altura),
    ]
    posicoes = np.vstack([xx.ravel(), yy.ravel()])
    if dados.empty:
        return xx, yy, np.zeros_like(xx)
    valores = np.vstack([dados.x, dados.y])
    try:
        kernel = st.gaussian_kde(valores, weights=dados.duracao)
        densidade = np.reshape(kernel(posicoes).T, xx.shape)
    except (ValueError, np.linalg.LinAlgError):
        # Sparse/collinear data: fixed 25-pixel Gaussian kernels, never discard a group.
        densidade = np.zeros_like(xx)
        for x, y, weight in zip(dados.x, dados.y, dados.duracao):
            densidade += weight * np.exp(-((xx-x)**2 + (yy-y)**2)/(2*25**2)) / (2*np.pi*25**2)
        return xx, yy, densidade
    # gaussian_kde normaliza os pesos para que a integral seja 1. Restaurar a
    # duracao total transforma o resultado em densidade acumulada de tempo,
    # permitindo comparar os dois grupos em uma mesma escala absoluta.
    densidade *= float(dados.duracao.sum())
    return xx, yy, densidade


def desenha(ax, imagem_path: Path, mapa, limites, titulo: str, escala_maxima: float):
    xmin, xmax, ymin, ymax = limites
    xx, yy, densidade = mapa
    imagem = mpimg.imread(imagem_path)
    ax.imshow(
        imagem,
        extent=(0, LARGURA_TELA, 0, ALTURA_TELA),
        zorder=0,
        aspect="auto",
    )

    ax.pcolormesh(xx, yy, densidade, cmap=HEAT_CMAP,
                  vmin=0, vmax=max(escala_maxima, 1e-12), shading="gouraud", zorder=1)
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), title=titulo)
    ax.set_xlabel("x-coordinate")
    ax.set_ylabel("y-coordinate")


def main() -> None:
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=raiz_dados() / "data")
    parser.add_argument("--images-dir", type=Path, default=raiz_dados() / "telas")
    parser.add_argument("--output-dir", type=Path, default=raiz_dados() / "graficos/agregados/heatmaps")
    parser.add_argument("--aoi-config", type=Path, default=raiz / "config/aoi_por_versao.json")
    parser.add_argument("--grid-width", type=int, default=160)
    parser.add_argument("--grid-height", type=int, default=160)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument(
        "--permitir-grupos-desiguais",
        action="store_true",
        help="Gera os mapas mesmo se os grupos tiverem tamanhos diferentes",
    )
    parser.add_argument("--recovered-data-dir", type=Path, help="Padrao: pasta recuperados/data ao lado de data")
    args = parser.parse_args()

    grupos = descobre_participantes(args.data_dir, args.recovered_data_dir)
    quantidades = {versao: len(pastas) for versao, pastas in grupos.items()}
    if 0 in quantidades.values():
        raise ValueError(f"Os dois grupos precisam ter participantes: {quantidades}")
    if len(set(quantidades.values())) != 1 and not args.permitir_grupos_desiguais:
        raise ValueError(
            f"Grupos com tamanhos diferentes: {quantidades}. "
            "Complete a coleta ou use --permitir-grupos-desiguais."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    salva_fontes(sorted([(pasta, versao) for versao, pastas in grupos.items() for pasta in pastas]), args.output_dir)
    print(f"Participants: With Atom={quantidades['lambda']}, Without Atom={quantidades['omega']}")

    summary = []
    for tarefa in TAREFAS:
        mapas = {}
        metadados = {}
        limites_por_versao = {}
        for versao in VERSOES:
            limites = carrega_limites_codigo(args.aoi_config, versao, tarefa)
            limites_por_versao[versao] = limites
            dados, usados = agrega_fixacoes(grupos[versao], tarefa, limites)
            mapas[versao] = calcula_mapa(
                dados, limites, args.grid_width, args.grid_height
            )
            metadados[versao] = (
                len(dados),
                usados,
                float(dados.duracao.sum()) / 1000.0,
            )

        escala_maxima = max(float(mapas[v][2].max()) for v in VERSOES)
        for versao in VERSOES:
            n_fixacoes, usados, duracao_total = metadados[versao]
            summary.append(dict(Task=tarefa, Condition=LABELS[versao], Participants=len(grupos[versao]),
                                Contributors=len(usados), TotalFixations=n_fixacoes,
                                TotalFixationTimeSeconds=duracao_total, SharedScaleMaximum=escala_maxima))

        fig, eixos = plt.subplots(1, 2, figsize=(15, 8), layout="constrained")
        for ax, versao in zip(eixos, VERSOES):
            n_fixacoes, usados, duracao_total = metadados[versao]
            desenha(
                ax,
                args.images_dir / versao / f"{tarefa}.png",
                mapas[versao],
                limites_por_versao[versao],
                f"{LABELS[versao]} (n={len(grupos[versao])})\n"
                f"Total: {n_fixacoes} fixations; {duracao_total:.1f} s",
                escala_maxima,
            )
        fig.suptitle(f"Aggregated fixation heatmaps — {case_label(tarefa)}")
        heat_scale(fig, eixos, escala_maxima)
        fig.savefig(args.output_dir / f"comparison_{tarefa.lower()}.png", dpi=args.dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"{tarefa}: heatmaps generated")
    pd.DataFrame(summary).to_csv(args.output_dir / "summary.csv", index=False)


if __name__ == "__main__":
    main()
