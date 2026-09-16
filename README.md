# Public Health Insurance Demographic & Trend Dashboard

An end-to-end data analytics and visualization platform built with **Python**, **Pandas**, **Altair**, and **Streamlit** to explore 5 years of U.S. Census Bureau Small Area Health Insurance Estimates (SAHIE) across all U.S. counties (2018–2022).

The application features an automated, validated ETL pipeline, population-weighted aggregation logic, and an interactive dashboard for county-level ranking and demographic disparity analysis.

---

## 🚀 Key Features

* **Automated & Validated ETL Pipeline:** Reads and parses multi-year Census SAHIE Excel workbooks, validates schema constraints, checks duplicate keys, filters out invalid/zero denominators, and generates a structured data-quality audit report (`processed_sahie.quality.json`).
* **Population-Weighted Rate Calculations:** Calculates aggregate uninsured percentages as `100 * sum(NUI) / sum(NIPR)` rather than taking simple averages of row percentages, preventing smaller rural counties from skewing regional baselines.
* **Granular Cohort Isolation:** Isolates discrete demographic groups (Age, Sex, Income-to-Poverty Ratio) to avoid double-counting overlapping categories across county lines.
* **Interactive Visualization Suite:** 
  * **Trend Analysis:** Multi-year longitudinal trajectories showing national and state uninsured rate shifts.
  * **County Rankings:** Dynamic Top-N leaderboard highlighting high-risk and low-risk counties with 90% margin-of-error (`pctui_moe`) tracking.
  * **Demographic Breakdowns:** Side-by-side disparity analysis across income tiers and age demographics.
* **Data Export:** Built-in capability to export filtered cohort subsets directly to CSV.

---

## 🛠️ Architecture & Tech Stack

* **Language:** Python 3.10+
* **Data Engineering & Processing:** Pandas, NumPy
* **Visualization:** Altair, Streamlit
* **Quality Assurance & Testing:** Python `unittest` (regression and calculation checks)

### File Structure

| File | Description |
| :--- | :--- |
| `app.py` | Main Streamlit interface with interactive filters, visualization tabs, and data export. |
| `analysis.py` | Core calculation engine handling cohort selection and population-weighted aggregations. |
| `data_prep.py` | ETL script streaming raw Excel inputs, enforcing validation bounds, and writing clean data. |
| `test_analysis.py` | Automated test suite verifying weighting math, edge-case filters, and geography mappings. |
| `processed_sahie.quality.json` | Automated quality report detailing data integrity, excluded rows, and missing values. |
| `requirements.txt` | Python package dependencies. |

---

## 💻 Local Setup & Execution

### 1. Clone & Set Up Environment
```bash
git clone [https://github.com/saisravan98/SAHIE-Health-Insurance-Dashboard.git](https://github.com/saisravan98/SAHIE-Health-Insurance-Dashboard.git)
cd SAHIE-Health-Insurance-Dashboard
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Dashboard
Ensure `processed_sahie.csv` is present in the root directory, then run:
```bash
python3 -m streamlit run app.py
```
Open http://localhost:8501 in your browser.

### 3. Rebuild Dataset from Raw Census Files (Optional)
1. Place `sahie_2018.xlsx` through `sahie_2022.xlsx` in a `raw_data/` directory.
2. Execute the preprocessing pipeline:
```bash
python3 data_prep.py --input-dir raw_data
```

---

## 🧪 Testing & Verification

Run the test suite to verify calculation accuracy and data validation:
```bash
python3 -m unittest test_analysis.py -v
```

---

## 📊 Data Source & Methodology Notes

* **Data Authority:** U.S. Census Bureau – Small Area Health Insurance Estimates (SAHIE).
* **Geographic Resolution:** County level (`geocat=50`) using unified state-plus-county FIPS keys.
* **Confidence Conventions:** Margin-of-error figures adhere to the Census Bureau's 90% confidence level standard.
