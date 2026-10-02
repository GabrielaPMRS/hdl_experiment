"""Gera agregados exploratorios da ideia 1 sem alterar as saidas principais."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from fontes_agregados import RECUPERADOS, seleciona_fontes


PARTICIPANTES = (
    "P01", "P02", "P03", "P04", "P07", "P11",
    "P12", "P14", "P15", "P17", "P18", "P20",
)


def executa(script: Path, argumentos: list[str], ambiente: dict[str, str]):
    comando = [sys.executable, str(script), *argumentos]
    print("Executando:", script.name, " ".join(argumentos), flush=True)
    subprocess.run(comando, check=True, env=ambiente)


def salva_fontes_reais(
    output_dir: Path,
    demo_dir: Path,
    por_nome: dict[str, tuple[Path, str]],
):
    """Substitui referencias da area temporaria pelos caminhos persistentes."""
    linhas_dados = []
    linhas_json = []
    for participante in PARTICIPANTES:
        pasta, versao = por_nome[participante]
        origem = "recuperado" if participante in RECUPERADOS else "normal"
        linhas_dados.append(
            [participante, versao, origem, pasta, pasta / "resumo_tarefas.csv"]
        )
        linhas_json.append(
            [
                participante,
                versao,
                demo_dir / "coletas" / participante / f"resultado{participante}.json",
            ]
        )

    for subpasta in ("heatmaps", "tempos"):
        caminho = output_dir / subpasta / "fontes_utilizadas.csv"
        with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo)
            writer.writerow(["Participante", "Versao", "Origem", "Pasta", "Resumo"])
            writer.writerows(linhas_dados)

    caminho = output_dir / "tentativas" / "fontes_utilizadas.csv"
    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Participante", "Versao", "Arquivo"])
        writer.writerows(linhas_json)


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo-dir", type=Path, default=Path.home() / "Documents/demo"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Padrao: DEMO/graficos/agregados/ideia_1",
    )
    args = parser.parse_args()

    demo_dir = args.demo_dir.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else demo_dir / "graficos" / "agregados" / "ideia_1"
    )
    fontes = seleciona_fontes(
        demo_dir / "data", demo_dir / "recuperados" / "data"
    )
    por_nome = {pasta.name: (pasta, versao) for pasta, versao in fontes}
    ausentes = sorted(set(PARTICIPANTES) - set(por_nome))
    if ausentes:
        raise FileNotFoundError(
            "Participantes processados ausentes: " + ", ".join(ausentes)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "participantes_incluidos.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Participante", "Versao", "FonteProcessamento"])
        for participante in PARTICIPANTES:
            _, versao = por_nome[participante]
            writer.writerow(
                [
                    participante,
                    versao,
                    "recuperado" if participante in RECUPERADOS else "normal",
                ]
            )

    ambiente = os.environ.copy()
    ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="hdl_ideia_1_") as temporario:
        staging = Path(temporario)
        dados_normais = staging / "data"
        dados_recuperados = staging / "recuperados" / "data"
        coletas = staging / "coletas"

        for participante in PARTICIPANTES:
            origem, _ = por_nome[participante]
            raiz_destino = (
                dados_recuperados
                if participante in RECUPERADOS
                else dados_normais
            )
            shutil.copytree(origem, raiz_destino / participante)

            pasta_coleta = coletas / participante
            pasta_coleta.mkdir(parents=True)
            resultado = (
                demo_dir
                / "coletas"
                / participante
                / f"resultado{participante}.json"
            )
            if not resultado.is_file():
                raise FileNotFoundError(f"JSON ausente: {resultado}")
            shutil.copy2(resultado, pasta_coleta / resultado.name)

        executa(
            raiz / "scripts" / "gera_heatmaps_agregados.py",
            [
                "--data-dir", str(dados_normais),
                "--recovered-data-dir", str(dados_recuperados),
                "--images-dir", str(demo_dir / "telas"),
                "--output-dir", str(output_dir / "heatmaps"),
                "--permitir-grupos-desiguais",
            ],
            ambiente,
        )
        for regiao in ("codigo", "aoi1"):
            executa(
                raiz / "scripts" / "gera_violin_tempo_aoi.py",
                [
                    "--data-dir", str(dados_normais),
                    "--recovered-data-dir", str(dados_recuperados),
                    "--output-dir", str(output_dir / "tempos"),
                    "--regiao", regiao,
                ],
                ambiente,
            )
        executa(
            raiz / "scripts" / "gera_tentativas_agregadas.py",
            [
                "--coletas-dir", str(coletas),
                "--output-dir", str(output_dir / "tentativas"),
            ],
            ambiente,
        )

    salva_fontes_reais(output_dir, demo_dir, por_nome)

    print(f"Ideia 1 gerada em: {output_dir}")
    print("Lambda: 6 participantes; Omega: 8 participantes")


if __name__ == "__main__":
    main()
