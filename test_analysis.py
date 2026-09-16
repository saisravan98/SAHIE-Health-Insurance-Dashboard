import unittest
import pandas as pd
from analysis import select_cohort, annual_rates


class CohortTests(unittest.TestCase):
    def setUp(self):
        base = dict(year=2022, geocat=50, racecat=0, agecat=0, sexcat=0, iprcat=0)
        self.data = pd.DataFrame([
            dict(base, state_name='A', fips='01001', NUI=10, NIPR=100),
            dict(base, state_name='B', fips='02001', NUI=180, NIPR=900),
            dict(base, state_name='A', fips='01000', NUI=1000, NIPR=2000, geocat=40),
            dict(base, state_name='A', fips='01001', NUI=50, NIPR=100, sexcat=1),
            dict(base, state_name='A', fips='01001', NUI=30, NIPR=100, year=2021),
        ])

    def test_population_denominator(self):
        cohort = select_cohort(self.data, (2022, 2022))
        self.assertEqual(len(cohort), 2)
        self.assertAlmostEqual(annual_rates(cohort).uninsured_pct.iloc[0], 19.0)

    def test_state_and_full_county_identifier(self):
        cohort = select_cohort(self.data, (2022, 2022), states=['B'], counties=['02001'])
        self.assertEqual(len(cohort), 1)
        self.assertAlmostEqual(annual_rates(cohort).uninsured_pct.iloc[0], 20.0)

    def test_demographic_and_year_filters(self):
        cohort = select_cohort(self.data, (2022, 2022), sex=1)
        self.assertEqual(len(cohort), 1)
        self.assertAlmostEqual(annual_rates(cohort).uninsured_pct.iloc[0], 50.0)

    def test_empty_selection(self):
        cohort = select_cohort(self.data, (2020, 2020))
        self.assertTrue(annual_rates(cohort).empty)


if __name__ == '__main__':
    unittest.main()
