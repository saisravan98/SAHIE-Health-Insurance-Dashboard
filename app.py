"""Descriptive SAHIE county dashboard for 2018–2022."""
from pathlib import Path
import altair as alt
import streamlit as st
from analysis import AGE, SEX, INCOME, load_data, select_cohort, annual_rates

st.set_page_config(page_title='SAHIE Health Insurance Dashboard', layout='wide')
st.title('Health insurance coverage across US counties')
st.caption('U.S. Census Bureau SAHIE estimates · 2018–2022 · Academic team project')


@st.cache_data
def cached_data(path, modified_time):
    return load_data(path)


path = Path(__file__).with_name('processed_sahie.csv')
if not path.exists():
    st.info('Prepare the data first using the steps in README.md.')
    st.stop()
data = cached_data(str(path), path.stat().st_mtime_ns)
counties = data[data.geocat.eq(50)]
years = sorted(counties.year.unique().tolist())
if not years:
    st.error('No county observations are available.')
    st.stop()
st.sidebar.header('Select a comparable population')
year_range = (years[0], years[-1])
if len(years) > 1:
    year_range = st.sidebar.slider('Years', int(years[0]), int(years[-1]), tuple(map(int, year_range)))
states = st.sidebar.multiselect('States', sorted(counties.state_name.unique()))
available = counties[counties.state_name.isin(states)] if states else counties
labels = available[['fips', 'county_label']].drop_duplicates().set_index('fips').county_label.to_dict()
chosen = st.sidebar.multiselect('Counties', sorted(labels), format_func=labels.get)
age = st.sidebar.selectbox('Age', list(AGE), format_func=AGE.get)
sex = st.sidebar.selectbox('Sex', list(SEX), format_func=SEX.get)
income = st.sidebar.selectbox('Income', list(INCOME), format_func=INCOME.get)
cohort = select_cohort(data, year_range, states, chosen, age, sex, income)
if cohort.empty:
    st.info('No estimates match this selection. Broaden the filters.')
    st.stop()
trend = annual_rates(cohort)
latest = int(cohort.year.max())
current = cohort[cohort.year.eq(latest)]
latest_rate = trend.loc[trend.year.eq(latest), 'uninsured_pct'].iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric(f'Uninsured in selected counties ({latest})', f'{latest_rate:.2f}%')
c2.metric('Counties in latest year', current.fips.nunique())
c3.metric('Years represented', cohort.year.nunique())
st.caption('Combined rate = 100 × total uninsured ÷ total population in the selected demographic group. '
           'Race is held at all races because county-level race breakdowns are unavailable. '
           'County boundaries can change between years; check geographic comparability before interpreting trends.')
trend_tab, ranks_tab, demo_tab = st.tabs(['Trend', 'County rankings', 'Demographic comparisons'])
with trend_tab:
    st.altair_chart(alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X('year:O', title='Year'), y=alt.Y('uninsured_pct:Q', title='Uninsured (%)'),
        tooltip=['year:O', alt.Tooltip('uninsured_pct:Q', format='.2f')]), use_container_width=True)
with ranks_tab:
    selected_year = st.selectbox('Ranking year', sorted(cohort.year.unique()), index=cohort.year.nunique()-1)
    ranked = cohort[cohort.year.eq(selected_year)].sort_values('PCTUI', ascending=False)
    maximum = min(100, len(ranked))
    n = st.slider('Counties shown', 1, maximum, min(10, maximum)) if maximum > 1 else 1
    st.altair_chart(alt.Chart(ranked.head(n)).mark_bar().encode(
        y=alt.Y('county_label:N', sort='-x', title='County'),
        x=alt.X('PCTUI:Q', title='Uninsured (%)'),
        tooltip=['county_label', 'PCTUI', 'pctui_moe']), use_container_width=True)
    st.dataframe(ranked.head(n)[['county_label', 'PCTUI', 'pctui_moe', 'NUI', 'NIPR']], hide_index=True)
    st.caption('pctui_moe is the published 90% margin of error in percentage points. '
               'Ranks alone do not establish statistically significant differences.')
with demo_tab:
    st.write(f'Comparisons for {latest}; other selected demographic dimensions remain fixed.')
    st.caption('Age and income groups overlap. Compare their rates separately; do not sum them.')
    for dimension, mapping in [('age', AGE), ('sex', SEX), ('income', INCOME)]:
        records = []
        for code, label in mapping.items():
            settings = dict(age=age, sex=sex, income=income)
            settings[dimension] = code
            subset = select_cohort(data, (latest, latest), states, chosen, **settings)
            rate = annual_rates(subset)
            if not rate.empty:
                records.append({'group': label, 'uninsured_pct': float(rate.uninsured_pct.iloc[0])})
        import pandas as pd
        st.subheader(dimension.title())
        st.altair_chart(alt.Chart(pd.DataFrame(records)).mark_bar().encode(
            y=alt.Y('group:N', title=None), x=alt.X('uninsured_pct:Q', title='Uninsured (%)'),
            tooltip=['group', alt.Tooltip('uninsured_pct:Q', format='.2f')]), use_container_width=True)
st.download_button('Download selected observations', cohort.to_csv(index=False), 'selected_sahie.csv', 'text/csv')
st.caption('Descriptive estimates support exploration. This project does not estimate causal effects or train predictive models.')
