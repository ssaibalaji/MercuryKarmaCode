#!/usr/bin/env python3
"""
Flask API for Playwright automation:
- Opens Cricbuzz
- Navigates to IPL 2026
- Clicks the Table tab
- Returns final URL

Setup:
    pip install flask playwright
    playwright install

Run:
    python app.py

API:
    GET http://localhost:5000/run-cricbuzz
"""

from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import traceback

app = Flask(__name__)


def run_cricbuzz(headless=True):
    result = {
        "success": False,
        "final_url": None,
        "message": "",
    }

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)

            page = browser.new_page()

            # 1) Open Bing and search for Cricbuzz
            page.goto("https://www.bing.com", timeout=60000)

            page.fill('input[name="q"]', 'cricbuzz.com')
            page.keyboard.press('Enter')

            # 2) Click Cricbuzz result
            page.wait_for_selector(
                'a[href^="https://www.cricbuzz.com"]',
                timeout=15000
            )

            page.click('a[href^="https://www.cricbuzz.com"]')

            page.wait_for_load_state("networkidle")

            # 3) Open Series menu
            try:
                page.wait_for_selector('text=Series', timeout=8000)
                page.click('text=Series')

            except Exception:
                try:
                    page.locator(
                        'a:has-text("Series")'
                    ).first.click()
                except Exception:
                    pass

            # 4) Open IPL 2026
            ipl_selector = (
                'text=/Indian Premier League.*2026|'
                'IPL 2026|'
                'Indian Premier League 2026/'
            )

            try:
                page.wait_for_selector(ipl_selector, timeout=8000)
                page.click(ipl_selector)

            except Exception:
                links = page.locator(
                    'a:has-text("IPL"), '
                    'a:has-text("Indian Premier League")'
                )

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
                    try:
                        page.click('text=IPL')
                    except Exception:
                        pass

            page.wait_for_load_state("networkidle")

            # 5) Click Table tab
            try:
                page.wait_for_selector('text=Table', timeout=10000)
                page.click('text=Table')

                page.wait_for_load_state("networkidle")

            except Exception:
                try:
                    page.locator(
                        'a:has-text("Table")'
                    ).first.click()

                    page.wait_for_load_state("networkidle")

                except Exception:
                    pass

            # Final response
            result["success"] = True
            result["final_url"] = page.url
            result["message"] = "Navigation completed successfully"

            browser.close()

    except Exception as e:
        result["message"] = str(e)
        result["trace"] = traceback.format_exc()

    return result


@app.route("/run-cricbuzz", methods=["GET"])
def run_api():
    response = run_cricbuzz(headless=True)
    return jsonify(response)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Flask Playwright API is running"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )