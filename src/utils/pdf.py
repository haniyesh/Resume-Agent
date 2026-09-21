from io import BytesIO
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_file):
    if isinstance(pdf_file, bytes):
        pdf_file = BytesIO(pdf_file)
    reader = PdfReader(pdf_file)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text()
    return resume_text
