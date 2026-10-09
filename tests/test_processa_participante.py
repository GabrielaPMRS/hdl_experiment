"""Confere a portabilidade contra os recortes ja existentes, sem sobrescreve-los."""
import hashlib
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from caminhos import raiz_dados
from processa_participante import RECUPERADOS, separa


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/participantes_com_problema'))
from _recuperacao import confere_hash


class IntegridadeTest(unittest.TestCase):
    def test_conversao_git_e_alteracao_real(self):
        original = b'10,20,12:00:00:001\r\n30,40,12:00:00:002\r\n'
        esperado = hashlib.sha256(original).hexdigest()
        self.assertTrue(confere_hash(original, esperado))
        self.assertTrue(confere_hash(original.replace(b'\r\n', b'\n'), esperado))
        self.assertFalse(confere_hash(original.replace(b'10,20', b'11,20'), esperado))


class CaminhosTest(unittest.TestCase):
    def test_repositorio_irmao(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(raiz_dados(), Path(__file__).resolve().parents[2] / 'HDL-Experiment-Data')

    def test_override(self):
        with patch.dict(os.environ, {'HDL_DATA_ROOT': '/tmp/dados-hdl'}):
            self.assertEqual(raiz_dados(), Path('/tmp/dados-hdl'))


class RecortesTest(unittest.TestCase):
    def test_equivalencia_com_dados_existentes(self):
        raiz = raiz_dados()
        if not (raiz / 'coletas').is_dir():
            self.skipTest('Repositorio de dados indisponivel.')
        for coleta in sorted((raiz / 'coletas').glob('P*')):
            participante = coleta.name
            original = raiz / 'data' / participante
            if participante in RECUPERADOS or not (original / 'resumo_tarefas.csv').exists():
                continue
            with self.subTest(participante=participante), tempfile.TemporaryDirectory() as tmp:
                destino = Path(tmp)
                separa(raiz, participante, destino, 5.0)
                for arquivo in destino.glob('*.txt'):
                    self.assertEqual(arquivo.read_text(), (original / arquivo.name).read_text(encoding='utf-8-sig'))
                for arquivo in destino.glob('*.csv'):
                    with arquivo.open(encoding='utf-8-sig', newline='') as novo, (original / arquivo.name).open(encoding='utf-8-sig', newline='') as antigo:
                        novas, antigas = list(csv.DictReader(novo)), list(csv.DictReader(antigo))
                    self.assertEqual(len(novas), len(antigas))
                    for nova, antiga in zip(novas, antigas):
                        self.assertEqual(nova.keys(), antiga.keys())
                        for chave in nova:
                            try:
                                self.assertAlmostEqual(float(nova[chave]), float(antiga[chave].replace(",", ".")))
                            except ValueError:
                                self.assertEqual(nova[chave], antiga[chave])


if __name__ == '__main__':
    unittest.main()
