#!/usr/bin/env python3
"""
Playwright script to open a browser, search for cricbuzz.com,
navigate to the site, open the Series -> Indian Premier League 2026
page and then click the "Table" menu.

Usage:
  pip install playwright
  playwright install
  python playwright_cricbuzz.py
"""
try:
    from playwright.sync_api import sync_playwright
except Exception:
    import sys
    sys.stderr.write(
        "Missing dependency: playwright.\nInstall with: pip install playwright\nThen run: playwright install\n"
    )
    sys.exit(1)
import time

def main(headless=False):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()

        # 1) Open a search engine and search for cricbuzz.com
        page.goto("https://www.bing.com", timeout=60000)
        page.fill('input[name="q"]', 'cricbuzz.com')
        page.keyboard.press('Enter')

        # 2) Click the first result that points to cricbuzz
        page.wait_for_selector('a[href^="https://www.cricbuzz.com"]', timeout=15000)
        page.click('a[href^="https://www.cricbuzz.com"]')
        page.wait_for_load_state('networkidle')

        # 3) Open the "Series" menu (try text match) and click IPL 2026
        try:
            page.wait_for_selector('text=Series', timeout=8000)
            page.click('text=Series')
        except Exception:
            # best-effort alternative if the exact text isn't present
            try:
                page.locator('a:has-text("Series")').first.click()
            except Exception:
                pass

        # Try a few patterns to find the IPL 2026 link
        ipl_selector = 'text=/Indian Premier League.*2026|IPL 2026|Indian Premier League 2026/'
        try:
            page.wait_for_selector(ipl_selector, timeout=8000)
            page.click(ipl_selector)
        except Exception:
            # fallback: click any link that contains 'IPL' and '2026' in its text
            links = page.locator('a:has-text("IPL"), a:has-text("Indian Premier League")')
            try:
                count = links.count()
            except Exception:
                count = 0
            clicked = False
            for i in range(count):
                try:
                    txt = links.nth(i).inner_text()
                    if '2026' in txt or 'IPL 2026' in txt:
                        links.nth(i).click()
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                # as a last resort, try any link with 'IPL'
                try:
                    page.click('text=IPL')
                except Exception:
                    pass

        page.wait_for_load_state('networkidle')

        # 4) On the landed page, find and click the "Table" menu/tab
        try:
            page.wait_for_selector('text=Table', timeout=10000)
            page.click('text=Table')
            page.wait_for_load_state('networkidle')
        except Exception:
            # alternative locator
            try:
                page.locator('a:has-text("Table")').first.click()
                page.wait_for_load_state('networkidle')
            except Exception:
                pass

        print('Final URL:', page.url)
        time.sleep(2)
        browser.close()


if __name__ == '__main__':
    main(headless=False)
