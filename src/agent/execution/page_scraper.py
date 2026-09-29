import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# دقت کنید: اینجا آدرس فایل را به صورت رشته متنی می‌دهیم، نه یک لیست!
def extract_and_analyze_phds(json_file_path: str = "data/phd_positions.json"):
    
    # 1. لود کردن لیست پروژه‌ها از فایل
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except FileNotFoundError:
        print(f"❌ فایل {json_file_path} پیدا نشد!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for job in jobs[:3]:
            print(f"🔄 In processing jobs: {job.get('url', 'بدون لینک')} ...")
            
            # بقیه کدهای Playwright...
            
        browser.close()

if __name__ =="__main__":
    extract_and_analyze_phds()