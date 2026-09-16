"""Cohort selection and denominator-aware descriptive statistics."""
import pandas as pd

AGE = {0: 'Under 65', 1: '18–64', 2: '40–64', 3: '50–64', 4: 'Under 19', 5: '21–64'}
SEX = {0: 'Both sexes', 1: 'Male', 2: 'Female'}
INCOME = {0: 'All incomes', 1: 'At or below 200% poverty', 2: 'At or below 250% poverty',
          3: 'At or below 138% poverty', 4: 'At or below 400% poverty', 5: '138–400% poverty'}


def load_data(path):
    data = pd.read_csv(path, dtype={'statefips': str, 'countyfips': str})
    data['fips'] = data['statefips'].str.zfill(2) + data['countyfips'].str.zfill(3)
    data['county_label'] = data['county_name'].fillna('') + ', ' + data['state_name'] + ' (' + data['fips'] + ')'
    return data


def select_cohort(data, years, states=(), counties=(), age=0, sex=0, income=0):
    mask = (data['geocat'].eq(50) & data['racecat'].eq(0)
            & data['agecat'].eq(age) & data['sexcat'].eq(sex) & data['iprcat'].eq(income)
            & data['year'].between(*years))
    if states:
        mask &= data['state_name'].isin(states)
    if counties:
        mask &= data['fips'].isin(counties)
    return data.loc[mask].copy()


def annual_rates(cohort):
    """Aggregate disjoint counties for one fixed demographic cohort per year."""
    totals = cohort.groupby('year', as_index=False)[['NUI', 'NIPR']].sum()
    totals['uninsured_pct'] = 100 * totals['NUI'] / totals['NIPR'].where(totals['NIPR'] > 0)
    return totals
