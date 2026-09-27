"""Log in to LinkedIn once and reuse the saved browser session afterwards.

The first run opens a real browser window on the LinkedIn login page; finish the
login by hand (email, password, 2FA, CAPTCHA), and the script notices you are in
and stores the cookies for later runs. Later runs load the saved session and go
straight to the feed, which avoids the login form and its bot checks.

Run as a script:
    python browser_bot.py                  # log in (first run) and save the session
    python browser_bot.py --check          # is the saved session still valid?
    python browser_bot.py --fresh          # discard the session and log in again
    python browser_bot.py --timeout 300    # longer window to type your password

Or as a module from the project root:
    python -m src.agent.execution.browser_bot --check
"""

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).resolve().parents[2] / "data" / "linkedin_session.json"
LOGIN_URL = "https://www.linkedin.com/login"
FEED_URL = "https://www.linkedin.com/feed/"
DEFAULT_TIMEOUT = 180
BROWSER_TIMEOUT = 30


def log(message):
    """Print a progress line and flush, so output shows up while running."""
    print(message, flush=True)


LOGIN_MARKERS = "input#session_key, form#loginform, a[href*='/login'], a[href*='/signup']"
SIGNED_IN_MARKERS = (
    ".global-nav, #global-nav, [data-globalnav], a.global-nav__link, "
    "a[href*='/in/'][class*='global-nav'], button[aria-label*='Search']"
)
CONFIRM_CHECKS = 2


def session_path(value):
    """Return a usable session file path, or None when there is nothing to load."""
    path = Path(value)
    if not path.exists():
        return None
    if not path.stat().st_size:
        log(f"Ignoring empty session file {path}")
        return None
    return path


def is_signed_in(page):
    """True only when the login form is gone and signed-in navigation is present.

    A URL check is not enough: LinkedIn redirects anonymous visitors to paths
    like `/` or `/feed/`, which would otherwise look signed in and make the
    script close the browser the moment it opens.
    """
    if any(part in page.url for part in ("/login", "/signin", "/checkpoint")):
        return False
    if page.locator(LOGIN_MARKERS).count() > 0:
        return False
    return page.locator(SIGNED_IN_MARKERS).count() > 0


def wait_for_login(page, timeout):
    """Poll until LinkedIn shows signed-in navigation, or the timeout expires."""
    log(f"Finish the login in the browser window ({timeout}s to do it).")
    deadline = time.monotonic() + timeout
    confirmed = 0
    last_report = 0.0
    while time.monotonic() < deadline:
        if page.is_closed():
            log("Browser window was closed, cancelling.")
            return False
        if is_signed_in(page):
            confirmed += 1
            if confirmed >= CONFIRM_CHECKS:
                return True
        else:
            confirmed = 0
        if time.monotonic() - last_report >= 15:
            last_report = time.monotonic()
            log(f"Still waiting for the login... ({page.url})")
        page.wait_for_timeout(1000)
    return False


def launch_browser(playwright, headless):
    """Start Chromium, making the window visible and maximized when headed."""
    log(f"Launching Chromium ({'headless' if headless else 'headed'})...")
    return playwright.chromium.launch(
        headless=headless,
        args=[] if headless else ["--start-maximized", "--window-position=0,0"],
    )


def check_saved_session(path, headless):
    """Return True when the saved session still opens the feed without a login."""
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headless)
        try:
            context = browser.new_context(storage_state=str(path))
            page = context.new_page()
            page.goto(
                FEED_URL, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000
            )
            return is_signed_in(page)
        finally:
            browser.close()


def login_and_save_session(session_file, url, timeout, headless):
    """Open LinkedIn, wait for the manual login, and save the resulting session."""
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headless)
        try:
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000)
            if not wait_for_login(page, timeout):
                log("Login did not complete in time. Nothing was saved.")
                return 1
            log("Login detected. Confirming on the feed page...")
            page.goto(FEED_URL, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000)
            if not is_signed_in(page):
                log(f"Login did not hold on {FEED_URL}, nothing was saved.")
                return 1
            session_file.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(session_file))
        finally:
            browser.close()

    log(f"Session saved to {session_file}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Log in to LinkedIn and save the browser session for reuse."
    )
    parser.add_argument(
        "--session",
        default=str(SESSION_FILE),
        help=f"Session file to use (default: {SESSION_FILE})",
    )
    parser.add_argument(
        "--url", default=LOGIN_URL, help=f"Login page to open (default: {LOGIN_URL})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait for the login to finish (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check whether the saved session is still valid",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore the saved session and log in again",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser headless; a manual login is not possible",
    )
    args = parser.parse_args()

    session_file = None if args.fresh else session_path(args.session)

    if args.headless and session_file is None:
        log("Error: --headless needs an existing session; log in once first.")
        return 1

    try:
        if args.check:
            if session_file is None:
                log(f"No saved session at {args.session}. Run once without --check.")
                return 1
            valid = check_saved_session(session_file, args.headless)
            log(
                f"Session at {session_file} is "
                f"{'still valid' if valid else 'expired; log in again'}."
            )
            return 0 if valid else 1

        if session_file is not None:
            log(f"Found a saved session at {session_file}, checking it...")
            if check_saved_session(session_file, args.headless):
                log("Session is still valid, no login needed.")
                return 0
            log("Session expired, falling back to a new login.")

        return login_and_save_session(
            Path(args.session), args.url, args.timeout, args.headless
        )
    except PlaywrightTimeoutError as exc:
        log(f"Error: the page did not load in time ({exc})")
        return 1
    except PlaywrightError as exc:
        log(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
