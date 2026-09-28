import json
from pathlib import Path
from playwright.sync_api import sync_playwright
# from agents.tailoring.llm_rewriter import tailor_resume

DEFAULT_JSON_FILE = Path(__file__).resolve().parents[2] / "data" / "phd_positions.json"
DATA_DIR = DEFAULT_JSON_FILE.parent


def _read_local_job(file_path: str) -> str:
    path = Path(file_path)
    if not path.is_absolute():
        path = DATA_DIR / path

    return path.read_text(encoding="utf-8")


def _extract_page_text(page, url: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Beautiful Soup is required for URL scraping. Install it with: "
            "python -m pip install beautifulsoup4"
        ) from exc

    page.goto(url, timeout=60000)
    soup = BeautifulSoup(page.content(), "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def extract_and_analyze_phds(json_file: str | Path = DEFAULT_JSON_FILE):
    with open(json_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not jobs:
        print(f"No PhD positions found in {json_file}. Add job entries with a url or file_path to begin.")
        return

    browser = None
    page = None
    playwright = None

    try:
        for job in jobs[:3]:
            print("Processing job...")

            if "file_path" in job:
                full_description = _read_local_job(job["file_path"])
            elif "url" in job:
                if page is None:
                    playwright = sync_playwright().start()
                    browser = playwright.chromium.launch(headless=True)
                    page = browser.new_page()
                full_description = _extract_page_text(page, job["url"])
            else:
                print("Skipping job because it has no url or file_path.")
                continue

            print(f"Extracted text length: {len(full_description)} characters")
    finally:
        if browser is not None:
            browser.close()
        if playwright is not None:
            playwright.stop()


if __name__ == "__main__":
    extract_and_analyze_phds()
