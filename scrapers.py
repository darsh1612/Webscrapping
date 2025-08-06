import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

def get_driver():
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

def scroll_page_fully(driver, scroll_times=8, wait_sec=2.5):
    """Scroll down to bottom to let JS/Lazy load finish."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_times):   
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(wait_sec)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached bottom of the page.")
            break
        last_height = new_height
    print("Scrolling complete.")


def scrape_amazon(query):
    """Scrapes product data from Amazon - keeping your working version."""
    driver = get_driver()
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    print(f"Scraping Amazon URL: {url}")
    driver.get(url) 
    # time.sleep(3)
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

def scrape_flipkart(query):
    """Improved Flipkart scraper with better selectors and longer wait times."""
    driver = get_driver()
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    print(f"Scraping Flipkart URL: {url}")
    driver.get(url)
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        # Longer wait time for Flipkart
        wait = WebDriverWait(driver, 20)
        # time.sleep(5)
        
        # Scroll to load more products
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        # time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Updated selectors for Flipkart 2024
        product_selectors = [
            "div[data-id]",  # Main product containers
            "div._1AtVbE",
            "div._13oc-S", 
            "div.s1Q9rs",
            "div._4ddWXP",
            "div.cPuFtr"  # Another common selector
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 5:  # Only use if we find a reasonable number of items
                print(f"Flipkart: Found {len(items)} items using: {selector}")
                break
        
        for item in items[:40]:
            # Title extraction with updated selectors
            title = "No title"
            title_selectors = [
                "div._4rR01T",
                "a._1fQZEK", 
                "div.s1Q9rs",
                "a.s1Q9rs",
                "div._2WkVRV",
                "a[title]",
                "h2 a",
                "div.KzDlHZ"  # Updated selector
            ]
            
            for t_sel in title_selectors:
                try:
                    title_elem = item.select_one(t_sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True) or title_elem.get('title', '')
                        if title and len(title) > 3:  # Ensure it's a meaningful title
                            break
                except:
                    continue
            
            # Price extraction with updated selectors
            price = "No price"
            price_selectors = [
                "div._30jeq3",
                "div._25b18c", 
                "span._30jeq3",
                "div._1_WHN1",
                "div.Nx9bqj",  # Updated selector
                "div._3I9_wc",  # Another price selector
                "span._2_R_DZ"  # Current price selector
            ]
            
            for p_sel in price_selectors:
                try:
                    price_elem = item.select_one(p_sel)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and '₹' in price_text:
                            price = clean_price(price_text)
                            break
                except:
                    continue
            
            # Image extraction
            image = "No image"
            try:
                img_elem = item.select_one("img")
                if img_elem:
                    image = img_elem.get('src') or img_elem.get('data-src', 'No image')
            except:
                pass
            
            # Link extraction
            link = "#"
            try:
                link_elem = item.select_one('a[href*="/p/"]')
                if not link_elem:
                    link_elem = item.select_one('a._1fQZEK')
                if not link_elem:
                    link_elem = item.select_one('a[href]')
                    
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    if href.startswith('/'):
                        link = "https://www.flipkart.com" + href
                    else:
                        link = href
            except:
                pass
                
            data["Title"].append(title)
            data["Price"].append(price)
            data["Image"].append(image)
            data["Link"].append(link)

    except Exception as e:
        print(f"Error scraping Flipkart: {e}")
    finally:
        driver.quit()
        
    return pd.DataFrame(data)

def scrape_myntra(query):
    driver = get_driver()
    url = f"https://www.myntra.com/{query.replace(' ', '-')}"
    print(f"Scraping Myntra URL: {url}")
    data = {"Title": [], "Price": [], "Image": [], "Rating": [], "Link": []}
    try:
        driver.get(url)
        scroll_page_fully(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.find_all("li", {"class": "product-base"})
        print(f"Found {len(items)} items on Myntra.")
        
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
        driver.save_screenshot("myntra_error.png")
    finally:
        driver.quit()
    df = pd.DataFrame(data)
    df['Source'] = 'Myntra'
    return df




def get_driverY():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def clean_priceY(text):
    import re
    num = re.sub(r'[^\d.]', '', text)
    return num if num else "No price"

def scrape_bewakoof(query):
    driver = get_driverY()
    url = f"https://www.bewakoof.com/search?q={query.replace(' ', '%20')}"
    driver.get(url)
    # time.sleep(5)

    # Scroll to load lazy content
    for _ in range(6):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        # time.sleep(2)

    page_html = driver.page_source   # get HTML before quitting
    driver.quit()

    soup = BeautifulSoup(page_html, "html.parser")


    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    cards = soup.select('a[data-testid="product-card-link"]')[:20]

    for card in cards:
        # Updated selectors for Levi's Shopify theme
        title_selectors = [
            'a.product-item__title',
            '.product-block__title-link',
            '.product-item-meta__title',
            'h3.product-title a',
            '.product-card__title',
            'a.full-unstyled-link'
        ]
        
        title_element = None
        for selector in title_selectors:
            title_element = card.select_one(selector)
            if title_element:
                break
        title = title_element.get_text(strip=True) if title_element else "No title"
        price = card.select_one('span.product-card-price').text.strip()
        image = card.select_one('img.product-card-image').get('src')
        link = card.get('href')
        data["Title"].append(title)
        data["Price"].append(clean_priceY(price))
        data["Image"].append(image)
        data["Link"].append(link)

    return pd.DataFrame(data)

def scrape_zara(query):
    """Improved Zara scraper with better image extraction for all products."""
    driver = get_driver()
    
    # Zara search URL format
    url = f"https://www.zara.com/in/en/search?searchTerm={query.replace(' ', '+')}"
    print(f"Scraping Zara URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 20)
        # time.sleep(5)
        
        # More aggressive scrolling to ensure ALL images load
        print("Starting enhanced scrolling for image loading...")
        
        # Scroll in smaller increments to trigger lazy loading
        for i in range(15):
            scroll_position = (i + 1) * (driver.execute_script("return document.body.scrollHeight") / 15)
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            # time.sleep(2)  # Wait for images to load
            
            # Check if new images are loading
            if i % 3 == 0:
                print(f"Scroll iteration {i+1}/15 - Loading images...")
        
        # Final scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(5)
        
        # Scroll back to top to ensure all content is processed
        driver.execute_script("window.scrollTo(0, 0);")
        # time.sleep(3)
        
        # Scroll down again slowly to trigger any remaining lazy loads
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        # time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(5)
        
        print("Enhanced scrolling complete. Extracting data...")
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Enhanced product selectors for Zara
        product_selectors = [
            "li.product-item",
            "div.product-item", 
            "article.product-item",
            "div[data-productid]",
            "li[data-productid]",
            "div.product-grid-product",
            "li.layout-product",
            "div._productContainer",
            "li._product",
            "div.product-card",
            "li.product-card",
            "article[data-productid]",
            "div.zds-item",
            "li.zds-item"
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 3:
                print(f"Zara: Found {len(items)} items using selector: {selector}")
                break
        
        # If still no items, try a more general approach
        if not items:
            # Look for any container that has both an image and some product-like attributes
            all_divs = soup.find_all(['div', 'li', 'article'])
            items = []
            for div in all_divs:
                if (div.find('img') and 
                    (any(keyword in str(div.get('class', [])).lower() for keyword in ['product', 'item', 'card']) or
                     div.get('data-productid') or
                     (div.find('a') and div.find(['h1', 'h2', 'h3', 'h4', 'p'])))):
                    items.append(div)
            print(f"Zara: Found {len(items)} items using fallback method")
        
        print(f"Processing {min(len(items), 20)} products...")
        
        for idx, item in enumerate(items[:20]):
            print(f"Processing product {idx + 1}/20...")
            
            # Enhanced title extraction
            title = "No title"
            title_selectors = [
                "p.product-name",
                "h2.product-name", 
                "h3.product-name",
                "div.product-name",
                "span.product-name",
                "a.product-link",
                "h2 a",
                "h3 a", 
                "h4 a",
                ".product-title",
                "p._productName",
                "h2._productName",
                "a[aria-label]",
                ".zds-product-name",
                "[data-testid*='product-name']"
            ]
            
            for t_sel in title_selectors:
                try:
                    title_elem = item.select_one(t_sel)
                    if title_elem:
                        title_text = title_elem.get_text(strip=True) or title_elem.get('aria-label', '')
                        if title_text and len(title_text) > 3:
                            title = title_text
                            break
                except:
                    continue
            
            # More aggressive fallback for title
            if title == "No title":
                for tag in ['a', 'h1', 'h2', 'h3', 'h4', 'p', 'span']:
                    try:
                        elem = item.find(tag)
                        if elem and elem.get_text(strip=True):
                            potential_title = elem.get_text(strip=True)
                            if 10 <= len(potential_title) <= 100 and not any(skip in potential_title.lower() 
                                for skip in ['price', 'add to', 'size', 'color']):
                                title = potential_title
                                break
                    except:
                        continue
            
            # Enhanced price extraction
            price = "No price"
            price_selectors = [
                "span.price",
                "div.price",
                "p.price",
                "span.product-price",
                "div.product-price",
                "span._price",
                "div._price",
                "span[data-price]",
                "div[data-price]",
                ".price-current",
                ".current-price",
                ".zds-price",
                "[data-testid*='price']",
                ".price-sale",
                ".money"
            ]
            
            for p_sel in price_selectors:
                try:
                    price_elem = item.select_one(p_sel)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and ('₹' in price_text or '$' in price_text or '€' in price_text or 
                                         any(c.isdigit() for c in price_text)):
                            price = clean_price(price_text)
                            break
                except:
                    continue
            
            # Enhanced image extraction with multiple fallback strategies
            image = "No image"
            
            # Strategy 1: Look for main product images with common patterns
            img_selectors = [
                "img.product-image",
                "img.media-image",
                "img[data-src]",
                "img[src*='product']",
                "img[alt*='product']", 
                "picture img",
                ".product-media img",
                ".media-wrapper img",
                "img[data-testid*='product']",
                "img.zds-image"
            ]
            
            for img_sel in img_selectors:
                try:
                    img_elem = item.select_one(img_sel)
                    if img_elem:
                        # Try multiple image source attributes
                        img_src = (img_elem.get('data-src') or 
                                 img_elem.get('src') or 
                                 img_elem.get('data-original') or
                                 img_elem.get('data-lazy-src') or
                                 img_elem.get('data-srcset', '').split()[0] if img_elem.get('data-srcset') else None)
                        
                        if img_src and img_src != "No image" and len(img_src) > 10:
                            image = img_src
                            break
                except:
                    continue
            
            # Strategy 2: If no image found, get the first image in the item
            if image == "No image":
                try:
                    all_imgs = item.find_all('img')
                    for img in all_imgs:
                        img_src = (img.get('data-src') or 
                                 img.get('src') or 
                                 img.get('data-original') or
                                 img.get('data-lazy-src'))
                        
                        if (img_src and 
                            len(img_src) > 10 and 
                            not any(skip in img_src.lower() for skip in ['icon', 'logo', 'sprite']) and
                            any(ext in img_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                            image = img_src
                            break
                except:
                    pass
            
            # Strategy 3: Look in srcset attribute
            if image == "No image":
                try:
                    img_elem = item.find('img')
                    if img_elem and img_elem.get('srcset'):
                        srcset = img_elem.get('srcset')
                        # Get the first URL from srcset
                        first_src = srcset.split(',')[0].strip().split()[0]
                        if first_src and len(first_src) > 10:
                            image = first_src
                except:
                    pass
            
            # Fix relative URLs
            if image and image != "No image" and not image.startswith('http'):
                if image.startswith('//'):
                    image = 'https:' + image
                elif image.startswith('/'):
                    image = 'https://www.zara.com' + image
                else:
                    image = 'https://www.zara.com/' + image
            
            # Enhanced link extraction
            link = "#"
            link_selectors = [
                'a[href*="/product/"]',
                'a.product-link',
                'a[data-productid]',
                'a[href*="/p/"]',
                'a[href]'
            ]
            
            for link_sel in link_selectors:
                try:
                    link_elem = item.select_one(link_sel)
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        if href.startswith('/'):
                            link = "https://www.zara.com" + href
                        elif href.startswith('http'):
                            link = href
                        else:
                            link = "https://www.zara.com/" + href
                        break
                except:
                    continue
            
            # Only add if we have some meaningful data
            if title != "No title" or price != "No price" or image != "No image":
                data["Title"].append(title)
                data["Price"].append(price)
                data["Image"].append(image)
                data["Link"].append(link)
                
                print(f"Product {idx + 1}: Title={title[:30]}{'...' if len(title) > 30 else ''}, "
                      f"Price={price}, Image={'Found' if image != 'No image' else 'Not found'}")
            else:
                print(f"Product {idx + 1}: Skipped - insufficient data")
    
    except Exception as e:
        print(f"Error scraping Zara: {e}")
        try:
            driver.save_screenshot("zara_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'Zara'
    print(f"Zara scraping complete. Successfully scraped {len(df)} products.")
    
    # Print summary of image extraction success
    images_found = len([img for img in df['Image'] if img != 'No image'])
    print(f"Images found: {images_found}/{len(df)} products")
    
    return df
    

import json
from urllib.parse import quote

def clean_price(price_text):
    """Enhanced price cleaning function"""
    if not price_text:
        return "No price"
    
    # Remove extra whitespace and newlines
    price_text = re.sub(r'\s+', ' ', price_text.strip())
    
    # Extract price using regex - handle multiple currencies
    price_patterns = [
        r'₹\s*[\d,]+\.?\d*',  # Indian Rupees
        r'Rs\.?\s*[\d,]+\.?\d*',  # Rupees alternative
        r'\$\s*[\d,]+\.?\d*',  # USD
        r'[\d,]+\.?\d*\s*₹',  # Number before currency
        r'[\d,]+\.?\d*\s*Rs',  # Number before Rs
        r'[\d,]+\.?\d*',  # Just numbers (fallback)
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, price_text)
        if match:
            return match.group().strip()
    
    return price_text.strip() if price_text.strip() else "No price"

def advanced_lazy_loading_scroll(driver, max_scrolls=15, scroll_pause=3):
    """
    Advanced scrolling function specifically designed for H&M's lazy loading.
    Scrolls slowly and waits for images to load at each step.
    """
    print("Starting advanced lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_images_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        # time.sleep(scroll_pause)
        
        # Check how many images have loaded
        images_with_src = driver.execute_script("""
            return document.querySelectorAll('img[src]:not([src=""])').length;
        """)
        
        if images_with_src > loaded_images_count:
            loaded_images_count = images_with_src
            print(f"Scroll {i+1}/{max_scrolls}: {loaded_images_count} images loaded")
        
        # Check if page height changed (more content loaded)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Try a few more scrolls to ensure everything is loaded
            if i > max_scrolls - 5:
                print("Page height stabilized, finishing scroll...")
                break
        else:
            last_height = new_height
    
    # Final scroll to bottom and back to top
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(scroll_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    # time.sleep(2)
    
    # Trigger any remaining lazy loads with a middle scroll
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    # time.sleep(2)
    
    final_images = driver.execute_script("""
        return document.querySelectorAll('img[src]:not([src=""])').length;
    """)
    print(f"Advanced scrolling complete. Total images loaded: {final_images}")

def force_lazy_image_loading(driver):
    """
    Force load lazy images by triggering their data-src to src conversion
    """
    try:
        # Execute JavaScript to force load images with data-src
        driver.execute_script("""
            // Force load images with data-src attributes
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => {
                if (img.dataset.src && !img.src.includes(img.dataset.src)) {
                    img.src = img.dataset.src;
                }
            });
            
            // Also try other common lazy loading patterns
            const lazyImages2 = document.querySelectorAll('img[data-original]');
            lazyImages2.forEach(img => {
                if (img.dataset.original && !img.src.includes(img.dataset.original)) {
                    img.src = img.dataset.original;
                }
            });
            
            // Force visibility check for intersection observer
            const allImages = document.querySelectorAll('img');
            allImages.forEach(img => {
                img.scrollIntoView({ behavior: 'auto', block: 'center' });
            });
        """)
        time.sleep(2)
        print("Forced lazy image loading completed")
    except Exception as e:
        print(f"Error in forced lazy loading: {e}")

def extract_price_from_element(item):
    """
    Enhanced price extraction with H&M-specific selectors and debugging
    """
    price = "No price"
    
    # H&M-specific price selectors (updated for 2024)
    price_selectors = [
        # Standard H&M price selectors
        'span.price-value',
        'div.price-value',
        'p.price-value',
        '.item-price .price-value',
        '.price .price-value',
        
        # General price selectors
        '.item-price',
        '.price',
        '.product-price',
        '.price-current',
        '.current-price',
        '.regular-price',
        '.sale-price',
        
        # Currency-specific selectors
        'span[class*="price"]',
        'div[class*="price"]',
        'p[class*="price"]',
        
        # Data attribute selectors
        'span[data-price]',
        'div[data-price]',
        '[data-testid*="price"]',
        
        # More specific H&M patterns
        '.item-details .price',
        '.product-tile .price',
        '.hm-product-item .price',
        '.plp-product .price',
        
        # Fallback selectors
        'span.money',
        'div.money',
        'strong.price',
        'em.price',
        'b[class*="price"]',
        'span[title*="price"]'
    ]
    
    # Try each selector
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                # Get text content
                price_text = price_elem.get_text(strip=True)
                
                # Also check for price in attributes
                if not price_text:
                    price_text = (price_elem.get('data-price') or 
                                price_elem.get('title') or 
                                price_elem.get('aria-label') or '')
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                 any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_price(price_text)
                    if cleaned_price != "No price":
                        print(f"Found price using selector '{selector}': {cleaned_price}")
                        return cleaned_price
        except Exception as e:
            continue
    
    # Additional strategy: Look for any element containing currency symbols
    try:
        all_text_elements = item.find_all(text=True)
        for text in all_text_elements:
            text_str = str(text).strip()
            if text_str and ('₹' in text_str or 'Rs' in text_str or '$' in text_str):
                # Check if this looks like a price
                if re.search(r'[₹$Rs].*\d+|\d+.*[₹$Rs]', text_str):
                    cleaned_price = clean_price(text_str)
                    if cleaned_price != "No price":
                        print(f"Found price in text content: {cleaned_price}")
                        return cleaned_price
    except:
        pass
    
    # Final strategy: Look for patterns in all text within the item
    try:
        full_text = item.get_text()
        # Look for price patterns in the full text
        price_patterns = [
            r'₹\s*[\d,]+\.?\d*',
            r'Rs\.?\s*[\d,]+\.?\d*',
            r'\$\s*[\d,]+\.?\d*',
            r'INR\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*₹',
            r'[\d,]+\.?\d*\s*Rs'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # Take the first reasonable match
                for match in matches:
                    if any(c.isdigit() for c in match):
                        cleaned_price = clean_price(match)
                        if cleaned_price != "No price":
                            print(f"Found price using regex pattern: {cleaned_price}")
                            return cleaned_price
    except:
        pass
    
    return price

def debug_price_extraction(driver, item_index=0):
    """
    Debug function to inspect the HTML structure for price extraction
    """
    try:
        # Get page source and parse
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find product items
        product_selectors = [
            'article.hm-product-item',
            'div.product-item',
            'li.product-item',
            'article[data-articlecode]',
            'div[data-articlecode]'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if items:
                print(f"Found items using selector: {selector}")
                break
        
        if not items:
            print("No product items found for debugging")
            return
        
        if item_index >= len(items):
            item_index = 0
        
        item = items[item_index]
        print(f"\n=== DEBUGGING ITEM {item_index + 1} ===")
        print(f"Item classes: {item.get('class', [])}")
        print(f"Item HTML (first 500 chars):\n{str(item)[:500]}...")
        
        # Look for all elements that might contain price
        potential_price_elements = item.find_all(['span', 'div', 'p', 'strong', 'em'])
        
        print(f"\n=== POTENTIAL PRICE ELEMENTS ===")
        for i, elem in enumerate(potential_price_elements[:10]):  # Show first 10
            text = elem.get_text(strip=True)
            classes = elem.get('class', [])
            if text:
                print(f"{i+1}. Tag: {elem.name}, Classes: {classes}, Text: '{text}'")
        
        # Show all text content
        all_text = item.get_text()
        print(f"\n=== ALL TEXT CONTENT ===")
        print(all_text[:300] + "..." if len(all_text) > 300 else all_text)
        
    except Exception as e:
        print(f"Error in debug function: {e}")

def scrape_hnm(query):
    """
    Enhanced H&M scraper with improved price detection and debugging
    """
    driver = get_driver()
    
    # H&M India search URL structure
    encoded_query = quote(query)
    url = f"https://www2.hm.com/en_in/search-results.html?q={encoded_query}"
    print(f"Scraping H&M URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 20)
        # time.sleep(5)
        
        # Advanced lazy loading scroll
        advanced_lazy_loading_scroll(driver, max_scrolls=20, scroll_pause=3)
        
        # Force load any remaining lazy images
        force_lazy_image_loading(driver)
        
        # Additional wait to ensure all content is loaded
        # time.sleep(5)
        
        # Debug the first item to understand structure
        print("\n=== DEBUGGING PRICE STRUCTURE ===")
        debug_price_extraction(driver, item_index=0)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Method 1: Try to extract data from __NEXT_DATA__ JSON
        products_from_json = []
        try:
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            if next_data_script:
                json_data = json.loads(next_data_script.string)
                
                # Try different JSON paths where products might be stored
                possible_paths = [
                    ['props', 'pageProps', 'searchResults', 'products'],
                    ['props', 'pageProps', 'products'],
                    ['props', 'initialProps', 'searchResults', 'products'],
                    ['props', 'pageProps', 'searchResults', 'results'],
                    ['props', 'pageProps', 'plpResults', 'products'],
                    ['props', 'pageProps', 'productListPage', 'products'],
                    ['props', 'pageProps', 'category', 'products']
                ]
                
                for path in possible_paths:
                    try:
                        temp_data = json_data
                        for key in path:
                            temp_data = temp_data[key]
                        if temp_data and isinstance(temp_data, list) and len(temp_data) > 0:
                            products_data = temp_data
                            print(f"Found {len(products_data)} products in JSON path: {' -> '.join(path)}")
                            
                            for product in products_data:
                                try:
                                    title = product.get('title', product.get('name', product.get('productName', 'No title')))
                                    
                                    # Enhanced price extraction from JSON with more fields
                                    price = "No price"
                                    price_fields = [
                                        'price', 'priceValue', 'currentPrice', 'sellingPrice', 
                                        'displayPrice', 'formattedPrice', 'listPrice', 'retailPrice',
                                        'whitePrice', 'redPrice', 'originalPrice', 'salePrice'
                                    ]
                                    
                                    for field in price_fields:
                                        if field in product:
                                            price_data = product[field]
                                            if isinstance(price_data, dict):
                                                # Try different keys within the price object
                                                price_keys = ['value', 'current', 'price', 'amount', 'display', 'formatted']
                                                for key in price_keys:
                                                    if key in price_data and price_data[key]:
                                                        price = clean_price(str(price_data[key]))
                                                        if price != "No price":
                                                            break
                                                if price != "No price":
                                                    break
                                            elif isinstance(price_data, (str, int, float)):
                                                price = clean_price(str(price_data))
                                                if price != "No price":
                                                    break
                                    
                                    # Enhanced image extraction from JSON
                                    image = "No image"
                                    image_fields = ['images', 'image', 'mainImage', 'defaultImage', 'thumbnail']
                                    for field in image_fields:
                                        if field in product:
                                            img_data = product[field]
                                            if isinstance(img_data, list) and img_data:
                                                img_obj = img_data[0]
                                                if isinstance(img_obj, dict):
                                                    image = (img_obj.get('url') or 
                                                           img_obj.get('src') or 
                                                           img_obj.get('href'))
                                                else:
                                                    image = str(img_obj)
                                                if image and image != "No image":
                                                    break
                                            elif isinstance(img_data, str):
                                                image = img_data
                                                break
                                    
                                    # Fix image URLs
                                    if image and image != "No image" and not image.startswith('http'):
                                        if image.startswith('//'):
                                            image = 'https:' + image
                                        elif image.startswith('/'):
                                            image = 'https://www2.hm.com' + image
                                    
                                    # Link extraction from JSON
                                    link = "#"
                                    link_fields = ['url', 'link', 'href', 'productUrl']
                                    for field in link_fields:
                                        if field in product and product[field]:
                                            link = product[field]
                                            break
                                    
                                    if link == "#" and ('articleNumber' in product or 'id' in product or 'productId' in product):
                                        product_id = (product.get('articleNumber') or 
                                                    product.get('id') or 
                                                    product.get('productId'))
                                        if product_id:
                                            link = f"https://www2.hm.com/en_in/productpage.{product_id}.html"
                                    
                                    # Fix relative URLs
                                    if link and link != "#" and not link.startswith('http'):
                                        if link.startswith('/'):
                                            link = 'https://www2.hm.com' + link
                                        else:
                                            link = 'https://www2.hm.com/' + link
                                    
                                    products_from_json.append({
                                        'title': title,
                                        'price': price,
                                        'image': image,
                                        'link': link
                                    })
                                    
                                except Exception as e:
                                    print(f"Error processing JSON product: {e}")
                                    continue
                            break
                    except (KeyError, TypeError):
                        continue
                        
        except Exception as e:
            print(f"Error extracting from JSON: {e}")
        
        # Method 2: Enhanced HTML parsing with improved price extraction
        html_products = []
        
        print("\n=== STARTING HTML PARSING ===")
        
        # Enhanced H&M product selectors
        product_selectors = [
            'article.hm-product-item',
            'div.product-item',
            'li.product-item', 
            'article[data-articlecode]',
            'div[data-articlecode]',
            'li[data-articlecode]',
            'article.product-tile',
            'div.product-tile',
            'li.product-tile',
            'article.plp-product-item',
            'div.item-product',
            'li.item-product',
            'div.product-card',
            'article.product-card',
            'li[data-product-id]',
            'div[data-product-id]',
            'article[data-product-id]',
            'div.js-product-tile',
            'li.js-product-tile'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 3:
                print(f"H&M: Found {len(items)} items using selector: {selector}")
                break
        
        # If no specific selectors work, try a more general approach
        if not items:
            print("Trying fallback selectors...")
            potential_items = soup.find_all(['article', 'div', 'li'])
            items = []
            for item in potential_items:
                if (item.find('img') and 
                    (item.find('a') or item.find(['h1', 'h2', 'h3', 'h4'])) and
                    (any(cls for cls in item.get('class', []) if 'product' in cls.lower()) or
                     item.get('data-articlecode') or
                     item.get('data-product-id'))):
                    items.append(item)
            print(f"Found {len(items)} items using fallback method")
        
        print(f"Processing {min(len(items), 25)} products...")
        
        for idx, item in enumerate(items[:25]):
            try:
                # Enhanced title extraction (keeping existing logic)
                title = "No title"
                title_selectors = [
                    'h3.item-heading a',
                    'h3.item-heading',
                    'h2.product-item-headline a',
                    'h2.product-item-headline',
                    'a.item-link',
                    'h3 a[data-name]',
                    'h3[data-name]',
                    'a.link',
                    '.item-details h3',
                    '.product-title',
                    'h3.pdp-product-name',
                    '.item-heading-text',
                    'h4.item-heading',
                    'span.item-heading',
                    'div.item-heading',
                    'a[title]',
                    'h2 a',
                    'h3 a',
                    'h4 a'
                ]
                
                for t_sel in title_selectors:
                    try:
                        title_elem = item.select_one(t_sel)
                        if title_elem:
                            title_text = (title_elem.get_text(strip=True) or 
                                        title_elem.get('data-name', '') or
                                        title_elem.get('title', '') or
                                        title_elem.get('alt', ''))
                            if title_text and len(title_text) > 3:
                                title = title_text
                                break
                    except:
                        continue
                
                # If still no title, try more aggressive extraction
                if title == "No title":
                    for tag in ['a', 'h1', 'h2', 'h3', 'h4', 'span', 'div']:
                        try:
                            elem = item.find(tag)
                            if elem:
                                text = elem.get_text(strip=True)
                                if (text and 10 <= len(text) <= 100 and 
                                    not any(skip in text.lower() for skip in 
                                           ['price', '₹', '$', 'add to', 'size', 'color', 'sale', 'new'])):
                                    title = text
                                    break
                        except:
                            continue
                
                # IMPROVED PRICE EXTRACTION
                print(f"\n--- Processing item {idx + 1}: {title[:30]}... ---")
                price = extract_price_from_element(item)
                
                # Enhanced image extraction (keeping existing logic)
                image = "No image"
                
                # Strategy 1: Look for images with actual src (loaded images)
                try:
                    imgs = item.find_all('img')
                    for img in imgs:
                        src = img.get('src', '')
                        if (src and len(src) > 10 and 
                            not any(skip in src.lower() for skip in ['placeholder', 'blank', 'loading']) and
                            any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                            image = src
                            break
                except:
                    pass
                
                # Strategy 2: Look for data-src attributes (lazy loaded)
                if image == "No image":
                    try:
                        imgs = item.find_all('img')
                        for img in imgs:
                            data_src = (img.get('data-src') or 
                                      img.get('data-original') or 
                                      img.get('data-lazy-src'))
                            if (data_src and len(data_src) > 10 and
                                any(ext in data_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                                image = data_src
                                break
                    except:
                        pass
                
                # Strategy 3: Look in srcset
                if image == "No image":
                    try:
                        img_elem = item.find('img')
                        if img_elem and img_elem.get('srcset'):
                            srcset = img_elem.get('srcset')
                            first_src = srcset.split(',')[0].strip().split()[0]
                            if first_src and len(first_src) > 10:
                                image = first_src
                    except:
                        pass
                
                # Fix relative image URLs
                if image and image != "No image" and not image.startswith('http'):
                    if image.startswith('//'):
                        image = 'https:' + image
                    elif image.startswith('/'):
                        image = 'https://www2.hm.com' + image
                    else:
                        image = 'https://www2.hm.com/' + image
                
                # Enhanced link extraction (keeping existing logic)
                link = "#"
                link_selectors = [
                    'a.item-link',
                    'h3 a',
                    'h2 a',
                    'h4 a',
                    'a[href*="productpage"]',
                    'a[href*="/product/"]',
                    'a[href*="/p/"]',
                    'a[data-articlecode]',
                    'a[href]'
                ]
                
                for link_sel in link_selectors:
                    try:
                        link_elem = item.select_one(link_sel)
                        if link_elem and link_elem.get('href'):
                            href = link_elem['href']
                            if href.startswith('/'):
                                link = "https://www2.hm.com" + href
                            elif href.startswith('http'):
                                link = href
                            else:
                                link = "https://www2.hm.com/" + href
                            break
                    except:
                        continue
                
                # Only add products with meaningful data
                if (title != "No title" or price != "No price" or image != "No image"):
                    html_products.append({
                        'title': title,
                        'price': price,
                        'image': image,
                        'link': link
                    })
                    
                    print(f"✓ Product {idx + 1}: Title={title[:40]}{'...' if len(title) > 40 else ''}, "
                          f"Price={price}, Image={'✓' if image != 'No image' else '✗'}")
                
            except Exception as e:
                print(f"Error processing HTML product {idx + 1}: {e}")
                continue
        
        # Combine results, prioritizing JSON data if available and sufficient
        if products_from_json and len(products_from_json) >= 10:
            all_products = products_from_json
            print(f"Using JSON data: {len(all_products)} products")
        else:
            all_products = html_products
            print(f"Using HTML parsing: {len(all_products)} products")
        
        # If we have both but neither is sufficient, combine them
        if len(all_products) < 10 and products_from_json and html_products:
            combined = products_from_json + html_products
            seen_titles = set()
            unique_products = []
            for product in combined:
                title_lower = product['title'].lower()[:30]
                if title_lower not in seen_titles and product['title'] != "No title":
                    seen_titles.add(title_lower)
                    unique_products.append(product)
            all_products = unique_products
            print(f"Combined unique products: {len(all_products)}")
        
        # Populate the data dictionary
        for product in all_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print summary
        images_found = len([img for img in data['Image'] if img != 'No image'])
        prices_found = len([price for price in data['Price'] if price != 'No price'])
        print(f"\n=== H&M SCRAPING SUMMARY ===")
        print(f"Total products: {len(all_products)}")
        print(f"Images found: {images_found}")
        print(f"Prices found: {prices_found}")
        print(f"Success rate - Images: {images_found/len(all_products)*100:.1f}%" if all_products else "0%")
        print(f"Success rate - Prices: {prices_found/len(all_products)*100:.1f}%" if all_products else "0%")
        
    except Exception as e:
        print(f"Error scraping H&M: {e}")
        try:
            driver.save_screenshot("hm_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'H&M'
    return df



import json
import time
import pandas as pd
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
# Note: You need to have a get_driver() function defined elsewhere in your code.
# from your_utility_module import get_driver, shopify_lazy_loading_scroll, extract_shopify_price, clean_price

def scrape_levis(query):
    """
    Enhanced Levi's India scraper - levi.in is Shopify-based
    Different from H&M structure, uses Shopify's search system
    """
    driver = get_driver()
    
    # Levi's India search URL structure (Shopify-based)
    encoded_query = quote(query)
    url = f"https://levi.in/search?q={encoded_query}"
    print(f"Scraping Levi's URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 15)
        # time.sleep(3)
        
        # Shopify lazy loading scroll (different approach than H&M)
        shopify_lazy_loading_scroll(driver, max_scrolls=10, scroll_pause=2)
        
        # Additional wait for Shopify AJAX
        # time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Method 1: Try to extract from Shopify JSON data
        products_from_json = []
        try:
            # Look for Shopify product data in various script tags
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    # Ensure script.string is not None before loading
                    if script.string:
                        json_data = json.loads(script.string)
                        if 'products' in json_data and isinstance(json_data['products'], list):
                            products_data = json_data['products']
                            print(f"Found {len(products_data)} products in Shopify JSON")
                            
                            for product in products_data:
                                try:
                                    title = product.get('title', 'No title')
                                    
                                    # Shopify price extraction from JSON
                                    price = "No price"
                                    if 'price' in product:
                                        price_value = product['price']
                                        if isinstance(price_value, (int, float)):
                                            # Convert from paise to rupees
                                            price = f"₹{price_value/100:.0f}"
                                    elif 'variants' in product and product.get('variants'):
                                        variant = product['variants'][0]
                                        if 'price' in variant:
                                            price_value = variant['price']
                                            if isinstance(price_value, str):
                                                price_value = float(price_value.replace(',', ''))
                                            if isinstance(price_value, (int, float)):
                                                 # Convert from paise to rupees
                                                price = f"₹{price_value/100:.0f}"

                                    # Shopify image extraction from JSON
                                    image = "No image"
                                    if product.get('featured_image'):
                                        image = product['featured_image']
                                        if not image.startswith('http'):
                                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                                    elif product.get('images'):
                                        image = product['images'][0]
                                        if not image.startswith('http'):
                                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                                    
                                    # Shopify URL/handle from JSON
                                    link = "#"
                                    if 'handle' in product:
                                        link = f"https://levi.in/products/{product['handle']}"
                                    elif 'url' in product:
                                        link = f"https://levi.in{product['url']}"
                                    
                                    products_from_json.append({
                                        'title': title, 'price': price, 'image': image, 'link': link
                                    })
                                    
                                except Exception as e:
                                    print(f"Error processing Shopify JSON product: {e}")
                                    continue
                            # Once we find a valid product list in JSON, we can stop
                            if products_from_json:
                                break 
                except json.JSONDecodeError:
                    continue # Ignore scripts that are not valid JSON
                except Exception as e:
                    print(f"Error parsing script tag: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting from Shopify JSON: {e}")

        # Method 2: HTML parsing with Shopify-specific selectors
        html_products = []
        
        print("\n=== STARTING SHOPIFY HTML PARSING ===")
        
        product_selectors = [
            '.product-item', '.product-card', 'article.product-item', 'div.product-item',
            'li.product-item', '.grid-item', '.grid-product', 'article.grid-item',
            'div.grid-item', '.product', '.product-block', '.product-tile', 'article.product',
            'div.product', '.collection-item', '.search-item', 'article.collection-item',
            '[data-product-id]', '[data-product-handle]', '.js-product-item'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 3:
                print(f"Levi's: Found {len(items)} items using selector: {selector}")
                break
        
        if not items:
            print("Trying Shopify fallback selectors...")
            potential_items = soup.find_all(['div', 'article', 'li'])
            items = []
            for item in potential_items:
                if (item.find('img') and 
                    item.find('a') and
                    (any(cls for cls in item.get('class', []) if 'product' in cls.lower()) or
                     item.get('data-product-id') or item.get('data-product-handle') or
                     (item.find(['h2', 'h3', 'h4']) and
                     (item.find(class_=lambda x: x and 'price' in x.lower()) or
                      item.find(text=lambda x: x and '₹' in str(x)))))):
                    items.append(item)
            print(f"Found {len(items)} items using Shopify fallback method")
        
        print(f"Processing {min(len(items), 25)} products...")
        
        for idx, item in enumerate(items[:25]):
            try:
                # Use the new title extraction function
                title = extract_levis_title(item, idx + 1)
                
                print(f"\n--- Processing Levi's item {idx + 1}: {title[:30]}... ---")
                
                price = extract_shopify_price(item)
                
                image = "No image"
                # Logic to find image (from your original code)
                all_imgs = item.find_all('img')
                for img in all_imgs:
                    src = img.get('data-src') or img.get('src')
                    if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        image = src.split('?')[0] # Clean up URL params
                        if not image.startswith('http'):
                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                        break
                        
                link = "#"
                # Logic to find link (from your original code)
                link_elem = item.find('a', href=lambda href: href and "/products/" in href)
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('/'):
                        link = "https://levi.in" + href
                    elif href.startswith('http'):
                        link = href
                
                if title != "No title" or price != "No price":
                    html_products.append({'title': title, 'price': price, 'image': image, 'link': link})
                    print(f"✓ Product {idx + 1}: Title={title[:40]}{'...' if len(title) > 40 else ''}, "
                          f"Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            
            except Exception as e:
                print(f"Error processing Levi's HTML product {idx + 1}: {e}")
                continue
        
        # Combine results
        if products_from_json and len(products_from_json) >= 5:
            all_products = products_from_json
            print(f"\nUsing Shopify JSON data: {len(all_products)} products")
        else:
            all_products = html_products
            print(f"\nUsing HTML parsing: {len(all_products)} products")
        
        # Populate the data dictionary
        for product in all_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print summary
        if all_products:
            images_found = len([img for img in data['Image'] if img != 'No image'])
            prices_found = len([price for price in data['Price'] if price != 'No price'])
            titles_found = len([title for title in data['Title'] if title != 'No title'])
            print(f"\n=== LEVI'S SCRAPING SUMMARY ===")
            print(f"Total products: {len(all_products)}")
            print(f"Titles found: {titles_found}")
            print(f"Images found: {images_found}")
            print(f"Prices found: {prices_found}")
            print(f"Success rate - Titles: {titles_found/len(all_products)*100:.1f}%")
            print(f"Success rate - Images: {images_found/len(all_products)*100:.1f}%")
            print(f"Success rate - Prices: {prices_found/len(all_products)*100:.1f}%")
        
    except Exception as e:
        print(f"An error occurred in scrape_levis: {e}")
        try:
            driver.save_screenshot("levis_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = "Levi's"
    return df


def extract_levis_title(item, item_index):
    """
    Extracts the title from a Levi's product item using a list of CSS selectors,
    with a fallback to a generic title if none is found.
    """
    # Selector from user screenshot is prioritized.
    title_selectors = [
        '.st-name span',
        'a.product-item__title',
        '.product-block__title-link',
        '.product-item-meta__title',
        'h3.product-title a',
        '.product-card__title',
        'a.full-unstyled-link',
        '.card__heading a',
        'h2.product-title'
    ]

    for selector in title_selectors:
        title_element = item.select_one(selector)
        if title_element:
            title = title_element.get_text(strip=True)
            if title and len(title) > 5:
                return title
    
    # Fallback to a generated title if no selector works
    print(f"Could not find title for item {item_index}, generating placeholder.")
    return f"Levi's Product {item_index + 1}"

def shopify_lazy_loading_scroll(driver, max_scrolls=10, scroll_pause=2):
    """
    Shopify-specific scrolling function
    Shopify sites often load content differently than other platforms
    """
    print("Starting Shopify lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for i in range(max_scrolls):
        # Scroll down gradually
        scroll_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        
        # Wait for Shopify AJAX requests
        # time.sleep(scroll_pause)
        
        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height and i > max_scrolls - 3:
            print("No new content loading, finishing scroll...")
            break
        else:
            last_height = new_height
        
        print(f"Shopify scroll {i+1}/{max_scrolls}")
    
    # Final scroll to ensure all content is loaded
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(scroll_pause)
    
    print("Shopify scrolling complete")


def extract_shopify_price(item):
    """
    Shopify-specific price extraction for Levi's
    """
    price = "No price"
    
    # Shopify price selectors
    price_selectors = [
        # Standard Shopify price classes
        '.price',
        '.product-price',
        '.money',
        'span.money',
        'div.money',
        '.price-current',
        '.current-price',
        '.regular-price',
        '.sale-price',
        
        # Shopify theme-specific
        '.price-item',
        '.price-regular',
        '.product-price-current',
        '.grid-item-price',
        '.item-price',
        
        # Levi's Shopify specific
        '.product-info .price',
        '.product-details .price',
        '.product-form .price',
        
        # Generic Shopify patterns
        '[data-price]',
        'span[class*="price"]',
        'div[class*="price"]',
        'span[class*="money"]',
        'div[class*="money"]'
    ]
    
    # Try each selector
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                # Also check data attributes
                if not price_text:
                    price_text = (price_elem.get('data-price') or 
                                price_elem.get('data-money') or '')
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                 any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_price(price_text)
                    if cleaned_price != "No price":
                        print(f"Found Shopify price using selector '{selector}': {cleaned_price}")
                        return cleaned_price
        except Exception as e:
            continue
    
    # Shopify-specific: Look for price in JSON-LD or microdata
    try:
        # Check for price in any span/div containing currency
        all_spans = item.find_all(['span', 'div', 'p'])
        for span in all_spans:
            text = span.get_text(strip=True)
            if text and re.search(r'₹\s*[\d,]+|Rs\s*[\d,]+|\$\s*[\d,]+', text):
                cleaned_price = clean_price(text)
                if cleaned_price != "No price":
                    print(f"Found Shopify price in span/div: {cleaned_price}")
                    return cleaned_price
    except:
        pass
    
    return price


def debug_levis_structure(driver, item_index=0):
    """
    Debug function for Levi's Shopify structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Try to find products
        selectors_to_try = ['.product-item', '.grid-item', '.product', '[data-product-id]']
        
        items = []
        for selector in selectors_to_try:
            items = soup.select(selector)
            if items:
                print(f"Found {len(items)} items with selector: {selector}")
                break
        
        if not items:
            print("No Shopify product items found")
            return
        
        if item_index >= len(items):
            item_index = 0
        
        item = items[item_index]
        print(f"\n=== DEBUGGING LEVI'S SHOPIFY ITEM {item_index + 1} ===")
        print(f"Item classes: {item.get('class', [])}")
        print(f"Item HTML (first 300 chars):\n{str(item)[:300]}...")
        
        # Look for price elements
        potential_price_elements = item.find_all(['span', 'div', 'p'])
        price_elements = []
        for elem in potential_price_elements:
            text = elem.get_text(strip=True)
            if text and ('₹' in text or 'Rs' in text or '$' in text or 'price' in elem.get('class', [])):
                price_elements.append(elem)
        
        print(f"\n=== POTENTIAL PRICE ELEMENTS ===")
        for i, elem in enumerate(price_elements[:5]):
            text = elem.get_text(strip=True)
            classes = elem.get('class', [])
            print(f"{i+1}. Tag: {elem.name}, Classes: {classes}, Text: '{text}'")
        
    except Exception as e:
        print(f"Error in Levi's debug function: {e}")



