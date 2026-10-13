"""Verify source metrics, full cohorts, AOI exclusion and density units."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from caminhos import raiz_dados
from gera_desempenho_tarefas import load_sessions, participant_totals
from gera_heatmaps_agregados import calcula_mapa
from gera_heatmaps_agregados_aoi import carrega_fixacoes, desenha
from plot_common import LABELS
import matplotlib.pyplot as plt


class SessionMetricsTest(unittest.TestCase):
    def test_full_cohort_and_json_totals(self):
        root = raiz_dados() / 'coletas'
        if not root.exists():
            self.skipTest('Data repository unavailable')
        data, _ = load_sessions(root)
        self.assertEqual(len(data), 26 * 4)
        self.assertTrue((data.groupby(['Task','Condition']).size() == 13).all())
        for participant in ('P00','P01'):
            session = json.loads((root/participant/f'resultado{participant}.json').read_text(encoding='utf-8-sig'))
            if isinstance(session, list):
                session = session[0]
            for q in session['perguntas']:
                task = f'T{int(q["codigoId"].split("-")[-1]):02}'
                row = data.loc[(data.Participant == participant) & (data.Task == task)].iloc[0]
                self.assertEqual(row.ExecutionTimeSeconds, q['segundos'])
                self.assertEqual(row.Attempts, q['tentativas'])
                self.assertEqual(row.Condition, LABELS[session['versaoExperimento']])

    def test_totals_are_per_participant_and_include_all_tasks(self):
        rows = [dict(Participant=participant, Condition=condition, Task=task,
                     ExecutionTimeSeconds=value, Attempts=1)
                for participant, condition, value in [('P00','With Atom',10), ('P01','Without Atom',20)]
                for task in ('T01','T02','T04','T05')]
        data = pd.DataFrame(rows)
        totals = participant_totals(data, 'ExecutionTimeSeconds').set_index('Participant')
        self.assertEqual(totals.loc['P00','ExecutionTimeSeconds'], 40)
        self.assertEqual(totals.loc['P01','ExecutionTimeSeconds'], 80)
        self.assertEqual(list(participant_totals(data, 'Attempts').Attempts), [4,4])
        with self.assertRaises(ValueError):
            participant_totals(data.iloc[1:], 'ExecutionTimeSeconds')
        with self.assertRaises(ValueError):
            participant_totals(pd.concat([data, data.iloc[:1]]), 'ExecutionTimeSeconds')


class AOITest(unittest.TestCase):
    def test_outside_aoi_never_enters_density(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'P01'
            folder.mkdir()
            # Outside AOI and outside code cannot affect the AOI map.
            pd.DataFrame({'x':[300,310,320,100], 'y':[600,620,800,600],
                          'duracao':[100,200,999999,999999]}).to_csv(folder/'Fixations P01 T01.csv', index=False)
            data, metrics = carrega_fixacoes([folder], 'omega','T01',(245,820,270,900),(520,650))
            self.assertEqual(list(data.duracao), [100,200])
            self.assertEqual(metrics[0]['FixacoesAOI1'], 2)
            self.assertAlmostEqual(metrics[0]['TempoAOI1Segundos'], .3)
            self.assertEqual(metrics[0]['FixacoesForaAOI1'], 1)

    def test_density_scales_with_total_duration(self):
        data = pd.DataFrame({'x':[300.,330.,360.,390.], 'y':[550.,580.,560.,610.],
                             'duracao':[100.,200.,150.,300.]})
        first = calcula_mapa(data, (245,820,520,650),40,40)[2]
        data['duracao'] *= 2
        second = calcula_mapa(data, (245,820,520,650),40,40)[2]
        np.testing.assert_allclose(second, first*2)

    def test_empty_and_single_fixation(self):
        for data in (pd.DataFrame(columns=['x','y','duracao']),
                     pd.DataFrame({'x':[300.],'y':[550.],'duracao':[100.]})):
            density = calcula_mapa(data, (245,820,520,650),10,10)[2]
            self.assertTrue(np.isfinite(density).all())
            self.assertTrue((density >= 0).all())


if __name__ == '__main__':
    unittest.main()
