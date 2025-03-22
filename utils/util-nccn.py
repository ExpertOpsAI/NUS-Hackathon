import os
import requests
from urllib.parse import urlparse
from PyPDF2 import PdfReader
from openai import AzureOpenAI
import json
import tiktoken
from dotenv import load_dotenv
import re
import shutil
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# NCCN => labels => clinical trials => publications
#labels (Manual) => clinical trials => publications

# Load environment variables from .env file
load_dotenv()

# Read environment variables
api_version = os.getenv("OPENAI_API_VERSION")
api_key = os.getenv("OPENAI_API_KEY")
azure_endpoint = os.getenv("OPENAI_API_BASE")
deployment_name = os.getenv("OPENAI_CHAT_MODEL")

# Set up Azure OpenAI
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    print("extract_text_from_pdf")
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

# Function to chunk the text: gpt-3.5-turbo or gpt-4o
def chunk_text(text, max_tokens):
    enc = tiktoken.encoding_for_model("gpt-4o")
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = enc.decode(tokens[i:i+max_tokens])
        chunks.append(chunk)
    return chunks

# Function to extract entities (approved drugs, experimental drugs, PubMed links, FDA links) using Azure OpenAI
def extract_entities(text):
    print("extract_entities")
    chunks = chunk_text(text, 4096)
    approved_drugs, experimental_drugs, pubmed_links, asco_links, fda_links = [], [], [], [], []

    for chunk in chunks:   
        input_prompt = f"""
        Extract the following information from the below KNOWLEDGE BASE SECTION and return it in JSON format.
        KNOWLEDGE BASE SECTION START *********************************************************:
        {chunk}
        ********************************************************* KNOWLEDGE BASE SECTION END
        1. Extract Drug names as drug_names from KNOWLEDGE BASE SECTION (separated into approved and experimental),
        2. Extract PubMed article as pubmed_article_links links from KNOWLEDGE BASE SECTION (only include if there is a URL link starting with )
        3. Extract ASCO article links as asco_article_links from KNOWLEDGE BASE SECTION(only include if there is a URL link starting with ),
        4. Extract FDA label links as fda_label_links from KNOWLEDGE BASE SECTION (only include if there is a URL link starting with ).
        Note: Only include information available within the KNOWLEDGE BASE SECTION. If a requested type of information is not found in KNOWLEDGE BASE SECTION, return empty value of that variable in the result.
        """
  
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps find information related to drug names, PubMed publications, clinical trials, FDA drug labels, and other information requested by users from the provided knowledge base."},
                {"role": "user", "content": input_prompt}
            ],
            temperature=0
        )

        try:
            raw_json = response.choices[0].message.content.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3]
            entities = json.loads(raw_json)
            print('input prompts: ', input_prompt)
            print('output: ', raw_json)
            # Extract information from the parsed JSON, handling empty values
            approved_drugs.extend(entities.get("drug_names", {}).get("approved", []))
            experimental_drugs.extend(entities.get("drug_names", {}).get("experimental", []))
            pubmed_links.extend(entities.get("pubmed_article_links", []))
            asco_links.extend(entities.get("asco_article_links", []))
            fda_links.extend(entities.get("fda_label_links", []))
        except json.JSONDecodeError:
            print("Error decoding JSON response from OpenAI")
        
    return list(set(approved_drugs)), list(set(experimental_drugs)), list(set(pubmed_links)), list(set(asco_links)), list(set(fda_links))

# # Function to extract clinical trial IDs (NCT numbers) from FDA label text using Azure OpenAI
# def extract_clinical_trial_ids(text):
#     print("extract_clinical_trial_ids")
#     chunks = chunk_text(text, 2048)
#     clinical_trial_ids = []

#     for chunk in chunks:
#         input_prompt = f"Extract clinical trial IDs (NCT numbers) from the following text and return in JSON format:\n\n{chunk}"
#         response = client.chat.completions.create(
#             model=deployment_name,
#             messages=[
#                 {"role": "system", "content": "You are a Healthtech AI assistant that helps find information related to drug names, PubMed publications, clinical trials, FDA drug labels, and others."},
#                 {"role": "user", "content": input_prompt}
#             ],
#             temperature=0
#         )
        
