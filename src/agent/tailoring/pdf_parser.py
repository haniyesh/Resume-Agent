import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Reads a PDF file and extracts all raw text, preserving basic layout flow.
    
    Args:
        pdf_path (str): The absolute or relative path to the PDF resume.
        
    Returns:
        str: The extracted and concatenated text from all pages.
    """
    try:
        # 1. Open the PDF document using PyMuPDF
        document = fitz.open(pdf_path)
        full_text = ""
        
        # 2. Iterate through all pages and extract text
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            
            # Extract text (using "text" mode is usually sufficient for resumes)
            # You can also use "blocks" if you need to detect columns, but let's keep it simple first
            page_text = page.get_text("text")
            full_text += page_text + "\n"
            
        document.close()
        return full_text
        
    except FileNotFoundError:
        print(f"[Error] Resume file not found at: {pdf_path}")
        return ""
    except Exception as e:
        print(f"[Error] Failed to read PDF: {e}")
        return ""

def clean_resume_text(raw_text: str) -> str:
    """
    Cleans the extracted text to remove noise (extra spaces, weird unicode characters).
    THIS IS THE PART YOU NEED TO CUSTOMIZE.
    """
    if not raw_text:
        return ""
        
    # Remove excessive newlines (more than 2 consecutive newlines become just 2)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', raw_text)
    
    # Remove weird bullet points and replace them with standard ones (e.g., unicode dots)
    cleaned_text = re.sub(r'[•●▪]', '-', cleaned_text)
    
    # Remove leading/trailing whitespaces
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

# --- Debugging / Testing Block ---
if __name__ == "__main__":
    # Test path - make sure you put a sample PDF in this location
    test_pdf_path = "../../data/resume.pdf"
    
    print("[System] Extracting text...")
    raw = extract_text_from_pdf(test_pdf_path)
    
    print("[System] Cleaning text...")
    clean = clean_resume_text(raw)
    
    print("\n--- Extracted Resume ---")
    print(clean[:500] + "...\n[TEXT TRUNCATED FOR DISPLAY]")