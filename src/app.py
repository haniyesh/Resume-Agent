import streamlit as st
import requests
import yaml
from html import escape
from utils.resume_pdf import generate_resume_pdf, merge_revised_resume, _has_content
from utils.search_jobs import search_jobs as adzuna_search_jobs
from agent import extract_job_titles_from_resume

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
    add_section("Highlights", f"<p>{_display_value(summary)}</p>" if _has_content(summary) else "")

    experience_html = []
    for job in data.get("work_experience") or []:
        if not isinstance(job, dict) or not _has_content(job):
            continue
        title = _display_value(job.get("job_title", ""))
        company = _display_value(job.get("company", ""))
        location = _display_location(job.get("location"))
        metadata = " | ".join(part for part in (location, _display_dates(job)) if part)
        achievements = [
            f"<li>{_display_value(item)}</li>"
            for item in (job.get("achievements") or []) if _has_content(item)
        ]
        experience_html.append(
            f"<div class='resume-entry'><div class='entry-title'><strong>{title}</strong>"
            f"<span>{company}</span></div>"
            f"<div class='entry-meta'>{metadata}</div>"
            f"<p>{_display_value(job.get('description', ''))}</p>"
            f"<ul>{''.join(achievements)}</ul></div>"
        )
    add_section("Work Experience", "".join(experience_html))

    education_html = []
    for item in data.get("education") or []:
        if not isinstance(item, dict) or not _has_content(item):
            continue
        degree = " ".join(
            part for part in (item.get("degree"), item.get("field_of_study")) if part
        )
        metadata = " | ".join(
            part for part in (_display_location(item.get("location")), _display_dates(item)) if part
        )
        honors = "".join(
            f"<li>{_display_value(honor)}</li>"
            for honor in (item.get("honors") or []) if _has_content(honor)
        )
        education_html.append(
            f"<div class='resume-entry'><div class='entry-title'><strong>{_display_value(degree)}</strong>"
            f"<span>{_display_value(item.get('institution', ''))}</span></div>"
            f"<div class='entry-meta'>{metadata}</div><ul>{honors}</ul></div>"
        )
    add_section("Education", "".join(education_html))

    skills = [skill for skill in (data.get("skills") or []) if _has_content(skill)]
    add_section("Skills", f"<p>{_display_value(', '.join(str(skill) for skill in skills))}</p>" if skills else "")

    certifications = data.get("certifications") or []
    certificates_html = "".join(
        f"<li><strong>{_display_value(item.get('title', ''))}</strong>"
        f" | {_display_value(item.get('issuer', ''))}</li>"
        for item in certifications if isinstance(item, dict) and _has_content(item)
    )
    add_section("Certifications", f"<ul>{certificates_html}</ul>" if certificates_html else "")

    projects = data.get("projects") or []
    projects_html = "".join(
        f"<div class='resume-entry'><div class='entry-title'><strong>{_display_value(item.get('title', ''))}</strong></div>"
        f"<p>{_display_value(item.get('description', ''))}</p></div>"
        for item in projects if isinstance(item, dict) and _has_content(item)
    )
    add_section("Projects", projects_html)

    languages = [
        item for item in (data.get("languages") or [])
        if isinstance(item, dict) and _has_content(item.get("language"))
    ]
    languages_html = "".join(
        f"<li><strong>{_display_value(item.get('language', ''))}</strong>"
        + (f" | {_display_value(item.get('proficiency', ''))}" if _has_content(item.get("proficiency")) else "")
        + "</li>"
        for item in languages
    )
    add_section("Languages", f"<ul>{languages_html}</ul>" if languages_html else "")

    volunteer_html = []
    for item in data.get("volunteer_experience") or []:
        if not isinstance(item, dict) or not _has_content(item):
            continue
        metadata = " | ".join(
            part for part in (_display_location(item.get("location")), _display_dates(item)) if part
        )
        volunteer_html.append(
            f"<div class='resume-entry'><div class='entry-title'><strong>{_display_value(item.get('role', ''))}</strong>"
            f"<span>{_display_value(item.get('organization', ''))}</span></div>"
            f"<div class='entry-meta'>{metadata}</div>"
            f"<p>{_display_value(item.get('description', ''))}</p></div>"
        )
    add_section("Volunteer Experience", "".join(volunteer_html))

    interests = [x for x in (data.get("interests") or []) if _has_content(x)]
    add_section(
        "Interests",
        f"<p>{_display_value(', '.join(str(x) for x in interests))}</p>" if interests else ""
    )

    references_html = "".join(
        f"<li><strong>{_display_value(item.get('name', ''))}</strong>"
        f" | {_display_value(item.get('relationship', ''))}"
        + (f" | {_display_value(item.get('contact_info', {}).get('email', ''))}"
           if isinstance(item.get("contact_info"), dict) and _has_content(item["contact_info"].get("email"))
           else "")
        + "</li>"
        for item in data.get("references") or [] if isinstance(item, dict) and _has_content(item)
    )
    add_section("References", f"<ul>{references_html}</ul>" if references_html else "")

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
        job_location = st.text_input("Job location (optional)")

    if uploaded_file is not None:
        with st.spinner("Extracting job titles from your resume..."):
            try:
                titles = extract_job_titles_from_resume(uploaded_file.read())
            except (ValueError, yaml.YAMLError, requests.RequestException) as exc:
                st.error(f"Failed to extract job titles: {exc}")
                titles = []
        st.session_state.job_titles = list(dict.fromkeys(titles))
        st.session_state.selected_titles = []

    if st.session_state.get("job_titles"):
        st.subheader(":mag: Search Adzuna by role")
        titles = st.session_state.job_titles

        saved = [t for t in st.session_state.get("selected_titles", []) if t in titles]
        if saved != st.session_state.get("selected_titles", []):
            st.session_state.selected_titles = saved

        selected_titles = st.multiselect(
            "Choose one or more job titles from your resume:",
            titles,
            key="selected_titles",
        )
        if st.button("Search Adzuna", use_container_width=True):
            if not selected_titles:
                st.warning("Select at least one job title to search.")
            else:
                with st.spinner(f"Searching for {', '.join(selected_titles)}..."):
                    all_jobs = []
                    total_count = 0
                    failed = []
                    for title in selected_titles:
                        try:
                            result = adzuna_search_jobs(
                                title,
                                location=job_location.strip() or None,
                            )
                        except (ValueError, requests.RequestException) as exc:
                            failed.append((title, exc))
                        else:
                            all_jobs.extend(result["results"])
                            total_count += result["count"] or 0
                    for title, exc in failed:
                        st.error(f"Search failed for '{title}': {exc}")
                    st.session_state.jobs = all_jobs
                    st.session_state.job_count = total_count
        display_jobs()

        st.divider()
        st.markdown("**Edit job titles**")

        new_title = st.text_input("Add a job title")
        if st.button("Add", use_container_width=True) and new_title.strip():
            if new_title.strip() not in titles:
                st.session_state.job_titles = [*titles, new_title.strip()]
                st.rerun()
            else:
                st.warning(f"'{new_title.strip()}' is already in the list.")

        for title in list(titles):
            if st.button(f"Remove  {title}", key=f"remove_{title}", use_container_width=True):
                st.session_state.job_titles = [t for t in titles if t != title]
                st.rerun()
    else:
        st.info("Upload a resume to extract job titles and search open roles.")

def display_jobs():
    jobs = st.session_state.get("jobs") or []
    if not jobs:
        return
    count = st.session_state.get("job_count")
    title = f":mag: Found {count or len(jobs)} jobs on Adzuna"
    if count:
        title += f" (showing {len(jobs)})"
    st.markdown(f"##### {title}")
    with st.container():
        for job in jobs:
            salary = ""
            if job.get("salary_min") or job.get("salary_max"):
                salary = f" | {job.get('currency', '')} {job.get('salary_min', '') or ''}-{job.get('salary_max', '') or ''}"
                if job.get("salary_is_estimated"):
                    salary += " (est.)"
            st.markdown(
                f"**{escape(job.get('title', ''))}** — {escape(job.get('company', ''))}"
                + (f"\n\n{escape(job.get('location', ''))}{salary}" if job.get("location") or salary else "")
            )
            if job.get("description"):
                with st.expander("Description", expanded=False):
                    st.markdown(job["description"][:2000], unsafe_allow_html=False)
            if job.get("url"):
                st.markdown(f"[View listing]({job['url']})")

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
