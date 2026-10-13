import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import selecao_participantes as selection
from caminhos import raiz_dados
from fontes_agregados import seleciona_fontes
from gera_desempenho_tarefas import load_sessions


class SelectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name)/'selection.json'
        self.patch = patch.object(selection, 'CONFIG', self.config)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write(self, value):
        self.config.write_text(json.dumps({'incluidos': value}))

    def test_default_all_and_manual_order(self):
        self.write(None)
        self.assertEqual(selection.seleciona_nomes(['P02','P00','P01']), ['P00','P01','P02'])
        self.write(['P02','P00'])
        self.assertEqual(selection.seleciona_nomes(['P00','P01','P02']), ['P00','P02'])

    def test_invalid_selections_fail(self):
        for value in ([], ['P00','P00'], ['P99'], ['00'], 'P00', [True], ['P000']):
            with self.subTest(value=value):
                self.write(value)
                with self.assertRaises(ValueError):
                    selection.seleciona_nomes(['P00','P01'])

    def test_same_cohort_for_json_and_fixations(self):
        root = raiz_dados()
        if not (root/'coletas').exists():
            self.skipTest('Data repository unavailable')
        self.write(['P00','P01','P03'])
        data, sources = load_sessions(root/'coletas')
        ocular = seleciona_fontes(root/'data')
        self.assertEqual(set(data.Participant), {'P00','P01','P03'})
        self.assertEqual(len(data), 12)
        self.assertEqual(set(sources.Participant), {p.name for p,v in ocular})
        self.assertTrue(all('recuperados' in p.parts for p,v in ocular if p.name in {'P00','P03'}))


if __name__ == '__main__':
    unittest.main()
