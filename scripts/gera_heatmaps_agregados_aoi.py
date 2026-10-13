"""Aggregate only AOI fixations, with a shared accumulated-time density scale."""

from __future__ import annotations

from caminhos import raiz_dados
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fontes_agregados import salva_fontes, seleciona_fontes
from plot_common import LABELS, HEAT_CMAP, case_label, heat_scale
from gera_heatmaps_agregados import (
    ALTURA_TELA,
    LARGURA_TELA,
    TAREFAS,
    VERSOES,
    calcula_mapa,
)


def limites(configuracao: dict, versao: str, tarefa: str):
    try:
        item = configuracao[versao][tarefa]
        codigo, aoi = item["codigo"], item["aoi1"]
    except KeyError as erro:
        raise ValueError(f"Limites ausentes: {versao}/{tarefa}") from erro
    for nome, valores in (("codigo", codigo), ("aoi1", aoi)):
        if (not isinstance(valores, list) or len(valores) != 2
                or any(not isinstance(v, (int, float)) for v in valores)
                or min(valores) < 0 or max(valores) > ALTURA_TELA
                or valores[0] <= valores[1]):
            raise ValueError(
                f"{versao}/{tarefa}/{nome} deve ser [base, topo] em pixels da tela"
            )
    if not min(codigo) <= min(aoi) < max(aoi) <= max(codigo):
        raise ValueError(f"AOI1 fora do painel de codigo: {versao}/{tarefa}")
    codigo_xy = (245.0, 820.0, ALTURA_TELA - max(codigo), ALTURA_TELA - min(codigo))
    aoi_y = (ALTURA_TELA - max(aoi), ALTURA_TELA - min(aoi))
    return codigo_xy, aoi_y


def carrega_fixacoes(pastas, versao, tarefa, codigo_xy, aoi_y):
    xmin, xmax, ymin, ymax = codigo_xy
    aoi_min, aoi_max = aoi_y
    quadros = []
    linhas = []
    for pasta in pastas:
        caminho = pasta / f"Fixations {pasta.name} {tarefa}.csv"
        dados = pd.read_csv(caminho)
        if not {"x", "y", "duracao"}.issubset(dados.columns):
            raise ValueError(f"Colunas de fixacao ausentes: {caminho}")
        dados = dados.loc[
            np.isfinite(dados.x) & np.isfinite(dados.y)
            & np.isfinite(dados.duracao) & (dados.duracao > 0)
            & dados.x.between(xmin, xmax, inclusive="both")
            & dados.y.between(ymin, ymax, inclusive="both"),
            ["x", "y", "duracao"],
        ].copy()
        dentro = dados.y.between(aoi_min, aoi_max, inclusive="both")
        duracao_dentro = float(dados.loc[dentro, "duracao"].sum()) / 1000.0
        duracao_fora = float(dados.loc[~dentro, "duracao"].sum()) / 1000.0
        linhas.append({
            "Participante": pasta.name,
            "Versao": versao,
            "Tarefa": tarefa,
            "FixacoesAOI1": int(dentro.sum()),
            "TempoAOI1Segundos": duracao_dentro,
            "FixacoesForaAOI1": int((~dentro).sum()),
            "TempoForaAOI1Segundos": duracao_fora,
            "ArquivoFixacoes": str(caminho.resolve()),
        })
        if not dados.empty:
            quadros.append(dados.loc[dentro])
    if not quadros:
        return pd.DataFrame(columns=["x", "y", "duracao"]), linhas
    return pd.concat(quadros, ignore_index=True), linhas


def desenha(ax, imagem, mapa, codigo_xy, aoi_y, titulo, escala_maxima):
    xmin, xmax, ymin, ymax = codigo_xy
    xx, yy, densidade = mapa
    ax.imshow(mpimg.imread(imagem), extent=(0, LARGURA_TELA, 0, ALTURA_TELA),
              zorder=0, aspect="auto")

    # Density is estimated from AOI fixations only. Clip kernel tails at AOI edges.
    masked = np.ma.masked_where((yy < aoi_y[0]) | (yy > aoi_y[1]), densidade)
    ax.pcolormesh(xx, yy, masked, cmap=HEAT_CMAP, vmin=0,
                  vmax=max(escala_maxima, 1e-12), shading="gouraud", zorder=1)
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), title=titulo,
           xlabel="x-coordinate", ylabel="y-coordinate")


