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
    You need to implement this based on your Selenium setup
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_westside(query):
    """
    Enhanced Westside scraper with comprehensive image detection and data extraction
    """
    driver = get_driver()
    
    # Westside search URL structure
    encoded_query = quote(query)
    url = f"https://www.westside.com/search?q={encoded_query}"
    print(f"Scraping Westside URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for initial page load
        wait = WebDriverWait(driver, 25)
        time.sleep(5)
        
        # Enhanced lazy loading scroll for Westside
        enhanced_westside_scroll(driver, max_scrolls=20, scroll_pause=3)
        
        # Force load any remaining lazy images with multiple strategies
        force_westside_lazy_loading(driver)
        
        # Additional wait to ensure all content is loaded
        time.sleep(7)
        
        # Debug the structure to understand Westside's HTML
        print("\n=== DEBUGGING WESTSIDE STRUCTURE ===")
        debug_westside_structure(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract products using enhanced HTML parsing
        html_products = extract_westside_html_products(soup)
        
        print(f"Found {len(html_products)} products from HTML parsing")
        
        # Populate the data dictionary
        for product in html_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print detailed summary
        images_found = len([img for img in data['Image'] if img != 'No image'])
        prices_found = len([price for price in data['Price'] if price != 'No price'])
        print(f"\n=== WESTSIDE SCRAPING SUMMARY ===")
        print(f"Total products: {len(html_products)}")
        print(f"Images found: {images_found}")
        print(f"Prices found: {prices_found}")
        if html_products:
            # Added a check to prevent division by zero
            success_rate_images = (images_found / len(html_products)) * 100 if len(html_products) > 0 else 0
            success_rate_prices = (prices_found / len(html_products)) * 100 if len(html_products) > 0 else 0
            print(f"Success rate - Images: {success_rate_images:.1f}%")
            print(f"Success rate - Prices: {success_rate_prices:.1f}%")
        else:
            print("Success rate: 0%")
        
        # Print sample of first few products for debugging
        print(f"\n=== SAMPLE PRODUCTS ===")
        for i, product in enumerate(html_products[:3]):
            print(f"Product {i+1}:")
            print(f"  Title: {product['title'][:50]}...")
            print(f"  Price: {product['price']}")
            print(f"  Image: {'✓' if product['image'] != 'No image' else '✗'} ({product['image'][:50]}...)")
            print(f"  Link: {product['link'][:50]}...")
        
    except Exception as e:
        print(f"Error scraping Westside: {e}")
        try:
            driver.save_screenshot("westside_error.png")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'Westside'
    return df

def enhanced_westside_scroll(driver, max_scrolls=20, scroll_pause=3):
    """
    Enhanced scrolling function specifically designed for Westside's lazy loading.
    """
    print("Starting enhanced Westside lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        time.sleep(scroll_pause)
        
        # **CORRECTED JAVASCRIPT** - The selector string is now valid JavaScript.
        js_script = """
            return document.querySelectorAll(
                '.product-card, .product-item, .product-tile, .card, ' +
                '[class*="product"], [class*="item"], [class*="card"], ' +
                'article, .grid-item, .collection-item'
            ).length;
        """
        products_loaded = driver.execute_script(js_script)
        
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
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(3)
    
    print("Enhanced Westside scrolling complete")

def force_westside_lazy_loading(driver):
    """
    Force load lazy images and content specific to Westside with multiple strategies
    """
    try:
        print("Forcing Westside lazy loading...")
        
        # **CORRECTED JAVASCRIPT** - Strategy 1
        js_strategy_1 = """
            console.log('Starting image lazy loading...');
            const lazyImages = document.querySelectorAll(
                'img[data-src], img[data-original], img[data-lazy-src], ' +
                'img[data-srcset], img[loading="lazy"], img[class*="lazy"], img[class*="lazyload"]'
            );
            console.log('Found', lazyImages.length, 'lazy images');
            lazyImages.forEach((img, index) => {
                const dataSrc = img.dataset.src || img.dataset.original || img.dataset.lazySrc || img.dataset.srcset;
                if (dataSrc && !img.src.includes(dataSrc)) {
                    console.log('Loading image', index, ':', dataSrc);
                    img.src = dataSrc;
                    img.removeAttribute('loading');
                }
            });
            return lazyImages.length;
        """
        driver.execute_script(js_strategy_1)
        time.sleep(3)
        
        # Strategy 2
        js_strategy_2 = """
            console.log('Triggering scroll and resize events...');
            const allImages = document.querySelectorAll('img');
            allImages.forEach((img, index) => {
                try {
                    img.scrollIntoView({ behavior: 'auto', block: 'center' });
                    img.dispatchEvent(new Event('load'));
                    img.dispatchEvent(new Event('appear'));
                    img.dispatchEvent(new Event('inview'));
                } catch(e) {
                    console.log('Error with image', index, ':', e);
                }
            });
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
            window.dispatchEvent(new Event('load'));
            return allImages.length;
        """
        driver.execute_script(js_strategy_2)
        time.sleep(3)
        
        # **CORRECTED JAVASCRIPT** - Strategy 3
        js_strategy_3 = """
            console.log('Handling Shopify-specific lazy loading...');
            const shopifyImages = document.querySelectorAll(
                'img[class*="Image--lazyLoad"], img[class*="lazyload"], img[data-widths], ' +
                'img[data-sizes], .product-single__photo img, .product-photo-container img, .grid-product__image img'
            );
            shopifyImages.forEach((img, index) => {
                const possibleSrcs = [
                    img.dataset.src, img.dataset.original, img.dataset.lazySrc, img.dataset.srcset
                ];
                for (let src of possibleSrcs) {
                    if (src && !img.src.includes(src)) {
                        console.log('Loading Shopify image', index, ':', src);
                        img.src = src;
                        break;
                    }
                }
                img.classList.remove('lazyload', 'Image--lazyLoad');
            });
            return shopifyImages.length;
        """
        driver.execute_script(js_strategy_3)
        time.sleep(3)
        
        # Strategy 4
        js_strategy_4 = """
            console.log('Handling background images...');
            const bgElements = document.querySelectorAll('[data-bg], [data-background], [data-bg-src]');
            bgElements.forEach((el, index) => {
                const bgSrc = el.dataset.bg || el.dataset.background || el.dataset.bgSrc;
                if (bgSrc) {
                    el.style.backgroundImage = `url("${bgSrc}")`;
                    console.log('Set background image', index, ':', bgSrc);
                }
            });
            return bgElements.length;
        """
        driver.execute_script(js_strategy_4)
        
        print("Westside lazy loading strategies completed")
        
    except Exception as e:
        print(f"Error in Westside forced lazy loading: {e}")

def debug_westside_structure(driver):
    """
    Debug function to inspect Westside's HTML structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("=== WESTSIDE STRUCTURE ANALYSIS ===")
        
        potential_containers = [
            '.product-card', '.product-item', '.product-tile', '.card',
            '.grid-item', '.collection-item', 'article', '[class*="product"]',
            '[class*="item"]', '[class*="card"]', '[class*="tile"]',
            '[data-product]', '[data-id]'
        ]
        
        best_selector = None
        max_products = 0
        
        for selector in potential_containers:
            elements = soup.select(selector)
            if elements:
                product_like = []
                for elem in elements:
                    if (elem.find('img') and 
                        elem.find('a') and 
                        len(elem.get_text(strip=True)) > 20 and
                        len(elem.get_text(strip=True)) < 300):
                        product_like.append(elem)
                
                if len(product_like) > max_products:
                    max_products = len(product_like)
                    best_selector = selector
                
                print(f"Selector '{selector}': {len(elements)} total, {len(product_like)} product-like")
        
        print(f"Best selector: {best_selector} with {max_products} products")
        
        all_images = soup.find_all('img')
        print(f"\nImage analysis: {len(all_images)} total images found")
        
        lazy_patterns = {
            'data-src': len(soup.find_all('img', attrs={'data-src': True})),
            'data-original': len(soup.find_all('img', attrs={'data-original': True})),
            'data-lazy-src': len(soup.find_all('img', attrs={'data-lazy-src': True})),
            'loading="lazy"': len(soup.find_all('img', attrs={'loading': 'lazy'})),
            'class contains lazy': len([img for img in all_images if any('lazy' in cls.lower() for cls in img.get('class', []))])
        }
        
        print("Lazy loading patterns found:")
        for pattern, count in lazy_patterns.items():
            if count > 0:
                print(f"  {pattern}: {count} images")
        
        print("\nSample image analysis:")
        for i, img in enumerate(all_images[:5]):
            attrs = dict(img.attrs)
            print(f"  Image {i+1}: {attrs}")
            
    except Exception as e:
        print(f"Error in Westside debug function: {e}")

def extract_westside_html_products(soup):
    """
    Enhanced HTML parsing for Westside products with better filtering
    """
    html_products = []
    seen_products = set()  # To avoid duplicates
    
    print("\n=== STARTING WESTSIDE HTML PARSING ===")
    
    # More specific selectors for Westside (Shopify-based)
    product_selectors = [
        'article.card-wrapper',
        '.card-wrapper',
        '.grid__item .card',
        '.product-card-wrapper',
        '.collection .card',
        'li.grid__item',
        '.grid-product',
        '.product-item',
        '[data-product-handle]'
    ]
    
    items = []
    selector_used = None
    
    # Try each selector and pick the one with most valid products
    for selector in product_selectors:
        try:
            potential_items = soup.select(selector)
            
            # Filter out invalid items
            filtered_items = []
            for item in potential_items:
                # Check if it has basic product structure
                if not (item.find('img') and item.find('a')):
                    continue
                    
                # Check for product-specific attributes
                has_product_handle = item.get('data-product-handle')
                has_product_link = item.find('a', href=lambda x: x and '/products/' in x)
                has_price_element = item.find(class_=lambda x: x and 'price' in x.lower())
                
                if has_product_handle or has_product_link or has_price_element:
                    filtered_items.append(item)
            
            if len(filtered_items) > len(items):
                items = filtered_items
                selector_used = selector
                
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue
    
    print(f"Westside: Found {len(items)} items using selector: {selector_used}")
    
    # Process items with duplicate detection
    for idx, item in enumerate(items[:30]):
        try:
            # Extract product data
            title = extract_westside_title_improved(item)
            price = extract_westside_price_improved(item)
            image = extract_westside_image_improved(item)
            link = extract_westside_link_improved(item)
            
            # Create unique identifier to avoid duplicates
            product_id = f"{title}_{price}_{image[:50] if image != 'No image' else ''}"
            
            # Skip if already seen
            if product_id in seen_products:
                print(f"Skipping duplicate product {idx + 1}: {title[:30]}...")
                continue
                
            # Validate product quality
            if is_valid_westside_product(title, price, image, link):
                seen_products.add(product_id)
                html_products.append({
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                })
                
                print(f"✓ Product {len(html_products)}: {title[:40]}{'...' if len(title) > 40 else ''}")
                print(f"    Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            else:
                print(f"✗ Skipped invalid item {idx + 1}: {title[:30]}...")
                
        except Exception as e:
            print(f"Error processing Westside product {idx + 1}: {e}")
            continue
    
    return html_products

def extract_westside_title_improved(item):
    """Improved title extraction with better selectors"""
    
    # Westside/Shopify specific title selectors
    title_selectors = [
        '.card__heading a',
        '.card__information .card__heading',
        '.card-information__text h3',
        '.full-unstyled-link',
        '.card__content .card__information h3',
        'h3.card__heading a',
        '.product-item-meta__title',
        'a[href*="/products/"]'
    ]
    
    for selector in title_selectors:
        try:
            elem = item.select_one(selector)
            if elem:
                title_text = elem.get_text(strip=True)
                
                # Additional validation
                if (title_text and 
                    len(title_text.strip()) > 5 and 
                    len(title_text.strip()) < 150 and
                    not any(invalid in title_text.lower() for invalid in [
                        'log in', 'sign up', 'register', 'login', 
                        'create account', 'forgot password'
                    ])):
                    
                    return ' '.join(title_text.split())
        except:
            continue
    
    # Fallback: look for any link with product URL
    try:
        product_link = item.find('a', href=lambda x: x and '/products/' in x)
        if product_link:
            title = product_link.get_text(strip=True)
            if title and len(title) > 5 and 'log in' not in title.lower():
                return title
    except:
        pass
    
    return "No title"

def extract_westside_price_improved(item):
    """Improved price extraction for Westside"""
    
    price_selectors = [
        '.price-item--regular',
        '.price__regular .price-item',
        '.price .money',
        '.card__information .price',
        '.product-price .money',
        'span.money',
        '.price-current',
        '.regular-price',
        '[data-price]'
    ]
    
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                # Check for data attributes first
                price_text = (price_elem.get('data-price') or 
                             price_elem.get_text(strip=True))
                
                if price_text:
                    cleaned_price = clean_price_improved(price_text)
                    if cleaned_price != "No price":
                        return cleaned_price
        except:
            continue
    
    return "No price"

def extract_westside_image_improved(item):
    """Improved image extraction for Westside"""
    
    try:
        imgs = item.find_all('img')
        for img in imgs:
            # Check primary src first
            src = img.get('src', '')
            
            # Skip logo and placeholder images
            if any(skip in src.lower() for skip in [
                'logo', 'placeholder', 'blank', 'loading', 'spinner'
            ]):
                continue
            
            # Look for product images
            if (src and len(src) > 15 and 
                any(indicator in src.lower() for indicator in [
                    'product', '.jpg', '.jpeg', '.png', '.webp', 'cdn'
                ])):
                
                return format_westside_image_url(src)
            
            # Check data attributes for lazy loading
            for attr in ['data-src', 'data-original', 'srcset']:
                data_src = img.get(attr)
                if data_src:
                    # For srcset, take the first URL
                    if attr == 'srcset':
                        data_src = data_src.split(' ')[0]
                    
                    if (len(data_src) > 15 and 
                        any(indicator in data_src.lower() for indicator in [
                            'product', '.jpg', '.jpeg', '.png', '.webp'
                        ])):
                        return format_westside_image_url(data_src)
    
    except Exception as e:
        print(f"Error extracting image: {e}")
    
    return "No image"

def extract_westside_link_improved(item):
    """Improved link extraction for Westside"""
    
    # Look for product links specifically
    link_selectors = [
        'a[href*="/products/"]',
        '.card__heading a',
        '.full-unstyled-link',
        'a.card__link'
    ]
    
    for selector in link_selectors:
        try:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                
                # Ensure it's a product link
                if '/products/' in href:
                    if href.startswith('/'):
                        return "https://www.westside.com" + href
                    elif href.startswith('http'):
                        return href
        except:
            continue
    
    return "#"

def is_valid_westside_product(title, price, image, link):
    """Validate if the scraped data represents a valid product"""
    
    # Title validation
    if (title == "No title" or 
        len(title) < 5 or 
        any(invalid in title.lower() for invalid in [
            'log in', 'login', 'sign up', 'register', 'create account',
            'forgot password', 'newsletter', 'subscribe'
        ])):
        return False
    
    # Must have either price or valid product link
    has_price = price != "No price"
    has_product_link = link != "#" and "/products/" in link
    
    if not (has_price or has_product_link):
        return False
    
    return True

def clean_price_improved(price_text):
    """Improved price cleaning function"""
    if not price_text:
        return "No price"
    
    try:
        # Remove extra whitespace
        price_text = ' '.join(str(price_text).split())
        
        # Extract price using regex
        patterns = [
            r'₹\s*([\d,]+\.?\d*)',
            r'Rs\.?\s*([\d,]+\.?\d*)', 
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*₹',
            r'([\d,]+\.?\d*)\s*Rs'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_text)
            if match:
                number = match.group(1).replace(',', '')
                try:
                    # Validate it's a number
                    float(number)
                    
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

def format_westside_image_url(url):
    """Format image URL to ensure it's complete"""
    if not url:
        return "No image"
    
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.westside.com' + url
    elif url.startswith('http'):
        return url
    else:
        return 'https://www.westside.com/' + url.lstrip('/')



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
        
        # Shopify lazy loading scroll (different approach than H&M)
        shopify_lazy_loading_scroll(driver, max_scrolls=10, scroll_pause=2)
        
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
                                    
                                    price = "No price"
                                    if 'price' in product:
                                        price_value = product['price']
                                        if isinstance(price_value, (int, float)):
                                            price = f"₹{price_value/100:.0f}"
                                    elif 'variants' in product and product.get('variants'):
                                        variant = product['variants'][0]
                                        if 'price' in variant:
                                            price_value = variant['price']
                                            if isinstance(price_value, str):
                                                price_value = float(price_value.replace(',', ''))
                                            if isinstance(price_value, (int, float)):
                                                price = f"₹{price_value/100:.0f}"

                                    image = "No image"
                                    if product.get('featured_image'):
                                        image = product['featured_image']
                                        if not image.startswith('http'):
                                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                                    elif product.get('images'):
                                        image = product['images'][0]
                                        if not image.startswith('http'):
                                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                                    
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
                title = extract_levis_title(item, idx)
                
                print(f"\n--- Processing Levi's item {idx + 1}: {title[:30]}... ---")
                
                price = extract_shopify_price(item)
                
                image = "No image"
                all_imgs = item.find_all('img')
                for img in all_imgs:
                    src = img.get('data-src') or img.get('src')
                    if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        image = src.split('?')[0] # Clean up URL params
                        if not image.startswith('http'):
                            image = 'https:' + image if image.startswith('//') else 'https://levi.in' + image
                        break
                        
                link = "#"
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
            success_rate_titles = (titles_found / len(all_products)) * 100 if len(all_products) > 0 else 0
            success_rate_images = (images_found / len(all_products)) * 100 if len(all_products) > 0 else 0
            success_rate_prices = (prices_found / len(all_products)) * 100 if len(all_products) > 0 else 0
            print(f"Success rate - Titles: {success_rate_titles:.1f}%")
            print(f"Success rate - Images: {success_rate_images:.1f}%")
            print(f"Success rate - Prices: {success_rate_prices:.1f}%")
        
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
    title_selectors = [
        '.st-name span', 'a.product-item__title', '.product-block__title-link',
        '.product-item-meta__title', 'h3.product-title a', '.product-card__title',
        'a.full-unstyled-link', '.card__heading a', 'h2.product-title'
    ]

    for selector in title_selectors:
        title_element = item.select_one(selector)
        if title_element:
            title = title_element.get_text(strip=True)
            if title and len(title) > 5:
                return title
    
    print(f"Could not find title for item {item_index + 1}, generating placeholder.")
    return f"Levi's Product {item_index + 1}"

def shopify_lazy_loading_scroll(driver, max_scrolls=10, scroll_pause=2):
    """
    Shopify-specific scrolling function
    Shopify sites often load content differently than other platforms
    """
    print("Starting Shopify lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for i in range(max_scrolls):
        scroll_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(scroll_pause)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height and i > max_scrolls - 3:
            print("No new content loading, finishing scroll...")
            break
        else:
            last_height = new_height
        
        print(f"Shopify scroll {i+1}/{max_scrolls}")
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)
    
    print("Shopify scrolling complete")

def extract_shopify_price(item):
    """
    Shopify-specific price extraction for Levi's
    """
    price = "No price"
    
    price_selectors = [
        '.price', '.product-price', '.money', 'span.money', 'div.money',
        '.price-current', '.current-price', '.regular-price', '.sale-price',
        '.price-item', '.price-regular', '.product-price-current',
        '.grid-item-price', '.item-price', '.product-info .price',
        '.product-details .price', '.product-form .price', '[data-price]',
        'span[class*="price"]', 'div[class*="price"]', 'span[class*="money"]',
        'div[class*="money"]'
    ]
    
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                if not price_text:
                    price_text = (price_elem.get('data-price') or 
                                  price_elem.get('data-money') or '')
                
                if price_text and ('₹' in price_text or 'Rs' in price_text or '$' in price_text or 
                                   any(c.isdigit() for c in price_text)):
                    cleaned_price = clean_price(price_text)
                    if cleaned_price != "No price":
                        # This print statement can be noisy, you might want to comment it out for cleaner logs
                        # print(f"Found Shopify price using selector '{selector}': {cleaned_price}")
                        return cleaned_price
        except Exception:
            continue
    
    try:
        all_spans = item.find_all(['span', 'div', 'p'])
        for span in all_spans:
            text = span.get_text(strip=True)
            if text and re.search(r'₹\s*[\d,]+|Rs\s*[\d,]+|\$\s*[\d,]+', text):
                cleaned_price = clean_price(text)
                if cleaned_price != "No price":
                    # This print statement can be noisy as well
                    # print(f"Found Shopify price in span/div: {cleaned_price}")
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

        


def scrape_urbanic(query):
    """
    Enhanced Urbanic scraper targeting specific class structure
    """
    driver = get_driver()
    
    # Urbanic India search URL structure
    clean_query = query.replace(' ', '').lower()
    url = f"https://in.urbanic.com/search/result/{clean_query}?source=3"
    print(f"Scraping Urbanic URL: {url}")
    
    data = {"Title": [], "Price": [], "Image": [], "Link": []}
    
    try:
        driver.get(url)
        
        # Wait for React app to load
        wait = WebDriverWait(driver, 30)
        print("Waiting for Urbanic React app to load...")
        time.sleep(10)
        
        # Wait specifically for product cards
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                "a[class*='index-module_verticalCard'], a[class*='verticalCard']")))
            print("Product cards found!")
        except:
            print("Product cards not found, continuing anyway...")
        
        # Enhanced scrolling to load more products
        enhanced_urbanic_targeted_scroll(driver, max_scrolls=25, scroll_pause=3)
        
        # Force load all images
        force_urbanic_targeted_loading(driver)
        
        # Additional wait
        time.sleep(8)
        
        # Debug and extract products
        print("\n=== DEBUGGING URBANIC TARGETED STRUCTURE ===")
        debug_urbanic_targeted_structure(driver)
        
        # Extract products using targeted approach
        html_products = extract_urbanic_targeted_products(driver)
        
        print(f"Found {len(html_products)} products from targeted extraction")
        
        # Populate the data dictionary
        for product in html_products:
            data["Title"].append(product['title'])
            data["Price"].append(product['price'])
            data["Image"].append(product['image'])
            data["Link"].append(product['link'])
        
        # Print detailed summary
        images_found = len([img for img in data['Image'] if img != 'No image'])
        prices_found = len([price for price in data['Price'] if price != 'No price'])
        print(f"\n=== URBANIC SCRAPING SUMMARY ===")
        print(f"Total products: {len(html_products)}")
        print(f"Images found: {images_found}")
        print(f"Prices found: {prices_found}")
        if html_products:
            success_rate_images = (images_found / len(html_products)) * 100
            success_rate_prices = (prices_found / len(html_products)) * 100
            print(f"Success rate - Images: {success_rate_images:.1f}%")
            print(f"Success rate - Prices: {success_rate_prices:.1f}%")
        else:
            print("Success rate: 0%")
        
        # Print sample products
        print(f"\n=== SAMPLE PRODUCTS ===")
        for i, product in enumerate(html_products[:3]):
            print(f"Product {i+1}:")
            print(f"  Title: {product['title'][:50]}...")
            print(f"  Price: {product['price']}")
            print(f"  Image: {'✓' if product['image'] != 'No image' else '✗'}")
            print(f"  Link: {product['link'][:50]}...")
        
    except Exception as e:
        print(f"Error scraping Urbanic: {e}")
        try:
            driver.save_screenshot("urbanic_targeted_error.png")
            with open("urbanic_targeted_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved error screenshot and page source")
        except:
            pass
    
    finally:
        driver.quit()
    
    df = pd.DataFrame(data)
    df['Source'] = 'Urbanic'
    return df


