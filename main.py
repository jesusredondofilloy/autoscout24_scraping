from Miner.AutoScout24Scraper import AutoScout24Scraper
from Analysis.DataProcessor import DataProcessor
from Analysis.MileagePriceRegression import MileagePriceRegression
from Miner.TextFileHandler import TextFileHandler

import os


def main(scrape=False):
    zip_list = where_to_search()
    if scrape:
        scrape_autoscout(zip_list)
    # Data Processing
    data_preprocessed = preprocess()
    # Mileage-Price Regression
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


def scrape_autoscout(zip_list):
    scraper = AutoScout24Scraper(
        make, model, cat, year_from, year_to, body, gear,
        power_from, power_to, powertype, zip_list, zipr, headless=headless
    )
    scraper.scrape(num_pages, verbose=True)
    scraper.save_to_csv(downloaded_listings_file)
    scraper.quit_browser()


def where_to_search():
    handler = TextFileHandler(zip_list_file_path)
    # dtype=str preserves leading zeros in German zip codes (e.g. 04109)
    handler.load_data_csv(dtype={'Zip': str})
    return handler.export_column('Zip')


if __name__ == "__main__":
    # --- Search parameters ---
    make = "skoda"
    model = "skoda_test"        # label for output file only, does not affect the URL
    cat = "ma65mo16621"         # model ID from AutoScout24 URL (cat= parameter)
    year_from = "2020"
    year_to = ""
    body = "5"                  # body type: 1=sedan 2=hatchback 3=estate 4=van 5=SUV 6=cabrio 7=coupe
    gear = "A"                  # gearbox: A=automatic, M=manual
    power_from = ""
    power_to = ""
    powertype = "kw"

    # --- Scraping options ---
    num_pages = 3               # pages per zip code — keep low for testing
    zipr = 200                  # search radius in km
    headless = False            # set True to run Chrome without a visible window

    zip_list_file_path = 'Miner/german_zips.csv'
    downloaded_listings_file = f'listings/listings_{make}_{model}.csv'
    output_file_preprocessed = f'listings/listings_{make}_{model}_preprocessed.csv'

    if not os.path.exists("listings"):
        os.makedirs("listings")

    main(scrape=True)
