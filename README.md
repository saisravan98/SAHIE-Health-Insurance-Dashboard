# Health insurance coverage across US counties

An academic data analysis project using U.S. Census Bureau Small Area Health Insurance Estimates (SAHIE) for 2018–2022. The Streamlit dashboard explores annual uninsured rates, county rankings, and demographic differences.

Original team: Sai Sravan Chintala and Nikhilesh Katakam. Sai contributed to both code and analysis. The portfolio revision separates cohort selection and rate calculations from the UI, adds Excel ingestion and data-quality checks, and corrects filter and aggregation behavior. The revision is separate from the original academic submission.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data_prep.py --input-dir raw_data
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`. Put the supplied `sahie_2018.xlsx` through `sahie_2022.xlsx` exports in `raw_data/`. The parser detects the data header after the Census documentation rows. It reads the first worksheet and supports these Excel exports; it does not yet ingest Census ZIP, CSV or TXT downloads directly.

The handoff ZIP includes `processed_sahie.csv` for immediate local use. Raw Excel inputs and the generated full CSV are excluded from Git by `.gitignore`. To rebuild from source, use the five original workbooks. The dataset is a historical 2018–2022 snapshot, not a live feed.

## Data and methodology

Source program: [U.S. Census Bureau SAHIE](https://www.census.gov/programs-surveys/sahie.html). Field definitions and the 90% margin-of-error convention were checked against documentation embedded in the supplied workbooks.

- A record is one year, geographic area, and demographic combination. It is an aggregate estimate, not an individual person or medical record.
- The dashboard uses county rows (`geocat=50`) and holds race at all races (`racecat=0`); race breakdowns are only available at state level in these files.
- Each chart selects one age, sex, and income category before aggregating across counties. State totals and county detail are never combined.
- Combined uninsured percentage is `100 * sum(NUI) / sum(NIPR)`. A simple mean of row percentages gives small populations the same weight as large populations and is not used for the combined rate.
- Full state-plus-county FIPS identifiers distinguish counties sharing the same three-digit county code.
- Demographic panels vary one category at a time while keeping the other filters fixed. Age and income categories overlap and must not be added together.
- County rankings use published `PCTUI`; `pctui_moe` is the published 90% margin of error in percentage points. No aggregate confidence interval or significance claim is computed.

Preparation validates required columns, years, duplicate keys, numeric bounds, and consistency between counts and published rounded percentages. Missing estimates, zero denominators, and unavailable Kalawao County estimates are excluded and counted in `processed_sahie.quality.json`. Invalid unexpected values fail the run; partial output does not replace an existing completed CSV.

## Files

| File | Purpose |
|---|---|
| `data_prep.py` | Stream Excel rows, validate observations, and write the CSV and quality report |
| `analysis.py` | Select comparable cohorts and compute denominator-aware annual rates |
| `app.py` | Streamlit filters, trend, county rankings, demographic comparisons, and CSV export |
| `test_analysis.py` | Regression checks for weighted rates, geography, demographics, and empty selections |
| `.github/workflows/checks.yml` | Proposed GitHub Actions test and syntax-check workflow |

## Verification

```bash
python -m unittest -v
python -m py_compile app.py analysis.py data_prep.py
```

The handoff verification record is in `VALIDATION.md`. A local test pass is not a GitHub Actions run or a deployed application.

## Interpretation limits

This project demonstrates data preparation, descriptive analysis, and visualization. It does not train a predictive model, implement MLOps, establish a causal effect of COVID-19, or evaluate statistical significance of differences. County boundaries can change across years, and a fixed FIPS selection can lose observations when geography definitions change. Reconcile boundaries before making longitudinal claims about fixed areas. Aggregate subgroup composition can also change over time.

The original presentation's statements about correlation, pandemic impact, and overall improvements require re-analysis before reuse. Its claimed animation is not implemented in the supplied original app. The original deck is not included in this portfolio package.

## Next work

Add a tested CSV-download ingestion path and a small redistributable demo dataset, review the UI locally, and document one reproducible finding with its population definition and uncertainty. A predictive or causal extension should be a separately evaluated project with an appropriate baseline and validation design.
