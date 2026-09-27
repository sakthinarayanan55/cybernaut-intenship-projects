"""
Review scraper module.

IMPORTANT:
Amazon and Flipkart actively guard against automated scraping, and scraping
against a site's Terms of Service carries legal/account risk — so treat the
Selenium path here as an educational starting point, expect selectors to
need updating as site layouts change, and go easy on request rate.

For development, demos, and building/testing the dashboard, use the mock
data generator below — it produces realistic review data instantly with
no network access required.
"""
import os
import random
import re
import shutil
import time
from datetime import datetime, timedelta

# Known product categories and brands, used to validate that a searched
# term looks like a real product before generating/fetching reviews for it.
# This is a simple keyword check (not a live catalog lookup) — good enough
# to reject obvious junk input like random numbers or names.
PRODUCT_CATEGORY_WORDS = [
    'phone', 'smartphone', 'mobile', 'iphone', 'headphone', 'headphones',
    'earphone', 'earphones', 'earbud', 'earbuds', 'airpods', 'speaker',
    'laptop', 'notebook', 'tablet', 'ipad', 'watch', 'smartwatch', 'band',
    'tv', 'television', 'camera', 'dslr', 'lens', 'monitor', 'keyboard',
    'mouse', 'charger', 'powerbank', 'power bank', 'cable', 'router',
    'fridge', 'refrigerator', 'washing machine', 'microwave', 'oven',
    'mixer', 'grinder', 'ac', 'air conditioner', 'fan', 'cooler', 'heater',
    'shoes', 'sneakers', 'sandals', 'slippers', 'bag', 'backpack', 'wallet',
    'belt', 'sunglasses', 'jacket', 'tshirt', 't-shirt', 'shirt', 'jeans',
    'perfume', 'trimmer', 'shaver', 'hairdryer', 'iron', 'vacuum',
    'console', 'controller', 'joystick', 'processor', 'graphics card', 'gpu',
    'ssd', 'hdd', 'pendrive', 'memory card', 'printer', 'projector'
]

PRODUCT_BRAND_WORDS = [
    'apple', 'samsung', 'redmi', 'xiaomi', 'mi', 'oneplus', 'realme', 'vivo',
    'oppo', 'motorola', 'moto', 'nokia', 'asus', 'acer', 'dell', 'hp', 'lenovo',
    'msi', 'lg', 'sony', 'jbl', 'boat', 'noise', 'fireboltt', 'fastrack',
    'titan', 'casio', 'philips', 'bajaj', 'prestige', 'pigeon', 'whirlpool',
    'godrej', 'haier', 'voltas', 'blue star', 'canon', 'nikon', 'gopro',
    'logitech', 'hp', 'nike', 'adidas', 'puma', 'reebok', 'woodland',
    'bata', 'skechers', 'levis', "levi's", 'wrangler', 'ray-ban', 'rayban'
]


def is_valid_product(name):
    """
    Best-effort check that a searched term looks like a real product
    (contains a recognizable brand or product-category word), rather than
    random text or a plain number. Not a live catalog lookup — a simple
    keyword guard so junk input doesn't generate fake reviews.
    """
    if not name:
        return False

    cleaned = name.strip().lower()

    # Reject pure numbers / no letters at all
    if not re.search(r'[a-zA-Z]', cleaned):
        return False

    # Reject if too short to be meaningful
    if len(cleaned) < 3:
        return False

    for word in PRODUCT_CATEGORY_WORDS + PRODUCT_BRAND_WORDS:
        if word in cleaned:
            return True

    return False


class ReviewScraper:
    def __init__(self):
        self.sample_positive = [
            "Excellent product, works exactly as described!",
            "Really happy with this purchase, great value for money.",
            "Amazing build quality and fast delivery.",
            "Works perfectly, would definitely recommend to others.",
            "Best purchase I've made this year, love it!",
            "Great performance and the battery life is fantastic.",
        ]
        self.sample_negative = [
            "Terrible quality, broke within a week.",
            "Very disappointed, does not match the description.",
            "Waste of money, would not recommend.",
            "Product arrived damaged and customer service was unhelpful.",
            "Poor performance, expected much better for this price.",
            "Stopped working after two days, very frustrating.",
        ]
        self.sample_neutral = [
            "It's okay, does the job but nothing special.",
            "Average product, matches the price point.",
            "Decent but there are better options available.",
            "Works fine, no major complaints so far.",
            "Delivery was on time, product is as expected.",
        ]

    def generate_mock_reviews(self, product_name, count=60):
        """Generates realistic sample review data for development/demo use."""
        reviews = []
        pool = (
            [(t, 'pos') for t in self.sample_positive] +
            [(t, 'neg') for t in self.sample_negative] +
            [(t, 'neu') for t in self.sample_neutral]
        )
        for _ in range(count):
            text, tone = random.choice(pool)
            if tone == 'pos':
                rating = random.choice([4, 5])
            elif tone == 'neg':
                rating = random.choice([1, 2])
            else:
                rating = 3

            days_ago = random.randint(0, 180)
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

            reviews.append({
                'text': f"{text} (Regarding {product_name})",
                'rating': rating,
                'date': date
            })
        return reviews

    def scrape_reviews(self, product_name, source='flipkart', max_reviews=50):
        """
        Real scraper using Selenium. Requires Google Chrome installed locally.
        webdriver-manager auto-downloads a matching chromedriver.
        This is intentionally disabled in Vercel/serverless deployments where
        a browser runtime is not available.
        """
        if os.environ.get('VERCEL') == '1':
            raise RuntimeError('Live scraping is disabled in serverless deployments.')

        chrome_binary = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
        if not chrome_binary:
            raise RuntimeError('No Chrome/Chromium browser found on this machine.')

        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0')

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        reviews = []
        try:
            if source == 'flipkart':
                reviews = self._scrape_flipkart(driver, product_name, max_reviews)
            else:
                raise ValueError(f"Unsupported source: {source}")
        finally:
            driver.quit()

        return reviews

    def _scrape_flipkart(self, driver, product_name, max_reviews):
        # NOTE: these CSS selectors match Flipkart's layout at the time of
        # writing and WILL need updating if the site changes. Inspect the
        # page (F12 -> Elements) and adjust selectors if this stops working.
        search_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(3)

        product_links = driver.find_elements(By.CSS_SELECTOR, "a.CGtC98")
        if not product_links:
            return []

        product_url = product_links[0].get_attribute('href')
        driver.get(product_url)
        time.sleep(3)

        reviews = []
        review_blocks = driver.find_elements(By.CSS_SELECTOR, "div.ZmyHeo")
        for block in review_blocks[:max_reviews]:
            reviews.append({
                'text': block.text.strip(),
                'rating': None,
                'date': datetime.now().strftime('%Y-%m-%d')
            })

        return reviews
