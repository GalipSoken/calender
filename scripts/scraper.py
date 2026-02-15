import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scripts.database import get_db, TuikCalendar, create_tables
from datetime import datetime

class TuikScraper:
    def __init__(self):
        self.url = "https://www.tuik.gov.tr/Kurumsal/Veri_Takvimi"
        self.driver = None
        self.institutions = ["TCMB", "BDDK", "HMB", "TÜİK", "SPK"]
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver_path = ChromeDriverManager().install()
        # Fix for webdriver-manager returning THIRD_PARTY_NOTICES
        if "THIRD_PARTY_NOTICES" in driver_path:
            import os
            driver_path = os.path.dirname(driver_path) + "/chromedriver"
            
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def select_institution(self, institution_name):
        try:
            # Wait for search box or dropdown
            wait = WebDriverWait(self.driver, 10)
            
            # Using the search input as seen in browser inspection
            # Class: pl-5 mb-1 inputtext col-12
            # Placeholder: "Tarih, Yayın Adı veya Kurum Adını Ara ..."
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Kurum Adını Ara']")))
            search_box.clear()
            search_box.send_keys(institution_name)
            time.sleep(2) # Wait for filter to apply
            print(f"Filtered for {institution_name}")
            return True
        except Exception as e:
            print(f"Error selecting institution {institution_name}: {e}")
            return False

    def select_year(self, year):
        try:
            wait = WebDriverWait(self.driver, 10)
            # The year dropdown might be identified by text or specific attributes
            # Based on inspection, it's a dropdown button. We might need to click it and then select the year.
            # However, looking at the screenshot, it seems to be a standard dropdown.
            # Let's try to find the dropdown that contains the current year (e.g. 2026)
            
            # This is tricky because there are multiple dropdowns. 
            # We can try to find the button that likely shows the year.
            dropdowns = self.driver.find_elements(By.CLASS_NAME, "dropdown-toggle")
            year_dropdown = None
            for dd in dropdowns:
                if str(year) in dd.text or any(str(y) in dd.text for y in range(2020, 2030)):
                    year_dropdown = dd
                    break
            
            if year_dropdown:
                year_dropdown.click()
                time.sleep(1)
                # Now find the option with the text `year`
                # The options are likely in a sibling div with class dropdown-menu
                options = self.driver.find_elements(By.CLASS_NAME, "dropdown-item")
                for opt in options:
                    if str(year) == opt.text.strip():
                        opt.click()
                        time.sleep(2) # Wait for update
                        print(f"Selected year {year}")
                        return True
            
            print(f"Year {year} not found or already selected.")
            return False
        except Exception as e:
            print(f"Error selecting year {year}: {e}")
            return False

    def select_status(self, status):
        # status: "Yayımlananlar" or "Yayımlanacaklar"
        try:
            wait = WebDriverWait(self.driver, 10)
            dropdowns = self.driver.find_elements(By.CLASS_NAME, "dropdown-toggle")
            status_dropdown = None
            for dd in dropdowns:
                if "Yayımlan" in dd.text:
                    status_dropdown = dd
                    break
            
            if status_dropdown:
                if status in status_dropdown.text:
                    print(f"Status {status} already selected.")
                    return True

                status_dropdown.click()
                time.sleep(1)
                options = self.driver.find_elements(By.CLASS_NAME, "dropdown-item")
                for opt in options:
                    if status in opt.text:
                        opt.click()
                        time.sleep(2)
                        print(f"Selected status {status}")
                        return True
                        
            print(f"Status {status} selection failed.")
            return False
        except Exception as e:
            print(f"Error selecting status {status}: {e}")
            return False

    def parse_table(self, institution, status):
        data = []
        try:
            # Wait for potential load
            time.sleep(2)
            
            # Find all timeline items
            items = self.driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
            print(f"Debug: Found {len(items)} timeline items (before filtering)")

            for item in items:
                try:
                    # Extract Data
                    institution_element = item.find_element(By.CLASS_NAME, "card-title")
                    institution_name = institution_element.text.strip()
                    
                    # Verify institution matches (or is one of target if UI filter is broad)
                    # The UI filter might show other things? 
                    # If we searched for "TCMB", likely only TCMB.
                    # But let's check.
                    if institution != institution_name:
                        # Should we skip? 
                        # The user wants specific institutions. 
                        # If the scraper iterates "TCMB", and we see "TCMB", good.
                        # If we see "TÜİK", maybe we shouldn't add it to "TCMB" list?
                        # Actually, data is appended to a list.
                        pass
                        
                    description_element = item.find_element(By.CLASS_NAME, "box-item")
                    description = description_element.text.strip()
                    
                    # Date and Period
                    dt_div = item.find_element(By.CLASS_NAME, "dt")
                    date_element = dt_div.find_element(By.CLASS_NAME, "date")
                    date_text = date_element.text.strip() # "Tarih:16-02-2026 19:00:00"
                    
                    # Clean up date text
                    publish_date_str = date_text.replace("Tarih:", "").strip()
                    try:
                        publish_date = datetime.strptime(publish_date_str, "%d-%m-%Y %H:%M:%S")
                    except ValueError:
                         # Try another format or fallback?
                         print(f"Date parse error: {publish_date_str}")
                         continue

                    # Status mapping
                    db_status = "Yayımlandı" if status == "Yayımlananlar" else "Yayımlanacak"

                    # Extract URL
                    # The timeline-item usually contains an 'a' tag.
                    try:
                        link_element = item.find_element(By.TAG_NAME, "a")
                        data_url = link_element.get_attribute("href")
                        # Handle relative URLs if any, though usually absolute or handled by browser
                    except:
                        data_url = None

                    record = {
                        "kurum": institution_name,
                        "aciklama": description,
                        "tarih": publish_date,
                        "url": data_url,
                        "durum": db_status
                    }
                    data.append(record)
                
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue

            return data

        except Exception as e:
            print(f"Error parsing table: {e}")
            return []

    def save_to_db(self, data):
        db = next(get_db())
        count = 0
        try:
            for item in data:
                # Avoid duplicates? 
                # Check if exists (optional, or just insert)
                # User didn't specify unique constraint, but good practice.
                exists = db.query(TuikCalendar).filter_by(
                    tarih=item['tarih'], 
                    kurum=item['kurum'], 
                    aciklama=item['aciklama']
                ).first()
                
                if not exists:
                    record = TuikCalendar(**item)
                    db.add(record)
                    count += 1
            db.commit()
            print(f"Saved {count} new records to DB.")
        except Exception as e:
            db.rollback()
            print(f"Error saving to DB: {e}")
        finally:
            db.close()

    def run(self, years=[2026]):
        self.setup_driver()
        create_tables()
        
        try:
            self.driver.get(self.url)
            time.sleep(5) # Initial load
            
            for year in years:
                # Select Year first
                if not self.select_year(year):
                    continue

                for status in ["Yayımlananlar", "Yayımlanacaklar"]:
                    self.select_status(status)
                    
                    for inst in self.institutions: # "TCMB", "BDDK", etc.
                        self.select_institution(inst)
                        
                        # Parse
                        data = self.parse_table(inst, status)
                        print(f"Found {len(data)} records for {inst} - {year} - {status}")
                        
                        # Save
                        if data:
                            self.save_to_db(data)
                        
                        # Clear search for next institution
                        # self.select_institution("") # clears it?
                        
        finally:
            self.close_driver()

if __name__ == "__main__":
    scraper = TuikScraper()
    scraper.run(years=[2026])