#         try:
#             raw_json = response.choices[0].message.content.strip()
#             if raw_json.startswith("```json"):
#                 raw_json = raw_json[7:-3]
#             trial_ids = json.loads(raw_json)
#             clinical_trial_ids.extend(trial_ids)
#         except Exception as e:
#             print(f"Error extracting clinical trial IDs: {e}")

#     return list(set(clinical_trial_ids))


# Function to download and save documents
def download_and_save(url, path):
    print("download_and_save")
    response = requests.get(url)
    with open(path, 'wb') as file:
        file.write(response.content)

# Function to download clinical trial documents based on NCT IDs
def download_clinical_trials(nct_ids, path):
    print("download_clinical_trials")
    for nct_id in nct_ids:
        trial_url = f""
        file_path = os.path.join(path, f"{nct_id}.xml")
        download_and_save(trial_url, file_path)

# Function to get the filename from a URL
def get_filename_from_url(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)

# Function to create directory structure and store drug information
def create_directory_structure(base_dir, approved_drugs, experimental_drugs, pubmed_links, fda_links):
    print("create_directory_structure")
    # Create subdirectories for approved and experimental drugs
    approved_dir = os.path.join(base_dir, "Drugs/Approved")
    experimental_dir = os.path.join(base_dir, "Drugs/Experimental")
    
    os.makedirs(approved_dir, exist_ok=True)
    os.makedirs(experimental_dir, exist_ok=True)
    
    # Store approved drugs in text files
    for drug in approved_drugs:
        drug_dir = os.path.join(approved_dir, drug)
        os.makedirs(drug_dir, exist_ok=True)
        drug_file_path = os.path.join(drug_dir, f"{drug}.txt")
        with open(drug_file_path, "w", encoding='utf-8') as drug_file:
            drug_file.write(drug)
    
    # Store experimental drugs in text files
    for drug in experimental_drugs:
        drug_dir = os.path.join(experimental_dir, drug)
        os.makedirs(drug_dir, exist_ok=True)
        drug_file_path = os.path.join(drug_dir, f"{drug}.txt")
        with open(drug_file_path, "w", encoding='utf-8') as drug_file:
            drug_file.write(drug)

    # Download and save PubMed articles
    if pubmed_links:
        pubmed_dir = os.path.join(base_dir, "Publications/Journals/PubMed")
        os.makedirs(pubmed_dir, exist_ok=True)
        for i, link in enumerate(pubmed_links):
            file_path = os.path.join(pubmed_dir, get_filename_from_url(link))
            download_and_save(link, file_path)
    
    # Download and save FDA labels in the respective drug directories
    if fda_links:
        for i, link in enumerate(fda_links):
            filename = get_filename_from_url(link)
            for drug in approved_drugs:
                if drug.lower() in link.lower():
                    drug_dir = os.path.join(approved_dir, drug)
                    file_path = os.path.join(drug_dir, filename)
                    download_and_save(link, file_path)
                    fda_text = extract_text_from_pdf(file_path)
                    clinical_trial_ids = extract_clinical_trial_ids(fda_text)
                    trial_path = os.path.join(base_dir, "Clinical_Trials/Ongoing/Phase_II")  # Adjust phase as necessary
                    os.makedirs(trial_path, exist_ok=True)
                    download_clinical_trials(clinical_trial_ids, trial_path)
                    break
            for drug in experimental_drugs:
                if drug.lower() in link.lower():
                    drug_dir = os.path.join(experimental_dir, drug)
                    file_path = os.path.join(drug_dir, filename)
                    download_and_save(link, file_path)
                    fda_text = extract_text_from_pdf(file_path)
                    clinical_trial_ids = extract_clinical_trial_ids(fda_text)
                    trial_path = os.path.join(base_dir, "Clinical_Trials/Ongoing/Phase_II")  # Adjust phase as necessary
                    os.makedirs(trial_path, exist_ok=True)
                    download_clinical_trials(clinical_trial_ids, trial_path)
                    break

# def process_pubmed_links(pubmed_links):
#     return

# def process_clinical_trials():
#     return