def enhanced_urbanic_targeted_scroll(driver, max_scrolls=25, scroll_pause=3):
    """
    Targeted scrolling for Urbanic to load product cards
    """
    print("Starting targeted Urbanic scrolling...")
    
    last_product_count = 0
    no_change_count = 0
    
    for i in range(max_scrolls):
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        
        # Count product cards specifically
        js_count_script = """
            const productCards = document.querySelectorAll(
                'a[class*="index-module_verticalCard"], a[class*="verticalCard"]'
            );
            return productCards.length;
        """
        
        current_product_count = driver.execute_script(js_count_script)
        
        if current_product_count > last_product_count:
            last_product_count = current_product_count
            no_change_count = 0
            print(f"Scroll {i+1}/{max_scrolls}: {current_product_count} product cards found")
        else:
            no_change_count += 1
            print(f"Scroll {i+1}/{max_scrolls}: No new products ({no_change_count}/5)")
        
        # Stop if no new products for 5 consecutive scrolls
        if no_change_count >= 5:
            print("No new products detected, stopping scroll...")
            break
    
    print(f"Targeted scrolling complete. Total products found: {last_product_count}")


def force_urbanic_targeted_loading(driver):
    """
    Force load images in product cards
    """
    try:
        print("Forcing targeted image loading...")
        
        js_image_loading = """
            console.log('Starting targeted image loading...');
            
            // Find all product cards
            const productCards = document.querySelectorAll(
                'a[class*="index-module_verticalCard"], a[class*="verticalCard"]'
            );
            
            console.log('Found', productCards.length, 'product cards');
            
            let processedImages = 0;
            productCards.forEach((card, cardIndex) => {
                try {
                    // Find image container within the card
                    const imageContainer = card.querySelector('div[class*="ub-image"], div[class*="index-module_image"]');
                    if (imageContainer) {
                        const images = imageContainer.querySelectorAll('img');
                        images.forEach((img) => {
                            try {
                                // Scroll image into view
                                img.scrollIntoView({behavior: 'auto', block: 'nearest'});
                                
                                // Trigger loading events
                                img.dispatchEvent(new Event('load'));
                                img.dispatchEvent(new Event('appear'));
                                
                                // Handle lazy loading attributes
                                if (img.dataset.src && !img.src.includes(img.dataset.src)) {
                                    img.src = img.dataset.src;
                                }
                                
                                processedImages++;
                            } catch(e) {
                                console.log('Error processing image:', e);
                            }
                        });
                    }
                } catch(e) {
                    console.log('Error processing card', cardIndex, ':', e);
                }
            });
            
            console.log('Processed', processedImages, 'images in product cards');
            return processedImages;
        """
        
        processed_images = driver.execute_script(js_image_loading)
        print(f"Processed {processed_images} images in product cards")
        time.sleep(3)
        
    except Exception as e:
        print(f"Error in targeted image loading: {e}")


