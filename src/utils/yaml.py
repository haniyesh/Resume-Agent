import re


def _sanitize_yaml_aliases(content: str) -> str:
    """Convert YAML anchors/aliases emitted by LLMs into valid plain keys.

    Example:
      - *job1:
          title: Senior Engineer
    becomes:
      - job1:
          title: Senior Engineer
    """
    cleaned = re.sub(r"(?m)^(\s*[-?]\s*)[*&]([A-Za-z0-9_-]+)\s*:\s*(.*)$", r"\1\2: \3", content)
    cleaned = re.sub(r"(?m)^(\s*)[*&]([A-Za-z0-9_-]+)\s*:\s*(.*)$", r"\1\2: \3", cleaned)
    cleaned = re.sub(r"(?m)^\s*[*&][A-Za-z0-9_-]+\s*$", "", cleaned)
    return cleaned


def extract_yaml(content):
    pattern = r'```yaml\s*(.*?)\s*```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    else:
        cleaned = content.strip()

    return _sanitize_yaml_aliases(cleaned)
