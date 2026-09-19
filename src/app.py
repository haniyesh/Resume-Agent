import streamlit as st
import yaml
from html import escape
from utils.pdf import extract_text_from_pdf
from utils.llm import parse_resume, review_resume
from utils.resume_pdf import generate_resume_pdf,merge_revised_resume
from agent import run_resume_agent

def _display_value(value):
    return escape(str(value)) if value not in (None, "") else ""


def _display_location(location):
    if not isinstance(location, dict):
        return ""
    return ", ".join(
        str(location.get(field))
        for field in ("city", "state", "country")
        if location.get(field)
    )


def _display_dates(item):
    start = item.get("start_date", "")
    end = item.get("end_date", "")
    if not start and not end:
        return ""
    return f"{_display_value(start)} - {_display_value(end or 'Present')}"


def _resume_html(data):
    data = data or {}
    personal_info = data.get("personal_info") or {}
    if not isinstance(personal_info, dict):
        personal_info = {"full_name": personal_info}

    contact = []
    for field in ("phone", "email", "linkedin", "github", "website"):
        if personal_info.get(field):
            contact.append(_display_value(personal_info[field]))
    address = _display_location(personal_info.get("address"))
    if address:
        contact.append(_display_value(address))

    html = [
        "<div class='resume-paper'>",
        "<div class='resume-header'>",
        f"<div class='resume-name'>{_display_value(personal_info.get('full_name', 'Resume'))}</div>",
        f"<div class='resume-headline'>{_display_value(personal_info.get('headline', ''))}</div>",
        f"<div class='resume-contact'>{' | '.join(contact)}</div>",
        "</div>",
    ]

    def add_section(title, body):
        if body:
            html.extend([f"<div class='resume-section'><h3>{title}</h3>{body}</div>"])

    summary = data.get("summary")
    add_section("Highlights", f"<p>{_display_value(summary)}</p>" if summary else "")

    experience_html = []
    for job in data.get("work_experience") or []:
        if not isinstance(job, dict):
            continue
        title = _display_value(job.get("job_title", ""))
        company = _display_value(job.get("company", ""))
        location = _display_location(job.get("location"))
        metadata = " | ".join(part for part in (location, _display_dates(job)) if part)
        experience_html.append(
            f"<div class='resume-entry'><div class='entry-title'><strong>{title}</strong>"
            f"<span>{company}</span></div>"
            f"<div class='entry-meta'>{metadata}</div>"
            f"<p>{_display_value(job.get('description', ''))}</p>"
            f"<ul>{''.join(f'<li>{_display_value(item)}</li>' for item in job.get('achievements') or [])}</ul></div>"
        )
    add_section("Work Experience", "".join(experience_html))

    education_html = []
    for item in data.get("education") or []:
        if not isinstance(item, dict):
            continue
        degree = " ".join(
            part for part in (item.get("degree"), item.get("field_of_study")) if part
        )
        metadata = " | ".join(
            part for part in (_display_location(item.get("location")), _display_dates(item)) if part
        )
        honors = "".join(f"<li>{_display_value(honor)}</li>" for honor in item.get("honors") or [])
        education_html.append(
            f"<div class='resume-entry'><div class='entry-title'><strong>{_display_value(degree)}</strong>"
            f"<span>{_display_value(item.get('institution', ''))}</span></div>"
            f"<div class='entry-meta'>{metadata}</div><ul>{honors}</ul></div>"
        )
    add_section("Education", "".join(education_html))

    skills = data.get("skills") or []
    add_section("Skills", f"<p>{_display_value(', '.join(str(skill) for skill in skills))}</p>" if skills else "")

    certifications = data.get("certifications") or []
    certificates_html = "".join(
        f"<li><strong>{_display_value(item.get('title', ''))}</strong>"
        f" | {_display_value(item.get('issuer', ''))}</li>"
        for item in certifications if isinstance(item, dict)
    )
    add_section("Certifications", f"<ul>{certificates_html}</ul>" if certificates_html else "")

    projects = data.get("projects") or []
    projects_html = "".join(
        f"<div class='resume-entry'><div class='entry-title'><strong>{_display_value(item.get('title', ''))}</strong></div>"
        f"<p>{_display_value(item.get('description', ''))}</p></div>"
        for item in projects if isinstance(item, dict)
    )
    add_section("Projects", projects_html)

    html.append("</div>")
    return "".join(html)


