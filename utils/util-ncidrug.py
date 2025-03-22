import requests
from bs4 import BeautifulSoup



# Step 1: Get the list of drug names from the NCI website
nci_url = ''
response = requests.get(nci_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract drug names
drug_names = []
article = soup.find('article')
if article:
    for section in article.find_all('section'):
        for li in section.find_all('li'):
            drug_name = li.get_text(strip=True)
            drug_names.append(drug_name)

# Extract the first word of each drug name
first_words = [name.split()[0] for name in drug_names]

# Function to get setid from DailyMed API
def get_setid(drug_name):
    api_url = f''
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['setid']
    return None

# Function to download PDF from DailyMed using setid
def download_pdf(setid, drug_name):
    pdf_url = f''
    pdf_response = requests.get(pdf_url)
    if pdf_response.status_code == 200:
        with open(f'{drug_name}.pdf', 'wb') as pdf_file:
            pdf_file.write(pdf_response.content)
        print(f'{drug_name} PDF downloaded successfully.')
    else:
        print(f'Failed to download PDF for {drug_name}.')

# Step 2: For each drug name, get setid and download the PDF
for drug_name in first_words:
    print(drug_name)
    setid = get_setid(drug_name)
    if setid:
        download_pdf(setid, drug_name)
    else:
        print(f'No setid found for {drug_name}.')
