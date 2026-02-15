import os
from dotenv import load_dotenv
from scripts.scraper import TuikScraper
import argparse

# .env dosyasını yükle
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Run TÜİK Data Calendar Scraper')
    parser.add_argument('--years', nargs='+', type=int, default=[2026], help='Years to scrape (e.g. 2026 2027)')
    args = parser.parse_args()

    print(f"Starting Scraper for years: {args.years}")
    try:
        scraper = TuikScraper()
        scraper.run(years=args.years)
        print("Scraping completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()