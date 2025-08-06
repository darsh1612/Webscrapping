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
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def scrape_souled_store(query):
    """
    The Souled Store scraper that scrapes one page of results with lazy loading support.
    """
    driver = get_driver()
    encoded_query = quote(query)
    url = f"https://www.thesouledstore.com/search?q={encoded_query}"
    
    all_products = []

    try:
        print(f"\n--- Scraping The Souled Store: {url} ---")
        
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        
        # Wait for the main product container to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-v-bd99a1be].row, .productCard, .col-lg-3')))
            time.sleep(5)
            print("Initial page loaded successfully")
        except:
            print("No products found or page failed to load.")
            return pd.DataFrame({"Title": [], "Price": [], "Image": [], "Link": [], "Source": []})

        # Enhanced scrolling for lazy loading
        enhanced_souled_store_scroll(driver, max_scrolls=20, scroll_pause=3)
        force_souled_store_lazy_loading(driver)
        time.sleep(8)

        print(f"\n=== DEBUGGING SOULED STORE STRUCTURE ===")
        debug_souled_store_structure(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        html_products = extract_souled_store_html_products(soup)
        print(f"Found {len(html_products)} products from HTML parsing")
        all_products.extend(html_products)

    except Exception as e:
        print(f"A critical error occurred during Souled Store scraping: {e}")
        try:
            driver.save_screenshot("souled_store_error.png")
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
    print(f"\n=== SOULED STORE SCRAPING SUMMARY ===")
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
    df['Source'] = 'The Souled Store'
    return df


def enhanced_souled_store_scroll(driver, max_scrolls=20, scroll_pause=3):
    """
    Enhanced scrolling function specifically designed for The Souled Store's lazy loading.
    """
    print("Starting enhanced Souled Store lazy loading scroll...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    loaded_products_count = 0
    
    for i in range(max_scrolls):
        # Scroll down in smaller increments to trigger lazy loading
        current_position = (i + 1) * (last_height / max_scrolls)
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Wait for content to load
        time.sleep(scroll_pause)
        
        # Check for Souled Store specific product containers
        js_script = """
            return document.querySelectorAll(
                '[data-v-bd99a1be].col-lg-3, .productCard, ' +
                '[data-v-2d5b3c05][data-v-bd99a1be].productCard, .animate-card'
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
    
    print("Enhanced Souled Store scrolling complete")


def force_souled_store_lazy_loading(driver):
    """
    Force load lazy images and content specific to The Souled Store
    """
    try:
        print("Forcing Souled Store lazy loading...")
        
        # Strategy 1: Handle standard lazy loading patterns
        js_strategy_1 = """
            console.log('Starting Souled Store image lazy loading...');
            const lazyImages = document.querySelectorAll(
                'img[data-src], img[data-original], img[data-lazy-src], ' +
                'img[data-srcset], img[loading="lazy"], img[class*="lazy"], ' +
                'img[class*="lazyload"], .customFade img, .imgBlock img'
            );
            console.log('Found', lazyImages.length, 'lazy images');
            lazyImages.forEach((img, index) => {
                const dataSrc = img.dataset.src || img.dataset.original || 
                               img.dataset.lazySrc || img.dataset.srcset;
                if (dataSrc && !img.src.includes(dataSrc)) {
                    console.log('Loading Souled Store image', index, ':', dataSrc);
                    img.src = dataSrc;
                    img.removeAttribute('loading');
                }
            });
            return lazyImages.length;
        """
        driver.execute_script(js_strategy_1)
        time.sleep(4)
        
        # Strategy 2: Trigger scroll and visibility events specifically for product cards
        js_strategy_2 = """
            console.log('Triggering Souled Store scroll and resize events...');
            const productCards = document.querySelectorAll('.productCard, [data-v-2d5b3c05].productCard');
            productCards.forEach((card, index) => {
                try {
                    card.scrollIntoView({ behavior: 'auto', block: 'center' });
                    const images = card.querySelectorAll('img');
                    images.forEach(img => {
                        img.dispatchEvent(new Event('load'));
                        img.dispatchEvent(new Event('appear'));
                        img.dispatchEvent(new Event('inview'));
                        img.dispatchEvent(new Event('scroll'));
                        img.classList.add('customFade-active');
                    });
                } catch(e) {
                    console.log('Error with Souled Store product card', index, ':', e);
                }
            });
            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new Event('resize'));
            window.dispatchEvent(new Event('load'));
            return productCards.length;
        """
        driver.execute_script(js_strategy_2)
        time.sleep(4)
        
        # Strategy 3: Handle Souled Store specific image containers and Vue.js lazy loading
        js_strategy_3 = """
            console.log('Handling Souled Store Vue.js lazy loading...');
            const imageBlocks = document.querySelectorAll(
                '.imgBlock img, .customFade img, [data-v-2d5b3c05] img'
            );
            imageBlocks.forEach((img, index) => {
                const possibleSrcs = [
                    img.dataset.src, img.dataset.original, img.dataset.lazySrc, 
                    img.dataset.srcset, img.getAttribute('src')
                ];
                for (let src of possibleSrcs) {
                    if (src && src.includes('http') && !img.src.includes(src)) {
                        console.log('Loading Souled Store block image', index, ':', src);
                        img.src = src;
                        break;
                    }
                }
                // Remove lazy loading classes and add active classes
                img.classList.remove('lazyload', 'lazy');
                img.classList.add('customFade-active', 'gm-loaded');
                img.parentElement?.classList.add('loaded');
            });
            return imageBlocks.length;
        """
        driver.execute_script(js_strategy_3)
        time.sleep(4)
        
        # Strategy 4: Force Vue.js component updates
        js_strategy_4 = """
            console.log('Forcing Vue.js component updates...');
            // Trigger intersection observer callbacks
            if (window.IntersectionObserver) {
                const images = document.querySelectorAll('img');
                images.forEach(img => {
                    if (img.getBoundingClientRect().top < window.innerHeight) {
                        const event = new Event('intersect');
                        img.dispatchEvent(event);
                    }
                });
            }
            
            // Force Vue reactivity updates
            const vueElements = document.querySelectorAll('[data-v-2d5b3c05], [data-v-bd99a1be]');
            vueElements.forEach(el => {
                el.dispatchEvent(new Event('update'));
                el.dispatchEvent(new Event('mounted'));
            });
            
            return vueElements.length;
        """
        driver.execute_script(js_strategy_4)
        time.sleep(3)
        
        print("Souled Store lazy loading strategies completed")
        
    except Exception as e:
        print(f"Error in Souled Store forced lazy loading: {e}")


def debug_souled_store_structure(driver):
    """
    Debug function to inspect The Souled Store's HTML structure
    """
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        print("=== SOULED STORE STRUCTURE ANALYSIS ===")
        
        # Check for the main row container
        main_row = soup.select('[data-v-bd99a1be].row')
        print(f"Main row containers found: {len(main_row)}")
        
        # Check for product columns
        product_cols = soup.select('[data-v-bd99a1be].col-lg-3')
        animate_cards = soup.select('.animate-card')
        
        print(f"Product columns (col-lg-3): {len(product_cols)}")
        print(f"Animate cards: {len(animate_cards)}")
        
        # Check for product cards
        product_cards = soup.select('.productCard')
        vue_product_cards = soup.select('[data-v-2d5b3c05][data-v-bd99a1be].productCard')
        
        print(f"Product cards: {len(product_cards)}")
        print(f"Vue product cards: {len(vue_product_cards)}")
        
        # Analyze image blocks
        img_blocks = soup.select('.imgBlock')
        custom_fade = soup.select('.customFade')
        
        print(f"Image blocks: {len(img_blocks)}")
        print(f"Custom fade elements: {len(custom_fade)}")
        
        # Analyze price elements
        offer_spans = soup.select('span[data-v-2d5b3c05].offer')
        fsemibold_spans = soup.select('.fsemibold')
        
        print(f"Offer spans: {len(offer_spans)}")
        print(f"Fsemibold spans: {len(fsemibold_spans)}")
        
        # Sample analysis
        if vue_product_cards:
            sample_card = vue_product_cards[0]
            print(f"\nSample product card classes: {sample_card.get('class', [])}")
            
            sample_link = sample_card.select_one('a[href]')
            if sample_link:
                print(f"Sample link href: {sample_link.get('href', '')[:50]}...")
                
            sample_image = sample_card.select_one('.imgBlock img, .customFade img')
            if sample_image:
                print(f"Sample image attributes: {dict(sample_image.attrs)}")
                
            sample_price = sample_card.select_one('span[data-v-2d5b3c05].offer.fsemibold')
            if sample_price:
                print(f"Sample price text: {sample_price.get_text(strip=True)}")
            
    except Exception as e:
        print(f"Error in Souled Store debug function: {e}")


def extract_souled_store_html_products(soup):
    """
    HTML parsing for The Souled Store products based on the specified structure
    """
    html_products = []
    seen_products = set()  # To avoid duplicates
    
    print("\n=== STARTING SOULED STORE HTML PARSING ===")
    
    # Find the main row container
    main_row = soup.select_one('[data-v-bd99a1be].row')
    if not main_row:
        print("No main row container found! Trying alternative selectors...")
        # Try alternative selectors
        main_row = soup.select_one('.row')
        if not main_row:
            print("No row container found at all!")
            return []
    
    # Find all product columns
    product_cols = main_row.select('[data-v-bd99a1be].col-lg-3, .col-lg-3, .animate-card')
    print(f"Found {len(product_cols)} product columns")
    
    for idx, col in enumerate(product_cols[:60]):  # Limit to avoid too many products
        try:
            # Find the product card within the column
            product_card = col.select_one('[data-v-2d5b3c05][data-v-bd99a1be].productCard, .productCard')
            
            if not product_card:
                print(f"No product card found in column {idx + 1}")
                continue
            
            # Extract product data using the specified structure
            title = extract_souled_store_title(product_card)
            price = extract_souled_store_price(product_card)
            image = extract_souled_store_image(product_card)
            link = extract_souled_store_link(product_card)
            
            # Create unique identifier to avoid duplicates
            product_id = f"{title}_{price}_{image[:50] if image != 'No image' else ''}"
            
            # Skip if already seen
            if product_id in seen_products:
                print(f"Skipping duplicate product {idx + 1}: {title[:50]}...")
                continue
                
            # Validate product quality
            if is_valid_souled_store_product(title, price, image, link):
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
            print(f"Error processing Souled Store product {idx + 1}: {e}")
            continue
    
    return html_products


def extract_souled_store_title(product_card):
    """
    Extract title from The Souled Store product card
    """
    try:
        # Try to get title from the main product link
        link_elem = product_card.select_one('a[href]')
        if link_elem:
            # Check for title attribute
            title = link_elem.get('title', '').strip()
            if title and len(title) > 3:
                return ' '.join(title.split())
            
            # Check for alt text in images
            img_elem = link_elem.select_one('img')
            if img_elem:
                alt_text = img_elem.get('alt', '').strip()
                if alt_text and len(alt_text) > 3:
                    return ' '.join(alt_text.split())
        
        # Try to extract from image block
        img_block = product_card.select_one('.imgBlock img, .customFade img')
        if img_block:
            alt_text = img_block.get('alt', '').strip()
            if alt_text and len(alt_text) > 3:
                return ' '.join(alt_text.split())
            
            title_attr = img_block.get('title', '').strip()
            if title_attr and len(title_attr) > 3:
                return ' '.join(title_attr.split())
        
        # Try to get from any text content in the card
        text_elements = product_card.select('span, div, p')
        for elem in text_elements:
            text = elem.get_text(strip=True)
            if (text and len(text) > 10 and len(text) < 100 and 
                not any(skip in text.lower() for skip in ['₹', 'rs', '$', 'price', 'offer'])):
                return ' '.join(text.split())
        
    except Exception as e:
        print(f"Error extracting Souled Store title: {e}")
    
    return "No title"


def extract_souled_store_price(product_card):
    """
    Extract price from The Souled Store product card using the specified structure:
    span[data-v-2d5b3c05].offer.fsemibold
    """
    try:
        # Follow the exact path specified
        price_elem = product_card.select_one('span[data-v-2d5b3c05].offer.fsemibold')
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            if price_text:
                cleaned_price = clean_souled_store_price(price_text)
                if cleaned_price != "No price":
                    return cleaned_price
        
        # Fallback: try different price selectors
        price_selectors = [
            '.offer.fsemibold',
            '.offer',
            '.fsemibold',
            'span.offer',
            '[data-v-2d5b3c05].offer',
            '.price',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            price_elem = product_card.select_one(selector)
            if price_elem:
                price_text = (price_elem.get('data-price') or 
                             price_elem.get_text(strip=True))
                if price_text:
                    cleaned_price = clean_souled_store_price(price_text)
                    if cleaned_price != "No price":
                        return cleaned_price
        
        # Try to find any text that looks like a price
        all_text = product_card.get_text()
        price_match = re.search(r'₹\s*(\d{2,5})', all_text)
        if price_match:
            return f"₹{price_match.group(1)}"
        
    except Exception as e:
        print(f"Error extracting Souled Store price: {e}")
    
    return "No price"


def extract_souled_store_image(product_card):
    """
    Extract image from The Souled Store product card using the specified structure:
    div[data-v-2d5b3c05].imgBlock > a.customFade > img
    """
    try:
        # Follow the exact path specified
        img_elem = product_card.select_one('[data-v-2d5b3c05].imgBlock .customFade img')
        
        if not img_elem:
            # Try without data-v attribute
            img_elem = product_card.select_one('.imgBlock .customFade img')
        
        if not img_elem:
            # Try direct imgBlock > img
            img_elem = product_card.select_one('.imgBlock img')
        
        if not img_elem:
            # Try any customFade img
            img_elem = product_card.select_one('.customFade img')
        
        if not img_elem:
            # Fallback to any image in the card
            img_elem = product_card.select_one('img')
        
        if img_elem:
            # Check primary src first
            src = img_elem.get('src', '')
            
            # Skip logo and placeholder images
            if src and not any(skip in src.lower() for skip in [
                'logo', 'placeholder', 'blank', 'loading', 'spinner', 'default'
            ]):
                if len(src) > 15:
                    return format_souled_store_image_url(src)
            
            # Check data attributes for lazy loading
            for attr in ['data-src', 'data-original', 'data-lazy-src', 'srcset', 'data-srcset']:
                data_src = img_elem.get(attr)
                if data_src:
                    # For srcset, take the first URL
                    if 'srcset' in attr:
                        data_src = data_src.split(' ')[0]
                    
                    if len(data_src) > 15:
                        return format_souled_store_image_url(data_src)
        
    except Exception as e:
        print(f"Error extracting Souled Store image: {e}")
    
    return "No image"


def extract_souled_store_link(product_card):
    """
    Extract link from The Souled Store product card
    """
    try:
        # Look for the main product link (usually wrapping the image)
        link_elem = product_card.select_one('a[href]')
        
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            
            if href.startswith('/'):
                return "https://www.thesouledstore.com" + href
            elif href.startswith('http'):
                return href
        
        # Try to find any link in the card
        all_links = product_card.select('a[href]')
        for link in all_links:
            href = link.get('href', '')
            if href and ('product' in href.lower() or len(href) > 10):
                if href.startswith('/'):
                    return "https://www.thesouledstore.com" + href
                elif href.startswith('http'):
                    return href
        
    except Exception as e:
        print(f"Error extracting Souled Store link: {e}")
    
    return "#"


def is_valid_souled_store_product(title, price, image, link):
    """
    Validate if the scraped data represents a valid Souled Store product
    """
    # Title validation
    if (title == "No title" or 
        len(title) < 3 or 
        any(invalid in title.lower() for invalid in [
            'log in', 'login', 'sign up', 'register', 'create account',
            'forgot password', 'newsletter', 'subscribe', 'cart', 'wishlist'
        ])):
        return False
    
    # Must have either price or valid product link
    has_price = price != "No price"
    has_product_link = link != "#" and ("thesouledstore.com" in link or "/product" in link)
    
    if not (has_price or has_product_link):
        return False
    
    return True


def clean_souled_store_price(price_text):
    """
    Clean price text for The Souled Store
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
                    if 50 <= price_val <= 50000:  # Reasonable price range for apparel
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


def format_souled_store_image_url(url):
    """
    Format image URL to ensure it's complete and accessible
    """
    if not url:
        return "No image"
    
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.thesouledstore.com' + url
    elif url.startswith('http'):
        return url
    else:
        return 'https://www.thesouledstore.com/' + url.lstrip('/')


# Example usage
if __name__ == "__main__":
    # Test the scraper
    query = "black shirt"
    df = scrape_souled_store(query)
    print(f"\nFinal results: {len(df)} products scraped")
    print(df.head())