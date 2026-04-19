from Miner.AutoScout24Scraper import AutoScout24Scraper
from Analysis.DataProcessor import DataProcessor
from Analysis.MileagePriceRegression import MileagePriceRegression

import os


def main(scrape=False):
    if scrape:
        scrape_autoscout()
    data_preprocessed = preprocess()
    perform_regression(data_preprocessed)


def perform_regression(data_preprocessed):
    grouped_data = data_preprocessed.groupby('mileage_grouped')['price'].agg(['mean', 'std']).reset_index()
    mileage_values = grouped_data['mileage_grouped']
    average_price_values = grouped_data['mean']
    std_deviation_values = grouped_data['std']
    regression = MileagePriceRegression(mileage_values, average_price_values, std_deviation_values)
    predicted_prices, best_degree = regression.do_regression()
    regression.plot_mileage_price(predicted_prices, best_degree)


def preprocess():
    processor = DataProcessor(downloaded_listings_file)
    data = processor.read_data()
    data_no_duplicates = processor.remove_duplicates(data)
    data_preprocessed = processor.preprocess_data(data_no_duplicates)
    data_rounded = processor.round(data_preprocessed, 1000)
    processor.save_processed_data(data_rounded, output_file_preprocessed)
    return data_preprocessed


def scrape_autoscout():
    scraper = AutoScout24Scraper(
        make, model, cat, year_from, year_to, km_from, km_to, price_to,
        body, gear, power_from, power_to, powertype, headless=headless
    )
    scraper.scrape(num_pages, verbose=True)
    scraper.save_to_csv(downloaded_listings_file)
    scraper.quit_browser()


def ask_filters():
    print("\n--- Search filters (press Enter to skip any filter) ---")
    yf = input("  Registration year from : ").strip()
    yt = input("  Registration year to   : ").strip()
    kf = input("  Mileage minimum (km)   : ").strip()
    kt = input("  Mileage maximum (km)   : ").strip()
    pt = input("  Maximum price (€)      : ").strip()
    print()
    return yf, yt, kf, kt, pt


if __name__ == "__main__":
    # --- Fixed search parameters ---
    make = "skoda"
    model = "skoda_test"        # label for output file only, does not affect the URL
    cat = "ma65mo16621"         # model ID from the AutoScout24 URL (cat= parameter)
    body = "5"                  # body type: 1=sedan 2=hatchback 3=estate 4=van 5=SUV 6=cabrio 7=coupe
    gear = "A"                  # gearbox: A=automatic, M=manual
    power_from = ""
    power_to = ""
    powertype = "kw"

    # --- Scraping options ---
    num_pages = 3               # set to 20 for a full run (AutoScout24 max)
    headless = False            # set True to run Chrome without a visible window

    # --- Interactive filters ---
    year_from, year_to, km_from, km_to, price_to = ask_filters()

    downloaded_listings_file = f'listings/listings_{make}_{model}.csv'
    output_file_preprocessed = f'listings/listings_{make}_{model}_preprocessed.csv'

    if not os.path.exists("listings"):
        os.makedirs("listings")

    main(scrape=True)
