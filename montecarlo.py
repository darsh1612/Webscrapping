import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
import json


def get_driver():
    """
    Set up and return a WebDriver instance
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_monte_carlo(query):
    """
    Monte Carlo scraper that scrapes one page of results with lazy loading support.
    """
    driver = get_driver()
    encoded_query = quote(query.replace(' ', '+'))
    url = f"https://www.montecarlo.in/search?type=product&q={encoded_query}"
    
    all_products = []

    try:
        print(f"\n--- Scraping Monte Carlo: {url} ---")
        
        driver.get(url)
        wait = WebDriverWait(driver, 25)
        
        # Wait for the product list to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.product-list__inner, .product-item')))
            time.sleep(5)
        except:
            print("No products found or page failed to load.")
            return pd.DataFrame({"Title": [], "Price": [], "Image": [], "Link": [], "Source": []})

        # Enhanced scrolling for lazy loading
        enhanced_monte_carlo_scroll(driver, max_scrolls=15, scroll_pause=3)
        force_monte_carlo_lazy_loading(driver)
        time.sleep(7)

        print(f"\n=== DEBUGGING MONTE CARLO STRUCTURE ===")
        debug_monte_carlo_structure(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        html_products = extract_monte_carlo_html_products(soup)
        print(f"Found {len(html_products)} products from HTML parsing")
        all_products.extend(html_products)

    except Exception as e:
        print(f"A critical error occurred during Monte Carlo scraping: {e}")
        try:
            driver.save_screenshot("monte_carlo_error.png")
        except:
            pass
    finally:
        driver.quit()

    # Create DataFrame from all collected products
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    for product in all_products:
        data["Title"].append(product['title'])
        data["Price"].append(product['price'])
        data["Image"].append(product['image'])
        data["Link"].append(product['link'])

    # Print detailed summary
    images_found = len([img for img in data['Image'] if img != 'No image'])
    prices_found = len([price for price in data['Price'] if price != 'No price'])
    print(f"\n=== MONTE CARLO SCRAPING SUMMARY ===")
    print(f"Total products found: {len(all_products)}")
    print(f"Images found: {images_found}")
    print(f"Prices found: {prices_found}")
    if all_products:
        success_rate_images = (images_found / len(all_products)) * 100 if len(all_products) > 0 else 0
        success_rate_prices = (prices_found / len(all_products)) * 100 if len(all_products) > 0 else 0
        print(f"Success rate - Images: {success_rate_images:.1f}%")
        print(f"Success rate - Prices: {success_rate_prices:.1f}%")
    else:
        print("Success rate: 0%")

    # Print sample of first few products for debugging
    print(f"\n=== SAMPLE PRODUCTS ===")
    for i, product in enumerate(all_products[:3]):
        print(f"Product {i+1}:")
        print(f"  Title: {product['title'][:50]}...")
        print(f"  Price: {product['price']}")
        print(f"  Image: {'✓' if product['image'] != 'No image' else '✗'} ({product['image'][:50]}...)")
        print(f"  Link: {product['link'][:50]}...")
    
    df = pd.DataFrame(data)
    df['Source'] = 'Monte Carlo'
    return df


def enhanced_monte_carlo_scroll(driver, max_scrolls=15, scroll_pause=3):
    """
    Enhanced scrolling function specifically designed for Monte Carlo's lazy loading.
    """
    print("Starting enhanced Monte Carlo lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        time.sleep(scroll_pause)
        
        # Check for Monte Carlo specific product containers
        js_script = """
            return document.querySelectorAll(
                '.product-item, .product-list__inner .product-item, ' +
                '.product-item.full_var, .product-item.var-5'
            ).length;
        """
        products_loaded = driver.execute_script(js_script)
        
        if products_loaded > loaded_products_count:
            loaded_products_count = products_loaded
            print(f"Scroll {i+1}/{max_scrolls}: {loaded_products_count} product elements detected")
        
        # Check if page height changed (more content loaded)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if i > max_scrolls - 3:
                print("Page height stabilized, finishing scroll...")
                break
        else:
            last_height = new_height
    
    # Final scroll patterns to ensure everything loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(3)
    
    print("Enhanced Monte Carlo scrolling complete")


def force_monte_carlo_lazy_loading(driver):
    """
    Force load lazy images and content specific to Monte Carlo
    """
    try:
        print("Forcing Monte Carlo lazy loading...")
        
        # Strategy 1: Handle standard lazy loading patterns
        js_strategy_1 = """
            console.log('Starting Monte Carlo image lazy loading...');
            const lazyImages = document.querySelectorAll(
                'img[data-src], img[data-original], img[data-lazy-src], ' +
                'img[data-srcset], img[loading="lazy"], img[class*="lazy"], ' +
                'img[class*="lazyload"], .product-item__image-wrapper img'
            );
            console.log('Found', lazyImages.length, 'lazy images');
            lazyImages.forEach((img, index) => {
                const dataSrc = img.dataset.src || img.dataset.original || 
                               img.dataset.lazySrc || img.dataset.srcset;
                if (dataSrc && !img.src.includes(dataSrc)) {
                    console.log('Loading Monte Carlo image', index, ':', dataSrc);
                    img.src = dataSrc;
                    img.removeAttribute('loading');
                }
            });
            return lazyImages.length;
        """
        driver.execute_script(js_strategy_1)
        time.sleep(3)
        
        # Strategy 2: Trigger scroll and visibility events specifically for product items
        js_strategy_2 = """
            console.log('Triggering Monte Carlo scroll and resize events...');
            const productItems = document.querySelectorAll('.product-item');
            productItems.forEach((item, index) => {
                try {
                    item.scrollIntoView({ behavior: 'auto', block: 'center' });
                    const images = item.querySelectorAll('img');
                    images.forEach(img => {
                        img.dispatchEvent(new Event('load'));
                        img.dispatchEvent(new Event('appear'));
                        img.dispatchEvent(new Event('inview'));
                        img.dispatchEvent(new Event('scroll'));
                    });
                } catch(e) {
                    console.log('Error with Monte Carlo product item', index, ':', e);
                }
            });
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
            window.dispatchEvent(new Event('load'));
            return productItems.length;
        """
        driver.execute_script(js_strategy_2)
        time.sleep(3)
        
        # Strategy 3: Handle Monte Carlo specific image containers
        js_strategy_3 = """
            console.log('Handling Monte Carlo specific lazy loading...');
            const imageWrappers = document.querySelectorAll(
                '.product-item__image-wrapper img, .product-item__image-wrapper--multiple img'
            );
            imageWrappers.forEach((img, index) => {
                const possibleSrcs = [
                    img.dataset.src, img.dataset.original, img.dataset.lazySrc, 
                    img.dataset.srcset, img.getAttribute('src')
                ];
                for (let src of possibleSrcs) {
                    if (src && src.includes('http') && !img.src.includes(src)) {
                        console.log('Loading Monte Carlo wrapper image', index, ':', src);
                        img.src = src;
                        break;
                    }
                }
                // Remove lazy loading classes
                img.classList.remove('lazyload', 'lazy');
            });
            return imageWrappers.length;
        """
        driver.execute_script(js_strategy_3)
        time.sleep(3)
        
        print("Monte Carlo lazy loading strategies completed")
        
    except Exception as e:
        print(f"Error in Monte Carlo forced lazy loading: {e}")


def debug_monte_carlo_structure(driver):
    """
    Debug function to inspect Monte Carlo's HTML structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("=== MONTE CARLO STRUCTURE ANALYSIS ===")
        
        # Check for the main product list container
        product_list = soup.select('.product-list__inner')
        print(f"Product list containers found: {len(product_list)}")
        
        # Check for different product item variants
        product_items_full = soup.select('.product-item.full_var')
        product_items_var5 = soup.select('.product-item.var-5')
        all_product_items = soup.select('.product-item')
        
        print(f"Product items (full_var): {len(product_items_full)}")
        print(f"Product items (var-5): {len(product_items_var5)}")
        print(f"Total product items: {len(all_product_items)}")
        
        # Analyze image wrappers
        image_wrappers = soup.select('.product-item__image-wrapper')
        image_wrappers_multiple = soup.select('.product-item__image-wrapper--multiple')
        
        print(f"Image wrappers: {len(image_wrappers)}")
        print(f"Image wrappers (multiple): {len(image_wrappers_multiple)}")
        
        # Analyze info sections
        info_sections = soup.select('.product-item__info')
        meta_sections = soup.select('.product-item-meta')
        titles = soup.select('.product-item-meta__title')
        prices = soup.select('.product-item-meta__price-list-container')
        
        print(f"Info sections: {len(info_sections)}")
        print(f"Meta sections: {len(meta_sections)}")
        print(f"Titles: {len(titles)}")
        print(f"Price containers: {len(prices)}")
        
        # Sample analysis
        if all_product_items:
            sample_item = all_product_items[0]
            print(f"\nSample product item classes: {sample_item.get('class', [])}")
            
            sample_image = sample_item.select_one('.product-item__image-wrapper img')
            if sample_image:
                print(f"Sample image attributes: {dict(sample_image.attrs)}")
                
            sample_title = sample_item.select_one('.product-item-meta__title')
            if sample_title:
                print(f"Sample title text: {sample_title.get_text(strip=True)[:50]}...")
                
            sample_price = sample_item.select_one('.price--highlight .visually-hidden')
            if sample_price:
                print(f"Sample price text: {sample_price.get_text(strip=True)}")
            
    except Exception as e:
        print(f"Error in Monte Carlo debug function: {e}")


