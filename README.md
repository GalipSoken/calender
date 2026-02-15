# TÜİK Data Calendar Scraper

This project is a web scraper designed to fetch data publication calendars from the [TÜİK Data Calendar](https://www.tuik.gov.tr/Kurumsal/Veri_Takvimi) for specific institutions (TCMB, BDDK, HMB, TÜİK, SPK).

It scrapes both "Yayımlananlar" and "Yayımlanacaklar" records and stores them in a Supabase PostgreSQL database.

## Features

-   **Targeted Scraping**: Fetches data for TCMB, BDDK, HMB, TÜİK, and SPK.
-   **Link Extraction**: Captures the source URL for each data item.
-   **Database Integration**: Stores data in a structured PostgreSQL database.
-   **Automation**: Includes a GitHub Actions workflow for manual triggering.
