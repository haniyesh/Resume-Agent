import json
from fpdf import FPDF

# =================================================================
# 1. Resume PDF Class Definition
# =================================================================
class ResumePDF(FPDF):
    def header(self):
        """ This method is automatically called for every new page """
        pass # We want a custom header on the first page only, so we leave this empty

    def add_custom_header(self, name: str, contact_info: str):
        """ Renders the candidate's name and contact information """
        self.set_font("helvetica", "B", 24)
        # RGB Color (Dark Blue for professional look)
        self.set_text_color(44, 62, 80) 
        self.cell(0, 10, name, new_x="LMARGIN", new_y="NEXT", align="C")
        
        self.set_font("helvetica", "", 11)
        self.set_text_color(127, 140, 141) # Gray color
        self.cell(0, 8, contact_info, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5) # Add a small line break (margin)

    def add_section_title(self, title: str):
        """ Renders a section title (e.g., SKILLS, EXPERIENCE) with a bottom line """
        self.set_font("helvetica", "B", 14)
        self.set_text_color(41, 128, 185) # Blue color
        self.cell(0, 10, title.upper(), new_x="LMARGIN", new_y="NEXT", align="L")
        
        # Draw a horizontal line under the title
        current_y = self.get_y()
        self.line(self.l_margin, current_y, self.w - self.r_margin, current_y)
        self.ln(3)

    def add_section_body(self, text: str):
        """ Renders the main body text for a section """
        self.set_font("helvetica", "", 11)
        self.set_text_color(0, 0, 0) # Black color
        # multi_cell automatically handles text wrapping for long paragraphs
        self.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

# =================================================================
# 2. Main Generator Function
# =================================================================
def generate_tailored_pdf(resume_data: dict, output_filename: str):
    """
    Takes a structured Python dictionary and generates a PDF.
    """
    print(f"🔄 [PDF Generator] Creating PDF: {output_filename} ...")
    
    pdf = ResumePDF()
    pdf.add_page()
    
    # Set global margins (Left, Top, Right)
    pdf.set_margins(20, 20, 20)

    # 1. Header Section
    pdf.add_custom_header(
        name=resume_data.get("name", "Candidate Name"),
        contact_info=resume_data.get("contact", "Email | LinkedIn | GitHub")
    )

    # 2. Summary Section
    if "summary" in resume_data:
        pdf.add_section_title("Professional Summary")
        pdf.add_section_body(resume_data["summary"])

    # 3. Skills Section
    if "skills" in resume_data:
        pdf.add_section_title("Core Competencies")
        pdf.add_section_body(resume_data["skills"])

    # 4. Experience / Projects Section
    if "projects" in resume_data:
        pdf.add_section_title("Relevant Projects & Research")
        for project in resume_data["projects"]:
            # Render Project Title in Bold
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 6, project["title"], new_x="LMARGIN", new_y="NEXT")
            # Render Project Description in Regular font
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, project["description"], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    # Save the file to disk
    pdf.output(output_filename)
    print(f"✅ [PDF Generator] Success! Resume saved as '{output_filename}'")

# =================================================================
# 3. Test the Module
# =================================================================
if __name__ == "__main__":
    # Mock Data: This is the structure we will force the LLM to output later
    mock_ai_output = {
        "name": "Haniye Shakibayi Senobari",
        "contact": "Istanbul, Turkiye | haniye.sh@example.com | github.com/haniye",
        "summary": "Master's student in Artificial Intelligence at Bahcesehir University with a 3.50 GPA. Deeply focused on computer vision, generative AI, and financial market analysis using Hidden Markov Models. Proven ability to bridge mathematical optimization with practical AI applications.",
        "skills": "Python, YOLO, Qdrant, MQL5, Pine Script, Open-Source LLMs (Llama-3), Computer Vision (2D transformations), Optimization (Gauss-Newton).",
        "projects": [
            {
                "title": "Cognitive Safety Agent (YOLOv8 & LLM)",
                "description": "- Developed an autonomous agent integrating YOLOv8 and open-source LLMs to analyze safety hazards in real-time.\n- Implemented Qdrant for RAG-based safety rule retrieval."
            },
            {
                "title": "Financial Regime Detection using HMM",
                "description": "- Applied Hidden Markov Models to detect market stress and regime switching on XAUUSD and BTCUSD.\n- Backtested strategies using Pine Script and MQL5."
            }
        ]
    }
    
    generate_tailored_pdf(mock_ai_output, "Tailored_Resume_Haniye.pdf")