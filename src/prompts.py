RESUME_YAML_SCHEMA = """
personal_info:
  full_name: string
  address:
    street: string
    city: string
    state: string
    zip: string
    country: string
  phone: string
  email: string
  linkedin: string
  github: string
  website: string
summary: string
work_experience:
  - job_title: string
    company: string
    location:
      city: string
      state: string
    start_date: date
    end_date: date
    description: string
    achievements:
      - string
education:
  - degree: string
    field_of_study: string
    institution: string
    location:
      city: string
      state: string
    start_date: date
    end_date: date
    honors:
      - string
skills:
  - string
certifications:
  - title: string
    issuer: string
    date_obtained: date
    expiration_date: date
projects:
  - title: string
    description: string
    technologies:
      - string
    url: string
languages:
  - language: string
    proficiency: string
volunteer_experience:
  - role: string
    organization: string
    location:
      city: string
      state: string
    start_date: date
    end_date: date
    description: string
interests:
  - string
references:
  - name: string
    relationship: string
    contact_info:
      phone: string
      email: string
"""

LLM_YAML_PARSE_PROMPT = """
**Task:** You are a powerful resume parser. Your job is to extract and structure information from a given resume into a predefined YAML schema. The schema is provided below, and you should ensure that the extracted data adheres to the specified field names in snake_case format.

**YAML Schema:** {resume_schema}

**Input:** {resume_text}

**Instructions:**

1. Read the resume text carefully.
2. Identify and extract relevant information corresponding to each field in the provided YAML schema.
3. Fill in the schema with the extracted information, ensuring to convert all field names to snake_case.
4. Format the output as a valid YAML document that matches the schema.
5. Make sure to add double quotes around the values that are strings. This is important for the YAML parser.

**Note:** Ensure that the output is a well-formed YAML document and all dates are in the format `YYYY-MM-DD`. For any section that is not present in the resume, output it as an empty list `[]` (for example `skills: []`). Do NOT invent placeholder or empty entries such as `[null]`, `[]` entries containing `null`, or mappings whose fields are all `null`.
"""

YAML_REPAIR_PROMPT = """
Your previous output was not valid YAML.

**Parser Error:**
{error}

**Invalid YAML:**
{invalid_yaml}

**Task:** Fix the YAML so it parses correctly. Do NOT change the meaning of the data. Return ONLY the corrected YAML document inside a ```yaml code block```, without any additional text.
"""

REVIEW_OUTPUT_SCHEMA = """
section_name_1:
  impact_level: string
  revised_content: string | list | dict
  revision_suggestion: list[string]
section_name_2:
  impact_level: string
  revised_content: string | list | dict
  revision_suggestion: list[string]
...
"""

RESUME_REVIEW_PROMPT = """
**Task:** You are an expert resume reviewer. Your job is to analyze the provided resume data in YAML format and suggest improvements for each section. For each suggestion, you should provide an impact score (Low, Medium, High) and the revised version.

**YAML Input Data:** {resume_data}

**Instructions:**

1. Read the provided YAML resume data carefully.
2. For each section, evaluate the content and suggest improvements.
3. For each suggestion, include:
   - An impact score (Low, Medium, High).
   - The revised version of the text.
   - Suggestion on how to improve the section.

**YAML Output Schema:**

```yaml
{review_output_schema}
```

**Output Requirement:**

- Please provide the output strictly in the above YAML format, without any additional explanations or text.
- Make sure to add double quotes around the values that are strings. This is important for the YAML parser.
- The output must be a single mapping: each top-level key is a section name, and its value is a mapping with exactly the keys `impact_level`, `revised_content`, and `revision_suggestion`.
- For sections whose content is a list (for example `skills` or `interests`), do NOT put plain list items directly under the section name. Instead keep the three keys at the section level and place the revised list under `revised_content`, like this:

```yaml
skills:
  impact_level: Medium
  revised_content:
    - "Python"
    - "FastAPI"
  revision_suggestion:
    - "Add more technical skills"
```
"""

JOB_TITLES_PROMPT = """
**Task:** Extract up to {max_titles} job titles from the resume text below. Base titles on the candidate's work experience, roles, and summary. Return ONLY a valid YAML list of strings, for example:

```yaml
- "Data Engineer"
- "Machine Learning Engineer"
```

Do NOT invent roles that are not in the resume. If no job titles are found, return an empty list.

**Resume text:**
{resume_text}
"""

JOB_DESCRIPTION_REVIEW_PROMPT = """
**Task:** You are an expert resume reviewer. Your job is to analyze the provided resume data in YAML format against the provided job description. Suggest improvements for each section of the resume to better align with the job description. For each suggestion, you should provide an impact score (Low, Medium, High), the revised version of the text, and a list of suggestions on how to improve the section.

**YAML Input Data:** {resume_data}

**Job Description:** {job_description}

**Instructions:**

1. Read the provided YAML resume data and the job description carefully.
2. For each section of the resume, evaluate the content in the context of the job description and suggest improvements.
3. For each suggestion, include:
   - An impact score (Low, Medium, High).
   - The revised version of the text.
   - A list of suggestions on how to improve the section.

4. For the `skills` section, identify the technical skills required by the job description that are currently missing from the resume and include them inside the `revised_content` list, alongside the existing skills. Do not drop any existing skill.

**YAML Output Schema:**

```yaml
{review_output_schema}
```

**Output Requirement:**

- Please provide the output strictly in the above YAML format, without any additional explanations or text.
- Make sure to add double quotes around the values that are strings. This is important for the YAML parser.
- The output must be a single mapping: each top-level key is a section name, and its value is a mapping with exactly the keys `impact_level`, `revised_content`, and `revision_suggestion`.
- For sections whose content is a list (for example `skills` or `interests`), do NOT put plain list items directly under the section name. Instead keep the three keys at the section level and place the revised list under `revised_content`, like this:

```yaml
skills:
  impact_level: Medium
  revised_content:
    - "Python"
    - "FastAPI"
  revision_suggestion:
    - "Add more technical skills"
```
"""
