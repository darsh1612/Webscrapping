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


def scrape_libas(query):
    """
    Enhanced Libas scraper that scrapes the first two pages of results.
    """
    driver = get_driver()
    encoded_query = quote(query)
    base_url = f"https://www.libas.in/search?q={encoded_query}"
    
    all_products = []

    try:
        for page_num in range(1, 3): # Scrape pages 1 and 2
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}&p={page_num}"

            print(f"\n--- Scraping Libas Page {page_num}: {url} ---")
            
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 25)
                # Check for a specific element that indicates products are present
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-v-74577c89], .product-card, .st-product')))
                time.sleep(5)
            except:
                print(f"No products found on page {page_num}, or page failed to load. Stopping.")
                break

            enhanced_libas_scroll(driver, max_scrolls=20, scroll_pause=3)
            force_libas_lazy_loading(driver)
            time.sleep(7)

            print(f"\n=== DEBUGGING LIBAS STRUCTURE (Page {page_num}) ===")
            debug_libas_structure(driver)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            html_products = extract_libas_html_products(soup)
            print(f"Found {len(html_products)} products from HTML parsing on page {page_num}")
            all_products.extend(html_products)

    except Exception as e:
        print(f"A critical error occurred during Libas scraping: {e}")
        try:
            driver.save_screenshot("libas_error.png")
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

    # Print detailed summary for all pages
    images_found = len([img for img in data['Image'] if img != 'No image'])
    prices_found = len([price for price in data['Price'] if price != 'No price'])
    print(f"\n=== LIBAS SCRAPING SUMMARY (ALL PAGES) ===")
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
    print(f"\n=== SAMPLE PRODUCTS (ALL PAGES) ===")
    for i, product in enumerate(all_products[:3]):
        print(f"Product {i+1}:")
        print(f"  Title: {product['title'][:50]}...")
        print(f"  Price: {product['price']}")
        print(f"  Image: {'✓' if product['image'] != 'No image' else '✗'} ({product['image'][:50]}...)")
        print(f"  Link: {product['link'][:50]}...")
    
    df = pd.DataFrame(data)
    df['Source'] = 'Libas'
    return df

