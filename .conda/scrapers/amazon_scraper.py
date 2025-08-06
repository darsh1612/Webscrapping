import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_driver():
    """Initializes and returns a Selenium WebDriver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    return webdriver.Chrome(options=options)

def clean_price(price_text):
    """Extracts numeric value from price string, returns 'No price' if not found."""
    if not price_text:
        return "No price"
    cleaned = re.sub(r'[^\d.]', '', price_text.replace(',', ''))
    return cleaned if cleaned else "No price"

def scrape_amazon(query):
    """Scrapes product data from Amazon."""
    driver = get_driver()
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    driver.get(url)
    time.sleep(3)
    products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    for p in products[:20]:
        try:
            # Multiple title selectors for Amazon
            title_selectors = [
                ".//span[@class='a-size-medium a-color-base a-text-normal']",
                ".//h2[@class='s-result-item']//span",
                ".//h2//a//span[@class='a-size-base-plus']",
                ".//h2//span"
            ]
            title = "No title"
            for selector in title_selectors:
                try:
                    title = p.find_element(By.XPATH, selector).text
                    if title and title != "No title":
                        break
                except:
                    continue
        except:
            title = "No title"
            
        try:
            price = p.find_element(By.CLASS_NAME, "a-price-whole").text
        except:
            try:
                price = p.find_element(By.CLASS_NAME, "a-price-range").text
            except:
                price = "No price"
                
        try:
            image = p.find_element(By.TAG_NAME, "img").get_attribute("src")
        except:
            image = "No image"
            
        try:
            link = p.find_element(By.CLASS_NAME, "a-link-normal").get_attribute("href")
        except:
            link = "#"
            
        data["Title"].append(title)
        data["Price"].append(clean_price(price))
        data["Image"].append(image)
        data["Link"].append(link)
    driver.quit()
    return pd.DataFrame(data)