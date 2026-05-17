"""Live mouse coordinate reporter using PyAutoGUI.

Shows X/Y coordinates and the RGB color of the pixel under the cursor.
Run and watch the console. Press Ctrl+C to quit or move mouse to top-left to trigger fail-safe.

Usage:
    python my_test_lab\pyautogui_demo\aidemo\mouse_coords.py
"""
import time
import sys
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0


def main(poll_interval=0.08):
    print('Mouse coordinate reporter — Ctrl+C to exit. Move mouse to top-left to abort.')
    try:
        while True:
            x, y = pyautogui.position()
            try:
                rgb = pyautogui.pixel(x, y)
            except Exception:
                rgb = ('N/A', 'N/A', 'N/A')

            # Overwrite the same console line
            sys.stdout.write(f'\rX:{x:4} Y:{y:4}   RGB:{rgb}')
            sys.stdout.flush()
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print('\nExiting mouse coordinate reporter.')


if __name__ == '__main__':
    main()