def debug_urbanic_targeted_structure(driver):
    """
    Debug the specific Urbanic structure
    """
    try:
        print("=== URBANIC TARGETED STRUCTURE ANALYSIS ===")
        
        # Check for product cards
        product_card_selectors = [
            'a[class*="index-module_verticalCard"]',
            'a[class*="verticalCard"]',
            'a.index-module_verticalCard__zl8sA',
            'a[class*="index-module_m__y9ZaN"]',
            'a[class*="index-module_urbanic__gqH-h"]'
        ]
        
        for selector in product_card_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Selector '{selector}': {len(elements)} elements")
                
                if len(elements) > 0:
                    # Analyze first element
                    first_element = elements[0]
                    classes = first_element.get_attribute('class')
                    href = first_element.get_attribute('href')
                    print(f"  First element classes: {classes}")
                    print(f"  First element href: {href}")
                    
                    # Check for image container
                    image_containers = first_element.find_elements(By.CSS_SELECTOR, 
                        'div[class*="ub-image"], div[class*="index-module_image"]')
                    print(f"  Image containers in first element: {len(image_containers)}")
                    
                    if image_containers:
                        img_container = image_containers[0]
                        img_classes = img_container.get_attribute('class')
                        print(f"  Image container classes: {img_classes}")
                        
                        images = img_container.find_elements(By.TAG_NAME, 'img')
                        print(f"  Images in container: {len(images)}")
                        
                        if images:
                            img = images[0]
                            img_src = img.get_attribute('src')
                            img_classes = img.get_attribute('class')
                            print(f"  First image src: {img_src[:100]}...")
                            print(f"  First image classes: {img_classes}")
            
            except Exception as e:
                print(f"Error with selector '{selector}': {e}")
        
        # Check page structure
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Look for the specific classes mentioned
        vertical_cards = soup.find_all('a', class_=lambda x: x and 'verticalCard' in str(x))
        print(f"\nBeautifulSoup found {len(vertical_cards)} vertical cards")
        
        if vertical_cards:
            first_card = vertical_cards[0]
            print(f"First card classes: {first_card.get('class')}")
            print(f"First card href: {first_card.get('href')}")
            
            # Look for image container
            image_div = first_card.find('div', class_=lambda x: x and ('ub-image' in str(x) or 'image' in str(x)))
            if image_div:
                print(f"Image div classes: {image_div.get('class')}")
                img = image_div.find('img')
                if img:
                    print(f"Image src: {img.get('src', 'No src')}")
                    print(f"Image classes: {img.get('class')}")
        
    except Exception as e:
        print(f"Error in targeted debug: {e}")


