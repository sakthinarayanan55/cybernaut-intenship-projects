import argparse
import json
import re
import sys
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
TOP_250_URL = "https://www.imdb.com/chart/top/"
BATCH_SCRIPT = r"""
const urls = arguments[0];
const callback = arguments[arguments.length - 1];
Promise.all(urls.map(url => {
  if (!url || url === 'N/A') return Promise.resolve({ url, cast: [], genres: [] });
  return fetch(url, { credentials: 'include' }).then(res => res.text()).then(html => {
    let cast = [], genres = [];
    const ldMatches = html.match(/<script type="application\/ld\+json">(.*?)<\/script>/gs);
    if (ldMatches) {
      for (const m of ldMatches) {
        try {
          const data = JSON.parse(m.replace(/<script type="application\/ld\+json">|<\/script>/g, ''));
          if (data['@type'] === 'Movie') {
            if (data.actor) cast = data.actor.map(a => a.name).filter(Boolean);
            if (data.genre) genres = Array.isArray(data.genre) ? data.genre : [data.genre];
            break;
          }
        } catch (e) {}
      }
    }
    return { url, cast, genres };
  }).catch(err => ({ url, cast: [], genres: [], error: err.toString() }));
})).then(results => callback(results));
"""
def is_float(val):
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False
def text_or_default(item, selector, default="N/A"):
    try:
        return item.find_element(By.CSS_SELECTOR, selector).text.strip()
    except Exception:
        return default
class IMDbScraper:
    def __init__(self, headless=True, page_delay=4):
        self.page_delay = page_delay
        self.driver = self._init_driver(headless)
    def _init_driver(self, headless):
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        for arg in ["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
                    "--window-size=1920,1080", "--disable-notifications",
                    "--disable-popup-blocking", "--disable-blink-features=AutomationControlled"]:
            opts.add_argument(arg)
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        return driver
    def _chart_genres(self):
        genres_by_id = {}
        try:
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', self.driver.page_source)
            if m:
                edges = (json.loads(m.group(1)).get("props", {}).get("pageProps", {})
                         .get("pageData", {}).get("chartTitles", {}).get("edges", []))
                for edge in edges:
                    node = edge.get("node", {})
                    mid = node.get("id")
                    g_list = [g.get("genre", {}).get("text") for g in node.get("titleGenres", {}).get("genres", [])
                              if g.get("genre", {}).get("text")]
                    if mid and g_list:
                        genres_by_id[mid] = ", ".join(g_list)
        except Exception as e:
            print(f"[!] Could not extract genres: {e}")
        return genres_by_id
    def _fetch_cast_and_genre(self, urls, batch_size=25):
        details = {}
        for i in range(0, len(urls), batch_size):
            chunk = urls[i:i + batch_size]
            try:
                for item in self.driver.execute_async_script(BATCH_SCRIPT, chunk):
                    details[item["url"]] = item
            except Exception as e:
                print(f"[!] Batch fetch error at {i}: {e}")
            print(f"    [Progress] {min(i + batch_size, len(urls))}/{len(urls)} movies enriched")
            time.sleep(0.3)
        return details
    def _parse_item(self, item, index, chart_genres):
        # Use DOM order as the ranking source of truth; the on-page rank badge
        # can be stale/duplicated during virtualized-scroll rendering.
        rank = index
        title = re.sub(r"^\d+\.\s*", "", text_or_default(item, ".ipc-title__text, .cli-title h4, .cli-title h3"))
        movie_url, movie_id = "N/A", ""
        try:
            href = item.find_element(By.CSS_SELECTOR, "a.ipc-title-link-wrapper, a.ipc-lockup-overlay").get_attribute("href")
            if href:
                movie_url = href.split("?")[0]
                match = re.search(r"(tt\d+)", movie_url)
                movie_id = match.group(1) if match else ""
        except Exception:
            pass
        meta = [el.text.strip() for el in item.find_elements(By.CSS_SELECTOR, ".cli-title-metadata li, .cli-title-metadata span") if el.text.strip()]
        year = meta[0] if len(meta) >= 1 else "N/A"
        runtime = meta[1] if len(meta) >= 2 else "N/A"
        rating = text_or_default(item, ".ipc-rating-star--rating")
        votes = text_or_default(item, ".ipc-rating-star--voteCount").replace("(", "").replace(")", "").strip()
        return {
            "Ranking": rank,
            "Movie Title": title,
            "Year": year,
            "Rating": float(rating) if is_float(rating) else None,
            "Runtime": runtime,
            "Votes": votes,
            "Genre": chart_genres.get(movie_id, "N/A"),
            "Cast": "N/A",
            "Movie URL": movie_url,
            "Movie ID": movie_id,
        }
    def scrape_top_250(self):
        print(f"[*] Navigating to {TOP_250_URL}")
        self.driver.get(TOP_250_URL)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"))
            )
        except Exception as e:
            print(f"[!] Timeout waiting for list: {e}")
        time.sleep(self.page_delay)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        chart_genres = self._chart_genres()
        items = self.driver.find_elements(By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
        print(f"[+] Located {len(items)} movie entries")
        movies = [self._parse_item(item, i, chart_genres) for i, item in enumerate(items, start=1)]

        # Dedupe: virtualized scrolling can render the same title twice; keep first occurrence.
        seen = set()
        movies = [m for m in movies if not ((k := (m["Movie ID"] or m["Movie URL"])) in seen or seen.add(k))]

        urls = [m["Movie URL"] for m in movies if m["Movie URL"] != "N/A"]
        if urls:
            details_map = self._fetch_cast_and_genre(urls)
            for m in movies:
                d = details_map.get(m["Movie URL"])
                if d:
                    if d.get("cast"):
                        m["Cast"] = ", ".join(d["cast"][:3])
                    if d.get("genres"):
                        m["Genre"] = ", ".join(d["genres"])
        cols = ["Ranking", "Movie Title", "Year", "Rating", "Runtime", "Votes", "Genre", "Cast", "Movie URL"]
        df = pd.DataFrame(movies)[cols].sort_values("Ranking", kind="stable").reset_index(drop=True)
        return df
    def save_to_csv(self, df, path="imdb_top_250_movies.csv"):
        df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\r\n")
        print(f"[SUCCESS] Saved {len(df)} records to {path}")
        return path
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="IMDb Top 250 Scraper")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--output", type=str, default="imdb_top_250_movies.csv")
    args = parser.parse_args()
    start = time.time()
    with IMDbScraper(headless=args.headless) as scraper:
        df = scraper.scrape_top_250()
        scraper.save_to_csv(df, args.output)
    print(f"\n[SUCCESS] Done in {time.time() - start:.2f}s")
    print(df[["Ranking", "Movie Title", "Year", "Rating", "Genre", "Cast"]].head(5).to_string(index=False))
if __name__ == "__main__":
    main()