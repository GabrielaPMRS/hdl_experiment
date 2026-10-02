"""Gera dois CSVs para inspecao dos participantes Lambda e Omega.

Cada linha representa um participante em uma tarefa. As metricas oculares
usam a mesma area do codigo e as mesmas fontes normais/recuperadas dos
heatmaps agregados.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from fontes_agregados import RECUPERADOS, seleciona_fontes


TAREFAS = ("T01", "T02", "T04", "T05")
ALTURA_TELA = 1080.0
X_MIN_CODIGO = 245.0
X_MAX_CODIGO = 820.0
METRICAS_OUTLIER = (
    "TempoAplicacaoSegundos",
    "FixacoesCodigo",
    "TempoFixacaoCodigoSegundos",
    "Tentativas",
)


def carrega_aoi(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def limites_codigo(configuracao: dict, versao: str, tarefa: str):
    topo, base = sorted(configuracao[versao][tarefa]["codigo"])
    return (
        X_MIN_CODIGO,
        X_MAX_CODIGO,
        ALTURA_TELA - base,
        ALTURA_TELA - topo,
    )


def carrega_sessao(coletas_dir: Path, participante: str) -> tuple[dict, Path]:
    caminho = coletas_dir / participante / f"resultado{participante}.json"
    if not caminho.is_file():
        raise FileNotFoundError(f"JSON da coleta ausente: {caminho}")
    with caminho.open(encoding="utf-8-sig") as arquivo:
        sessao = json.load(arquivo)
    if isinstance(sessao, list):
        if len(sessao) != 1:
            raise ValueError(f"Esperada uma sessao em {caminho}")
        sessao = sessao[0]
    return sessao, caminho.resolve()


def calcula_linhas(
    fontes: list[tuple[Path, str]],
    coletas_dir: Path,
    configuracao: dict,
) -> pd.DataFrame:
    linhas = []
    for pasta, versao in fontes:
        participante = pasta.name
        sessao, json_path = carrega_sessao(coletas_dir, participante)
        if sessao.get("participanteId") != participante:
            raise ValueError(f"Participante inconsistente em {json_path}")
        if str(sessao.get("versaoExperimento", "")).lower() != versao:
            raise ValueError(f"Versao inconsistente em {json_path}")

        perguntas = {
            f"T{int(pergunta['codigoId'].split('-')[-1]):02d}": pergunta
            for pergunta in sessao["perguntas"]
        }
        resumo_path = pasta / "resumo_tarefas.csv"
        resumo = pd.read_csv(resumo_path)
        mapeamento = resumo.set_index("TarefaReal")
        demografia = sessao.get("demografia", {})

        for tarefa in TAREFAS:
            pergunta = perguntas[tarefa]
            item = mapeamento.loc[tarefa]
            fixacoes_path = pasta / f"Fixations {participante} {tarefa}.csv"
            fixacoes = pd.read_csv(fixacoes_path)
            fixacoes = fixacoes.loc[
                np.isfinite(fixacoes.x)
                & np.isfinite(fixacoes.y)
                & np.isfinite(fixacoes.duracao)
                & (fixacoes.duracao > 0)
            ].copy()
            xmin, xmax, ymin, ymax = limites_codigo(
                configuracao, versao, tarefa
            )
            no_codigo = fixacoes.loc[
                fixacoes.x.between(xmin, xmax, inclusive="both")
                & fixacoes.y.between(ymin, ymax, inclusive="both")
            ]
            tempo_aplicacao = float(pergunta["segundos"])
            tempo_codigo = float(no_codigo.duracao.sum()) / 1000.0
            linhas.append(
                {
                    "Participante": participante,
                    "Versao": versao,
                    "Tarefa": tarefa,
                    "PosicaoExecucao": int(pergunta["ordemExecucao"]),
                    "CodigoId": pergunta["codigoId"],
                    "FonteProcessamento": (
                        "recuperado" if participante in RECUPERADOS else "normal"
                    ),
                    "MetodoSegmentacao": item.get(
                        "Metodo", "gaps_eye_tracker"
                    ),
                    "TempoAplicacaoSegundos": tempo_aplicacao,
                    "Tentativas": int(pergunta["tentativas"]),
                    "FixacoesTela": int(len(fixacoes)),
                    "TempoFixacaoTelaSegundos": (
                        float(fixacoes.duracao.sum()) / 1000.0
                    ),
                    "FixacoesCodigo": int(len(no_codigo)),
                    "TempoFixacaoCodigoSegundos": tempo_codigo,
                    "DuracaoMediaFixacaoCodigoMs": (
                        float(no_codigo.duracao.mean())
                        if not no_codigo.empty
                        else 0.0
                    ),
                    "PercentualTempoAplicacaoEmFixacaoCodigo": (
                        100.0 * tempo_codigo / tempo_aplicacao
                        if tempo_aplicacao > 0
                        else np.nan
                    ),
                    "ExperienciaAnos": demografia.get("experienciaAnos", ""),
                    "Proficiencia": demografia.get("proficiencia", ""),
                    "ExperienciaHardware": demografia.get(
                        "experienciaHardware", ""
                    ),
                    "AreaExperiencia": demografia.get("areaExperiencia", ""),
                    "ExperienciaSoftware": demografia.get(
                        "experienciaSoftware", ""
                    ),
                    "ArquivoResultado": str(json_path),
                    "PastaDadosOculares": str(pasta.resolve()),
                }
            )

    dados = pd.DataFrame(linhas)
    if dados.duplicated(["Participante", "Tarefa"]).any():
        raise ValueError("Ha linhas duplicadas por participante e tarefa")
    return dados


def adiciona_indicadores_exploratorios(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.copy()
    grupos = dados.groupby(["Versao", "Tarefa"], sort=False)

    for metrica in METRICAS_OUTLIER:
        mediana = grupos[metrica].transform("median")
        q1 = grupos[metrica].transform(lambda valores: valores.quantile(0.25))
        q3 = grupos[metrica].transform(lambda valores: valores.quantile(0.75))
        iqr = q3 - q1
        inferior = q1 - 1.5 * iqr
        superior = q3 + 1.5 * iqr
        dados[f"MedianaGrupo_{metrica}"] = mediana
        dados[f"RazaoParaMediana_{metrica}"] = np.where(
            mediana > 0, dados[metrica] / mediana, np.nan
        )
        dados[f"RankDecrescente_{metrica}"] = grupos[metrica].rank(
            method="min", ascending=False
        ).astype(int)
        dados[f"OutlierIQR_{metrica}"] = (
            (dados[metrica] < inferior) | (dados[metrica] > superior)
        )

    dados["TempoAplicacaoAcimaDobroMediana"] = (
        dados["RazaoParaMediana_TempoAplicacaoSegundos"] > 2.0
    )
    colunas_iqr = [f"OutlierIQR_{metrica}" for metrica in METRICAS_OUTLIER]
    dados["PossivelOutlierIQR"] = dados[colunas_iqr].any(axis=1)
    dados["MetricasSinalizadasIQR"] = dados.apply(
        lambda linha: ",".join(
            metrica
            for metrica in METRICAS_OUTLIER
            if bool(linha[f"OutlierIQR_{metrica}"])
        )
        or "nenhuma",
        axis=1,
    )
    return dados


def salva_por_versao(dados: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    proveniencia = ["ArquivoResultado", "PastaDadosOculares"]
    dados = dados[
        [coluna for coluna in dados.columns if coluna not in proveniencia]
        + proveniencia
    ]
    caminhos = []
    for versao in ("lambda", "omega"):
        caminho = output_dir / f"dados_participantes_{versao}.csv"
        grupo = dados.loc[dados.Versao == versao].sort_values(
            ["Participante", "Tarefa"]
        )
        grupo.to_csv(
            caminho,
            index=False,
            encoding="utf-8-sig",
            float_format="%.3f",
        )
        caminhos.append(caminho)
        print(
            f"{versao}: {grupo.Participante.nunique()} participantes, "
            f"{len(grupo)} linhas -> {caminho}"
        )
    return caminhos


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path, default=Path.home() / "Documents/demo/data"
    )
    parser.add_argument(
        "--recovered-data-dir",
        type=Path,
        help="Padrao: recuperados/data ao lado de data",
    )
    parser.add_argument(
        "--coletas-dir",
        type=Path,
        default=Path.home() / "Documents/demo/coletas",
    )
    parser.add_argument(
        "--aoi-config", type=Path, default=raiz / "config/aoi_por_versao.json"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home()
        / "Documents/demo/graficos/agregados/dados_participantes",
    )
    args = parser.parse_args()

    fontes = seleciona_fontes(args.data_dir, args.recovered_data_dir)
    configuracao = carrega_aoi(args.aoi_config)
    dados = calcula_linhas(fontes, args.coletas_dir, configuracao)
    dados = adiciona_indicadores_exploratorios(dados)
    salva_por_versao(dados, args.output_dir)


if __name__ == "__main__":
    main()
