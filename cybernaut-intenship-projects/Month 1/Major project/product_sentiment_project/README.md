# Product Sentiment Analyzer and Review Dashboard

A Flask-based web app that analyzes product review sentiment (positive/negative/neutral)
and displays it on an interactive dashboard with charts.

## Project structure
```
product_sentiment_project/
├── app.py                  # Flask backend + REST API
├── database.py             # SQLite storage (products, reviews)
├── sentiment_analyzer.py   # VADER sentiment classification + word frequency
├── scraper.py              # Mock review generator + Selenium scraper (Flipkart)
├── requirements.txt
├── templates/
│   └── index.html          # Dashboard page
└── static/
    ├── css/style.css
    └── js/dashboard.js     # Fetches API data, renders Chart.js charts
```

## 1. Setup in VS Code

1. Unzip this project and open the folder in VS Code.
2. Open a terminal in VS Code (`` Ctrl+` ``) and create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Run the app

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 3. Using the dashboard

1. Type a product name (e.g. "Bluetooth Headphones") in the search box.
2. Keep **"Use sample data"** checked and click **Analyze Reviews** — this generates
   realistic mock review data instantly, so you can demo the full pipeline
   (sentiment classification → database → charts) without needing live scraping.
3. Click on a product chip to view its dashboard: sentiment distribution (pie),
   sentiment trend over time (line), frequent words (bar chart), and the raw
   review list with per-review sentiment tags.

## 4. Real scraping (optional, advanced)

Uncheck "Use sample data" to attempt a live Selenium scrape of Flipkart search
results. Important caveats:

- Requires **Google Chrome** installed locally (webdriver-manager auto-downloads
  a matching driver).
- Flipkart's HTML structure changes over time — the CSS selectors in
  `scraper.py` (`_scrape_flipkart`) may need updating. Use browser dev tools
  (F12 → Elements) to find current selectors if it stops returning results.
- Automated scraping may violate a site's Terms of Service and can get your
  IP/account rate-limited or blocked. Use responsibly, scrape slowly, and
  check `robots.txt` before scraping any site for anything beyond learning
  purposes. Amazon in particular has strong anti-bot protections and isn't
  implemented here for that reason — Flipkart was chosen as the more
  scraping-tolerant starting point.
- For a class/major project submission, most instructors are fine with mock
  data standing in for the live scrape in your demo — the scraping logic
  itself (`scraper.py`) demonstrates the technique, and the rest of the
  pipeline (sentiment analysis → storage → dashboard) runs on real code either way.

## 5. Install it on your phone (as a mobile app / PWA)

This project ships with PWA (Progressive Web App) support — a phone can "install"
it from the browser and it behaves like a native app (own icon, full-screen, no
address bar), without needing the Play Store or Xcode.

**Step 1 — get the app reachable from your phone.** Pick one:

- **Same WiFi (quick, for demos):**
  1. On your laptop, find its local IP: Windows → `ipconfig` (look for "IPv4 Address",
     e.g. `192.168.1.5`); Mac/Linux → `ifconfig` or `ip addr`.
  2. In `app.py`, change the last line to:
     ```python
     app.run(debug=True, port=5000, host='0.0.0.0')
     ```
  3. Run `python app.py`, then on your phone (connected to the same WiFi), open
     `http://<your-laptop-ip>:5000` in the browser (e.g. `http://192.168.1.5:5000`).

- **From anywhere (for a real submission/demo link):** deploy the Flask app to a
  free host like Render.com or PythonAnywhere, then use that public URL instead.

**Step 2 — install it:**
- **Android (Chrome):** open the URL → tap the ⋮ menu → **"Add to Home screen" / "Install app"**.
- **iPhone (Safari):** open the URL → tap the Share icon → **"Add to Home Screen"**.

The app icon appears on the home screen and opens full-screen like a native app.
`static/manifest.json` and `static/service-worker.js` control this — edit the
`name`/`theme_color` in `manifest.json` if you want to rebrand it, and regenerate
`static/icons/icon-192.png` / `icon-512.png` if you want a different logo.

## 6. Build a Windows .exe (standalone desktop app)

This packages the whole app — server, dashboard, everything — into a single
`.exe` file. Double-clicking it starts the server in the background and opens
your browser to the dashboard automatically. No Python install needed on the
machine that runs the `.exe` (Python is only needed on the machine that *builds* it).

**You must run this build on Windows** (a Windows `.exe` can't be built from
Mac/Linux). Do this from the same VS Code terminal you've already got set up:

```powershell
pip install pyinstaller
```

Then, from inside `product_sentiment_project` (with your venv still active), run:

```powershell
pyinstaller --onefile --name Sentiment-IQ --add-data "templates;templates" --add-data "static;static" app_desktop.py
```

This takes a minute or two. When it finishes, your `.exe` is at:

```
dist\Sentiment-IQ.exe
```

Double-click `Sentiment-IQ.exe` — a console window opens (that's the running server;
leave it open) and your browser launches to the dashboard automatically. Copy
`Sentiment-IQ.exe` anywhere you like — the `dist` folder is the only thing you need
to hand someone to run the app; they don't need Python, VS Code, or the source
files. The SQLite database (`sentiment_data.db`) is created next to wherever
`Sentiment-IQ.exe` is placed, and persists between runs.

To close the app, close the console window (or press Ctrl+C in it).

**If you change the code later**, re-run the `pyinstaller` command above to
rebuild `Sentiment-IQ.exe` — it doesn't auto-update.

## 7. Extending this project

- **Switch database**: replace `database.py` with a MongoDB (pymongo) or
  PostgreSQL (psycopg2/SQLAlchemy) version — keep the same method names
  (`add_product`, `add_reviews`, `get_products`, `get_reviews`) so `app.py`
  doesn't need to change.
- **Add Amazon scraping**: write an `_scrape_amazon` method in `scraper.py`
  following the same pattern as `_scrape_flipkart`, using BeautifulSoup for
  static content where possible (lighter weight than Selenium).
- **Deploy**: backend to Render or an AWS EC2 instance; since the frontend is
  served directly by Flask here, the whole app can be deployed as one service
  (no separate Vercel/Netlify step needed) — or split it into a React frontend
  later if you want closer to the original spec.
- **Word cloud visual**: the `word_frequency` data from `/api/analytics/<id>`
  is already shaped for a word-cloud library (e.g. `wordcloud2.js`) if you want
  a visual upgrade over the bar chart.
