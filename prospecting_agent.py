import requests
import pandas as pd
import time
import re
import json
import os
import hashlib
import numpy as np
import joblib
from typing import List, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AdvancedProspectingAgent:
    def __init__(self, config: Dict):
        self.config = config
        self.encoder = OneHotEncoder(handle_unknown='ignore')
        self._init_components()
        self.load_models()

    def _init_components(self):
        self.email_tracker = self.EmailTracker()
        self.rl_engine = self.ReinforcementLearning()
        self.nlp_processor = self.NLPInterface(self.config['deepseek']['api_key'])

    class EmailTracker:
        def __init__(self):
            self.tracking_data = {}
            
        def create_tracking_pixel(self, email: str) -> str:
            pixel_id = hashlib.sha256(email.encode()).hexdigest()
            self.tracking_data[pixel_id] = {
                'email': email,
                'opens': 0,
                'replies': 0,
                'last_engaged': None
            }
            return f"{self.config['tracking']['base_url']}/pixel/{pixel_id}"

    class ReinforcementLearning:
        def __init__(self):
            self.model = RandomForestClassifier()
            self.training_data = []
            self.feature_labels = ['industry', 'title', 'company_size', 'location']
            
        def update_model(self, features: Dict, success: bool):
            encoded_features = self._encode_features(features)
            self.training_data.append((encoded_features, success))
            
            if len(self.training_data) % 100 == 0:
                self._retrain_model()
                
        def _retrain_model(self):
            X = np.array([x[0] for x in self.training_data])
            y = np.array([x[1] for x in self.training_data])
            self.model.fit(X, y)
            
        def predict_success(self, prospect: Dict) -> float:
            features = self._encode_features(prospect)
            return self.model.predict_proba([features])[0][1]

    class NLPInterface:
        def __init__(self, api_key: str):
            self.api_key = api_key
            
        def parse_query(self, query: str) -> Dict:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [{
                    "role": "system",
                    "content": "Convert queries to JSON filters. Valid filters: industry, location, min_employees, technologies."
                }, {
                    "role": "user", 
                    "content": query
                }],
                "temperature": 0.1
            }
            
            try:
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                response.raise_for_status()
                return json.loads(response.json()['choices'][0]['message']['content'])
            except Exception as e:
                print(f"API Error: {e}")
                return {}

    def get_companies(self, filters: Dict) -> List[Dict]:
        params = {
            'user_key': self.config['crunchbase']['api_key'],
            'industries': filters.get('industry', ''),
            'locations': filters.get('location', ''),
            'min_employees': filters.get('min_employees', 100)
        }
        
        try:
            response = requests.get(
                self.config['crunchbase']['endpoint'],
                params=params,
                timeout=15
            )
            return response.json().get('data', {}).get('items', [])
        except Exception as e:
            print(f"Crunchbase Error: {e}")
            return []

    def get_contacts(self, domain: str) -> List[Dict]:
        headers = {'Authorization': f"Bearer {self.config['apollo']['api_key']}"}
        data = {
            'q_organization_domains': domain,
            'person_titles': ['business development', 'sales', 'cto', 'ceo']
        }
        
        try:
            response = requests.post(
                self.config['apollo']['endpoint'],
                headers=headers,
                json=data,
                timeout=15
            )
            return response.json().get('people', [])
        except Exception as e:
            print(f"Apollo Error: {e}")
            return []

    def validate_email(self, email: str) -> bool:
        try:
            response = requests.post(
                'https://api.neverbounce.com/v4/single/check',
                auth=(self.config['neverbounce']['api_key'], ''),
                json={'email': email},
                timeout=10
            )
            return response.json().get('result') == 'valid'
        except Exception as e:
            print(f"Validation Error: {e}")
            return False

    def generate_prospects(self, query: str) -> pd.DataFrame:
        filters = self.nlp_processor.parse_query(query)
        companies = self.get_companies(filters)
        
        prospects = []
        for company in companies[:self.config.get('max_companies', 50)]:
            contacts = self.get_contacts(company['domain'])
            for contact in contacts:
                email = self.find_valid_email(
                    contact['first_name'],
                    contact['last_name'],
                    company['domain']
                )
                if email and self.validate_email(email):
                    prospect = self._create_prospect_record(contact, company, email)
                    prospect['success_prob'] = self.rl_engine.predict_success(prospect)
                    prospects.append(prospect)
        
        return pd.DataFrame(prospects).sort_values('success_prob', ascending=False)

    def send_outreach_email(self, prospect: Dict, template: str) -> bool:
        msg = MIMEMultipart()
        msg['From'] = self.config['email']['address']
        msg['To'] = prospect['email']
        msg['Subject'] = self.config['email']['subject']
        
        tracking_pixel = self.email_tracker.create_tracking_pixel(prospect['email'])
        body = template.format(**prospect) + f"<img src='{tracking_pixel}' width='1' height='1'>"
        msg.attach(MIMEText(body, 'html'))
        
        try:
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email']['address'], self.config['email']['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False

# Configuration
config = {
    'crunchbase': {
        'api_key': 'YOUR_CRUNCHBASE_KEY',
        'endpoint': 'https://api.crunchbase.com/api/v4/searches/organizations'
    },
    'apollo': {
        'api_key': 'YOUR_APOLLO_KEY',
        'endpoint': 'https://api.apollo.io/v1/mixed_people/search'
    },
    'deepseek': {
        'api_key': 'YOUR_DEEPSEEK_KEY'
    },
    'email': {
        'address': 'your@email.com',
        'password': 'your_password',
        'smtp_server': 'smtp.example.com',
        'smtp_port': 587,
        'subject': 'Partnership Opportunity'
    },
    'tracking': {
        'base_url': 'https://your-tracking-domain.com'
    },
    'max_companies': 100
}

if __name__ == "__main__":
    agent = AdvancedProspectingAgent(config)
    
    # Example query execution
    prospects = agent.generate_prospects(
        "Find AI companies in California with over 200 employees"
    )
    
    # Save and send emails
    prospects.to_csv('ai_prospects.csv', index=False)
    
    with open('email_template.html') as f:
        template = f.read()
        
    for _, row in prospects.iterrows():
        agent.send_outreach_email(row.to_dict(), template)
