import requests
import os
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CRUNCHBASE_API_KEY")

BASE_URL = "https://api.crunchbase.com/api/v4/searches/organizations"

SEARCH_TERMS = [
    "AI", "Artificial Intelligence", "Machine Learning", 
    "Quantum Computing", "Quantum Technology",
    "Space", "Aerospace", "Satellites", "Defense", 
    "Biotech", "Biotechnology", "Pharma", "Pharmaceuticals",
    "Electric Cars", "EV", "Energy", "Semiconductors",
    "Robotics", "Automation"
]


def search_companies(term: str, limit: int = 10,after_id=None):
    """
    Fetch company data from Crunchbase based on description as categories are blocked on Basic API.
    Returns a list of companies with name, domain and other details.
    """
    headers = {
        "X-Cb-User-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "field_ids": ["identifier", "short_description", "location_identifiers", 
                      "linkedin", "twitter", "permalink", "website_url"],
        "limit": limit,
        "query": [
            {
                "type": "predicate",
                "field_id": "short_description",
                "operator_id": "contains",
                "values": [term]
            },
            {
                "type": "predicate",
                "field_id": "identifier",
                "operator_id": "contains",
                "values": [term]
            }
        ]
    }

    if after_id:
        # Handle pagination
        payload["after_id"] = after_id

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            companies = []
            for item in data.get("entities", []):
                properties = item.get("properties", {})
                companies.append({
                    "name": properties.get("identifier", {}).get("value", "N/A"),
                    "description": properties.get("short_description", "N/A"),
                    "location": (
                        properties.get("location_identifiers", [{}])[0].get("value", "N/A")
                        if isinstance(properties.get("location_identifiers"), list)
                        else "N/A"
                    ),
                    "linkedin": properties.get("linkedin", {}).get("value", "N/A"),
                    "twitter": properties.get("twitter", {}).get("value", "N/A"),
                    "website_url": properties.get("website_url", "N/A"),
                    "permalink": properties.get("permalink", "N/A"),
                    "search_term": term
                })
            return companies, data.get("after_id", None)
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return [], None
    
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return [], None

def get_all_target_companies(limit_per_term=10):
    """
    Fetches companies using search terms in descriptions.
    """
    all_companies = []
    for term in SEARCH_TERMS:
        print(f"🔍 Searching companies with term: {term}...")
        after_id = None

        while True: 
            companies, after_id = search_companies(term, limit=limit_per_term, after_id=after_id)
            all_companies.extend(companies)

            # If no more pages, stop fetching
            if not after_id:
                break
    return all_companies

def save_companies_to_csv(companies, filename="outputs/companies.csv"):
    """
    Saves company data to CSV.
    """
    df = pd.DataFrame(companies)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename}")