from scrapers.crunchbase_scraper import get_all_target_companies, save_companies_to_csv
from scrapers.apollo_people import process_companies_from_csv
from extractors.email_finder import process_employee_emails

if __name__ == "__main__":
    print("🔍 Fetching companies from Crunchbase...")
    companies = get_all_target_companies(limit_per_term=10)

    if companies:
        print(f"✅ {len(companies)} companies retrieved.")
        save_companies_to_csv(companies)
    
        print("🔍 Fetching decision-makers via Apollo.io...")
        process_companies_from_csv("outputs/companies.csv")

        print("🔍 Validating emails using Hunter.io...")
        process_employee_emails("outputs/decision_makers.csv")

        print("✅ Workflow completed successfully!")

    else:
        print("No companies found.")