def enhanced_libas_scroll(driver, max_scrolls=20, scroll_pause=3):
    """
    Enhanced scrolling function specifically designed for Libas's lazy loading.
    """
    print("Starting enhanced Libas lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        time.sleep(scroll_pause)
        
        # Check for Libas-specific product containers
        js_script = """
            return document.querySelectorAll(
                'div[data-v-74577c89], .st-product, .product-card, .product-item, ' +
                '.product-tile, .card, [class*="product"], [class*="item"], ' +
                '[class*="card"], [class*="st-"], article, .grid-item'
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
    
    print("Enhanced Libas scrolling complete")

def force_libas_lazy_loading(driver):
    """
    Force load lazy images and content specific to Libas with multiple strategies
    """
    try:
        print("Forcing Libas lazy loading...")
        
        # Strategy 1: Handle standard lazy loading patterns
        js_strategy_1 = """
            console.log('Starting Libas image lazy loading...');
            const lazyImages = document.querySelectorAll(
                'img[data-v-74577c89], img[data-src], img[data-original], ' +
                'img[data-lazy-src], img[data-srcset], img[loading="lazy"], ' +
                'img[class*="lazy"], img[class*="lazyload"]'
            );
            console.log('Found', lazyImages.length, 'lazy images');
            lazyImages.forEach((img, index) => {
                const dataSrc = img.dataset.src || img.dataset.original || 
                               img.dataset.lazySrc || img.dataset.srcset;
                if (dataSrc && !img.src.includes(dataSrc)) {
                    console.log('Loading Libas image', index, ':', dataSrc);
                    img.src = dataSrc;
                    img.removeAttribute('loading');
                }
            });
            return lazyImages.length;
        """
        driver.execute_script(js_strategy_1)
        time.sleep(3)
        
        # Strategy 2: Trigger scroll and visibility events
        js_strategy_2 = """
            console.log('Triggering Libas scroll and resize events...');
            const allImages = document.querySelectorAll('img[data-v-74577c89], img');
            allImages.forEach((img, index) => {
                try {
                    img.scrollIntoView({ behavior: 'auto', block: 'center' });
                    img.dispatchEvent(new Event('load'));
                    img.dispatchEvent(new Event('appear'));
                    img.dispatchEvent(new Event('inview'));
                    img.dispatchEvent(new Event('scroll'));
                } catch(e) {
                    console.log('Error with Libas image', index, ':', e);
                }
            });
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
            window.dispatchEvent(new Event('load'));
            return allImages.length;
        """
        driver.execute_script(js_strategy_2)
        time.sleep(3)
        
        # Strategy 3: Handle Libas-specific Vue.js data attributes
        js_strategy_3 = """
            console.log('Handling Libas Vue.js specific lazy loading...');
            const libasImages = document.querySelectorAll(
                'img[data-v-74577c89], div[data-v-74577c89] img, ' +
                '.st-product img, [class*="st-"] img, .slideshow-container img'
            );
            libasImages.forEach((img, index) => {
                const possibleSrcs = [
                    img.dataset.src, img.dataset.original, img.dataset.lazySrc, 
                    img.dataset.srcset, img.getAttribute('src')
                ];
                for (let src of possibleSrcs) {
                    if (src && src.includes('http') && !img.src.includes(src)) {
                        console.log('Loading Libas Vue image', index, ':', src);
                        img.src = src;
                        break;
                    }
                }
                // Remove lazy loading classes
                img.classList.remove('lazyload', 'lazy');
            });
            return libasImages.length;
        """
        driver.execute_script(js_strategy_3)
        time.sleep(3)
        
        # Strategy 4: Handle background images and slideshow
        js_strategy_4 = """
            console.log('Handling Libas background images and slideshow...');
            const bgElements = document.querySelectorAll(
                '[data-bg], [data-background], [data-bg-src], ' +
                '.slideshow-container [data-v-74577c89]'
            );
            bgElements.forEach((el, index) => {
                const bgSrc = el.dataset.bg || el.dataset.background || el.dataset.bgSrc;
                if (bgSrc) {
                    el.style.backgroundImage = `url("${bgSrc}")`;
                    console.log('Set Libas background image', index, ':', bgSrc);
                }
            });
            return bgElements.length;
        """
        driver.execute_script(js_strategy_4)
        
        print("Libas lazy loading strategies completed")
        
    except Exception as e:
        print(f"Error in Libas forced lazy loading: {e}")

def debug_libas_structure(driver):
    """
    Debug function to inspect Libas's HTML structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("=== LIBAS STRUCTURE ANALYSIS ===")
        
        # Libas-specific selectors based on the provided HTML structure
        potential_containers = [
            'div[data-v-74577c89]',
            '.st-product',
            '.product-card',
            '.product-item',
            '.product-tile',
            '.card',
            '.grid-item',
            '[class*="st-"]',
            '[class*="product"]',
            'article',
            '.slideshow-container',
            '[data-product]'
        ]
        
        best_selector = None
        max_products = 0
        
        for selector in potential_containers:
            elements = soup.select(selector)
            if elements:
                product_like = []
                for elem in elements:
                    # Check if element has product characteristics
                    has_link = elem.find('a')
                    has_image = elem.find('img')
                    has_text = len(elem.get_text(strip=True)) > 20
                    has_price_class = elem.find(class_=lambda x: x and any(
                        price_term in str(x).lower() for price_term in ['price', 'cost', 'amount']
                    ))
                    
                    if has_link and has_image and has_text and len(elem.get_text(strip=True)) < 500:
                        product_like.append(elem)
                
                if len(product_like) > max_products:
                    max_products = len(product_like)
                    best_selector = selector
                
                print(f"Selector '{selector}': {len(elements)} total, {len(product_like)} product-like")
        
        print(f"Best selector: {best_selector} with {max_products} products")
        
        # Analyze images
        all_images = soup.find_all('img')
        libas_images = soup.find_all('img', attrs={'data-v-74577c89': True})
        
        print(f"\nImage analysis:")
        print(f"Total images: {len(all_images)}")
        print(f"Libas Vue images (data-v-74577c89): {len(libas_images)}")
        
        lazy_patterns = {
            'data-v-74577c89': len(libas_images),
            'data-src': len(soup.find_all('img', attrs={'data-src': True})),
            'data-original': len(soup.find_all('img', attrs={'data-original': True})),
            'loading="lazy"': len(soup.find_all('img', attrs={'loading': 'lazy'})),
            'class contains lazy': len([img for img in all_images if any('lazy' in cls.lower() for cls in img.get('class', []))])
        }
        
        print("Lazy loading patterns found:")
        for pattern, count in lazy_patterns.items():
            if count > 0:
                print(f"  {pattern}: {count} images")
        
        print("\nSample Libas image analysis:")
        for i, img in enumerate(libas_images[:3]):
            attrs = dict(img.attrs)
            print(f"  Libas Image {i+1}: {attrs}")
            
    except Exception as e:
        print(f"Error in Libas debug function: {e}")

def extract_libas_html_products(soup):
    """
    Enhanced HTML parsing for Libas products with better filtering
    Based on the provided HTML structure with data-v-74577c89 attributes
    """
    html_products = []
    seen_products = set()  # To avoid duplicates
    
    print("\n=== STARTING LIBAS HTML PARSING ===")
    
    # Libas-specific selectors based on the provided HTML structure
    product_selectors = [
        'div[data-v-74577c89].st-product',
        'div[data-v-74577c89]',
        '.st-product',
        'article.card-wrapper',
        '.card-wrapper',
        '.grid__item .card',
        '.product-card-wrapper',
        '.collection .card',
        'li.grid__item',
        '[data-product-handle]',
        '.slideshow-container > div[data-v-74577c89]'
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
                    
                # Check for Libas-specific attributes
                has_vue_attr = item.get('data-v-74577c89') is not None
                has_product_link = item.find('a', href=lambda x: x and '/products/' in x)
                has_price_element = item.find(class_=lambda x: x and any(
                    price_term in str(x).lower() for price_term in ['price', 'st-price', 'cost']
                ))
                has_st_class = any('st-' in str(cls) for cls in item.get('class', []))
                
                if has_vue_attr or has_product_link or has_price_element or has_st_class:
                    filtered_items.append(item)
            
            if len(filtered_items) > len(items):
                items = filtered_items
                selector_used = selector
                
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue
    
    print(f"Libas: Found {len(items)} items using selector: {selector_used}")
    
    # Process items with duplicate detection
    for idx, item in enumerate(items[:60]):
        try:
            # Extract product data
            title = extract_libas_title_improved(item)
            price = extract_libas_price_improved(item)
            image = extract_libas_image_improved(item)
            link = extract_libas_link_improved(item)
            
            # Create unique identifier to avoid duplicates
            product_id = f"{title}_{price}_{image[:60] if image != 'No image' else ''}"
            
            # Skip if already seen
            if product_id in seen_products:
                print(f"Skipping duplicate product {idx + 1}: {title[:60]}...")
                continue
                
            # Validate product quality
            if is_valid_libas_product(title, price, image, link):
                seen_products.add(product_id)
                html_products.append({
                    'title': title,
                    'price': price,
                    'image': image,
                    'link': link
                })
                
                print(f"✓ Product {len(html_products)}: {title[:60]}{'...' if len(title) > 60 else ''}")
                print(f"    Price={price}, Image={'✓' if image != 'No image' else '✗'}")
            else:
                print(f"✗ Skipped invalid item {idx + 1}: {title[:60]}...")
                
        except Exception as e:
            print(f"Error processing Libas product {idx + 1}: {e}")
            continue
    
    return html_products

def extract_libas_title_improved(item):
    """
    Improved title extraction with Libas-specific selectors
    Based on the provided HTML structure
    """
    
    # Libas-specific title selectors based on the HTML structure
    title_selectors = [
        'span[data-v-74577c89][class*="st-text-"][class*="sm:st-text-"]',
        'span[data-v-74577c89]',
        '.st-title',
        '.card__heading a',
        '.card__information .card__heading',
        '.card-information__text h3',
        '.full-unstyled-link',
        'h3.card__heading a',
        '.product-item-meta__title',
        'a[href*="/products/"]',
        'span[class*="st-text-[12px]"]'
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

def extract_libas_price_improved(item):
    """
    Improved price extraction for Libas based on the provided HTML structure
    """
    
    # Libas-specific price selectors based on the HTML structure
    price_selectors = [
        'div[data-v-74577c89][class*="st-product-price"]',
        'span[data-v-74577c89][class*="new-price"]',
        '.st-price',
        '.price-item--regular',
        '.price__regular .price-item',
        '.price .money',
        '.card__information .price',
        '.product-price .money',
        'span.money',
        '.price-current',
        '.regular-price',
        '[data-price]',
        'span[class*="st-text-[#000000]"]'
    ]
    
    for selector in price_selectors:
        try:
            price_elem = item.select_one(selector)
            if price_elem:
                # Check for data attributes first
                price_text = (price_elem.get('data-price') or 
                             price_elem.get_text(strip=True))
                
                if price_text:
                    cleaned_price = clean_libas_price_improved(price_text)
                    if cleaned_price != "No price":
                        return cleaned_price
        except:
            continue
    
    return "No price"

def extract_libas_image_improved(item):
    """
    Improved image extraction for Libas based on Vue.js structure
    """
    
    try:
        # Look for Libas-specific images first
        libas_imgs = item.find_all('img', attrs={'data-v-74577c89': True})
        
        for img in libas_imgs:
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
                    'product', '.jpg', '.jpeg', '.png', '.webp', 'cdn', 'shopify'
                ])):
                
                return format_libas_image_url(src)
            
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
                        return format_libas_image_url(data_src)
        
        # Fallback to any img in the item
        all_imgs = item.find_all('img')
        for img in all_imgs:
            src = img.get('src', '')
            if (src and len(src) > 15 and 
                any(indicator in src.lower() for indicator in [
                    'product', '.jpg', '.jpeg', '.png', '.webp'
                ]) and
                not any(skip in src.lower() for skip in [
                    'logo', 'placeholder', 'blank'
                ])):
                return format_libas_image_url(src)
    
    except Exception as e:
        print(f"Error extracting Libas image: {e}")
    
    return "No image"

