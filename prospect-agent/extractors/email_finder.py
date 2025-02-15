import requests
import os
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# Common email formats for fallback predictions
COMMON_FORMATS = [
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{first}{last}@{domain}",
    "{first}_{last}@{domain}",
    "{first}-{last}@{domain}"
]

MAX_RETRIES = 3 

def get_email_from_hunter(full_name, company_domain, max_retries=3):
    """
    Uses Hunter.io Email Finder API to get a person's email
    """

    if not full_name or not company_domain:
        return None

    first_name, last_name = full_name.split(" ", 1) if " " in full_name else (full_name, "")
    url = "https://api.hunter.io/v2/email-finder"
    params = {
        "api_key": HUNTER_API_KEY,
        "first_name": first_name,
        "last_name": last_name,
        "domain": company_domain
    }

    # response = requests.get(url, params=params)

    # if response.status_code == 200:
    #     data = response.json().get("data", {})
    #     return data.get("email", None)
    
    # return None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("data", {}).get("email", None)
            elif response.status_code == 429:
                rate_limit_reset = response.headers.get("X-RateLimit-Reset")
                wait_time = int(rate_limit_reset) - int(time.time()) if rate_limit_reset else (5 * attempt)
                print(f"⚠️ Hunter.io Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Hunter.io API Error ({response.status_code}): {response.text}")
                return None
        except requests.exceptions.Timeout:
            print(f"Timeout error, retrying {attempt}/{max_retries}...")
            time.sleep(5 * attempt)
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None

    print("Hunter.io request failed after multiple attempts.")
    return None

def get_email_from_apollo(company_domain):
    """
    Fetches emails from Apollo.io
    """
    url = "https://api.apollo.io/api/v1/mixed_people/search"
    headers = {"x-api-key": APOLLO_API_KEY}
    payload = {"q_organization_domains": company_domain, "per_page": 10}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("people"):
                    return data["people"][0].get("email", None)

            elif response.status_code == 429:
                print(f"Apollo.io Rate Limit hit. Retrying in {5 * attempt} sec...")
                time.sleep(5 * attempt)

            else:
                print(f" Apollo.io API Error ({response.status_code}): {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Apollo.io Request Error: {e}. Retrying {attempt}/{MAX_RETRIES}...")
            time.sleep(5 * attempt)

    print("Apollo.io request failed after multiple attempts.")
    return None


def predict_email(full_name, company_domain):
    """Generates possible email patterns"""
    first, last = full_name.split(" ", 1) if " " in full_name else (full_name, "")
    for fmt in COMMON_FORMATS:
        email = fmt.format(first=first.lower(), last=last.lower(), domain=company_domain)
        if validate_email(email) == "valid":
            return email
    return None

def validate_email(email):
    """
    Uses Hunter.io Email Verifier API to check if an email is valid
    """
    # if not email or email in ["email_not_unlocked@domain.com", ""]:
    if not email:
        return "invalid"

    url = "https://api.hunter.io/v2/email-verifier"
    params = {"api_key": HUNTER_API_KEY, "email": email}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {}).get("status", "unknown")
    except requests.exceptions.RequestException as e:
        print(f"Email Verification Error: {e}")

    return "unknown"

def process_employee_emails(employees_file, output_file="outputs/validated_emails.csv"):
    """
    Extracts & validates emails for employees from Apollo data.
    If an email is missing, it fetches from Hunter.io
    """
    df = pd.read_csv(employees_file)

    def find_or_validate_email(row):
        email = str(row["email"]) if pd.notna(row["email"]) else ""
        company = row["company"]
        name = row["name"]

        # if pd.isna(email) or email.strip() in ["", "email_not_unlocked@domain.com"]:
        #     email = get_email_from_hunter(name, company)


        # if email:
        #     return email, validate_email(email)


        # return None, "not_found"

        if email.strip() in ["", "email_not_unlocked@domain.com"]:
            email = get_email_from_hunter(name, company) or \
                    get_email_from_apollo(company) or \
                    predict_email(name, company)

            return email, validate_email(email) if email else "not_found"


    df[["email", "email_status"]] = df.apply(lambda row: find_or_validate_email(row), axis=1, result_type="expand")

    df.to_csv(output_file, index=False)
    print(f"✅ Validated emails saved to {output_file}")
