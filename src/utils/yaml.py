import re

import yaml


def _repair_block_end_error(content, error):
    """Fix a mapping key mis-indented at the same level as a block sequence.

    LLMs commonly emit a sequence indented under a key and then continue with
    the next mapping key at the *same* indentation as the sequence items::

        work_experience:
          - job_title: "Engineer"
          skills: []

    PyYAML reads ``skills`` as part of the sequence and fails with
    ``expected <block end>, but found '?'``. Re-indent the offending key and
    its block back to the parent mapping's indentation.
    """
    problem = getattr(error, "problem_mark", None)
    context = getattr(error, "context_mark", None)
    if problem is None or context is None:
        return content
    if "expected <block end>" not in (getattr(error, "problem", "") or ""):
        return content
    if problem.column != context.column:
        return content

    lines = content.split("\n")
    key_line = problem.line
    if key_line is None or key_line >= len(lines):
        return content
    key_indent = len(lines[key_line]) - len(lines[key_line].lstrip())

    parent_indent = 0
    for i in range(context.line - 1, -1, -1):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(lines[i]) - len(lines[i].lstrip())
        if indent < context.column:
            parent_indent = indent
            break

    shift = key_indent - parent_indent
    if shift <= 0:
        return content

    for i in range(key_line, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        if (len(line) - len(line.lstrip())) < key_indent:
            break
        lines[i] = line[shift:]

    return "\n".join(lines)


def repair_yaml(content, max_passes=10):
    """Apply deterministic repairs until the YAML parses.

    Returns the repaired YAML text, or ``None`` when the document cannot be
    fixed deterministically (the caller can then fall back to the LLM).
    """
    for _ in range(max_passes):
        try:
            yaml.safe_load(content)
            return content
        except yaml.YAMLError as exc:
            fixed = _repair_block_end_error(content, exc)
            if fixed == content:
                return None
            content = fixed
    return None


def _sanitize_yaml_aliases(content: str) -> str:
    """Convert YAML anchors/aliases emitted by LLMs into valid plain keys.

    Example:
      - *job1:
          title: Senior Engineer
    becomes:
      - job1:
          title: Senior Engineer
    """
    cleaned = re.sub(r"(?m)^(\s*[-?]\s*)[*&]([A-Za-z0-9_-]+)\s*:[ \t]*(.*)$", r"\1\2: \3", content)
    cleaned = re.sub(r"(?m)^(\s*)[*&]([A-Za-z0-9_-]+)\s*:[ \t]*(.*)$", r"\1\2: \3", cleaned)
    cleaned = re.sub(r"(?m)^\s*[*&][A-Za-z0-9_-]+\s*$", "", cleaned)
    return cleaned


def extract_yaml(content):
    pattern = r'```(?:yaml|yml)?\s*(.*?)\s*```'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    else:
        cleaned = content.strip()

    return _sanitize_yaml_aliases(cleaned)