def download_pdf(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {url}")
    else:
        print(f"Failed to download: {url}")

def extract_drug_name_from_text(text):
    # Take the first 25 words
    words = text.split()[:25]
    
    # Exclude specific unwanted words
    exclude_words = {"HIGHLI", "HIGHLIGHTS", "OF", "PRESCRIBING", "INFORMATION", "WARNINGS", "PRECAUTIONS", "AND", "NG", "THESE", "DO", "NOT", "INCLUDE", "ALL", "THE", "TO", "USE", "SEE", "FULL", "SAFELY", "EFFECTIVELY.", "FOR"}

    # Filter capitalized words that are not in the exclude list and are less than 12 characters in length
    capitalized_words = [word for word in words if word.isupper() and word not in exclude_words and len(word) < 12 and  len(word) > 5]
    
    # Return the first remaining capitalized word as the drug name
    if capitalized_words:
        drug_name = capitalized_words[0]
        return drug_name.lower().replace('®', '').replace(' ', '_')  # Return a lowercase, underscore-separated version
    return None

def extract_clinical_trial_ids(text):
    # Define the pattern to match NCT numbers
    nct_pattern = re.compile(r'NCT\d{8}')
    return nct_pattern.findall(text)

def download_clinical_trial_data(nct_id, output_path, base_dir):
    api_url = f'    response = requests.get(api_url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded clinical trial data for {nct_id}")
        # logic to convert clinical trail into pdf

        # logic to download pubmed articles
        try:
            response_json = response.json()
            #print(str(response_json["protocolSection"]["referencesModule"]))
            for obj in response_json["protocolSection"]["referencesModule"]["references"]:
                process_pubmed_links([f""], base_dir)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print(f"Failed to download clinical trial data for {nct_id}")

def process_fda_label_links(fda_links, base_dir):
    approved_drugs_dir = os.path.join(base_dir, "drugs", "approved")
    #os.makedirs(approved_drugs_dir, exist_ok=True)
    
    for url in fda_links:
        pdf_filename = os.path.join(approved_drugs_dir, url.split('/')[-1])
        if not url.startswith(""):
            continue
        download_pdf(url, pdf_filename)
        
        text = extract_text_from_pdf(pdf_filename)
        drug_name = extract_drug_name_from_text(text)
        clinical_trial_ids = extract_clinical_trial_ids(text)
        
        if drug_name:
            drug_dir = os.path.join(approved_drugs_dir, drug_name)
            labels_dir = os.path.join(drug_dir, "labels")
            os.makedirs(labels_dir, exist_ok=True)
            
            clinicaltrials_dir = os.path.join(drug_dir, "clinicaltrials")
            os.makedirs(clinicaltrials_dir, exist_ok=True)
            
            # Move the label PDF to the labels directory
            new_pdf_filename = os.path.join(labels_dir, url.split('/')[-1])
            if os.path.exists(new_pdf_filename):
                os.remove(new_pdf_filename)
            shutil.move(pdf_filename, new_pdf_filename)
            
            # Download clinical trial documents
            for nct_id in clinical_trial_ids:
                clinical_trial_filename = os.path.join(clinicaltrials_dir, f'{nct_id}.json')
                download_clinical_trial_data(nct_id, clinical_trial_filename, base_dir)
        else:
            print(f"Could not determine the drug name for {url}")

# def download_asco_article(url, output_path):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
#         'Accept-Language': 'en-US,en;q=0.9',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Referer': 'https://www.google.com/',
#         'Connection': 'keep-alive',
#     }
#     try:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             with open(output_path, 'wb') as f:
#                 f.write(response.content)
#             print(f"Downloaded: {url}")
#         else:
#             print(f"Failed to download: {url} - Status Code: {response.status_code}")
#             print(f"Response content: {response.content[:1000]}")  # Print the first 1000 characters of the response content for debugging
#     except Exception as e:
#         print(f"Exception occurred while downloading {url}: {e}")

def get_pdf_url(doi_url):
    # Send a GET request to the DOI URL to follow the redirect
    response = requests.get(doi_url, allow_redirects=True)
    redirected_url = response.url
    # Check for known patterns and construct the PDF URL
    if "nejm.org" in redirected_url:
        # NEJM specific PDF URL format
        pdf_url = redirected_url.replace("/doi/", "/doi/pdf/")
    elif "linkinghub.elsevier.com" in redirected_url:
        # Elsevier specific handling, we need to extract the pii and use it
        soup = BeautifulSoup(response.content, 'html.parser')
        pii = redirected_url.split('/')[-1]  # Extracting the pii from the URL
        pdf_url = f""  
    else:
        # Default: Just try to append '/pdf' to the DOI URL, this may work for some cases
        pdf_url = ""

    return pdf_url

def convert_ncbi_to_pubmed_url(ncbi_url):
    # Check if the URL starts with the specified prefix
    if ncbi_url.startswith(""):
        # Extract the number using regular expression
        match = re.search(r'/pubmed/(\d+)', ncbi_url)
        if match:
            pmid = match.group(1)
            pubmed_url = f""
            return pubmed_url
        else:
            return ncbi_url  # Return the original URL if no PMID is found
    else:
        return ncbi_url 

def process_pubmed_links(pubmed_links, base_dir):   
    print(pubmed_links, base_dir)
    pubmed_dir = os.path.join(base_dir, "publications", "pubmed")
    for url in pubmed_links:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': '',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        print(url)
        pubmed_url = convert_ncbi_to_pubmed_url(url)
        print("pubmed_url", pubmed_url)

        response = requests.get(pubmed_url, headers=headers)
        content = response.text  # Use .text to get the content as a string

        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # Initialize variables with default values
        pmcid = None
        doi = None
        pmid = "unknown"  # Default value if PMID is not found

        # Extract the PMID
        try:
            pmid = soup.find('span', class_='identifier pubmed').find('strong').text.strip()
        except AttributeError:
            print("PMID not found on the page.")

        # Extract the PMCID
        try:
            pmcid = soup.find('span', class_='identifier pmc').find('a').text.strip()
        except AttributeError:
            print("PMCID not found on the page.")

        # Extract the DOI
        try:
            doi = soup.find('span', class_='identifier doi').find('a').text.strip()
        except AttributeError:
            print("DOI not found on the page.")

        # Form the URL and attempt to download the PDF
        pdf_url = None
        if pmcid:
            pdf_url = f""
            print(f"Attempting to download PDF from PMC URL: {pdf_url}")
        elif doi:
            pdf_url = get_pdf_url(f"")
            print(f"Attempting to download PDF from DOI URL: {pdf_url}")

        if pdf_url:
            print("pdf_url", pdf_url)
            try:
                # Attempt to download the PDF with headers to mimic a browser
                pdf_response = requests.get(pdf_url, headers=headers)
                
                # Check if the request was successful
                if pdf_response.status_code == 200:
                    # Define the PDF filename using the PMID
                    pdf_filename = f"{pmid}.pdf"
                    
                    # Save the PDF content to a file
                    with open(os.path.join(pubmed_dir, pdf_filename), 'wb') as pdf_file:
                        pdf_file.write(pdf_response.content)
                    
                    print(f"PDF downloaded successfully as {pdf_filename}")
                else:
                    print(f"Failed to download PDF. HTTP status code: {pdf_response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred while trying to download the PDF: {e}")
        else:
            print("No valid PMCID or DOI found to form a URL.")



# def process_asco_links(asco_links, base_dir):
#     asco_dir = os.path.join(base_dir, "publications", "asco")
#     # os.makedirs(asco_dir, exist_ok=True)
    
#     for url in asco_links:
#         # # Create a valid filename from the URL
#         # filename = re.sub(r'\W+', '_', url.split('/')[-1]) + '.html'
#         # output_path = os.path.join(asco_dir, filename)
        
#         # download_asco_article(url, output_path)

# Define the directory structure
directory_structure = [
    "guidelines/nccn/2024",
    "guidelines/asco/2024",
    "guidelines/esmo/2024",
    "drugs/approved",
    "drugs/experimental",
    "publications/pubmed",
    "publications/asco",
    "miscellaneous/reports",
    "miscellaneous/case_studies",
    "miscellaneous/others"
]




# Main function to execute the process
def main():
    # Making directories
    # pdf_path = "cancer_treatment_repository/nsclc/guidelines/nccn/2024/nscl_v72024.pdf"
    # base_dir = "cancer_treatment_repository/nsclc"

    pdf_path = "cancer_treatment_repository/breast/guidelines/nccn/2024/breast_v42024.pdf"
    base_dir = "cancer_treatment_repository/breast"
    # Create the directories
    for directory in directory_structure:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)

    # Extracting informations from NCCN guideline
    text = extract_text_from_pdf(pdf_path)
    approved_drugs, experimental_drugs, pubmed_links, asco_links, fda_links = extract_entities(text)
    #fda_links = [""]
    process_fda_label_links(fda_links, base_dir)    
    process_pubmed_links(pubmed_links, base_dir)
    #   process_asco_links(asco_links, base_dir)

    # print("Drugs and references have been successfully categorized and stored.")


# Starting the execution
main()