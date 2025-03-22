import requests
from bs4 import BeautifulSoup
import json

def fetch_fda_drug_data():
    url = ""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    drugs = []
    for row in soup.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        drug_name = cols[0].text.strip()
        link = cols[0].find('a')['href']
        drugs.append({'drug_name': drug_name, 'link': link})
    return drugs

# Fetch data and store in JSON file
fda_drugs = fetch_fda_drug_data()
with open("fda_drugs.json", "w") as f:
    json.dump(fda_drugs, f, indent=2)
