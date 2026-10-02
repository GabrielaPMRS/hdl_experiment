"""Gera agregados do quartil superior de tempo de fixacao na AOI1.

O ranking e separado por versao e tarefa. Entram os maiores tempos totais de
fixacao na AOI1, em quantidade equivalente ao quartil superior do grupo.
Os heatmaps mantem as fixacoes de todo o codigo e distinguem a AOI1 pela cor.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd

import gera_heatmaps_agregados_aoi as aoi
import gera_ideia_2 as ideia2
from fontes_agregados import seleciona_fontes


def calcula_selecao_aoi(fontes, aoi_config):
    with aoi_config.open(encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)
    linhas = []
    for versao in ideia2.VERSOES:
        pastas = [p for p, v in fontes if v == versao]
        for tarefa in ideia2.TAREFAS:
            codigo_xy, aoi_y = aoi.limites(configuracao, versao, tarefa)
            _, metricas = aoi.carrega_fixacoes(pastas, versao, tarefa, codigo_xy, aoi_y)
            for item in metricas:
                linhas.append({
                    "Participante": item["Participante"],
                    "Versao": versao,
                    "Tarefa": tarefa,
                    "TempoAOI1Segundos": item["TempoAOI1Segundos"],
                    "FixacoesAOI1": item["FixacoesAOI1"],
                    "TempoForaAOI1Segundos": item["TempoForaAOI1Segundos"],
                    "FixacoesForaAOI1": item["FixacoesForaAOI1"],
                    "ArquivoFixacoes": item["ArquivoFixacoes"],
                })

    selecao = pd.DataFrame(linhas).sort_values(
        ["Versao", "Tarefa", "TempoAOI1Segundos", "Participante"],
        ascending=[True, True, False, True],
    ).reset_index(drop=True)
    grupos = selecao.groupby(["Versao", "Tarefa"])
    selecao["Q3TempoAOI1Segundos"] = grupos["TempoAOI1Segundos"].transform(
        lambda valores: valores.quantile(0.75)
    )
    selecao["RankTempoAOI1Decrescente"] = grupos.cumcount() + 1
    selecao["ParticipantesNoGrupo"] = grupos["Participante"].transform("size")
    selecao["VagasQuartilSuperior"] = selecao.ParticipantesNoGrupo // 4
    if (selecao.VagasQuartilSuperior == 0).any():
        raise ValueError("Cada grupo precisa de pelo menos quatro participantes")
    selecao["IncluidoNosGraficos"] = (
        selecao.RankTempoAOI1Decrescente <= selecao.VagasQuartilSuperior
    )
    return selecao


def salva_selecao_aoi(output_dir, selecao):
    output_dir.mkdir(parents=True, exist_ok=True)
    colunas = [
        "Participante", "Versao", "Tarefa", "TempoAOI1Segundos",
        "FixacoesAOI1", "Q3TempoAOI1Segundos", "RankTempoAOI1Decrescente",
        "ParticipantesNoGrupo", "VagasQuartilSuperior", "ArquivoFixacoes",
    ]
    selecao.to_csv(output_dir / "avaliacao_quartil_superior_aoi1_por_tarefa.csv",
                   index=False, encoding="utf-8-sig", float_format="%.3f")
    for nome, mascara in (
        ("participantes_incluidos_por_tarefa.csv", selecao.IncluidoNosGraficos),
        ("participantes_excluidos_por_tarefa.csv", ~selecao.IncluidoNosGraficos),
    ):
        selecao.loc[mascara, colunas].to_csv(
            output_dir / nome, index=False, encoding="utf-8-sig", float_format="%.3f"
        )


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=Path.home() / "Documents/demo")
    parser.add_argument("--output-dir", type=Path,
                        help="Padrao: DEMO/graficos/agregados/ideia_3")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    demo_dir = args.demo_dir.resolve()
    output_dir = (args.output_dir.resolve() if args.output_dir
                  else demo_dir / "graficos" / "agregados" / "ideia_3")
    aoi_config = raiz / "config" / "aoi_por_versao.json"
    fontes = seleciona_fontes(demo_dir / "data", demo_dir / "recuperados" / "data")
    selecao = calcula_selecao_aoi(fontes, aoi_config)
    incluidos = ideia2.conjunto_incluido(selecao)
    salva_selecao_aoi(output_dir, selecao)

    ideia2.gera_heatmaps(output_dir / "heatmaps", demo_dir / "telas", aoi_config,
                         fontes, incluidos, args.dpi)
    ideia2.gera_heatmaps_aoi(output_dir / "heatmaps_aoi1", demo_dir / "telas",
                             aoi_config, fontes, incluidos, args.dpi)
    ideia2.gera_tempos(output_dir / "tempos", aoi_config, fontes, incluidos, args.dpi)
    ideia2.gera_tentativas(output_dir / "tentativas", demo_dir / "coletas",
                           incluidos, args.dpi)
    for pasta in ("heatmaps", "heatmaps_aoi1", "tempos"):
        ideia2.salva_fontes(output_dir / pasta / "fontes_utilizadas.csv",
                            fontes, incluidos, "dados", demo_dir)
    ideia2.salva_fontes(output_dir / "tentativas" / "fontes_utilizadas.csv",
                        fontes, incluidos, "json", demo_dir)

    contagens = selecao.loc[selecao.IncluidoNosGraficos].groupby(
        ["Versao", "Tarefa"]
    ).size().to_dict()
    print(f"Ideia 3 gerada em: {output_dir}")
    print(f"Participantes incluidos por versao/tarefa: {contagens}")


if __name__ == "__main__":
    main()
