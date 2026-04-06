"""
REQUIREMENTS:
    pip install pyautogui pandas openpyxl pyperclip

    Move your mouse to the TOP-LEFT corner of the screen at any time to abort.
"""

import pyautogui
import pyperclip
import pandas as pd
import time
import logging
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

EXCEL_FILE = "your file.xlsx"
SHEET_NAME = 0
PART_COLUMN = "Part"
LINE_COLUMN = "Line"
TARGET_LINE = "main line name" #used just for tracking changes 

TEST_MODE = False
TEST_BATCH_SIZE = 5

DELAY_SHORT = 0.2
DELAY_LONG = 1.0
DELAY_BETWEEN_PARTS = 0.2

LOG_FILE = f"deletion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger()

# ============================================================
# HELPER
# ============================================================

def type_text(text):
    pyperclip.copy(str(text))
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(DELAY_SHORT)


# ============================================================
# NAVIGATION
# ============================================================

def navigate_to_interchange_menu():
    log.info("  Navigating to interchange menu (2 -> 5 -> 5)...")
    pyautogui.press('2')
    time.sleep(DELAY_LONG)
    pyautogui.press('5')
    time.sleep(DELAY_LONG)
    pyautogui.press('5')
    time.sleep(DELAY_LONG)


def process_part(part, interchanges):
    log.info(f"  Processing part: {part} with {len(interchanges)} interchange(s)")

    for i, interchange in enumerate(interchanges):
        log.info(f"    Interchange {i+1}: {interchange['int_line']} | {interchange['int_part']}")

        type_text(TARGET_LINE)
        pyautogui.press('enter')
        time.sleep(DELAY_SHORT)

        type_text(part)
        pyautogui.press('enter')
        time.sleep(DELAY_LONG)

        type_text(interchange['int_line'])
        pyautogui.press('enter')
        time.sleep(DELAY_SHORT)

        type_text(interchange['int_part'])
        pyautogui.press('enter')
        time.sleep(DELAY_SHORT)


def return_to_part_search():
    log.info("  Returning to part search...")
    pass


# ============================================================
# DATA LOADING
# ============================================================

def load_gro_records(filepath, sheet):
    log.info(f"Loading Excel file: {filepath}")
    df = pd.read_excel(filepath, sheet_name=sheet, dtype=str)
    df.fillna("", inplace=True)
    df.columns = df.columns.str.strip()

    gro_rows = df[df[LINE_COLUMN].str.strip().str.upper() == TARGET_LINE.upper()]
    log.info(f"Found {len(gro_rows)} GRO part(s) in inventory.")

    col_pairs = [(f"Int Line {i}", f"Int Part {i}") for i in range(1, 11)]

    parts = []
    for _, row in gro_rows.iterrows():
        part = str(row[PART_COLUMN]).strip()
        interchanges = []

        for line_col, part_col in col_pairs:
            int_line = str(row[line_col]).strip()
            int_part = str(row[part_col]).strip()
            if int_line and int_part and int_line.upper() != "NAN" and int_part.upper() != "NAN":
                interchanges.append({
                    "int_line": int_line,
                    "int_part": int_part
                })

        if interchanges:
            parts.append({"part": part, "interchanges": interchanges})
            log.info(f"  Part {part}: {len(interchanges)} interchange(s)")

    log.info(f"Total parts to process: {len(parts)}")
    return parts


# ============================================================
# MAIN LOOP
# ============================================================

def run(parts):
    total = len(parts)
    success = 0
    failed = 0

    log.info("=" * 60)
    log.info(f"Starting processing of {total} GRO part(s).")
    if TEST_MODE:
        log.info(f"TEST MODE ON - only processing first {TEST_BATCH_SIZE} parts. No real keypresses.")
    log.info("Move mouse to TOP-LEFT corner at any time to abort.")
    log.info("=" * 60)

    if not TEST_MODE:
        for i in range(5, 0, -1):
            log.info(f"Starting in {i}... (switch to Firefox now)")
            time.sleep(1)

        navigate_to_interchange_menu()

    for index, entry in enumerate(parts):
        if TEST_MODE and index >= TEST_BATCH_SIZE:
            log.info(f"TEST MODE: Stopping after {TEST_BATCH_SIZE} parts.")
            break

        log.info(f"--- Part {index + 1}/{total}: {entry['part']} ---")

        try:
            if not TEST_MODE:
                process_part(entry["part"], entry["interchanges"])
                return_to_part_search()
                time.sleep(DELAY_BETWEEN_PARTS)

            log.info(f"  SUCCESS")
            success += 1

        except pyautogui.FailSafeException:
            log.warning("KILLSWITCH ACTIVATED - mouse moved to top-left corner. Stopping.")
            break

        except Exception as e:
            log.error(f"  FAILED: {e}")
            failed += 1
            try:
                if not TEST_MODE:
                    return_to_part_search()
            except Exception:
                pass

    log.info("=" * 60)
    log.info(f"Done. Success: {success} | Failed: {failed} | Total: {total}")
    log.info(f"Full log saved to: {LOG_FILE}")
    log.info("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    parts = load_gro_records(EXCEL_FILE, SHEET_NAME)
    if parts:
        run(parts)
    else:
        log.info("No GRO records found. Check your Excel file and column name configuration.")
