"""Gera a ideia 2 com corte do quartil superior por versao e tarefa.

Para cada combinacao Versao x Tarefa, o Q3 usa o tempo de aplicacao daquela
tarefa. Linhas acima do Q3 ficam fora dos agregados. Os heatmaps sao divididos
pelo numero de participantes para comparar grupos de tamanhos diferentes.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

import gera_heatmaps_agregados as heatmaps
import gera_tentativas_agregadas as tentativas
import gera_violin_tempo_aoi as tempos
from fontes_agregados import RECUPERADOS, seleciona_fontes


VERSOES = ("lambda", "omega")
TAREFAS = ("T01", "T02", "T04", "T05")


def carrega_sessao(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8-sig") as arquivo:
        sessao = json.load(arquivo)
    if isinstance(sessao, list):
        if len(sessao) != 1:
            raise ValueError(f"Esperada uma sessao em {caminho}")
        sessao = sessao[0]
    return sessao


def calcula_selecao(demo_dir: Path, por_nome: dict[str, tuple[Path, str]]):
    linhas = []
    for participante, (_, versao) in sorted(por_nome.items()):
        resultado = demo_dir / "coletas" / participante / f"resultado{participante}.json"
        if not resultado.is_file():
            raise FileNotFoundError(f"JSON ausente: {resultado}")
        sessao = carrega_sessao(resultado)
        perguntas = {
            f"T{int(p['codigoId'].split('-')[-1]):02d}": p
            for p in sessao["perguntas"]
        }
        ausentes = sorted(set(TAREFAS) - set(perguntas))
        if ausentes:
            raise ValueError(f"Tarefas ausentes em {resultado}: {', '.join(ausentes)}")
        for tarefa in TAREFAS:
            linhas.append({
                "Participante": participante,
                "Versao": versao,
                "Tarefa": tarefa,
                "TempoAplicacaoSegundos": float(perguntas[tarefa]["segundos"]),
                "FonteProcessamento": "recuperado" if participante in RECUPERADOS else "normal",
            })

    dados = pd.DataFrame(linhas)
    grupos = dados.groupby(["Versao", "Tarefa"], sort=False)
    dados["Q3VersaoTarefaSegundos"] = grupos["TempoAplicacaoSegundos"].transform(
        lambda valores: valores.quantile(0.75)
    )
    dados["RankTempoDecrescente"] = grupos["TempoAplicacaoSegundos"].rank(
        method="min", ascending=False
    ).astype(int)
    dados["AcimaQ3"] = dados.TempoAplicacaoSegundos > dados.Q3VersaoTarefaSegundos
    dados["IncluidoNosGraficos"] = ~dados.AcimaQ3
    excluidos = dados.loc[dados.AcimaQ3].groupby(["Versao", "Tarefa"]).size()
    if excluidos.nunique() != 1:
        raise ValueError(f"Quantidades desiguais acima do Q3: {excluidos.to_dict()}")
    return dados.sort_values(["Tarefa", "Versao", "RankTempoDecrescente"])


def salva_selecao(output_dir: Path, selecao: pd.DataFrame):
    output_dir.mkdir(parents=True, exist_ok=True)
    selecao.to_csv(
        output_dir / "avaliacao_quartil_tempo_por_tarefa.csv",
        index=False, encoding="utf-8-sig", float_format="%.3f",
    )
    colunas = ["Participante", "Versao", "Tarefa", "TempoAplicacaoSegundos",
               "Q3VersaoTarefaSegundos", "RankTempoDecrescente"]
    for nome, mascara in (
        ("participantes_incluidos_por_tarefa.csv", selecao.IncluidoNosGraficos),
        ("participantes_excluidos_por_tarefa.csv", selecao.AcimaQ3),
    ):
        selecao.loc[mascara, colunas].to_csv(
            output_dir / nome, index=False, encoding="utf-8-sig", float_format="%.3f"
        )


def conjunto_incluido(selecao: pd.DataFrame):
    return set(selecao.loc[
        selecao.IncluidoNosGraficos, ["Participante", "Tarefa"]
    ].itertuples(index=False, name=None))


def salva_fontes(caminho, fontes, incluidos, tipo, demo_dir):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Participante", "Versao", "Tarefa", "Origem", "Arquivo"])
        for pasta, versao in fontes:
            for tarefa in TAREFAS:
                if (pasta.name, tarefa) not in incluidos:
                    continue
                if tipo == "dados":
                    origem = "recuperado" if pasta.name in RECUPERADOS else "normal"
                    fonte = pasta / f"Fixations {pasta.name} {tarefa}.csv"
                else:
                    origem = "coleta"
                    fonte = demo_dir / "coletas" / pasta.name / f"resultado{pasta.name}.json"
                writer.writerow([pasta.name, versao, tarefa, origem, fonte])


def gera_heatmaps(output_dir, imagens_dir, aoi_config, fontes, incluidos, dpi):
    output_dir.mkdir(parents=True, exist_ok=True)
    for tarefa in TAREFAS:
        mapas, metadados, limites_por_versao = {}, {}, {}
        for versao in VERSOES:
            pastas = [p for p, v in fontes if v == versao and (p.name, tarefa) in incluidos]
            limites = heatmaps.carrega_limites_codigo(aoi_config, versao, tarefa)
            dados, usados = heatmaps.agrega_fixacoes(pastas, tarefa, limites)
            mapa = heatmaps.calcula_mapa(dados, limites, 100, 100)
            n = len(usados)
            mapas[versao] = (mapa[0], mapa[1], mapa[2] / n)
            limites_por_versao[versao] = limites
            metadados[versao] = (n, len(dados) / n, float(dados.duracao.sum()) / 1000.0 / n)

        escala_maxima = max(float(mapas[v][2].max()) for v in VERSOES)
        for versao in VERSOES:
            n, fix_media, duracao_media = metadados[versao]
            titulo = (f"{versao.capitalize()} - {tarefa} ({n} participantes; "
                      f"{fix_media:.1f} fixacoes/p.; {duracao_media:.1f} s/p.)")
            heatmaps.salva_individual(
                output_dir / f"heatmap_{versao}_{tarefa}.png",
                imagens_dir / versao / f"{tarefa}.png", mapas[versao],
                limites_por_versao[versao], titulo, escala_maxima, dpi,
            )

        fig, eixos = plt.subplots(1, 2, figsize=(14, 8))
        for eixo, versao in zip(eixos, VERSOES):
            n, fix_media, duracao_media = metadados[versao]
            heatmaps.desenha(
                eixo, imagens_dir / versao / f"{tarefa}.png", mapas[versao],
                limites_por_versao[versao],
                f"{versao.capitalize()} ({n} participantes; {fix_media:.1f} fixacoes/p.; "
                f"{duracao_media:.1f} s/p.)", escala_maxima,
            )
        fig.suptitle(f"Heatmaps medios por participante - {tarefa}")
        fig.tight_layout()
        fig.savefig(output_dir / f"comparacao_lambda_omega_{tarefa}.png",
                    dpi=dpi, bbox_inches="tight")
        plt.close(fig)


def filtra_linhas(dados, incluidos):
    mascara = [(p, t) in incluidos for p, t in zip(dados.Participante, dados.Tarefa)]
    return dados.loc[mascara].copy()


def salva_resumos_tempo(dados, output_dir, regiao):
    dados.to_csv(output_dir / f"tempos_{regiao}_por_participante_tarefa.csv",
                 index=False, encoding="utf-8-sig", float_format="%.3f")
    pivoteado = dados.pivot(index=["Participante", "Versao"], columns="Tarefa",
                            values="TempoFixacaoRegiaoSegundos").reset_index()
    pivoteado.columns.name = None
    presentes = [t for t in TAREFAS if t in pivoteado.columns]
    pivoteado["TarefasIncluidas"] = pivoteado[presentes].notna().sum(axis=1)
    pivoteado["TotalSegundosTarefasIncluidas"] = pivoteado[presentes].sum(axis=1, min_count=1)
    pivoteado["MediaSegundosTarefasIncluidas"] = pivoteado[presentes].mean(axis=1)
    pivoteado.to_csv(output_dir / f"resumo_tempos_{regiao}_por_participante.csv",
                     index=False, encoding="utf-8-sig", float_format="%.3f")
    resumo = dados.groupby(["Versao", "Tarefa"])["TempoFixacaoRegiaoSegundos"].agg(
        Participantes="count", MediaSegundos="mean", MedianaSegundos="median",
        DesvioPadraoSegundos="std", MinimoSegundos="min", MaximoSegundos="max",
    ).reset_index()
    resumo.to_csv(output_dir / f"resumo_tempos_{regiao}_por_versao.csv",
                  index=False, encoding="utf-8-sig", float_format="%.3f")


def gera_tempos(output_dir, aoi_config, fontes, incluidos, dpi):
    output_dir.mkdir(parents=True, exist_ok=True)
    configuracao = tempos.carrega_configuracao(aoi_config)
    for regiao in ("codigo", "aoi1"):
        dados = tempos.calcula_tempos(Path(), configuracao, regiao, participantes=fontes)
        dados = filtra_linhas(dados, incluidos)
        salva_resumos_tempo(dados, output_dir, regiao)
        tempos.gera_grafico(dados, output_dir / f"violin_tempo_fixacao_{regiao}.png",
                            dpi, regiao)


def gera_grafico_tentativas(dados, caminho, dpi):
    fig, ax = plt.subplots(figsize=(10, 6))
    posicoes, largura, maior_media = np.arange(len(TAREFAS)), 0.34, 0.0
    for indice, (versao, cor) in enumerate(zip(VERSOES, ("#cf5f56", "#397faa"))):
        grupo = dados.loc[dados.Versao == versao]
        medias = grupo.groupby("Tarefa").Tentativas.mean().reindex(TAREFAS)
        contagens = grupo.groupby("Tarefa").Participante.nunique().reindex(TAREFAS)
        if contagens.nunique() != 1:
            raise ValueError(f"N varia entre tarefas em {versao}: {contagens.to_dict()}")
        n = int(contagens.iloc[0])
        maior_media = max(maior_media, float(medias.max()))
        barras = ax.bar(posicoes + (indice - 0.5) * largura, medias, width=largura,
                        color=cor, label=f"{versao.capitalize()} (n={n} por tarefa)", zorder=3)
        ax.bar_label(barras, labels=[f"{v:.2f}".replace(".", ",") for v in medias],
                     padding=5, fontsize=11)
    ax.set_xticks(posicoes, TAREFAS)
    ax.set(xlabel="Tarefa", ylabel="Media de tentativas por participante",
           title="Media de tentativas por tarefa - Lambda e Omega")
    ax.set_ylim(0, max(2, maior_media * 1.22))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(caminho, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def gera_tentativas(output_dir, coletas_dir, incluidos, dpi):
    output_dir.mkdir(parents=True, exist_ok=True)
    dados, _ = tentativas.carrega_tentativas(coletas_dir)
    dados = filtra_linhas(dados, incluidos)
    dados.to_csv(output_dir / "tentativas_por_participante_tarefa.csv",
                 index=False, encoding="utf-8-sig")
    resumo = dados.groupby(["Versao", "Tarefa"]).Tentativas.agg(
        Participantes="count", Media="mean", Mediana="median", Minimo="min",
        Maximo="max", Total="sum")
    resumo.to_csv(output_dir / "resumo_tentativas_por_versao.csv",
                  encoding="utf-8-sig", float_format="%.3f")
    gera_grafico_tentativas(dados, output_dir / "comparacao_tentativas_barras.png", dpi)


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=Path.home() / "Documents/demo")
    parser.add_argument("--output-dir", type=Path,
                        help="Padrao: DEMO/graficos/agregados/ideia_2")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    demo_dir = args.demo_dir.resolve()
    output_dir = (args.output_dir.resolve() if args.output_dir
                  else demo_dir / "graficos" / "agregados" / "ideia_2")
    aoi_config = raiz / "config" / "aoi_por_versao.json"
    fontes = seleciona_fontes(demo_dir / "data", demo_dir / "recuperados" / "data")
    por_nome = {pasta.name: (pasta, versao) for pasta, versao in fontes}
    selecao = calcula_selecao(demo_dir, por_nome)
    incluidos = conjunto_incluido(selecao)
    salva_selecao(output_dir, selecao)

    gera_heatmaps(output_dir / "heatmaps", demo_dir / "telas", aoi_config,
                   fontes, incluidos, args.dpi)
    gera_tempos(output_dir / "tempos", aoi_config, fontes, incluidos, args.dpi)
    gera_tentativas(output_dir / "tentativas", demo_dir / "coletas", incluidos, args.dpi)
    salva_fontes(output_dir / "heatmaps" / "fontes_utilizadas.csv",
                  fontes, incluidos, "dados", demo_dir)
    salva_fontes(output_dir / "tempos" / "fontes_utilizadas.csv",
                  fontes, incluidos, "dados", demo_dir)
    salva_fontes(output_dir / "tentativas" / "fontes_utilizadas.csv",
                  fontes, incluidos, "json", demo_dir)

    contagens = selecao.loc[selecao.IncluidoNosGraficos].groupby(
        ["Versao", "Tarefa"]
    ).size().to_dict()
    print(f"Ideia 2 corrigida em: {output_dir}")
    print(f"Participantes incluidos por versao/tarefa: {contagens}")


if __name__ == "__main__":
    main()
