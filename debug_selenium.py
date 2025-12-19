"""
Debug: Check what elements are actually on the DartConnect page
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

match_url = "https://recap.dartconnect.com/matches/688e09b7f4fc02e124e7187f"

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.set_page_load_timeout(30)

try:
    print(f"Loading: {match_url}")
    driver.get(match_url)
    
    print("Waiting 5 seconds for JavaScript...")
    time.sleep(5)
    
    print("\n" + "=" * 80)
    print("PAGE TITLE:")
    print("=" * 80)
    print(driver.title)
    
    print("\n" + "=" * 80)
    print("PAGE SOURCE (first 1000 chars):")
    print("=" * 80)
    print(driver.page_source[:1000])
    
    print("\n" + "=" * 80)
    print("LOOKING FOR ELEMENTS:")
    print("=" * 80)
    
    # Check for various selectors
    selectors_to_check = [
        ("turn_stats class", "turn_stats"),
        ("cricketDarts class", "cricketDarts"),
        ("score-holder class", "score-holder"),
        ("table elements", "table"),
        ("tr elements", "tr"),
    ]
    
    from selenium.webdriver.common.by import By
    
    for name, class_name in selectors_to_check:
        elements = driver.find_elements(By.CLASS_NAME, class_name if '.' not in class_name else class_name.split('.')[1])
        print(f"{name}: {len(elements)} found")
    
    # Try finding by CSS selector
    print("\nTrying tbody > tr:")
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody > tr")
    print(f"  Found {len(rows)} rows")
    
    if rows:
        print(f"\n  First row HTML:")
        print(f"  {rows[0].get_attribute('outerHTML')[:200]}")
    
finally:
    driver.quit()
