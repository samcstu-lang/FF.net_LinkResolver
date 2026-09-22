import sys
from pathlib import Path
import time
import re
import ctypes

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / "input.txt"
OUTPUT_FILE = SCRIPT_DIR / "output.txt"
TIMEOUT = 25  # seconds
MAX_RETRIES = 2


def hide_window(driver):
    """Hide/minimize Chrome window using Windows ctypes API."""
    try:
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
        GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
        ShowWindow = ctypes.windll.user32.ShowWindow

        driver_pid = driver.service.process.pid

        def enum_windows_callback(hwnd, extra):
            pid = ctypes.c_ulong()
            GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == driver_pid:
                # SW_MINIMIZE = 6, SW_HIDE = 0, SW_FORCEMINIMIZE = 11
                ShowWindow(hwnd, 6)
            return True

        EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
    except Exception:
        pass


def create_driver():
    """Create an undetected Chrome WebDriver instance placed off-screen and minimized."""
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Position window completely off-screen (invisible to user)
    options.add_argument("--window-position=-3000,-3000")
    options.add_argument("--window-size=1280,720")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
    })

    driver = uc.Chrome(options=options, version_main=None)
    hide_window(driver)
    return driver


def resolve_single_link(driver, link):
    """
    Resolve link by extracting the download path and executing the
    internal HX-Request fetch directly in the browser.
    No ads clicked, no clipboard needed.
    """
    try:
        driver.get(link)

        # Wait for page to finish loading
        wait = WebDriverWait(driver, TIMEOUT)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)

        # Find the onclick attribute with the gateway path
        onclick = driver.execute_script('''
            const a = Array.from(document.querySelectorAll("a")).find(el => el.textContent.includes("Copy download link"));
            return a ? a.getAttribute("onclick") : null;
        ''')

        if not onclick:
            # Fallback wait for element
            copy_link = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//a[contains(text(), 'Copy download link')]"
                ))
            )
            onclick = copy_link.get_attribute("onclick")

        if not onclick:
            return None

        match = re.search(r"copyDownloadLink\('([^']+)'\)", onclick)
        if not match:
            return None

        download_path = match.group(1).replace(r"\/", "/")

        # Execute the htmx fetch directly in browser context to get the HX-Redirect header
        direct_url = driver.execute_async_script('''
            const path = arguments[0];
            const callback = arguments[arguments.length - 1];
            fetch(path, {headers: {"HX-Request": "true"}})
                .then(r => {
                    const url = r.headers.get("HX-Redirect");
                    callback(url || null);
                })
                .catch(err => callback(null));
        ''', download_path)

        if direct_url and "ts.fuckingfast.net" in direct_url:
            return direct_url

        return None

    except Exception:
        return None


def resolve_link_with_retries(driver, link):
    """Resolve a link with retry logic."""
    for attempt in range(MAX_RETRIES + 1):
        url = resolve_single_link(driver, link)
        if url:
            return link, url
        if attempt < MAX_RETRIES:
            time.sleep(1.5)
    return link, f"Failed: {link}"


def main():
    """Main execution - single off-screen Chrome window, fast direct fetch."""
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found")
        sys.exit(1)

    links = [line.strip() for line in INPUT_FILE.read_text().splitlines() if line.strip()]

    if not links:
        print(f"ERROR: No links found in {INPUT_FILE}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"FFDownloader - Fast Direct API Resolution")
    print(f"{'='*80}")
    print(f"Total links: {len(links)}")
    print(f"Mode: Background / Off-screen (No Ads, No Clipboard)")
    print(f"{'='*80}\n")

    start_time = time.time()
    driver = None

    try:
        driver = create_driver()
        results = {}

        for idx, link in enumerate(links, 1):
            file_id = link.split('/')[-1]
            original_link, resolved = resolve_link_with_retries(driver, link)
            results[original_link] = resolved

            is_success = not resolved.startswith("Failed:")
            status = "[OK]" if is_success else "[FAIL]"
            print(f"{status} [{idx:2d}/{len(links)}] {file_id}")

        elapsed_time = time.time() - start_time

        # Write results to output file
        with open(OUTPUT_FILE, "w") as f:
            for link in links:
                f.write(results[link] + "\n")

        successful = sum(1 for r in results.values() if not r.startswith("Failed:"))
        failed = len(results) - successful

        print(f"\n{'='*80}")
        print(f"[OK] Successful: {successful}/{len(links)}")
        print(f"[FAIL] Failed:     {failed}/{len(links)}")
        print(f"[TIME] Total Time: {elapsed_time:.1f}s ({elapsed_time/len(links):.1f}s per link)")
        print(f"[OUTPUT] Written to: {OUTPUT_FILE}")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