def extract_monte_carlo_html_products(soup):
    """
    HTML parsing for Monte Carlo products based on the specified structure
    """
    html_products = []
    seen_products = set()  # To avoid duplicates
    
    print("\n=== STARTING MONTE CARLO HTML PARSING ===")
    
    # Find the main product list container
    product_list = soup.select_one('.product-list__inner')
    if not product_list:
        print("No product list container found!")
        return []
    
    # Find all product items (both variants)
    product_items = product_list.select('.product-item')
    print(f"Found {len(product_items)} product items")
    
    for idx, item in enumerate(product_items[:60]):  # Limit to avoid too many products
        try:
            # Extract product data using the specified structure
            title = extract_monte_carlo_title(item)
            price = extract_monte_carlo_price(item)
            image = extract_monte_carlo_image(item)
            link = extract_monte_carlo_link(item)
            
            # Create unique identifier to avoid duplicates
            product_id = f"{title}_{price}_{image[:50] if image != 'No image' else ''}"
            
            # Skip if already seen
            if product_id in seen_products:
                print(f"Skipping duplicate product {idx + 1}: {title[:50]}...")
                continue
                
            # Validate product quality
            if is_valid_monte_carlo_product(title, price, image, link):
                seen_products.add(product_id)
                html_products.append({
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                })
                
                print(f"✓ Product {len(html_products)}: {title[:50]}{'...' if len(title) > 50 else ''}")
                print(f"    Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            else:
                print(f"✗ Skipped invalid item {idx + 1}: {title[:50]}...")
                
        except Exception as e:
            print(f"Error processing Monte Carlo product {idx + 1}: {e}")
            continue
    
    return html_products


def extract_monte_carlo_title(item):
    """
    Extract title from Monte Carlo product item using the specified structure:
    div.product-item__info > div.product-item-meta > div.title-wish > [class].product-item-meta__title
    """
    try:
        # Follow the exact path you specified
        title_elem = item.select_one('.product-item__info .product-item-meta .title-wish .product-item-meta__title')
        
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text.strip()) > 3:
                return ' '.join(title_text.split())
        
        # Fallback: try just the title class
        title_elem = item.select_one('.product-item-meta__title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text.strip()) > 3:
                return ' '.join(title_text.split())
        
        # Another fallback: look for any link with text
        link_elem = item.select_one('a[href*="/products/"]')
        if link_elem:
            title_text = link_elem.get_text(strip=True)
            if title_text and len(title_text.strip()) > 3:
                return ' '.join(title_text.split())
        
    except Exception as e:
        print(f"Error extracting Monte Carlo title: {e}")
    
    return "No title"


def extract_monte_carlo_price(item):
    """
    Extract price from Monte Carlo product item using the specified structure:
    div.product-item-meta__price-list-container > div.price-list.price-list--centered > 
    span.price.price--highlight > span.visually-hidden
    """
    try:
        # Follow the exact path you specified
        price_elem = item.select_one(
            '.product-item-meta__price-list-container .price-list.price-list--centered '
            '.price.price--highlight .visually-hidden'
        )
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            if price_text:
                cleaned_price = clean_monte_carlo_price(price_text)
                if cleaned_price != "No price":
                    return cleaned_price
        
        # Fallback: try different price selectors
        price_selectors = [
            '.price--highlight .visually-hidden',
            '.price--highlight',
            '.price-list .price',
            '.product-item-meta__price-list-container .price',
            '[data-price]',
            '.money'
        ]
        
        for selector in price_selectors:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = (price_elem.get('data-price') or 
                             price_elem.get_text(strip=True))
                if price_text:
                    cleaned_price = clean_monte_carlo_price(price_text)
                    if cleaned_price != "No price":
                        return cleaned_price
        
    except Exception as e:
        print(f"Error extracting Monte Carlo price: {e}")
    
    return "No price"


def extract_monte_carlo_image(item):
    """
    Extract image from Monte Carlo product item using the specified structure:
    div.product-item__image-wrapper.product-item__image-wrapper--multiple > a > img
    """
    try:
        # Follow the exact path you specified
        img_elem = item.select_one(
            '.product-item__image-wrapper.product-item__image-wrapper--multiple a img'
        )
        
        if not img_elem:
            # Try without the --multiple modifier
            img_elem = item.select_one('.product-item__image-wrapper a img')
        
        if not img_elem:
            # Fallback to any image in the item
            img_elem = item.select_one('img')
        
        if img_elem:
            # Check primary src first
            src = img_elem.get('src', '')
            
            # Skip logo and placeholder images
            if src and not any(skip in src.lower() for skip in [
                'logo', 'placeholder', 'blank', 'loading', 'spinner'
            ]):
                if len(src) > 15:
                    return format_monte_carlo_image_url(src)
            
            # Check data attributes for lazy loading
            for attr in ['data-src', 'data-original', 'srcset', 'data-srcset']:
                data_src = img_elem.get(attr)
                if data_src:
                    # For srcset, take the first URL
                    if 'srcset' in attr:
                        data_src = data_src.split(' ')[0]
                    
                    if len(data_src) > 15:
                        return format_monte_carlo_image_url(data_src)
        
    except Exception as e:
        print(f"Error extracting Monte Carlo image: {e}")
    
    return "No image"


def extract_monte_carlo_link(item):
    """
    Extract link from Monte Carlo product item
    """
    try:
        # Look for links in the image wrapper (as per your structure)
        link_elem = item.select_one('.product-item__image-wrapper a')
        
        if not link_elem:
            # Fallback to any product link
            link_elem = item.select_one('a[href*="/products/"]')
        
        if not link_elem:
            # Try any link in the item
            link_elem = item.select_one('a')
        
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            
            if href.startswith('/'):
                return "https://www.montecarlo.in" + href
            elif href.startswith('http'):
                return href
        
    except Exception as e:
        print(f"Error extracting Monte Carlo link: {e}")
    
    return "#"


def is_valid_monte_carlo_product(title, price, image, link):
    """
    Validate if the scraped data represents a valid Monte Carlo product
    """
    # Title validation
    if (title == "No title" or 
        len(title) < 3 or 
        any(invalid in title.lower() for invalid in [
            'log in', 'login', 'sign up', 'register', 'create account',
            'forgot password', 'newsletter', 'subscribe'
        ])):
        return False
    
    # Must have either price or valid product link
    has_price = price != "No price"
    has_product_link = link != "#" and ("/products/" in link or "montecarlo.in" in link)
    
    if not (has_price or has_product_link):
        return False
    
    return True


def clean_monte_carlo_price(price_text):
    """
    Clean price text for Monte Carlo
    """
    if not price_text:
        return "No price"
    
    try:
        # Remove extra whitespace
        price_text = ' '.join(str(price_text).split())
        
        # Extract price using regex patterns
        patterns = [
            r'₹\s*([\d,]+\.?\d*)',
            r'Rs\.?\s*([\d,]+\.?\d*)', 
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*₹',
            r'([\d,]+\.?\d*)\s*Rs',
            r'(\d{2,6})'  # Fallback for plain numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_text)
            if match:
                number = match.group(1).replace(',', '')
                try:
                    # Validate it's a number and reasonable price range
                    price_val = float(number)
                    if 100 <= price_val <= 100000:  # Reasonable price range
                        # Format based on currency symbol
                        if '₹' in price_text:
                            return f"₹{number}"
                        elif 'Rs' in price_text:
                            return f"Rs.{number}"
                        elif '$' in price_text:
                            return f"${number}"
                        else:
                            return f"₹{number}"
                        
                except ValueError:
                    continue
        
        return "No price"
        
    except Exception:
        return "No price"


def format_monte_carlo_image_url(url):
    """
    Format image URL to ensure it's complete and accessible
    """
    if not url:
        return "No image"
    
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.montecarlo.in' + url
    elif url.startswith('http'):
        return url
    else:
        return 'https://www.montecarlo.in/' + url.lstrip('/')