def extract_urbanic_targeted_products(driver):
    """
    Extract products using the exact class structure identified
    """
    products = []
    print("\n=== STARTING TARGETED PRODUCT EXTRACTION ===")
    
    try:
        # Target the specific product card classes
        product_card_selectors = [
            'a[class*="index-module_verticalCard"]',
            'a[class*="verticalCard"]',
            'a.index-module_verticalCard__zl8sA'
        ]
        
        product_cards = []
        used_selector = None
        
        # Find the selector that works
        for selector in product_card_selectors:
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(cards) > len(product_cards):
                    product_cards = cards
                    used_selector = selector
            except:
                continue
        
        print(f"Using selector: {used_selector}")
        print(f"Found {len(product_cards)} product cards")
        
        # Extract data from each product card
        for i, card in enumerate(product_cards[:15]):  # Limit to first 20
            try:
                print(f"Processing product card {i+1}...")
                
                # Extract link (href of the card)
                link = card.get_attribute('href') or "#"
                if link.startswith('/'):
                    link = 'https://in.urbanic.com' + link
                
                # Extract title and price from card text
                card_text = card.text.strip()
                title = extract_title_from_text(card_text)
                price = extract_price_from_text(card_text)
                
                # Extract image from image container
                image = extract_image_from_card(card)
                
                # Create product data
                product_data = {
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                }
                
                # Validate and add product
                if (product_data['title'] != "No title" or 
                    product_data['price'] != "No price" or 
                    product_data['image'] != "No image"):
                    
                    products.append(product_data)
                    print(f"✓ Product {len(products)}: {title[:40]}... | {price} | Image: {'✓' if image != 'No image' else '✗'}")
                else:
                    print(f"✗ Skipped product {i+1}: No valid data")
                
            except Exception as e:
                print(f"Error processing product card {i+1}: {e}")
                continue
        
    except Exception as e:
        print(f"Error in targeted extraction: {e}")
    
    return products


