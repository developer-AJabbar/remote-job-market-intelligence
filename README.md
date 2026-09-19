# Remote Job Market Intelligence Dashboard

A two-page Looker Studio BI dashboard, fed by a Python ETL pipeline, tracking 215 remote-friendly job listings across the US, UK, Germany, and the Netherlands.

![Dashboard preview](screenshots/page1_overview.png)

## 🔗 Live Dashboard
[View the live Looker Studio report](#) <!-- paste your published Looker Studio link here -->

## 📊 What it tracks

- **215 listings** pulled from two free job-board APIs
- **67 companies**, **29 job categories**
- Salary comparison across **US / GB / NL** markets (kept in native currency, not blended)
- In-demand skills extracted from job titles & descriptions
- Employment type mix, posting trends over time, and a full drill-down listings table

## 📄 Full write-up

See [`report/Remote_Job_Market_Report.pdf`](report/Remote_Job_Market_Report.pdf) for a page-by-page breakdown of the dashboard, methodology, and key insights.

## 🛠 Tech stack

| Stage | Tool |
|---|---|
| Extraction | Python (`requests`) — Remotive API, Adzuna API |
| Transformation | Python (`pandas`) — schema normalization, skill-keyword extraction |
| Storage | Google Sheets |
| Visualization | Looker Studio (responsive, 2-page report) |

## 📁 Repo structure

```
remote-job-market-dashboard/
├── pipeline/
│   └── job_market_pipeline.py     # Fetches + cleans data from both APIs
├── data/
│   ├── remote_jobs_data.csv       # One row per job listing
│   └── job_skills.csv             # One row per (job, skill) match
├── report/
│   └── Remote_Job_Market_Report.pdf
├── screenshots/
│   ├── page1_overview.png
│   └── page2_compensation.png
└── README.md
```

## ⚙️ How to run the pipeline

```bash
pip install requests pandas
python pipeline/job_market_pipeline.py
```

Remotive needs no API key. For Adzuna, get a free key at [developer.adzuna.com](https://developer.adzuna.com/) and paste it into the `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` variables at the top of the script.

The script outputs `remote_jobs_data.csv` and `job_skills.csv`, ready to import into Google Sheets and connect to Looker Studio.

## 📌 Notes on the data

- Category and country labels reflect each source's own taxonomy (including original German and Dutch category names from Adzuna) rather than being force-translated or merged.
- Salary figures are shown per-country rather than averaged together, since they're in different currencies (USD, GBP, EUR).
- ~47% of listings include salary data; ~71% don't specify an employment type — shown as-is rather than hidden.

## 👤 Author

**Abdul Jabbar Akhtar** — Data Analyst & BI Developer, Lahore, Pakistan
Freelance data analytics, BI dashboards, and backend development.