def salva_graficos(output_dir, tarefa, mapas, metadados, limites_por_versao,
                   imagens_dir, escala_maxima, dpi):
    def titulo(versao):
        item = metadados[versao]
        return (f"{LABELS[versao]} (n={item['Participantes']})\n"
                f"AOI total: {item['FixacoesAOI1']} fixations; "
                f"{item['TempoAOI1Segundos']:.1f} s")

    fig, eixos = plt.subplots(1, 2, figsize=(15, 8), layout="constrained")
    for ax, versao in zip(eixos, VERSOES):
        codigo_xy, aoi_y = limites_por_versao[versao]
        desenha(ax, imagens_dir / versao / f"{tarefa}.png", mapas[versao],
                codigo_xy, aoi_y, titulo(versao), escala_maxima)
    fig.suptitle(f"AOI-only fixation heatmaps — {case_label(tarefa)}")
    heat_scale(fig, eixos, escala_maxima)
    fig.savefig(output_dir / f"comparison_aoi_{tarefa.lower()}.png",
                dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path,
                        default=raiz_dados() / "data")
    parser.add_argument("--recovered-data-dir", type=Path)
    parser.add_argument("--images-dir", type=Path,
                        default=raiz_dados() / "telas")
    parser.add_argument("--aoi-config", type=Path,
                        default=raiz / "config/aoi_por_versao.json")
    parser.add_argument("--output-dir", type=Path,
                        default=raiz_dados() / "graficos/agregados/heatmaps_aoi1")
    parser.add_argument("--grid-size", type=int, default=160)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--permitir-grupos-desiguais", action="store_true")
    args = parser.parse_args()

    fontes = seleciona_fontes(args.data_dir, args.recovered_data_dir)
    grupos = {versao: [p for p, v in fontes if v == versao] for versao in VERSOES}
    quantidades = {v: len(grupos[v]) for v in VERSOES}
    if 0 in quantidades.values():
        raise ValueError(f"Os dois grupos precisam de participantes: {quantidades}")
    if (len(set(quantidades.values())) != 1
            and not args.permitir_grupos_desiguais):
        raise ValueError(f"Grupos com tamanhos diferentes: {quantidades}")
    with args.aoi_config.open(encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    salva_fontes(fontes, args.output_dir)
    detalhes = []
    resumos = []
    for tarefa in TAREFAS:
        mapas, metadados, limites_por_versao = {}, {}, {}
        for versao in VERSOES:
            codigo_xy, aoi_y = limites(configuracao, versao, tarefa)
            limites_por_versao[versao] = codigo_xy, aoi_y
            dados, linhas = carrega_fixacoes(
                grupos[versao], versao, tarefa, codigo_xy, aoi_y,
            )
            detalhes.extend(linhas)
            aoi_bounds = (*codigo_xy[:2], *aoi_y)
            mapas[versao] = calcula_mapa(dados, aoi_bounds,
                                         args.grid_size, args.grid_size)
            metadados[versao] = {
                "Participantes": len(grupos[versao]),
                "FixacoesAOI1": sum(l["FixacoesAOI1"] for l in linhas),
                "TempoAOI1Segundos": sum(l["TempoAOI1Segundos"] for l in linhas),
                "FixacoesForaAOI1": sum(l["FixacoesForaAOI1"] for l in linhas),
                "TempoForaAOI1Segundos": sum(l["TempoForaAOI1Segundos"] for l in linhas),
                "BaseAOI1Pixel": configuracao[versao][tarefa]["aoi1"][0],
                "TopoAOI1Pixel": configuracao[versao][tarefa]["aoi1"][1],
            }
        escala_maxima = max(float(mapas[v][2].max()) for v in VERSOES)
        for versao in VERSOES:
            resumos.append({"Versao": versao, "Tarefa": tarefa,
                            **metadados[versao],
                            "EscalaMaximaCompartilhada": escala_maxima})
        salva_graficos(args.output_dir, tarefa, mapas, metadados,
                       limites_por_versao, args.images_dir, escala_maxima, args.dpi)
        print(f"{tarefa}: With Atom={quantidades['lambda']}, Without Atom={quantidades['omega']}")

    names = {"Participante": "Participant", "Versao": "Condition", "Tarefa": "Task",
             "FixacoesAOI1": "AOIFixations", "TempoAOI1Segundos": "AOIFixationTimeSeconds",
             "FixacoesForaAOI1": "OutsideAOIFixations", "TempoForaAOI1Segundos": "OutsideAOIFixationTimeSeconds",
             "ArquivoFixacoes": "FixationSource", "Participantes": "Participants",
             "BaseAOI1Pixel": "AOIBottomPixel", "TopoAOI1Pixel": "AOITopPixel",
             "EscalaMaximaCompartilhada": "SharedScaleMaximum"}
    def english(rows):
        frame = pd.DataFrame(rows).rename(columns=names)
        frame["Condition"] = frame.Condition.map(LABELS)
        return frame
    english(detalhes).to_csv(
        args.output_dir / "participant_aoi_fixations.csv", index=False,
        encoding="utf-8-sig", float_format="%.6f",
    )
    english(resumos).to_csv(
        args.output_dir / "summary.csv", index=False,
        encoding="utf-8-sig", float_format="%.6f",
    )
    print(f"Resultados: {args.output_dir}")


if __name__ == "__main__":
    main()
