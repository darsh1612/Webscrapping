import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

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

def scrape_flipkart(query):
    """Scrapes product data from Flipkart."""
    driver = get_driver()
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    driver.get(url)
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        product_selectors = [
            "div[data-id]", "div._1AtVbE", "div._13oc-S", 
            "div.s1Q9rs", "div._4ddWXP", "div.cPuFtr"
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 5:
                break
        
        for item in items[:20]:
            title = "No title"
            title_selectors = [
                "div._4rR01T", "a._1fQZEK", "div.s1Q9rs", "a.s1Q9rs",
                "div._2WkVRV", "a[title]", "h2 a", "div.KzDlHZ"
            ]
            
            for t_sel in title_selectors:
                try:
                    title_elem = item.select_one(t_sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True) or title_elem.get('title', '')
                        if title and len(title) > 3:
                            break
                except: continue
            
            price = "No price"
            price_selectors = [
                "div._30jeq3", "div._25b18c", "span._30jeq3", "div._1_WHN1",
                "div.Nx9bqj", "div._3I9_wc", "span._2_R_DZ"
            ]
            
            for p_sel in price_selectors:
                try:
                    price_elem = item.select_one(p_sel)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and '₹' in price_text:
                            price = clean_price(price_text)
                            break
                except: continue
            
            image = "No image"
            try:
                img_elem = item.select_one("img")
                if img_elem:
                    image = img_elem.get('src') or img_elem.get('data-src', 'No image')
            except: pass
            
            link = "#"
            try:
                link_elem = item.select_one('a[href*="/p/"]') or item.select_one('a._1fQZEK') or item.select_one('a[href]')
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    link = "https://www.flipkart.com" + href if href.startswith('/') else href
            except: pass
                
            data["Title"].append(title)
            data["Price"].append(price)
            data["Image"].append(image)
            data["Link"].append(link)

    except Exception as e:
        print(f"Error scraping Flipkart: {e}")
    finally:
        driver.quit()
        
    return pd.DataFrame(data)