def extract_libas_link_improved(item):
    """
    Improved link extraction for Libas
    """
    
    # Look for product links specifically
    link_selectors = [
        'a[data-v-74577c89][href*="/products/"]',
        'a[href*="/products/"]',
        '.card__heading a',
        '.full-unstyled-link',
        'a.card__link',
        '.st-title a'
    ]
    
    for selector in link_selectors:
        try:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                
                # Ensure it's a product link
                if '/products/' in href:
                    if href.startswith('/'):
                        return "https://www.libas.in" + href
                    elif href.startswith('http'):
                        return href
        except:
            continue
    
    return "#"

def is_valid_libas_product(title, price, image, link):
    """
    Validate if the scraped data represents a valid Libas product
    """
    
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

def clean_libas_price_improved(price_text):
    """
    Improved price cleaning function for Libas
    """
    if not price_text:
        return "No price"
    
    try:
        # Remove extra whitespace
        price_text = ' '.join(str(price_text).split())
        
        # Extract price using regex patterns common in Indian e-commerce
        patterns = [
            r'₹\s*([\d,]+\.?\d*)',
            r'Rs\.?\s*([\d,]+\.?\d*)', 
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*₹',
            r'([\d,]+\.?\d*)\s*Rs',
            r'(\d{2,5})'  # Fallback for plain numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_text)
            if match:
                number = match.group(1).replace(',', '')
                try:
                    # Validate it's a number and reasonable price range
                    price_val = float(number)
                    if 100 <= price_val <= 50000:  # Reasonable price range for clothing
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

def format_libas_image_url(url):
    """
    Format image URL to ensure it's complete and accessible
    """
    if not url:
        return "No image"
    
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.libas.in' + url
    elif url.startswith('http'):
        return url
    else:
        return 'https://www.libas.in/' + url.lstrip('/')
