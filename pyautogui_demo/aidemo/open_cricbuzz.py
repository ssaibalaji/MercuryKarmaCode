"""PyAutoGUI script to open Chrome and navigate to Cricbuzz IPL points table.

Behavior:
- Launch Chrome if found (common install paths), otherwise open default browser.
- Navigate to `cricbuzz.com`, wait 3 seconds, then search for "browse series" and "Indian Premier League",
  then search for "Points table".

Notes / preconditions:
- Run on Windows with Chrome installed for best results.
- Keep the screen unlocked and visible; do not move mouse to screen corners (PyAutoGUI failsafe).
- This script uses keyboard navigation and search engine queries — it may need adjustments per system.

Usage:
Open PowerShell and run:
    python my_test_lab\pyautogui_demo\mydemo\open_cricbuzz.py

Abort: Move mouse to top-left corner to trigger PyAutoGUI fail-safe.
"""
import time
import subprocess
import shutil
import webbrowser
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def find_chrome_exe():
    # Try shutil.which first, then common install locations
    chrome = shutil.which('chrome') or shutil.which('chrome.exe')
    if chrome:
        return chrome
    common_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in common_paths:
        if shutil.os.path.exists(p):
            return p
    return None


def launch_chrome(chrome_path=None):
    if chrome_path:
        try:
            subprocess.Popen([chrome_path])
            return True
        except Exception:
            return False
    else:
        # fallback to default browser
        webbrowser.open('https://www.cricbuzz.com')
        return False


def type_and_search(query):
    # Focus address bar and type query
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.2)
    pyautogui.typewrite(query, interval=0.05)
    pyautogui.press('enter')


def main():
    print('Starting in 5 seconds. Move mouse to top-left to abort.')
    time.sleep(5)

    chrome = find_chrome_exe()
    launched = launch_chrome(chrome)
    if launched:
        # give Chrome time to start
        time.sleep(4)
    else:
        # If we opened the default browser via webbrowser, still wait
        time.sleep(4)

    try:
        # 1) Search for cricbuzz.com in the address bar
        type_and_search('cricbuzz.com')
        time.sleep(3)

        # Click at the coordinates where the page element is expected
        try:
            pyautogui.moveTo(945, 250, duration=0.3)
            pyautogui.click()
            time.sleep(3)

            # Then click another target position
            pyautogui.moveTo(934, 292, duration=0.3)
            pyautogui.click()
            time.sleep(3)

            # Then click the additional requested position
            pyautogui.moveTo(600, 313, duration=0.3)
            pyautogui.click()
            time.sleep(3)
        except pyautogui.FailSafeException:
            print('Click aborted by PyAutoGUI fail-safe.')

        print('Done — should have loaded the points table page.')

    except pyautogui.FailSafeException:
        print('Aborted by moving mouse to a corner (PyAutoGUI fail-safe).')


if __name__ == '__main__':
    main()
