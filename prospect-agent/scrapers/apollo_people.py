import requests
import os
import pandas as pd
from dotenv import load_dotenv
import time

# Load API Key
load_dotenv()
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

APOLLO_PEOPLE_URL = "https://api.apollo.io/api/v1/mixed_people/search"

def search_apollo_people(company_domain, job_titles, seniority_levels=["c_suite", "founder", "vp", "head", "director", "owner"]):
    """
    Fetches decision-makers from Apollo.io based on company domain and job titles.
    """
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    payload = {
        "q_organization_domains": company_domain,
        "person_titles": job_titles,
        "person_seniorities": seniority_levels,
        "per_page": 10,
        "page": 1,
    }

    for attempt in range(3):
        try:
            response = requests.post(APOLLO_PEOPLE_URL, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                decision_makers = [
                    {
                        "name": person.get("name", "N/A"),
                        "role": person.get("title", "N/A"),
                        "email": person.get("email", "N/A"),
                        "linkedin": person.get("linkedin_url", "N/A"),
                        "company": company_domain
                    }
                    for person in data.get("people", [])
                ]
                return decision_makers
            else:
                print(f"Apollo API Error ({response.status_code}): {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Request Error on attempt {attempt + 1}: {e}")
            time.sleep(3)

    return []

def process_companies_from_csv(companies_file="outputs/companies.csv", output_file="outputs/decision_makers.csv"):
    """
    Reads company domains from CSV and finds decision-makers for each company.
    """
    df = pd.read_csv(companies_file)

    if "name" not in df.columns or "website_url" not in df.columns:
        raise ValueError("CSV file missing required columns: 'name' or 'website_url'")

    all_decision_makers = []
    for _, row in df.iterrows():
        company_domain = row.get("website_url")

        if not isinstance(company_domain, str) or company_domain.strip() == "":
            print(f"Skipping {row['name']} (No valid domain)")
            continue

        print(f"🔍 Searching decision-makers for {row['name']} ({company_domain})...")
        decision_makers = search_apollo_people(company_domain, ["CEO", "Founder", "Co-Founder", "Owner", "Director","Head of Partnerships"])

        if decision_makers:
            all_decision_makers.extend(decision_makers)

    df_results = pd.DataFrame(all_decision_makers)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_results.to_csv(output_file, index=False)
    print(f"✅ Decision-makers data saved to {output_file}")
