import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import base64
import re

# Load environment variables from .env file
load_dotenv()


def convert_url(input_url):
    # Check for clinical trials URL
    match = re.search(r'NCT\d+', input_url)
    if match:
        trial_id = match.group(0)
        return f""
    
    # Check for PubMed URL
    match = re.search(r'pubmed/(\d+)\.pdf', input_url)
    if match:
        pubmed_id = match.group(1)
        return f""
    
    # Check for FDA label URL
    match = re.search(r'labels/(\d+s\d+lbl)\.pdf', input_url)
    if match:
        label_id = match.group(1)
        appl_no = label_id.split('s')[0]
        return f""
    
    # If no match, return the original URL
    return input_url


# Read environment variables
search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
search_index = os.getenv("AZURE_SEARCH_INDEX_NAME")
search_key = os.getenv("AZURE_SEARCH_API_KEY")

# Initialize the SearchClient
search_client = SearchClient(endpoint=search_endpoint, index_name=search_index, credential=AzureKeyCredential(search_key))

# Function to decode a base64 encoded string with custom padding logic
def decode_base64(encoded_string):
    # Add padding based on the last character of the string
    last_char = encoded_string[-1]
    
    if last_char == '0':
        # No padding needed
       
        encoded_string = encoded_string[:-1]
    elif last_char == '1':
        # Add one '=' padding
       
        encoded_string += '='
    elif last_char == '2':
        # Add two '=' padding
       
        encoded_string += '=='

    try:
        # Attempt to decode the base64 string
        # print(encoded_string)
        decoded_bytes = base64.b64decode(encoded_string)
        decoded_string = decoded_bytes.decode('utf-8')
        return decoded_string
    except (base64.binascii.Error, ValueError) as e:
        # If decoding fails, return the original string or handle it
        print(f"Warning: Failed to decode base64 string. Using original string. Error: {e}")
        return encoded_string
    
def perform_semantic_search(query):
    try:
        # Perform the search query using semantic configuration
        results = search_client.search(
            search_text=query,
            query_type='semantic',
            semantic_configuration_name='default',
            top=2  # Limit to top 3 results
        )

        # Initialize variables
        combined_results = []
        combined_references = []
        max_length = 1000000  # Maximum length allowed
        current_length = 0

        for result in results:
            content = result["content"]
            reference = convert_url(decode_base64(result["id"]))  
            content_length = len(content)

            # Check if adding this content would exceed the max_length
            if current_length + content_length > max_length:
                # Truncate the content to fit within the remaining allowed length
                remaining_length = max_length - current_length
                truncated_content = content[:remaining_length]
                combined_results.append(truncated_content)
                combined_references.append(reference)
                break  # Stop after adding this truncated content
            else:
                # Add full content and reference
                combined_results.append(content)
                combined_references.append(reference)
                current_length += content_length

        # Join the combined results and references into a final string
        final_result_content = "\n".join(combined_results)
        final_result_references = "\nReferences: " + "\n".join(combined_references)
        final_result = final_result_content + final_result_references

        # print(final_result)
        # print(len(final_result_content))
        # print(final_result_references)
        
        return final_result

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
# # Perform a semantic search with the given query
# perform_semantic_search("what is the side effect of crizotinib?")
