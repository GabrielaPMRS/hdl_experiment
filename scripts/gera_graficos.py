"""Regenerate the 18 comparison figures using the current participant selection."""
import argparse
import subprocess
import sys
from pathlib import Path
from caminhos import raiz_dados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=raiz_dados()/'graficos/agregados',
                        help='Parent folder for all four figure sets')
    parser.add_argument('--dpi', type=int, default=300)
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error('--dpi must be positive')
    scripts = Path(__file__).resolve().parent
    jobs = [
        ('gera_desempenho_tarefas.py', args.output_dir, []),
        ('gera_heatmaps_agregados.py', args.output_dir/'heatmaps', ['--permitir-grupos-desiguais']),
        ('gera_heatmaps_agregados_aoi.py', args.output_dir/'heatmaps_aoi1', ['--permitir-grupos-desiguais']),
    ]
    for name, output, extra in jobs:
        print(f'Running {name}', flush=True)
        subprocess.run([sys.executable, str(scripts/name), '--output-dir', str(output),
                        '--dpi', str(args.dpi), *extra], check=True)
    print(f'All comparison figures saved to {args.output_dir.resolve()}')


if __name__ == '__main__':
    main()
