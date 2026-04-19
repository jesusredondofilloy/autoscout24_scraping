import time
import urllib.parse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class AutoScout24Scraper:
    _XPATH_PRIMARY = "//article[@data-make]"
    _XPATH_FALLBACK = "//article[contains(@class, 'cldt-summary-full-item')]"
    _BASE_DOMAIN = "https://www.autoscout24.de"

    def __init__(self, make, model, cat, year_from, year_to, km_from, km_to, price_to,
                 body, gear, power_from, power_to, powertype, headless=False):
        self.make = make
        self.model = model          # label only — used for output file naming
        self.cat = cat              # e.g. "ma65mo16621" — encodes the model in DE URLs
        self.year_from = year_from
        self.year_to = year_to
        self.km_from = km_from
        self.km_to = km_to
        self.price_to = price_to
        self.body = body
        self.gear = gear
        self.power_from = power_from
        self.power_to = power_to
        self.powertype = powertype

        self.listing_frame = pd.DataFrame(columns=[
            "make", "model", "mileage", "fuel-type", "first-registration", "price",
            "url", "guid", "transmission", "engine-size", "body-type", "seller-type"
        ])

        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--incognito")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        if headless:
            self.options.add_argument("--headless=new")
        self.browser = webdriver.Chrome(options=self.options)

    def _build_url(self, page=1):
        params = [
            ('atype', 'C'),
            ('cy', 'D'),
            ('damaged_listing', 'exclude'),
            ('desc', '0'),
            ('ocs_listing', 'include'),
            ('powertype', self.powertype),
            ('sort', 'standard'),
            ('ustate', 'N,U'),
        ]
        for key, val in [
            ('body', self.body),
            ('cat', self.cat),
            ('fregfrom', self.year_from),
            ('fregto', self.year_to),
            ('gear', self.gear),
            ('kmfrom', self.km_from),
            ('kmto', self.km_to),
            ('powerfrom', self.power_from),
            ('powerto', self.power_to),
            ('priceto', self.price_to),
        ]:
            if val:
                params.append((key, val))

        if page > 1:
            params.extend([('page', page), ('source', 'listpage_pagination')])
        else:
            params.append(('source', 'homepage_search-mask'))

        return f"{self._BASE_DOMAIN}/lst/{self.make}?{urllib.parse.urlencode(params)}"

    def _find_listings(self):
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, self._XPATH_PRIMARY))
            )
            listings = self.browser.find_elements("xpath", self._XPATH_PRIMARY)
            if listings:
                return listings
        except TimeoutException:
            pass
        return self.browser.find_elements("xpath", self._XPATH_FALLBACK)

    def _extract_url(self, listing):
        try:
            link = listing.find_element("xpath", ".//a[@href]")
            href = link.get_attribute("href") or ""
            if href and not href.startswith("http"):
                href = self._BASE_DOMAIN + href
            return href or None
        except Exception:
            return None

    def scrape(self, num_pages, verbose=False):
        for page in range(1, num_pages + 1):
            webpage = self._build_url(page)
            self.browser.get(webpage)
            listings = self._find_listings()

            if verbose:
                print(f"[page {page}] found {len(listings)} listings")

            rows = []
            for listing in listings:
                row = {
                    "make": listing.get_attribute("data-make"),
                    "model": listing.get_attribute("data-model"),
                    "mileage": listing.get_attribute("data-mileage"),
                    "fuel-type": listing.get_attribute("data-fuel-type"),
                    "first-registration": listing.get_attribute("data-first-registration"),
                    "price": listing.get_attribute("data-price"),
                    "url": self._extract_url(listing),
                    "guid": listing.get_attribute("data-guid"),
                    "transmission": listing.get_attribute("data-transmission"),
                    "engine-size": listing.get_attribute("data-engine-size"),
                    "body-type": listing.get_attribute("data-body-type"),
                    "seller-type": listing.get_attribute("data-seller-type"),
                }
                rows.append(row)

                if verbose:
                    print(row)

            if rows:
                self.listing_frame = pd.concat(
                    [self.listing_frame, pd.DataFrame(rows)],
                    ignore_index=True
                )

            time.sleep(1)

    def save_to_csv(self, filename="listings.csv"):
        self.listing_frame.to_csv(filename, index=False)
        print("Data saved to", filename)

    def quit_browser(self):
        self.browser.quit()
