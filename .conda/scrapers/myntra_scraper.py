import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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

def scroll_page_fully(driver, scroll_times=8, wait_sec=2.5):
    """Scrolls down the page to trigger lazy loading of content."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_times):   
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_sec)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_myntra(query):
    """Scrapes product data from Myntra."""
    driver = get_driver()
    url = f"https://www.myntra.com/{query.replace(' ', '-')}"
    data = {"Title": [], "Price": [], "Image": [], "Rating": [], "Link": []}
    try:
        driver.get(url)
        scroll_page_fully(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.find_all("li", {"class": "product-base"})
        
        for item in items[:20]:
            title = item.find("h4", {"class": "product-product"}).text if item.find("h4", {"class": "product-product"}) else "No title"
            price_element = item.find("span", {"class": "product-discountedPrice"})
            price = price_element.text.replace("Rs. ", "") if price_element else (item.find("div", {"class": "product-price"}).text.replace("Rs. ", "") if item.find("div", {"class": "product-price"}) else "No price")
            image = item.find("img").get("src") if item.find("img") else "No image"
            rating_element = item.find("div", {"class": "product-ratingsContainer"})
            rating = float(rating_element.find("strong").text) if rating_element and rating_element.find("strong") else 0.0
            link_tag = item.find("a")
            link = f"https://www.myntra.com/{link_tag.get('href')}" if link_tag else "#"
            
            data["Title"].append(title)
            data["Price"].append(price)
            data["Image"].append(image)
            data["Rating"].append(rating)
            data["Link"].append(link)
    except Exception as e:
        print(f"An error occurred while scraping Myntra: {e}")
    finally:
        driver.quit()
    df = pd.DataFrame(data)
    df['Source'] = 'Myntra'
    return df