def scrape_lifestyle(query):
    """
    Enhanced Lifestyle scraper with comprehensive product extraction
    """
    driver = get_driver()
    
    # Lifestyle India search URL structure
    encoded_query = quote(query)
    url = f"https://www.lifestylestores.com/in/en/search?q={encoded_query}"
    print(f"Scraping Lifestyle URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 20)
        # time.sleep(5)
        
        # Advanced lazy loading scroll for Lifestyle
        advanced_lazy_loading_scroll_lifestyle(driver, max_scrolls=20, scroll_pause=3)
        
        # Force load any remaining lazy images
        force_lazy_image_loading_lifestyle(driver)
        
        # Additional wait to ensure all content is loaded
        # time.sleep(5)
        
        # Debug the first item to understand structure
        print("\n=== DEBUGGING LIFESTYLE PRICE STRUCTURE ===")
        debug_price_extraction_lifestyle(driver, item_index=0)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Method 1: Try to extract data from JSON/script tags
        products_from_json = extract_lifestyle_json_data(soup)
        
        # Method 2: Enhanced HTML parsing
        html_products = extract_lifestyle_html_data(soup)
        
        # Combine results intelligently
        all_products = combine_lifestyle_results(products_from_json, html_products)
        
        # Populate the data dictionary
        for product in all_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print summary
        print_lifestyle_summary(data, all_products)
        
    except Exception as e:
        print(f"Error scraping Lifestyle: {e}")
        try:
            driver.save_screenshot("lifestyle_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'Lifestyle'
    return df

def advanced_lazy_loading_scroll_lifestyle(driver, max_scrolls=15, scroll_pause=3):
    """
    Advanced scrolling function specifically designed for Lifestyle's lazy loading.
    """
    print("Starting Lifestyle lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_images_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        # time.sleep(scroll_pause)
        
        # Check how many images have loaded
        images_with_src = driver.execute_script("""
            return document.querySelectorAll('img[src]:not([src=""])').length;
        """)
        
        if images_with_src > loaded_images_count:
            loaded_images_count = images_with_src
            print(f"Lifestyle Scroll {i+1}/{max_scrolls}: {loaded_images_count} images loaded")
        
        # Check if page height changed
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height and i > max_scrolls - 5:
            print("Lifestyle page height stabilized, finishing scroll...")
            break
        else:
            last_height = new_height
    
    # Final scroll patterns
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(scroll_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    # time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    # time.sleep(2)
    
    final_images = driver.execute_script("""
        return document.querySelectorAll('img[src]:not([src=""])').length;
    """)
    print(f"Lifestyle scrolling complete. Total images loaded: {final_images}")

def force_lazy_image_loading_lifestyle(driver):
    """
    Force load lazy images for Lifestyle website
    """
    try:
        driver.execute_script("""
            // Common lazy loading patterns for Lifestyle
            const lazyImages = document.querySelectorAll('img[data-src], img[data-original], img[data-lazy-src]');
            lazyImages.forEach(img => {
                const src = img.dataset.src || img.dataset.original || img.dataset.lazySrc;
                if (src && !img.src.includes(src)) {
                    img.src = src;
                }
            });
            
            // Force visibility for intersection observer
            const allImages = document.querySelectorAll('img');
            allImages.forEach(img => {
                img.scrollIntoView({ behavior: 'auto', block: 'center' });
            });
            
            // Trigger any remaining lazy loading mechanisms
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
        """)
        # time.sleep(2)
        print("Lifestyle forced lazy image loading completed")
    except Exception as e:
        print(f"Error in Lifestyle forced lazy loading: {e}")

def extract_lifestyle_price_from_element(item):
    """
    Enhanced price extraction specifically for Lifestyle products
    """
    price = "No price"
    
    # Lifestyle-specific price selectors
    price_selectors = [
        # Primary Lifestyle price selectors
        '.price-current',
        '.price .current',
        '.product-price .current',
        '.price-value',
        '.product-price-value',
        'span.price',
        'div.price',
        '.current-price',
        '.sale-price',
        '.regular-price',
        '.offer-price',
        
        # Secondary selectors
        '.price-container .price',
        '.product-item-price',
        '.product-price',
        '.item-price',
        '.price-section .price',
        '.price-info .price',
        
        # Generic price patterns
        'span[class*="price"]',
        'div[class*="price"]',
        'p[class*="price"]',
        'strong[class*="price"]',
        
        # Data attribute selectors
        '[data-price]',
        '[data-testid*="price"]',
        '[data-cy*="price"]',
        
        # Currency-specific patterns
        'span.currency',
        'div.currency',
        '.amount',
        '.cost',
        '.value',
        
        # Lifestyle specific patterns (if any)
        '.ls-price',
        '.lifestyle-price',
        '.product-cost',
        '.item-cost'
    ]
    
    # Try each selector
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                # Check attributes if no text
                if not price_text:
                    price_text = (price_elem.get('data-price') or 
                                price_elem.get('title') or 
                                price_elem.get('aria-label') or '')
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                 any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_price(price_text)
                    if cleaned_price != "No price":
                        print(f"Lifestyle: Found price using selector '{selector}': {cleaned_price}")
                        return cleaned_price
        except Exception as e:
            continue
    
    # Look for currency symbols in text content
    try:
        all_text_elements = item.find_all(text=True)
        for text in all_text_elements:
            text_str = str(text).strip()
            if text_str and ('₹' in text_str or 'Rs' in text_str or '$' in text_str):
                if re.search(r'[₹$Rs].*\d+|\d+.*[₹$Rs]', text_str):
                    cleaned_price = clean_price(text_str)
                    if cleaned_price != "No price":
                        print(f"Lifestyle: Found price in text content: {cleaned_price}")
                        return cleaned_price
    except:
        pass
    
    # Final regex pattern search
    try:
        full_text = item.get_text()
        price_patterns = [
            r'₹\s*[\d,]+\.?\d*',
            r'Rs\.?\s*[\d,]+\.?\d*',
            r'\$\s*[\d,]+\.?\d*',
            r'INR\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*₹',
            r'[\d,]+\.?\d*\s*Rs'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                for match in matches:
                    if any(c.isdigit() for c in match):
                        cleaned_price = clean_price(match)
                        if cleaned_price != "No price":
                            print(f"Lifestyle: Found price using regex: {cleaned_price}")
                            return cleaned_price
    except:
        pass
    
    return price

def debug_price_extraction_lifestyle(driver, item_index=0):
    """
    Debug function for Lifestyle price extraction
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Lifestyle product selectors
        product_selectors = [
            '.product-item',
            '.product-card',
            '.product-tile',
            '.product-container',
            '.item-container',
            '.search-result-item',
            '.product-list-item',
            'article.product',
            'div.product',
            'li.product'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if items:
                print(f"Lifestyle: Found items using selector: {selector}")
                break
        
        if not items:
            print("No Lifestyle product items found for debugging")
            return
        
        if item_index >= len(items):
            item_index = 0
        
        item = items[item_index]
        print(f"\n=== DEBUGGING LIFESTYLE ITEM {item_index + 1} ===")
        print(f"Item classes: {item.get('class', [])}")
        print(f"Item HTML (first 500 chars):\n{str(item)[:500]}...")
        
        # Look for price elements
        potential_price_elements = item.find_all(['span', 'div', 'p', 'strong', 'em'])
        
        print(f"\n=== LIFESTYLE POTENTIAL PRICE ELEMENTS ===")
        for i, elem in enumerate(potential_price_elements[:10]):
            text = elem.get_text(strip=True)
            classes = elem.get('class', [])
            if text:
                print(f"{i+1}. Tag: {elem.name}, Classes: {classes}, Text: '{text}'")
        
        all_text = item.get_text()
        print(f"\n=== LIFESTYLE ALL TEXT CONTENT ===")
        print(all_text[:300] + "..." if len(all_text) > 300 else all_text)
        
    except Exception as e:
        print(f"Error in Lifestyle debug function: {e}")

def extract_lifestyle_json_data(soup):
    """
    Extract product data from JSON/script tags in Lifestyle website
    """
    products_from_json = []
    
    try:
        # Look for various script tags that might contain product data
        script_patterns = [
            'script#__NEXT_DATA__',
            'script[type="application/ld+json"]',
            'script[type="application/json"]',
            'script[id*="data"]',
            'script[class*="data"]'
        ]
        
        for pattern in script_patterns:
            scripts = soup.select(pattern)
            for script in scripts:
                try:
                    if script.string:
                        json_data = json.loads(script.string)
                        
                        # Try different JSON paths for Lifestyle
                        possible_paths = [
                            ['props', 'pageProps', 'searchResults', 'products'],
                            ['props', 'pageProps', 'products'],
                            ['props', 'initialProps', 'searchResults'],
                            ['data', 'products'],
                            ['searchResults', 'products'],
                            ['products'],
                            ['items'],
                            ['results']
                        ]
                        
                        for path in possible_paths:
                            try:
                                temp_data = json_data
                                for key in path:
                                    temp_data = temp_data[key]
                                
                                if temp_data and isinstance(temp_data, list) and len(temp_data) > 0:
                                    print(f"Lifestyle: Found {len(temp_data)} products in JSON path: {' -> '.join(path)}")
                                    
                                    for product in temp_data:
                                        try:
                                            title = (product.get('title') or 
                                                   product.get('name') or 
                                                   product.get('productName') or 
                                                   product.get('displayName') or 'No title')
                                            
                                            # Price extraction from JSON
                                            price = "No price"
                                            price_fields = [
                                                'price', 'priceValue', 'currentPrice', 'sellingPrice',
                                                'displayPrice', 'formattedPrice', 'listPrice', 'retailPrice',
                                                'salePrice', 'regularPrice', 'offerPrice', 'finalPrice'
                                            ]
                                            
                                            for field in price_fields:
                                                if field in product:
                                                    price_data = product[field]
                                                    if isinstance(price_data, dict):
                                                        price_keys = ['value', 'amount', 'price', 'current', 'display']
                                                        for key in price_keys:
                                                            if key in price_data and price_data[key]:
                                                                price = clean_price(str(price_data[key]))
                                                                if price != "No price":
                                                                    break
                                                    elif isinstance(price_data, (str, int, float)):
                                                        price = clean_price(str(price_data))
                                                    
                                                    if price != "No price":
                                                        break
                                            
                                            # Image extraction from JSON
                                            image = "No image"
                                            image_fields = ['images', 'image', 'mainImage', 'defaultImage', 'thumbnail', 'imageUrl']
                                            for field in image_fields:
                                                if field in product:
                                                    img_data = product[field]
                                                    if isinstance(img_data, list) and img_data:
                                                        img_obj = img_data[0]
                                                        if isinstance(img_obj, dict):
                                                            image = (img_obj.get('url') or img_obj.get('src'))
                                                        else:
                                                            image = str(img_obj)
                                                    elif isinstance(img_data, str):
                                                        image = img_data
                                                    
                                                    if image and image != "No image":
                                                        break
                                            
                                            # Fix relative URLs
                                            if image and image != "No image" and not image.startswith('http'):
                                                if image.startswith('//'):
                                                    image = 'https:' + image
                                                elif image.startswith('/'):
                                                    image = 'https://www.lifestylestores.com' + image
                                            
                                            # Link extraction from JSON
                                            link = "#"
                                            link_fields = ['url', 'link', 'href', 'productUrl', 'detailUrl']
                                            for field in link_fields:
                                                if field in product and product[field]:
                                                    link = product[field]
                                                    break
                                            
                                            # Fix relative URLs
                                            if link and link != "#" and not link.startswith('http'):
                                                if link.startswith('/'):
                                                    link = 'https://www.lifestylestores.com' + link
                                            
                                            products_from_json.append({
                                                'title': title,
                                                'price': price,
                                                'image': image,
                                                'link': link
                                            })
                                            
                                        except Exception as e:
                                            continue
                                    
                                    return products_from_json  # Return on first successful extraction
                                    
                            except (KeyError, TypeError):
                                continue
                                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error extracting Lifestyle JSON data: {e}")
    
    return products_from_json

def extract_lifestyle_html_data(soup):
    """
    Extract product data from HTML for Lifestyle website
    """
    html_products = []
    
    print("\n=== STARTING LIFESTYLE HTML PARSING ===")
    
    # Enhanced Lifestyle product selectors
    product_selectors = [
        '.product-item',
        '.product-card',
        '.product-tile',
        '.product-container',
        '.item-container',
        '.search-result-item',
        '.product-list-item',
        'article.product',
        'div.product',
        'li.product',
        '.grid-item',
        '.product-grid-item',
        '.search-item',
        '.result-item',
        '[data-product-id]',
        '[data-product-code]',
        '.ls-product-item',  # Lifestyle specific
        '.lifestyle-product'
    ]
    
    items = []
    for selector in product_selectors:
        items = soup.select(selector)
        if len(items) > 3:
            print(f"Lifestyle: Found {len(items)} items using selector: {selector}")
            break
    
    # Fallback approach
    if not items:
        print("Lifestyle: Trying fallback selectors...")
        potential_items = soup.find_all(['article', 'div', 'li'])
        items = []
        for item in potential_items:
            if (item.find('img') and 
                item.find('a') and
                (any(cls for cls in item.get('class', []) if 'product' in cls.lower()) or
                 item.get('data-product-id') or
                 item.get('data-product-code'))):
                items.append(item)
        print(f"Lifestyle: Found {len(items)} items using fallback method")
    
    print(f"Processing {min(len(items), 25)} Lifestyle products...")
    
    for idx, item in enumerate(items[:25]):
        try:
            # Title extraction
            title = extract_lifestyle_title(item)
            
            # Price extraction using our enhanced function
            print(f"\n--- Processing Lifestyle item {idx + 1}: {title[:30]}... ---")
            price = extract_lifestyle_price_from_element(item)
            
            # Image extraction
            image = extract_lifestyle_image(item)
            
            # Link extraction
            link = extract_lifestyle_link(item)
            
            # Only add products with meaningful data
            if (title != "No title" or price != "No price" or image != "No image"):
                html_products.append({
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                })
                
                print(f"✓ Lifestyle Product {idx + 1}: Title={title[:40]}{'...' if len(title) > 40 else ''}, "
                      f"Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            
        except Exception as e:
            print(f"Error processing Lifestyle HTML product {idx + 1}: {e}")
            continue
    
    return html_products

def extract_lifestyle_title(item):
    """Extract title from Lifestyle product item"""
    # Added 'a[aria-labelledby]' as the first selector based on debug output.
    title_selectors = [
        'a[aria-labelledby]',
        'h3 a',
        'h2 a',
        'h4 a',
        '.product-name',
        '.item-name',
        '.product-title',
        '.item-title',
        'a.product-link',
        'a.item-link',
        '.product-info h3',
        '.product-info h2',
        '.product-details h3',
        'a[title]',
        '.name',
        '.title'
    ]

    for selector in title_selectors:
        try:
            title_elem = item.select_one(selector)
            if title_elem:
                # Prioritize 'aria-labelledby', then text, then other attributes.
                title_text = (
                    title_elem.get('aria-labelledby', '') or
                    title_elem.get_text(strip=True) or
                    title_elem.get('title', '') or
                    title_elem.get('alt', '')
                )
                if title_text and len(title_text) > 3:
                    # Return the first valid title found.
                    return title_text
        except Exception as e:
            print(f"Error with selector '{selector}': {e}")
            continue

    return "No title"

def extract_lifestyle_image(item):
    """Extract image from Lifestyle product item"""
    image = "No image"
    
    # Look for loaded images first
    try:
        imgs = item.find_all('img')
        for img in imgs:
            src = img.get('src', '')
            if (src and len(src) > 10 and 
                not any(skip in src.lower() for skip in ['placeholder', 'blank', 'loading']) and
                any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                image = src
                break
    except:
        pass
    
    # Look for lazy-loaded images
    if image == "No image":
        try:
            imgs = item.find_all('img')
            for img in imgs:
                data_src = (img.get('data-src') or 
                          img.get('data-original') or 
                          img.get('data-lazy-src'))
                if (data_src and len(data_src) > 10 and
                    any(ext in data_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                    image = data_src
                    break
        except:
            pass
    
    # Fix relative URLs
    if image and image != "No image" and not image.startswith('http'):
        if image.startswith('//'):
            image = 'https:' + image
        elif image.startswith('/'):
            image = 'https://www.lifestylestores.com' + image
    
    return image

def extract_lifestyle_link(item):
    """Extract product link from Lifestyle product item"""
    link = "#"
    
    link_selectors = [
        'a.product-link',
        'a.item-link',
        'h3 a',
        'h2 a',
        'h4 a',
        'a[href*="/product/"]',
        'a[href*="/p/"]',
        'a[href]'
    ]
    
    for selector in link_selectors:
        try:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                if href.startswith('/'):
                    link = "https://www.lifestylestores.com" + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = "https://www.lifestylestores.com/" + href
                break
        except:
            continue
    
    return link

def combine_lifestyle_results(products_from_json, html_products):
    """Intelligently combine JSON and HTML results for Lifestyle"""
    if products_from_json and len(products_from_json) >= 10:
        all_products = products_from_json
        print(f"Lifestyle: Using JSON data: {len(all_products)} products")
    else:
        all_products = html_products
        print(f"Lifestyle: Using HTML parsing: {len(all_products)} products")
    
    # If both exist but neither is sufficient, combine them
    if len(all_products) < 10 and products_from_json and html_products:
        combined = products_from_json + html_products
        seen_titles = set()
        unique_products = []
        for product in combined:
            title_lower = product['title'].lower()[:30]
            if title_lower not in seen_titles and product['title'] != "No title":
                seen_titles.add(title_lower)
                unique_products.append(product)
        all_products = unique_products
        print(f"Lifestyle: Combined unique products: {len(all_products)}")
    
    return all_products

def print_lifestyle_summary(data, all_products):
    """Print summary of Lifestyle scraping results"""
    images_found = len([img for img in data['Image'] if img != 'No image'])
    prices_found = len([price for price in data['Price'] if price != 'No price'])
    
    print(f"\n=== LIFESTYLE SCRAPING SUMMARY ===")
    print(f"Total products: {len(all_products)}")
    print(f"Images found: {images_found}")
    print(f"Prices found: {prices_found}")
    if all_products:
        print(f"Success rate - Images: {images_found/len(all_products)*100:.1f}%")
        print(f"Success rate - Prices: {prices_found/len(all_products)*100:.1f}%")
    else:
        print("Success rate: 0%")


import re
import json
import time
import pandas as pd
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clean_nykaa_title(title_text):
    """Cleans up Nykaa product titles by removing price, discount, and other trailing info."""
    if not title_text:
        return "No title"
    
    # Define patterns that mark the end of a title
    stop_patterns = [
        'MRP:₹', 'MRP:', '₹', 'Rs.', '% Off', 'sizes', 'Shades'
    ]
    
    # A common pattern is also a long string of text with no spaces from the URL
    if '...' in title_text:
        title_text = title_text.split('...')[0].strip() + '...'

    for pattern in stop_patterns:
        if pattern in title_text:
            # Split the title at the first occurrence of a stop pattern
            title_text = title_text.split(pattern)[0].strip()
            
    # Remove any trailing characters that are not letters or numbers
    title_text = re.sub(r'[\s\W]+$', '', title_text)

    return title_text if title_text else "No title"

def clean_nykaa_price(price_text):
    """Enhanced price cleaning function for Nykaa"""
    if not price_text:
        return "No price"
    
    # Remove extra whitespace and newlines
    price_text = re.sub(r'\s+', ' ', price_text.strip())
    
    # Extract price using regex - handle multiple currencies and formats
    price_patterns = [
        r'₹\s*[\d,]+\.?\d*',  # Indian Rupees
        r'Rs\.?\s*[\d,]+\.?\d*',  # Rupees alternative
        r'MRP\s*₹\s*[\d,]+\.?\d*',  # MRP with Rupees
        r'Price\s*₹\s*[\d,]+\.?\d*',  # Price with Rupees
        r'\$\s*[\d,]+\.?\d*',  # USD
        r'[\d,]+\.?\d*\s*₹',  # Number before currency
        r'[\d,]+\.?\d*\s*Rs',  # Number before Rs
        r'[\d,]+\.?\d*',  # Just numbers (fallback)
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, price_text)
        if match:
            return match.group().strip()
    
    return price_text.strip() if price_text.strip() else "No price"

def advanced_nykaa_scroll(driver, max_scrolls=20, scroll_pause=3):
    """
    Advanced scrolling function for Nykaa's dynamic loading.
    """
    print("Starting Nykaa lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down progressively
        scroll_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        
        # Wait for content to load
        # time.sleep(scroll_pause)
        
        # Check how many products have loaded
        products_loaded = driver.execute_script("""
            return document.querySelectorAll('[data-testid="product-card"], .product-item, .nykaa-product, .css-xrzmfa').length;
        """)
        
        if products_loaded > loaded_products_count:
            loaded_products_count = products_loaded
            print(f"Scroll {i+1}/{max_scrolls}: {loaded_products_count} products loaded")
        
        # Check if page height changed
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if i > max_scrolls - 5:
                print("Page height stabilized, finishing scroll...")
                break
        else:
            last_height = new_height
    
    # Final comprehensive scroll
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(scroll_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    # time.sleep(2)
    
    final_products = driver.execute_script("""
        return document.querySelectorAll('[data-testid="product-card"], .product-item, .nykaa-product, .css-xrzmfa').length;
    """)
    print(f"Nykaa scrolling complete. Total products loaded: {final_products}")

def force_nykaa_image_loading(driver):
    """Force load lazy images in Nykaa"""
    try:
        driver.execute_script("""
            // Force load images with data-src attributes
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => {
                if (img.dataset.src && !img.src.includes(img.dataset.src)) {
                    img.src = img.dataset.src;
                }
            });
            
            // Handle Nykaa's specific lazy loading patterns
            const nykaaImages = document.querySelectorAll('img[data-original], img[data-lazy]');
            nykaaImages.forEach(img => {
                const src = img.dataset.original || img.dataset.lazy;
                if (src && !img.src.includes(src)) {
                    img.src = src;
                }
            });
            
            // Trigger intersection observer by scrolling images into view
            const allImages = document.querySelectorAll('img');
            allImages.forEach(img => {
                img.scrollIntoView({ behavior: 'auto', block: 'center' });
            });
        """)
        # time.sleep(3)
        print("Forced Nykaa image loading completed")
    except Exception as e:
        print(f"Error in forced lazy loading: {e}")

def extract_nykaa_price_from_element(item):
    """Enhanced price extraction for Nykaa products"""
    price = "No price"
    
    # Nykaa-specific price selectors
    price_selectors = [
        # Primary Nykaa price selectors
        '[data-testid="product-price"]',
        '.css-1d0jf8e',  # Common Nykaa price class
        '.css-111z9ua',  # Another common price class
        '.price-show',
        '.final-price',
        '.discounted-price',
        '.product-price',
        '.price-container .price',
        '.price-section .price',
        
        # Generic price selectors
        '.price',
        '.product-item-price',
        '.item-price',
        '.current-price',
        '.sale-price',
        '.regular-price',
        
        # Price within specific containers
        '.product-details .price',
        '.product-info .price',
        '.price-info .price',
        
        # Span and div variations
        'span[class*="price"]',
        'div[class*="price"]',
        'p[class*="price"]',
        
        # Data attribute selectors
        '[data-price]',
        '[data-testid*="price"]',
        '[data-qa*="price"]',
        
        # Typography classes that might contain prices
        '.typography-body-m',
        '.typography-body-s',
        'span.font-weight-bold',
        'div.font-weight-bold',
        
        # Fallback selectors
        'span.money',
        'div.money',
        'strong[class*="price"]',
        'em[class*="price"]'
    ]
    
    # Try each selector
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                # Get text content
                price_text = price_elem.get_text(strip=True)
                
                # Also check for price in attributes
                if not price_text:
                    price_text = (price_elem.get('data-price') or 
                                price_elem.get('title') or 
                                price_elem.get('aria-label') or '')
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                 'MRP' in price_text or any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_nykaa_price(price_text)
                    if cleaned_price != "No price":
                        print(f"Found price using selector '{selector}': {cleaned_price}")
                        return cleaned_price
        except Exception as e:
            continue
    
    # Look for price in all text elements
    try:
        all_text_elements = item.find_all(text=True)
        for text in all_text_elements:
            text_str = str(text).strip()
            if text_str and ('₹' in text_str or 'Rs' in text_str or '$' in text_str or 'MRP' in text_str):
                if re.search(r'[₹$Rs].*\d+|\d+.*[₹$Rs]|MRP.*\d+', text_str):
                    cleaned_price = clean_nykaa_price(text_str)
                    if cleaned_price != "No price":
                        print(f"Found price in text content: {cleaned_price}")
                        return cleaned_price
    except:
        pass
    
    # Final strategy: regex patterns in full text
    try:
        full_text = item.get_text()
        price_patterns = [
            r'₹\s*[\d,]+\.?\d*',
            r'Rs\.?\s*[\d,]+\.?\d*',
            r'MRP\s*₹\s*[\d,]+\.?\d*',
            r'\$\s*[\d,]+\.?\d*',
            r'INR\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*₹',
            r'[\d,]+\.?\d*\s*Rs'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                for match in matches:
                    if any(c.isdigit() for c in match):
                        cleaned_price = clean_nykaa_price(match)
                        if cleaned_price != "No price":
                            print(f"Found price using regex: {cleaned_price}")
                            return cleaned_price
    except:
        pass
    
    return price

def extract_nykaa_rating(item):
    """Extract rating information from Nykaa product"""
    rating = "No rating"
    
    rating_selectors = [
        '[data-testid="product-rating"]',
        '.rating',
        '.star-rating',
        '.product-rating',
        '.rating-container',
        '.stars',
        '[class*="rating"]',
        '[class*="star"]',
        '.css-1uodvt6',  # Common Nykaa rating class
        '.review-rating'
    ]
    
    for selector in rating_selectors:
        try:
            rating_elem = item.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Look for numeric rating
                rating_match = re.search(r'(\d+\.?\d*)\s*(?:/\s*5|★|stars?|out of)', rating_text, re.IGNORECASE)
                if rating_match:
                    rating = rating_match.group(1)
                    break
                elif re.search(r'\d+\.?\d*', rating_text):
                    # Fallback to first number found
                    num_match = re.search(r'\d+\.?\d*', rating_text)
                    if num_match:
                        rating = num_match.group()
                        break
        except:
            continue
    
    return rating

def debug_nykaa_structure(driver, item_index=0):
    """Debug function to inspect Nykaa's HTML structure"""
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Nykaa product selectors
        product_selectors = [
            '[data-testid="product-card"]',
            '.product-item',
            '.nykaa-product',
            '.css-xrzmfa',
            '.product-card',
            '.product-tile',
            'div[data-id]',
            '[data-qa="product"]'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if items:
                print(f"Found items using selector: {selector}")
                break
        
        if not items:
            print("No Nykaa product items found for debugging")
            return
        
        if item_index >= len(items):
            item_index = 0
        
        item = items[item_index]
        print(f"\n=== DEBUGGING NYKAA ITEM {item_index + 1} ===")
        print(f"Item classes: {item.get('class', [])}")
        print(f"Item HTML (first 500 chars):\n{str(item)[:500]}...")
        
        # Look for potential price elements
        potential_elements = item.find_all(['span', 'div', 'p', 'strong'])
        print(f"\n=== POTENTIAL ELEMENTS ===")
        for i, elem in enumerate(potential_elements[:15]):
            text = elem.get_text(strip=True)
            classes = elem.get('class', [])
            if text:
                print(f"{i+1}. Tag: {elem.name}, Classes: {classes}, Text: '{text}'")
        
    except Exception as e:
        print(f"Error in Nykaa debug function: {e}")

def scrape_nykaa(query):
    """
    Comprehensive Nykaa scraper with enhanced extraction capabilities
    """
    # Import the get_driver function (assuming it's defined elsewhere)
    # from your_driver_module import get_driver
    driver = get_driver()  # You'll need to ensure this function is available
    
    # Nykaa search URL structure
    encoded_query = quote(query)
    url = f"https://www.nykaa.com/search/result/?q={encoded_query}"
    print(f"Scraping Nykaa URL: {url}")
    
    data = {"Title": [], "Price": [], "Rating": [], "Image": [], "Link": [], "Brand": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 20)
        # time.sleep(5)
        
        # Try to wait for products to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                '[data-testid="product-card"], .product-item, .nykaa-product, .css-xrzmfa')))
        except:
            print("Products not found with primary selectors, continuing...")
        
        # Advanced scrolling for Nykaa
        advanced_nykaa_scroll(driver, max_scrolls=25, scroll_pause=4)
        
        # Force load images
        force_nykaa_image_loading(driver)
        
        # Additional wait
        # time.sleep(5)
        
        # Debug structure
        print("\n=== DEBUGGING NYKAA STRUCTURE ===")
        debug_nykaa_structure(driver, item_index=0)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Method 1: Try to extract from JSON data
        products_from_json = []
        try:
            # Look for JSON data in script tags
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    # Navigate through possible JSON structures for products
                    if isinstance(json_data, dict):
                        # Common paths where product data might be stored
                        possible_paths = [
                            ['props', 'pageProps', 'searchResults', 'products'],
                            ['props', 'pageProps', 'products'],
                            ['props', 'initialState', 'products'],
                            ['products'],
                            ['searchResults', 'products'],
                            ['data', 'products'],
                            ['response', 'products']
                        ]
                        
                        for path in possible_paths:
                            try:
                                temp_data = json_data
                                for key in path:
                                    temp_data = temp_data[key]
                                if temp_data and isinstance(temp_data, list):
                                    print(f"Found {len(temp_data)} products in JSON")
                                    
                                    for product in temp_data:
                                        if isinstance(product, dict):
                                            title = (product.get('name') or 
                                                   product.get('title') or 
                                                   product.get('productName') or 'No title')
                                            
                                            # Price extraction from JSON
                                            price = "No price"
                                            price_fields = ['price', 'mrp', 'sellingPrice', 'offerPrice', 
                                                          'displayPrice', 'currentPrice', 'finalPrice']
                                            for field in price_fields:
                                                if field in product and product[field]:
                                                    price = clean_nykaa_price(str(product[field]))
                                                    if price != "No price":
                                                        break
                                            
                                            # Brand extraction
                                            brand = (product.get('brand') or 
                                                   product.get('brandName') or 
                                                   product.get('manufacturer') or 'No brand')
                                            
                                            # Rating extraction
                                            rating = (product.get('rating') or 
                                                    product.get('averageRating') or 
                                                    product.get('starRating') or 'No rating')
                                            
                                            # Image extraction
                                            image = "No image"
                                            if 'images' in product and product['images']:
                                                if isinstance(product['images'], list):
                                                    image = product['images'][0]
                                                    if isinstance(image, dict):
                                                        image = image.get('url', image.get('src', 'No image'))
                                            elif 'image' in product:
                                                image = product['image']
                                            
                                            # Link extraction
                                            link = product.get('url', product.get('link', '#'))
                                            if link and not link.startswith('http'):
                                                link = 'https://www.nykaa.com' + link
                                            
                                            products_from_json.append({
                                                'title': title,
                                                'price': price,
                                                'rating': str(rating),
                                                'image': image,
                                                'link': link,
                                                'brand': brand
                                            })
                                    break
                            except (KeyError, TypeError):
                                continue
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Error extracting from JSON: {e}")
        
        # Method 2: HTML parsing with enhanced selectors
        html_products = []
        
        print("\n=== STARTING NYKAA HTML PARSING ===")
        
        # Enhanced Nykaa product selectors
        product_selectors = [
            'a.css-qlopj4', # This is the anchor tag that wraps the entire product card.
            'div.product-list-box', # This is often the main container
            '[data-testid="product-card"]',  # Primary Nykaa selector
            '.product-item',
            '.nykaa-product',
            '.css-xrzmfa',  # This was grabbing only the title, moved down
            '.product-card',
            '.product-tile',
            'div[data-id]',
            '[data-qa="product"]',
            '.css-1qf0ydp',  # Another common class
            'article.product',
            'div.product',
            'li.product',
            '.search-product-item',
            '.plp-product',
            '.product-listing-item'
        ]
        
        items = []
        for selector in product_selectors:
            items = soup.select(selector)
            if len(items) > 5:  # Need a reasonable number of products
                print(f"Nykaa: Found {len(items)} items using selector: {selector}")
                break
        
        # Fallback method if specific selectors don't work
        if not items:
            print("Trying Nykaa fallback selectors...")
            # Look for divs/articles that contain images and links (typical product structure)
            potential_items = soup.find_all(['div', 'article', 'li'])
            items = []
            for item in potential_items:
                if (item.find('img') and 
                    item.find('a') and
                    (any('product' in str(cls).lower() for cls in item.get('class', [])) or
                     item.get('data-id') or
                     item.get('data-testid'))):
                    items.append(item)
            print(f"Nykaa fallback: Found {len(items)} potential items")
        
        print(f"Processing {min(len(items), 30)} Nykaa products...")
        
        for idx, item in enumerate(items[:30]):
            try:
                # Title extraction
                title = "No title"
                title_selectors = [
                    '[data-testid="product-title"]',
                    '.product-title',
                    '.product-name',
                    'h3 a',
                    'h2 a',
                    'h4 a',
                    '.css-1gc4x7i',  # Common Nykaa title class
                    'a[title]',
                    '.product-item-title',
                    '.item-title',
                    'a.product-link'
                ]
                
                for t_sel in title_selectors:
                    try:
                        title_elem = item.select_one(t_sel)
                        if title_elem:
                            title_text = (title_elem.get_text(strip=True) or 
                                        title_elem.get('title', '') or
                                        title_elem.get('alt', ''))
                            if title_text and len(title_text) > 3:
                                title = title_text
                                break
                    except:
                        continue
                
                # Fallback: If no child selector worked, the item itself might be the title element.
                if title == "No title":
                    try:
                        item_text = item.get_text(strip=True)
                        if item_text and len(item_text) > 5:
                            title = item_text
                    except:
                        pass

                # Clean the final extracted title
                title = clean_nykaa_title(title)
                
                # Brand extraction
                brand = "No brand"
                brand_selectors = [
                    '[data-testid="product-brand"]',
                    '.brand-name',
                    '.product-brand',
                    '.brand',
                    '.css-1uodvt6'  # Common Nykaa brand class
                ]
                
                for b_sel in brand_selectors:
                    try:
                        brand_elem = item.select_one(b_sel)
                        if brand_elem:
                            brand_text = brand_elem.get_text(strip=True)
                            if brand_text and len(brand_text) > 1:
                                brand = brand_text
                                break
                    except:
                        continue
                
                # Price extraction using our enhanced function
                print(f"\n--- Processing Nykaa item {idx + 1}: {title[:30]}... ---")
                price = extract_nykaa_price_from_element(item)
                
                # Rating extraction
                rating = extract_nykaa_rating(item)
                
                # Image extraction
                image = "No image"
                
                # Look for loaded images first
                try:
                    imgs = item.find_all('img')
                    for img in imgs:
                        src = img.get('src', '')
                        if (src and len(src) > 10 and 
                            'nykaa' in src.lower() and
                            any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                            image = src
                            break
                except:
                    pass
                
                # Look for data-src (lazy loaded images)
                if image == "No image":
                    try:
                        imgs = item.find_all('img')
                        for img in imgs:
                            data_src = (img.get('data-src') or 
                                      img.get('data-original') or 
                                      img.get('data-lazy'))
                            if (data_src and len(data_src) > 10 and
                                any(ext in data_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                                image = data_src
                                break
                    except:
                        pass
                
                # Fix image URLs
                if image and image != "No image" and not image.startswith('http'):
                    if image.startswith('//'):
                        image = 'https:' + image
                    elif image.startswith('/'):
                        image = 'https://www.nykaa.com' + image
                
                # Link extraction
                link = "#"
                # Since the main item is now an anchor tag, we get its href directly.
                try:
                    if item.name == 'a' and item.get('href'):
                        link = item['href']
                    else:
                        # Fallback to searching for a link inside the item
                        link_elem = item.select_one('a[href]')
                        if link_elem and link_elem.get('href'):
                            link = link_elem['href']
                except:
                    pass

                # Make sure the link is absolute
                if link and link != "#" and not link.startswith('http'):
                    if link.startswith('/'):
                        link = "https://www.nykaa.com" + link
                    else:
                        link = "https://www.nykaa.com/" + link
                
                # Only add products with meaningful data
                if (title != "No title" or price != "No price" or image != "No image"):
                    html_products.append({
                        'title': title,
                        'price': price,
                        'rating': rating,
                        'image': image,
                        'link': link,
                        'brand': brand
                    })
                    
                    print(f"✓ Nykaa Product {idx + 1}: {title[:40]}{'...' if len(title) > 40 else ''}, "
                          f"Price={price}, Brand={brand}, Rating={rating}")
                
            except Exception as e:
                print(f"Error processing Nykaa product {idx + 1}: {e}")
                continue
        
        # Combine results
        if products_from_json and len(products_from_json) >= 10:
            all_products = products_from_json
            print(f"Using Nykaa JSON data: {len(all_products)} products")
        else:
            all_products = html_products
            print(f"Using Nykaa HTML parsing: {len(all_products)} products")
        
        # Populate data dictionary
        for product in all_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Rating"].append(product['rating'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
            data["Brand"].append(product['brand'])
        
        # Print summary
        images_found = len([img for img in data['Image'] if img != 'No image'])
        prices_found = len([price for price in data['Price'] if price != 'No price'])
        ratings_found = len([rating for rating in data['Rating'] if rating != 'No rating'])
        
        print(f"\n=== NYKAA SCRAPING SUMMARY ===")
        print(f"Total products: {len(all_products)}")
        print(f"Images found: {images_found}")
        print(f"Prices found: {prices_found}")
        print(f"Ratings found: {ratings_found}")
        if all_products:
            print(f"Success rate - Images: {images_found/len(all_products)*100:.1f}%")
            print(f"Success rate - Prices: {prices_found/len(all_products)*100:.1f}%")
            print(f"Success rate - Ratings: {ratings_found/len(all_products)*100:.1f}%")
        
    except Exception as e:
        print(f"Error scraping Nykaa: {e}")
        try:
            driver.save_screenshot("nykaa_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'Nykaa'
    return df

def scrape_ajio(query):
    """
    Enhanced AJIO scraper with improved product detection and data extraction
    """
    driver = get_driver()
    
    # AJIO search URL structure
    encoded_query = quote(query)
    url = f"https://www.ajio.com/search/?text={encoded_query}"
    print(f"Scraping AJIO URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        
        # Enhanced lazy loading scroll for AJIO
        enhanced_ajio_scroll(driver, max_scrolls=15, scroll_pause=3)
        
        # Force load any remaining lazy images
        force_ajio_lazy_loading(driver)
        
        # Additional wait to ensure all content is loaded
        time.sleep(5)
        
        # Debug the first few items to understand structure
        print("\n=== DEBUGGING AJIO STRUCTURE ===")
        debug_ajio_structure(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Method 1: Try to extract data from JSON (similar to H&M approach)
        products_from_json = extract_ajio_json_data(soup)
        
        # Method 2: Enhanced HTML parsing with improved product detection
        html_products = extract_ajio_html_products(soup)
        
        # Combine results intelligently
        if products_from_json and len(products_from_json) >= 10:
            all_products = products_from_json
            print(f"Using JSON data: {len(all_products)} products")
        else:
            all_products = html_products
            print(f"Using HTML parsing: {len(all_products)} products")
        
        # If we have both but neither is sufficient, combine them
        if len(all_products) < 10 and products_from_json and html_products:
            combined = products_from_json + html_products
            seen_titles = set()
            unique_products = []
            for product in combined:
                title_lower = product['title'].lower()[:30]
                if title_lower not in seen_titles and product['title'] != "No title":
                    seen_titles.add(title_lower)
                    unique_products.append(product)
            all_products = unique_products
            print(f"Combined unique products: {len(all_products)}")
        
        # Populate the data dictionary
        for product in all_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print summary
        images_found = len([img for img in data['Image'] if img != 'No image'])
        prices_found = len([price for price in data['Price'] if price != 'No price'])
        print(f"\n=== AJIO SCRAPING SUMMARY ===")
        print(f"Total products: {len(all_products)}")
        print(f"Images found: {images_found}")
        print(f"Prices found: {prices_found}")
        if all_products:
            print(f"Success rate - Images: {images_found/len(all_products)*100:.1f}%")
            print(f"Success rate - Prices: {prices_found/len(all_products)*100:.1f}%")
        else:
            print("Success rate: 0%")
        
    except Exception as e:
        print(f"Error scraping AJIO: {e}")
        try:
            driver.save_screenshot("ajio_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'AJIO'
    return df

def enhanced_ajio_scroll(driver, max_scrolls=15, scroll_pause=3):
    """
    Enhanced scrolling function specifically designed for AJIO's lazy loading.
    """
    print("Starting enhanced AJIO lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        time.sleep(scroll_pause)
        
        # Check how many product cards have loaded
        products_loaded = driver.execute_script("""
            return document.querySelectorAll('[data-testid], .product, .item, [class*="product"], [class*="item"]').length;
        """)
        
        if products_loaded > loaded_products_count:
            loaded_products_count = products_loaded
            print(f"Scroll {i+1}/{max_scrolls}: {loaded_products_count} product elements detected")
        
        # Check if page height changed (more content loaded)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if i > max_scrolls - 5:
                print("Page height stabilized, finishing scroll...")
                break
        else:
            last_height = new_height
    
    # Final scroll patterns to ensure everything loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)
    
    print("Enhanced AJIO scrolling complete")

def force_ajio_lazy_loading(driver):
    """
    Force load lazy images and content specific to AJIO
    """
    try:
        driver.execute_script("""
            // Force load images with data-src attributes
            const lazyImages = document.querySelectorAll('img[data-src], img[data-original], img[data-lazy-src]');
            lazyImages.forEach(img => {
                const dataSrc = img.dataset.src || img.dataset.original || img.dataset.lazySrc;
                if (dataSrc && !img.src.includes(dataSrc)) {
                    img.src = dataSrc;
                }
            });
            
            // Trigger intersection observer manually
            const allImages = document.querySelectorAll('img');
            allImages.forEach(img => {
                img.scrollIntoView({ behavior: 'auto', block: 'center' });
            });
            
            // Force any lazy loading mechanisms
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
        """)
        time.sleep(2)
        print("Forced AJIO lazy loading completed")
    except Exception as e:
        print(f"Error in AJIO forced lazy loading: {e}")

def debug_ajio_structure(driver):
    """
    Debug function to inspect AJIO's HTML structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("=== AJIO STRUCTURE ANALYSIS ===")
        
        # Look for common product container patterns
        potential_containers = [
            '[data-testid]',
            '.product',
            '.item',
            '[class*="product"]',
            '[class*="item"]',
            '[class*="card"]',
            '[class*="tile"]'
        ]
        
        for selector in potential_containers:
            elements = soup.select(selector)
            if elements and len(elements) > 5:
                print(f"Found {len(elements)} elements with selector: {selector}")
                
                # Analyze first few elements
                for i, elem in enumerate(elements[:3]):
                    classes = elem.get('class', [])
                    data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                    has_image = bool(elem.find('img'))
                    has_link = bool(elem.find('a'))
                    text_snippet = elem.get_text()[:100].strip()
                    
                    print(f"  Element {i+1}: Classes={classes}, Data={data_attrs}")
                    print(f"    Has image: {has_image}, Has link: {has_link}")
                    print(f"    Text: {text_snippet[:50]}...")
                break
        
        # Look for specific AJIO patterns
        ajio_specific = soup.select('[class*="rilrtl"], [class*="ajio"], [data-testid*="product"]')
        if ajio_specific:
            print(f"Found {len(ajio_specific)} AJIO-specific elements")
            
    except Exception as e:
        print(f"Error in AJIO debug function: {e}")

def extract_ajio_json_data(soup):
    """
    Extract product data from AJIO's JSON data
    """
    products_from_json = []
    
    try:
        # Look for JSON data in script tags
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', string=re.compile(r'window\.__INITIAL_STATE__')))
        script_tags.extend(soup.find_all('script', string=re.compile(r'window\.__NEXT_DATA__')))
        
        for script in script_tags:
            try:
                if script.string:
                    # Clean up the script content
                    script_content = script.string.strip()
                    
                    # Handle different JSON patterns
                    if 'window.__INITIAL_STATE__' in script_content:
                        json_start = script_content.find('{')
                        json_content = script_content[json_start:]
                        if json_content.endswith(';'):
                            json_content = json_content[:-1]
                    elif 'window.__NEXT_DATA__' in script_content:
                        json_start = script_content.find('{')
                        json_content = script_content[json_start:]
                    else:
                        json_content = script_content
                    
                    data = json.loads(json_content)
                    
                    # Try different paths where products might be stored
                    possible_paths = [
                        ['props', 'pageProps', 'products'],
                        ['props', 'pageProps', 'searchResults', 'products'],
                        ['props', 'pageProps', 'data', 'products'], 
                        ['searchResults', 'products'],
                        ['products'],
                        ['data', 'products'],
                        ['productList'],
                        ['results', 'products'],
                        ['search', 'products']
                    ]
                    
                    for path in possible_paths:
                        try:
                            temp_data = data
                            for key in path:
                                temp_data = temp_data[key]
                            
                            if temp_data and isinstance(temp_data, list) and len(temp_data) > 0:
                                print(f"Found {len(temp_data)} products in JSON path: {' -> '.join(path)}")
                                
                                for product in temp_data:
                                    try:
                                        # Extract title
                                        title = (product.get('name') or 
                                               product.get('title') or 
                                               product.get('productName') or
                                               product.get('displayName') or 'No title')
                                        
                                        # Extract price
                                        price = extract_ajio_price_from_json(product)
                                        
                                        # Extract image
                                        image = extract_ajio_image_from_json(product)
                                        
                                        # Extract link
                                        link = extract_ajio_link_from_json(product)
                                        
                                        if title != "No title" or price != "No price":
                                            products_from_json.append({
                                                'title': title,
                                                'price': price,
                                                'image': image,
                                                'link': link
                                            })
                                            
                                    except Exception as e:
                                        continue
                                        
                                if products_from_json:
                                    return products_from_json
                                    
                        except (KeyError, TypeError):
                            continue
                            
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"Error extracting AJIO JSON data: {e}")
    
    return products_from_json

def extract_ajio_price_from_json(product):
    """Extract price from AJIO JSON product data"""
    price = "No price"
    
    # Common price fields in AJIO JSON
    price_fields = [
        'price', 'finalPrice', 'sellingPrice', 'offerPrice', 'mrp',
        'discountedPrice', 'currentPrice', 'salePrice', 'listPrice'
    ]
    
    for field in price_fields:
        if field in product:
            price_data = product[field]
            if isinstance(price_data, dict):
                # Look for value, amount, or similar keys
                for key in ['value', 'amount', 'price', 'final', 'selling']:
                    if key in price_data and price_data[key]:
                        price = clean_price(str(price_data[key]))
                        if price != "No price":
                            return price
            elif isinstance(price_data, (str, int, float)):
                price = clean_price(str(price_data))
                if price != "No price":
                    return price
    
    return price

def extract_ajio_image_from_json(product):
    """Extract image from AJIO JSON product data"""
    image = "No image"
    
    # Common image fields
    image_fields = ['images', 'image', 'thumbnail', 'mainImage', 'defaultImage']
    
    for field in image_fields:
        if field in product:
            img_data = product[field]
            if isinstance(img_data, list) and img_data:
                img_obj = img_data[0]
                if isinstance(img_obj, dict):
                    image = (img_obj.get('url') or 
                           img_obj.get('src') or 
                           img_obj.get('href'))
                else:
                    image = str(img_obj)
            elif isinstance(img_data, str):
                image = img_data
            
            if image and image != "No image":
                # Fix relative URLs
                if not image.startswith('http'):
                    if image.startswith('//'):
                        image = 'https:' + image
                    elif image.startswith('/'):
                        image = 'https://www.ajio.com' + image
                return image
    
    return image

def extract_ajio_link_from_json(product):
    """Extract product link from AJIO JSON product data"""
    link = "#"
    
    # Common link fields
    link_fields = ['url', 'link', 'href', 'productUrl', 'detailUrl']
    
    for field in link_fields:
        if field in product and product[field]:
            link = product[field]
            break
    
    # Try to construct link from product ID or code
    if link == "#":
        id_fields = ['id', 'productId', 'code', 'productCode', 'sku']
        for field in id_fields:
            if field in product and product[field]:
                product_id = product[field]
                link = f"https://www.ajio.com/p/{product_id}"
                break
    
    # Fix relative URLs
    if link and link != "#" and not link.startswith('http'):
        if link.startswith('/'):
            link = 'https://www.ajio.com' + link
        else:
            link = 'https://www.ajio.com/' + link
    
    return link

def extract_ajio_html_products(soup):
    """
    Enhanced HTML parsing for AJIO products with better selectors
    """
    html_products = []
    
    print("\n=== STARTING AJIO HTML PARSING ===")
    
    # Enhanced AJIO product selectors based on common patterns
    product_selectors = [
        # AJIO-specific selectors
        '[data-testid*="product"]',
        '[data-testid*="item"]',
        '.product-tile',
        '.product-card',
        '.item-card',
        '.product-item',
        
        # Generic e-commerce patterns
        'article.product',
        'div.product',
        'li.product',
        'article[data-id]',
        'div[data-id]',
        'li[data-id]',
        
        # Container-based selectors (avoiding filters)
        'div[class*="product"]:has(img):has(a)',
        'article[class*="item"]:has(img)',
        'li[class*="tile"]:has(img)',
        
        # Pattern-based selectors
        '[class*="product"][class*="tile"]',
        '[class*="item"][class*="card"]',
        '[class*="product"][class*="wrapper"]'
    ]
    
    items = []
    selector_used = None
    
    # Try each selector and pick the one with most product-like items
    for selector in product_selectors:
        try:
            potential_items = soup.select(selector)
            
            # Filter out items that are clearly not products
            filtered_items = []
            for item in potential_items:
                # Skip if it looks like a filter or navigation element
                text = item.get_text().lower()
                classes = ' '.join(item.get('class', [])).lower()
                
                # Skip obvious non-product elements
                if any(skip in text for skip in [
                    'select all', 'clear all', 'filter', 'sort by', 'categories',
                    'brands', 'gender', 'occasion', 'discount', 'tags', 'rating'
                ]):
                    continue
                    
                if any(skip in classes for skip in [
                    'filter', 'facet', 'sort', 'nav', 'menu', 'sidebar'
                ]):
                    continue
                
                # Must have image and some meaningful content
                if item.find('img') and len(text.strip()) > 10:
                    filtered_items.append(item)
            
            if len(filtered_items) > len(items):
                items = filtered_items
                selector_used = selector
                
        except Exception as e:
            continue
    
    print(f"AJIO: Found {len(items)} items using selector: {selector_used}")
    
    # If no good selector found, try a different approach
    if not items:
        print("Trying alternative AJIO product detection...")
        
        # Look for elements with images and links (basic product indicators)
        all_elements = soup.find_all(['div', 'article', 'li'])
        for elem in all_elements:
            if (elem.find('img') and 
                elem.find('a') and 
                len(elem.get_text().strip()) > 20 and
                len(elem.get_text().strip()) < 200):
                
                # Additional filters to avoid navigation/filter elements
                text = elem.get_text().lower()
                if not any(skip in text for skip in [
                    'select all', 'clear all', 'filter', 'sort', 'categories'
                ]):
                    items.append(elem)
        
        items = items[:25]  # Limit to reasonable number
        print(f"Found {len(items)} items using fallback method")
    
    print(f"Processing {min(len(items), 25)} AJIO products...")
    
    for idx, item in enumerate(items[:25]):
        try:
            # Extract title with AJIO-specific selectors
            title = extract_ajio_title(item)
            
            # Extract price with enhanced logic
            price = extract_ajio_price_from_element(item)
            
            # Extract image
            image = extract_ajio_image(item)
            
            # Extract link
            link = extract_ajio_link(item)
            
            print(f"--- Processing AJIO item {idx + 1}: {title[:30]}... ---")
            
            # Only add products with meaningful data
            if (title != "No title" and 
                len(title) > 5 and 
                not any(skip in title.lower() for skip in [
                    'select all', 'clear all', 'filter', 'sort'
                ])):
                
                html_products.append({
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                })
                
                print(f"✓ Product {idx + 1}: Title={title[:40]}{'...' if len(title) > 40 else ''}, "
                      f"Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            else:
                print(f"✗ Skipped item {idx + 1}: Not a valid product")
                
        except Exception as e:
            print(f"Error processing AJIO product {idx + 1}: {e}")
            continue
    
    return html_products

def extract_ajio_title(item):
    """Extract title from AJIO product element"""
    title = "No title"

    # --- Strategy 1: Combine Brand and Name (Most Reliable for Ajio) ---
    try:
        brand_elem = item.select_one('.brand, .rilrtl-products-list__item__brand-name, .brand-name')
        name_elem = item.select_one('.name, .nameCls, .rilrtl-products-list__item__name, .product-name')
        
        brand = brand_elem.get_text(strip=True) if brand_elem else ''
        name = name_elem.get_text(strip=True) if name_elem else ''
        
        if brand and name:
            full_title = f"{brand} {name}"
            # Clean up known junk text
            if 'Quick View' in full_title:
                full_title = full_title.replace('Quick View', '').strip()
            return full_title
    except Exception:
        pass

    # --- Strategy 2: Use a list of specific selectors ---
    title_selectors = [
        # More specific Ajio selectors first
        '.nameCls',
        '.product-name',
        '.item-name',
        '.rilrtl-products-list__item__name',
        # Generic selectors
        '[data-testid*="name"]',
        '[data-testid*="title"]',
        '.product-title',
        '.item-title',
        'h3 a',
        'h2 a',
        'h4 a',
        'a[title]'
    ]
    
    for selector in title_selectors:
        try:
            elem = item.select_one(selector)
            if elem:
                title_text = (elem.get_text(strip=True) or 
                            elem.get('title', '') or
                            elem.get('alt', ''))
                if title_text and len(title_text) > 3:
                    title = title_text
                    break
        except:
            continue
    
    # Fallback: look for any reasonable text
    if title == "No title":
        for tag in ['a', 'h1', 'h2', 'h3', 'h4', 'span', 'div']:
            try:
                elem = item.find(tag)
                if elem:
                    text = elem.get_text(strip=True)
                    if (text and 10 <= len(text) <= 100 and 
                        not any(skip in text.lower() for skip in [
                            'price', '₹', '$', 'add to', 'size', 'color', 'sale'
                        ])):
                        title = text
                        break
            except:
                continue
    
    return title

def extract_ajio_price_from_element(item):
    """Extract price from AJIO product element"""
    
    # More specific AJIO price selectors first
    price_selectors = [
        '.price .price-actual', # For discounted price
        '.price-value',
        '.price',
        '.selling-price',
        '.final-price',
        '.offer-price',
        '[data-testid*="price"]',
        '.current-price',
        '.cost',
        'span[class*="price"]',
        'div[class*="price"]',
        'strong.price',
        '.product-price',
        '.item-price'
    ]
    
    # Try each selector
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                 any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_price(price_text)
                    if cleaned_price != "No price":
                        return cleaned_price
        except:
            continue
    
    # Fallback: look for currency symbols in any text
    try:
        all_text = item.get_text()
        price_patterns = [
            r'₹\s*[\d,]+\.?\d*',
            r'Rs\.?\s*[\d,]+\.?\d*',
            r'\$\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*₹',
            r'[\d,]+\.?\d*\s*Rs'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                for match in matches:
                    if any(c.isdigit() for c in match):
                        cleaned_price = clean_price(match)
                        if cleaned_price != "No price":
                            return cleaned_price
    except:
        pass
    
    return "No price"

def extract_ajio_image(item):
    """Extract image from AJIO product element"""
    image = "No image"
    
    try:
        # More specific container for the image
        img_container = item.select_one('.img-container, .img-holder, .image-container, .img')
        if not img_container:
            img_container = item # Fallback to the whole item

        # Look for loaded images first
        imgs = img_container.find_all('img')
        for img in imgs:
            src = img.get('src', '')
            if (src and len(src) > 10 and 
                not any(skip in src.lower() for skip in ['placeholder', 'blank', 'loading']) and
                ('ajio' in src.lower() or any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']))):
                image = src
                break
        
        # Look for lazy loaded images
        if image == "No image":
            for img in imgs:
                data_src = (img.get('data-src') or 
                          img.get('data-original') or 
                          img.get('data-lazy-src'))
                if (data_src and len(data_src) > 10 and
                    ('ajio' in data_src.lower() or any(ext in data_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']))):
                    image = data_src
                    break
        
        # Fix relative URLs
        if image and image != "No image" and not image.startswith('http'):
            if image.startswith('//'):
                image = 'https:' + image
            elif image.startswith('/'):
                image = 'https://www.ajio.com' + image
    
    except:
        pass
    
    return image

def extract_ajio_link(item):
    """Extract product link from AJIO product element"""
    link = "#"
    
    # Start with the most specific selector for the whole card
    link_elem = item.select_one('a.rilrtl-products-list__item-link, a.product-link, a.item-link')
    if not link_elem:
        # Fallback to the whole item being a link
        if item.name == 'a' and item.has_attr('href'):
            link_elem = item
        else:
             # Fallback to finding any link within the item
            link_elem = item.find('a')

    if link_elem and link_elem.has_attr('href'):
        href = link_elem['href']
        if href.startswith('/'):
            link = "https://www.ajio.com" + href
        elif href.startswith('http'):
            link = href
        else:
            link = "https://www.ajio.com/" + href
        return link

    # Keep original selectors as a final fallback
    link_selectors = [
        'a[href*="/p/"]',
        'a[href*="product"]',
        'a[href*="ajio.com"]',
        'h3 a',
        'h2 a',
        'a[href]'
    ]
    
    for selector in link_selectors:
        try:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                if href.startswith('/'):
                    link = "https://www.ajio.com" + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = "https://www.ajio.com/" + href
                break
        except:
            continue
    
    return link
