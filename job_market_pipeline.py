"""
Remote Job Market Intelligence Dashboard — Data Pipeline
==========================================================
Pulls remote job listings from Remotive (no key needed) and Adzuna
(free tier, key required), normalizes them into one schema, extracts
in-demand tech skills from job titles/descriptions, and exports two
clean CSVs ready to import into Google Sheets -> Looker Studio.

Requirements:
    pip install requests pandas

Before running:
    1. Remotive needs no API key — works out of the box.
    2. Get a free Adzuna key at https://developer.adzuna.com/
       (sign up -> create an app -> copy your APP_ID and APP_KEY)
    3. Paste those two values into the CONFIG section below.

Output:
    remote_jobs_data.csv   — one row per job listing
    job_skills.csv         — one row per (job, skill) match, for a
                              "skills demand" chart in Looker Studio
"""

import re
from datetime import datetime, timezone

import pandas as pd
import requests

# ---------------- CONFIG ----------------
ADZUNA_APP_ID = "8500f1f0"
ADZUNA_APP_KEY = "f0ef33df1a2635feeb73452c3a40a106"

# Country codes Adzuna supports, e.g. nl, gb, de, us, fr, ca, au...
# 'nl' is included by default since it's useful for an NL-focused job search.
ADZUNA_COUNTRIES = ["nl", "gb", "de", "us"]
ADZUNA_RESULTS_PER_COUNTRY = 50

# Skills to detect in job titles/descriptions for the "skills demand" chart.
# Add/remove keywords to match the roles you care about.
SKILL_KEYWORDS = [
    "Python", "SQL", "Power BI", "Tableau", "Excel", "Django", "Flask",
    "React", "JavaScript", "TypeScript", "Node.js", "AWS", "Azure", "GCP",
    "Docker", "Kubernetes", "Java", "C#", "Go", "R", "Machine Learning",
    "Data Analyst", "Data Engineer", "ETL", "Airflow", "Spark",
    "TensorFlow", "PyTorch", "REST API", "Django REST", "PostgreSQL",
    "MongoDB", "Git", "Linux", "Looker Studio", "BigQuery",
]

OUTPUT_JOBS_CSV = "remote_jobs_data.csv"
OUTPUT_SKILLS_CSV = "job_skills.csv"


# ---------------- FETCHERS ----------------
def fetch_remotive():
    """Pull all current listings from Remotive's free public API."""
    url = "https://remotive.com/api/remote-jobs"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])

    rows = []
    for j in jobs:
        rows.append({
            "source": "Remotive",
            "job_id": f"remotive_{j.get('id')}",
            "title": j.get("title"),
            "company_name": j.get("company_name"),
            "category": j.get("category"),
            "job_type": j.get("job_type"),
            "country": j.get("candidate_required_location"),
            "salary_raw": j.get("salary"),
            "salary_min": None,
            "salary_max": None,
            "url": j.get("url"),
            "date_posted": (j.get("publication_date") or "")[:10],
            "description": j.get("description", ""),
        })
    return rows


def fetch_adzuna():
    """Pull listings from Adzuna's free-tier API for each configured country."""
    if ADZUNA_APP_ID == "YOUR_APP_ID_HERE":
        print("Adzuna credentials not set — skipping Adzuna (Remotive-only run).")
        return []

    rows = []
    for country in ADZUNA_COUNTRIES:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": ADZUNA_RESULTS_PER_COUNTRY,
            "what": "remote",
            "content-type": "application/json",
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"Adzuna request failed for {country}: {resp.status_code}")
            continue

        for j in resp.json().get("results", []):
            rows.append({
                "source": "Adzuna",
                "job_id": f"adzuna_{j.get('id')}",
                "title": j.get("title"),
                "company_name": (j.get("company") or {}).get("display_name"),
                "category": (j.get("category") or {}).get("label"),
                "job_type": j.get("contract_time"),
                "country": country.upper(),
                "salary_raw": None,
                "salary_min": j.get("salary_min"),
                "salary_max": j.get("salary_max"),
                "url": j.get("redirect_url"),
                "date_posted": (j.get("created") or "")[:10],
                "description": j.get("description", ""),
            })
    return rows


# ---------------- PROCESSING ----------------
def extract_skills(text):
    """Return the list of known skill keywords found in a text block."""
    if not text:
        return []
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)
    return found


def build_dataset():
    print("Fetching Remotive listings...")
    remotive_rows = fetch_remotive()
    print(f"  -> {len(remotive_rows)} jobs")

    print("Fetching Adzuna listings...")
    adzuna_rows = fetch_adzuna()
    print(f"  -> {len(adzuna_rows)} jobs")

    all_rows = remotive_rows + adzuna_rows
    if not all_rows:
        raise SystemExit("No jobs fetched — check your internet connection or API keys.")

    df = pd.DataFrame(all_rows)

    # Skill extraction from title + description
    skill_rows = []
    for _, row in df.iterrows():
        text = f"{row['title']} {row['description']}"
        for skill in extract_skills(text):
            skill_rows.append({"job_id": row["job_id"], "skill": skill})
    skills_df = pd.DataFrame(skill_rows)

    # Drop the long description column before export (keeps the Sheet light)
    df = df.drop(columns=["description"])
    df["pulled_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return df, skills_df


if __name__ == "__main__":
    jobs_df, skills_df = build_dataset()
    jobs_df.to_csv(OUTPUT_JOBS_CSV, index=False)
    skills_df.to_csv(OUTPUT_SKILLS_CSV, index=False)
    print(f"\nSaved {len(jobs_df)} jobs to {OUTPUT_JOBS_CSV}")
    print(f"Saved {len(skills_df)} skill mentions to {OUTPUT_SKILLS_CSV}")