def extract_title_from_text(text):
    """Extract title from card text"""
    if not text or len(text) < 5:
        return "No title"
    
    # Split text into lines and find the title
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        # Skip lines that look like prices
        if any(curr in line for curr in ['₹', 'Rs', '$']):
            continue
        
        # Skip very short lines or navigation text
        if len(line) < 5 or any(skip in line.lower() for skip in [
            'new', 'sale', 'off', '%', 'free', 'shipping'
        ]):
            continue
        
        # This line is likely the title
        if len(line) > 5 and len(line) < 200:
            return line
    
    # Fallback: use first meaningful line
    for line in lines:
        if len(line) > 5 and len(line) < 200:
            return line
    
    return "No title"


def extract_price_from_text(text):
    """Extract price from card text"""
    if not text:
        return "No price"
    
    # Look for price patterns in the text
    price_patterns = [
        r'₹\s*([\d,]+\.?\d*)',
        r'Rs\.?\s*([\d,]+\.?\d*)', 
        r'\$\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*₹',
        r'([\d,]+\.?\d*)\s*Rs'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            number = match.group(1).replace(',', '')
            try:
                price_float = float(number)
                if 10 <= price_float <= 100000:  # reasonable price range
                    if '₹' in text:
                        return f"₹{number}"
                    elif 'Rs' in text:
                        return f"Rs.{number}"
                    elif '$' in text:
                        return f"${number}"
                    else:
                        return f"₹{number}"
            except ValueError:
                continue
    
    return "No price"


def extract_image_from_card(card_element):
    """Extract image from product card"""
    try:
        # Look for image container with specific classes
        image_container_selectors = [
            'div[class*="ub-image"]',
            'div[class*="index-module_image"]',
            'div.ub-image.index-module_image__7icpD',
            'div[class*="image"]'
        ]
        
        for selector in image_container_selectors:
            try:
                image_containers = card_element.find_elements(By.CSS_SELECTOR, selector)
                if image_containers:
                    container = image_containers[0]
                    
                    # Find images within the container
                    images = container.find_elements(By.TAG_NAME, 'img')
                    for img in images:
                        src = img.get_attribute('src')
                        if src and len(src) > 10:
                            # Skip placeholder images
                            if any(skip in src.lower() for skip in ['placeholder', 'blank', 'loading']):
                                continue
                            
                            return format_urbanic_image_url(src)
                        
                        # Check data attributes for lazy loading
                        for attr in ['data-src', 'data-original']:
                            data_src = img.get_attribute(attr)
                            if data_src and len(data_src) > 10:
                                return format_urbanic_image_url(data_src)
            except:
                continue
        
        # Fallback: look for any image in the card
        all_images = card_element.find_elements(By.TAG_NAME, 'img')
        for img in all_images:
            src = img.get_attribute('src')
            if src and len(src) > 10:
                return format_urbanic_image_url(src)
    
    except Exception as e:
        print(f"Error extracting image: {e}")
    
    return "No image"


def format_urbanic_image_url(url):
    """Format image URL to ensure it's complete"""
    if not url:
        return "No image"
    
    if url.startswith('data:'):
        return "No image"  # Skip data URLs
    
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://in.urbanic.com' + url
    elif url.startswith('http'):
        return url
    else:
        return 'https://in.urbanic.com/' + url.lstrip('/')
