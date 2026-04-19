import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class AutoScout24Scraper:
    # Primary: any article with a data-make attribute; fallback: legacy class name
    _XPATH_PRIMARY = "//article[@data-make]"
    _XPATH_FALLBACK = "//article[contains(@class, 'cldt-summary-full-item')]"
    _BASE_DOMAIN = "https://www.autoscout24.it"

    def __init__(self, make, model, version, year_from, year_to, power_from, power_to, powertype, zip_list, zipr,
                 headless=False):
        self.make = make
        self.model = model
        self.version = version
        self.year_from = year_from
        self.year_to = year_to
        self.power_from = power_from
        self.power_to = power_to
        self.powertype = powertype
        self.zip_list = zip_list
        self.zipr = zipr
        self.base_url = ("https://www.autoscout24.it/lst/{}/{}/ve_{}?atype=C&cy=I&damaged_listing=exclude&desc=0&"
                         "fregfrom={}&fregto={}&powerfrom={}&powerto={}&powertype={}&sort=standard&"
                         "source=homepage_search-mask&ustate=N%2CU&zip={}&zipr={}")
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

    def generate_urls(self, num_pages, zip):
        url_list = [self.base_url.format(self.make, self.model, self.version, self.year_from, self.year_to,
                                         self.power_from, self.power_to, self.powertype, zip, self.zipr)]
        for i in range(2, num_pages + 1):
            url_to_add = (self.base_url.format(self.make, self.model, self.version, self.year_from, self.year_to,
                                               self.power_from, self.power_to, self.powertype, zip, self.zipr) +
                          f"&page={i}&sort=standard&source=listpage_pagination&ustate=N%2CU")
            url_list.append(url_to_add)
        return url_list

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
        url_list = []
        for zip in self.zip_list:
            url_list.extend(self.generate_urls(num_pages, zip))

        for webpage in url_list:
            self.browser.get(webpage)
            listings = self._find_listings()

            if verbose:
                print(f"[{webpage}] found {len(listings)} listings")

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
