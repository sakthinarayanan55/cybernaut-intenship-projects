import time
import csv
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd

URL = "https://www.coingecko.com/"
CSV_FILE = "crypto_prices.csv"       # latest snapshot (overwritten each run)
HISTORY_FILE = "crypto_history.csv"  # timestamped log (appended each run)
TOP_N = 10                           # number of coins to scrape
HEADLESS = True              
ROW_SELECTOR = "table tbody tr"

def create_driver(headless=True):
    """Create and return a configured Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def dismiss_cookie_banner(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Accept') or contains(., 'accept')]")
            )
        ).click()
    except Exception:
        pass

def scrape_top_coins(driver, top_n=10):

    driver.get(URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ROW_SELECTOR))
    )
    dismiss_cookie_banner(driver)
    time.sleep(2)
    rows = driver.find_elements(By.CSS_SELECTOR, ROW_SELECTOR)
    coins_data = []
    for row in rows:
        if len(coins_data) >= top_n:
            break
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            row_text = [cell.text.strip() for cell in cells]
            name = extract_name(row, row_text)
            price = extract_price(row_text)
            change_24h = extract_24h_change(row_text)
            market_cap = extract_market_cap(row_text)
            if name and price != "N/A":
                coins_data.append({
                    "s_no": len(coins_data) + 1,   # serial number 1..top_n
                    "name": name,
                    "price": price,
                    "change_24h": change_24h,
                    "market_cap": market_cap,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
        except Exception as e:
            print(f"Skipped a row due to error: {e}")
            continue
    return coins_data

def extract_name(row, row_text):
    try:
        # The coin link text is normally the cleanest source of the name.
        name_el = row.find_element(By.CSS_SELECTOR, "a[href*='/en/coins/'], a[href*='/coins/']")
        text = name_el.text.strip()
        if text:
            return text.split("\n")[0].strip()
    except Exception:
        pass

    if len(row_text) > 1 and row_text[1]:
        raw = row_text[1]
        # Strip a trailing "Buy" button label if present.
        if raw.endswith("Buy"):
            raw = raw[:-3]
        return raw.strip()
    return None

def extract_price(row_text):
    for text in row_text:
        if text.startswith("$"):
            return text
    return "N/A"

def extract_24h_change(row_text):
    percent_values = [t for t in row_text if "%" in t]
    if len(percent_values) >= 2:
        return percent_values[1]
    if percent_values:
        return percent_values[0]
    return "N/A"

def extract_market_cap(row_text):
    dollar_values = [t for t in row_text if t.startswith("$")]
    if len(dollar_values) > 1:

        def parse(v):
            try:
                return float(v.replace("$", "").replace(",", ""))
            except (ValueError, AttributeError):
                return -1
        candidates = dollar_values[1:]
        if candidates:
            return max(candidates, key=parse)
    return "N/A"

def filter_top_gainers(coins_data, top_x=3):
    def parse_percent(value):
        try:
            return float(value.replace("%", "").replace(",", ""))
        except (ValueError, AttributeError):
            return float("-inf")

    sorted_coins = sorted(
        coins_data, key=lambda c: parse_percent(c["change_24h"]), reverse=True
    )
    return sorted_coins[:top_x]

def filter_by_price_threshold(coins_data, max_price=100):
    def parse_price(value):
        try:
            return float(value.replace("$", "").replace(",", ""))
        except (ValueError, AttributeError):
            return float("inf")
    return [c for c in coins_data if parse_price(c["price"]) <= max_price]

def save_to_csv(coins_data, filename):
    df = pd.DataFrame(coins_data)
    df.to_csv(filename, index=False)
    print(f"Saved latest snapshot to '{filename}'")

def append_to_history(coins_data, filename):
    file_exists = os.path.isfile(filename)
    df = pd.DataFrame(coins_data)
    df.to_csv(filename, mode="a", header=not file_exists, index=False)
    print(f"Appended data to history file '{filename}'")

def main():
    print("Starting Cryptocurrency Price Tracker...")
    driver = create_driver(headless=HEADLESS)
    try:
        coins_data = scrape_top_coins(driver, top_n=TOP_N)
        if not coins_data:
            print("No data was scraped. The website layout may have changed.")
            return
        print(f"\nScraped {len(coins_data)} coins:\n")
        for coin in coins_data:
            print(f"{coin['s_no']:<3} | {coin['name']:<10} | {coin['price']:<12} | "
                  f"{coin['change_24h']:<8} | {coin['market_cap']}")

        save_to_csv(coins_data, CSV_FILE)
        append_to_history(coins_data, HISTORY_FILE)
        print(f"History file '{HISTORY_FILE}' now contains a cumulative log "
              f"of every run (this run added {len(coins_data)} rows).")
        top_gainers = filter_top_gainers(coins_data, top_x=3)
        print("\nTop 3 gainers in the last 24h:")
        for coin in top_gainers:
            print(f"{coin['name']} -> {coin['change_24h']}")
    finally:
        driver.quit()
        print("\nBrowser closed. Done!")
if __name__ == "__main__":
    main()