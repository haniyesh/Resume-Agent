# agents/tailoring/pdf_parser.py

import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Reads a PDF file from the given path and extracts all text content.
    Returns the extracted text as a single string.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The PDF file was not found at path: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        extracted_text = ""
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
        return extracted_text.strip()
        
    except Exception as e:
        print(f"[Error] Failed to parse PDF file: {e}")
        return ""