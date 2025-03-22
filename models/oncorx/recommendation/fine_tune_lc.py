import fitz  # PyMuPDF
import os
import json

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def create_jsonl_from_pdfs(pdf_directory, output_jsonl_path):
    """Processes PDFs in a directory and writes the text content into a JSONL file."""
    with open(output_jsonl_path, 'w') as jsonl_file:
        for pdf_file in os.listdir(pdf_directory):
            if pdf_file.endswith(".pdf"):
                pdf_path = os.path.join(pdf_directory, pdf_file)
                extracted_text = extract_text_from_pdf(pdf_path)
                
                # Create JSON object
                jsonl_data = {
                    "text": extracted_text
                }
                
                # Write to JSONL file
                jsonl_file.write(json.dumps(jsonl_data) + "\n")

# Example usage
pdf_directory = "data/lung_cancers"  # Replace with the path to your PDFs
output_jsonl_path = "data/oncorx_rec_text.jsonl"  # Output file

create_jsonl_from_pdfs(pdf_directory, output_jsonl_path)
