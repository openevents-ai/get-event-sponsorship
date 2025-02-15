# Prospect Agent

## Description

A Python-based agent that builds **prospect email lists** from **Apollo.io**, **Hunter.io** and other email lookup services for target industries. It also includes email validation and fallback mechanisms when primary sources fail

## Features

- Scrapes professional contacts (Name, Email, Role, Company)
- Uses **Crunchbase & Apollo.io** for accurate data
- Validates emails with **Hunter.io** or fallback methods
- Outputs **clean CSV** formats
- Scalable architecture for future enhancements

## Installation

1.  Clone the Repository

```bash
git clone <repo-url>
cd prospect-agent
```

2. Install Dependencies

```bash
    poetry install
```

3.  Set Up API Keys

Create a `.env` file in the root directory and add:

```ini
CRUNCHBASE_API_KEY="your_crunchbase_api_key"
APOLLO_API_KEY="your_apollo_api_key"
HUNTER_API_KEY="your_hunter_api_key"
```

## Usage

Run the Email Extraction Pipeline using following command:

```bash
poetry run python main.py
```

### Output File (validated_emails.csv)

| Name       | Role     | Company     | Email            | Status |
| ---------- | -------- | ----------- | ---------------- | ------ |
| John Doe   | CEO      | ABC Corp    | john.doe@abc.com | Valid  |
| Jane Smith | Founder  | XYZ Ltd     | jane@xyz.com     | Valid  |
| Mark Lee   | Director | Example Inc | Not Found        | -      |

### Customization

Adjust Decision-Maker Roles if needed in order to do this modify `job_titles` list:

```python
job_titles = ["CEO", "Founder", "Owner", "Head of Partnerships"]
```
