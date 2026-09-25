from pathlib import Path
p=Path('scripts/gera_heatmaps_agregados.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace('import scipy.stats as st', 'import scipy.stats as st\nfrom fontes_agregados import seleciona_fontes, salva_fontes')
a=s.index('def descobre_participantes('); b=s.index('\ndef carrega_limites_codigo',a)
s=s[:a]+'''def descobre_participantes(data_dir: Path, recovered_dir=None) -> dict[str, list[Path]]:
    grupos = {versao: [] for versao in VERSOES}
    for pasta, versao in seleciona_fontes(data_dir, recovered_dir):
        grupos[versao].append(pasta)
    return grupos

'''+s[b:]
s=s.replace('    args = parser.parse_args()', '    parser.add_argument("--recovered-data-dir", type=Path, help="Padrao: pasta recuperados/data ao lado de data")\n    args = parser.parse_args()')
s=s.replace('descobre_participantes(args.data_dir)', 'descobre_participantes(args.data_dir, args.recovered_data_dir)')
s=s.replace('    args.output_dir.mkdir(parents=True, exist_ok=True)', '    args.output_dir.mkdir(parents=True, exist_ok=True)\n    salva_fontes(sorted([(pasta, versao) for versao, pastas in grupos.items() for pasta in pastas]), args.output_dir)')
s=s.replace('            print(f"Aviso: fixacoes ausentes: {caminho}")\n            continue', '            raise FileNotFoundError(f"Fixacoes ausentes: {caminho}")')
p.write_text(s,encoding='utf-8')
p=Path('scripts/gera_violin_tempo_aoi.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('import seaborn as sns', 'import seaborn as sns\nfrom fontes_agregados import seleciona_fontes, salva_fontes')
a=s.index('def descobre_participantes(');b=s.index('\ndef calcula_tempos',a)
s=s[:a]+'''def descobre_participantes(data_dir: Path, recovered_dir=None):
    return seleciona_fontes(data_dir, recovered_dir)

'''+s[b:]
s=s.replace('data_dir: Path, configuracao: dict, regiao: str\n', 'data_dir: Path, configuracao: dict, regiao: str, participantes=None\n')
s=s.replace('    participantes = descobre_participantes(data_dir)', '    if participantes is None:\n        participantes = descobre_participantes(data_dir)')
s=s.replace('    args = parser.parse_args()', '    parser.add_argument("--recovered-data-dir", type=Path, help="Padrao: pasta recuperados/data ao lado de data")\n    args = parser.parse_args()')
s=s.replace('    dados = calcula_tempos(args.data_dir, configuracao, args.regiao)', '    fontes = descobre_participantes(args.data_dir, args.recovered_data_dir)\n    dados = calcula_tempos(args.data_dir, configuracao, args.regiao, participantes=fontes)')
s=s.replace('    salva_resumos(dados, args.output_dir, args.regiao)', '    salva_fontes(fontes, args.output_dir)\n    salva_resumos(dados, args.output_dir, args.regiao)')
p.write_text(s,encoding='utf-8')
