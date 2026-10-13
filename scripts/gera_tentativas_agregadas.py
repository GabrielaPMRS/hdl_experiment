"""Generate per-case attempt distributions and per-participant totals."""
import argparse
from pathlib import Path
from caminhos import raiz_dados
from gera_desempenho_tarefas import load_sessions, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coletas-dir', type=Path, default=raiz_dados()/'coletas')
    parser.add_argument('--output-dir', type=Path, default=raiz_dados()/'graficos/agregados/attempts')
    parser.add_argument('--dpi', type=int, default=300)
    args = parser.parse_args()
    data, sources = load_sessions(args.coletas_dir)
    generate(data, sources, args.output_dir.parent, [('Attempts', args.output_dir.name)], args.dpi)
    print(f'Figures saved to {args.output_dir}')


if __name__ == '__main__':
    main()