def display_resume(data, label):
    st.markdown(
        """
        <style>
        .resume-paper { background: #ffffff; border: 1px solid #d9e1e5; padding: 28px 30px; color: #20252b; min-height: 620px; }
        .resume-header { border-bottom: 1px solid #0b9a9a; padding-bottom: 15px; margin-bottom: 18px; }
        .resume-name { color: #078c95; font: 700 25px Georgia, serif; }
        .resume-headline { color: #333; font: 15px Georgia, serif; text-align: right; margin-top: -24px; }
        .resume-contact { color: #555; font: 11px Arial, sans-serif; margin-top: 18px; }
        .resume-section { margin: 17px 0; }
        .resume-section h3 { color: #078c95; border-bottom: 1px solid #b7d7d8; font: 700 14px Georgia, serif; margin: 0 0 9px; padding-bottom: 3px; text-transform: uppercase; }
        .resume-section p, .resume-section li { font: 11px/1.45 Arial, sans-serif; margin: 4px 0; }
        .resume-entry { margin: 0 0 12px; }
        .entry-title { display: flex; justify-content: space-between; gap: 12px; font: 12px/1.3 Arial, sans-serif; }
        .entry-title span { color: #333; text-align: right; }
        .entry-meta { color: #777; font: italic 10px Arial, sans-serif; margin: 3px 0 5px; }
        .resume-section ul { margin: 4px 0 0 17px; padding: 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"**{label}**", unsafe_allow_html=False)
    st.markdown(_resume_html(data), unsafe_allow_html=True)
def main():
    st.title(":page_facing_up: Resume Parser and Reviewer")
    #st.sidebar.image("src/images/banner.png")
    st.sidebar.markdown("""
        :brain: ResumeAI is an advanced tool that leverages the power of Large Language Models (LLMs) to analyze and improve resumes.
    """)

    with st.sidebar:
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
        job_description = st.text_area("Enter job description (optional)").strip()

        if st.button("Run Analysis", use_container_width=True):
            if uploaded_file is not None:
                resume_text = extract_text_from_pdf(uploaded_file)
                with st.spinner("Parsing resume... [Step 1 of 2]"):
                    resume_yaml = parse_resume(resume_text)
                with st.spinner("Reviewing resume... [Step 2 of 2]"):
                    review_response = review_resume(resume_yaml, job_description)

                resume_data = yaml.safe_load(resume_yaml)
                review_data = yaml.safe_load(review_response)

                st.session_state.resume_data = resume_data
                st.session_state.review_data = review_data
                st.session_state.current_section = 0
                st.session_state.sections = list(resume_data.keys())

    if 'resume_data' in st.session_state and 'review_data' in st.session_state:
        display_analysis()
    else:
        st.info("Please upload a resume and run the analysis to view results.")

def display_analysis():
    col1, col2, col3 = st.columns([3, 1, 3])
    with col1:
        if st.button("⬅️", use_container_width=True) and st.session_state.current_section > 0:
            st.session_state.current_section -= 1
    with col2:
        page_number = f"{st.session_state.current_section + 1}/{len(st.session_state.sections)}"
        st.button(f"**{page_number}**", use_container_width=True)
    with col3:
        if st.button("➡️", use_container_width=True) and st.session_state.current_section < len(st.session_state.sections) - 1:
            st.session_state.current_section += 1

    current_section = st.session_state.sections[st.session_state.current_section]

    col1, col2 = st.columns(2)
    with col1:
        original_data = dict(st.session_state.resume_data)
        original_data = {
            "personal_info": original_data.get("personal_info", {}),
            current_section: original_data.get(current_section),
        }
        display_resume(original_data, "Original")
    with col2:
        revised_data = merge_revised_resume(
            st.session_state.resume_data,
            st.session_state.review_data,
        )
        revised_data = {
            "personal_info": revised_data.get("personal_info", {}),
            current_section: revised_data.get(current_section),
        }
        display_resume(revised_data, "Revised")

    revision_suggestion_placeholder = st.empty()
    current_section_data = st.session_state.review_data[current_section]
    impact_level = current_section_data["impact_level"]
    revision_suggestion = current_section_data["revision_suggestion"]

    with revision_suggestion_placeholder.expander("Revision Suggestions", expanded=True):
        if impact_level == "Low":
            st.info(f"Impact Level: {impact_level}")
        elif impact_level == "Medium":
            st.warning(f"Impact Level: {impact_level}")
        elif impact_level == "High":
            st.error(f"Impact Level: {impact_level}")

        for suggestion in revision_suggestion:
            st.markdown(f"- {suggestion}")

def download_resume():
    if 'resume_data' not in st.session_state:
        return
    if 'review_data' not in st.session_state:
        return
    
    revised_resume_data = merge_revised_resume(st.session_state.resume_data, st.session_state.review_data)
    pdf_content = generate_resume_pdf(revised_resume_data)
    st.download_button(
         label="Download Revised Resume (PDF)",
         data=pdf_content,
         file_name="revised_resume.pdf",
         mime="application/pdf"
     )

if 'resume_data' in st.session_state and 'review_data' in st.session_state: 
    download_resume()

if __name__ == "__main__":
    main()
