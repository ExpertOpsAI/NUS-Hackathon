import requests
import json

def fetch_pubmed_data(query, max_results=10):
    base_url = ""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    ids = data['esearchresult']['idlist']
    
    details_url = ""
    details_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json"
    }
    details_response = requests.get(details_url, params=details_params)
    return details_response.json()

# Fetch data and store in JSON file
pubmed_data = fetch_pubmed_data("lung cancer", max_results=5)
with open("pubmed_data.json", "w") as f:
    json.dump(pubmed_data, f, indent=2)
