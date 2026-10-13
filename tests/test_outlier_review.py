import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analisa_outliers import flag_iqr


class OutlierReviewTest(unittest.TestCase):
    def data(self, values):
        return pd.DataFrame([dict(Participant=f'P{i:02}',Condition='With Atom',Task='T01',
                                  ExecutionTimeSeconds=value,Attempts=1)
                             for i,value in enumerate(values)])

    def test_extreme_time_and_no_input_mutation(self):
        data=self.data([1,2,3,4,5,6,7,100])
        original=data.copy(deep=True)
        result=flag_iqr(data)
        self.assertEqual(set(result.Metric), {'ExecutionTimeSeconds'})
        self.assertEqual(len(result), len(data))
        times=result.loc[result.Metric=='ExecutionTimeSeconds']
        self.assertEqual(list(times.loc[times.Candidate].Participant), ['P07'])
        self.assertAlmostEqual(times.iloc[0].UpperFence, 11.5)
        pd.testing.assert_frame_equal(data,original)

    def test_zero_iqr_is_explicit_and_small_groups_not_flagged(self):
        data=self.data([1,1,1,1,1,1,1,2])
        result=flag_iqr(data)
        times=result.loc[result.Metric=='ExecutionTimeSeconds']
        self.assertTrue(times.iloc[-1].Candidate)
        self.assertIn('Zero IQR',times.iloc[-1].ReviewNote)
        small=flag_iqr(self.data([1,1,100]))
        self.assertFalse(small.Candidate.any())
        self.assertTrue(small.ReviewNote.str.contains('Insufficient').all())

    def test_grouping_does_not_mix_tasks_or_conditions(self):
        a=self.data([1,2,3,4,5,6,7,100])
        b=self.data([200,210,220,230,240,250,260,270])
        b['Condition']='Without Atom'
        result=flag_iqr(pd.concat([a,b],ignore_index=True))
        self.assertTrue((result.ReferenceN==8).all())
        pooled=flag_iqr(pd.concat([a,b],ignore_index=True),by_condition=False)
        self.assertTrue((pooled.ReferenceN==16).all())


if __name__ == '__main__':
    unittest.main()
