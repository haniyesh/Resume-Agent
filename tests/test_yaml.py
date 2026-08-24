import yaml

from src.resume_formatter import format_resume
from src.utils.yaml import extract_yaml


def test_extract_yaml_removes_undefined_aliases():
    content = '''
```yaml
experience:
  - company: Acme
    jobs:
      - *job1:
          title: Senior Engineer
          years: 2022-2024
```
'''

    cleaned = extract_yaml(content)
    loaded = yaml.safe_load(cleaned)

    assert loaded["experience"][0]["jobs"][0]["title"] == "Senior Engineer"


def test_format_resume_handles_string_personal_info():
    content = {"personal_info": "Jane Doe"}

    rendered = format_resume(content)

    assert "Jane Doe" in rendered
