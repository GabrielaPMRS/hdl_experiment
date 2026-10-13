"""Optional manual cohort selection, shared by all aggregate analyses."""
import json
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / 'config/participantes_analise.json'


def seleciona_nomes(disponiveis):
    """null includes everyone; an explicit list must exist in this data source."""
    disponiveis = set(disponiveis)
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    if not isinstance(config, dict) or set(config) != {'incluidos'}:
        raise ValueError(f'Use somente a chave "incluidos" em {CONFIG}')
    incluidos = config['incluidos']
    if incluidos is None:
        return sorted(disponiveis)
    if (not isinstance(incluidos, list) or not incluidos
            or any(not isinstance(p, str) or not re.fullmatch(r'P\d{2,}', p)
                   or p != f'P{int(p[1:]):02}' for p in incluidos)):
        raise ValueError('incluidos deve ser null ou uma lista nao vazia de IDs, como ["P00", "P01"].')
    if len(incluidos) != len(set(incluidos)):
        raise ValueError('Participantes repetidos na selecao.')
    ausentes = sorted(set(incluidos) - disponiveis)
    if ausentes:
        raise ValueError('Participantes selecionados indisponiveis: ' + ', '.join(ausentes))
    return sorted(incluidos)
