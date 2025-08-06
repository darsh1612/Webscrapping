import pandas as pd
from bs4 import BeautifulSoup
from .utils import (
    get_driver, advanced_nykaa_scroll, clean_nykaa_title, 
    extract_nykaa_price_from_element, extract_nykaa_rating, extract_nykaa_link
)

def scrape_nykaa(query):
    """Comprehensive Nykaa scraper with enhanced extraction capabilities."""
    driver = get_driver()
    url = f"https://www.nykaa.com/search/result/?q={query.replace(' ', '+')}"
    driver.get(url)

    advanced_nykaa_scroll(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    data = {"Title": [], "Price": [], "Image": [], "Rating": [], "Link": []}
    product_items = soup.select('a.css-qlopj4')

    if not product_items:
        product_items = soup.select('div.css-d5s2qy')

    for item in product_items[:25]:
        title_element = item.select_one('.css-xrzmfa') or item.select_one('.css-1rd7vky')
        title = clean_nykaa_title(title_element.get_text(strip=True)) if title_element else "No Title"

        price = extract_nykaa_price_from_element(item)
        rating = extract_nykaa_rating(item)
        link = extract_nykaa_link(item)

        image = "No image"
        if img_tag := item.select_one('img.css-11gn9r6'):
            image = img_tag.get('src', 'No image')

        data["Title"].append(title)
        data["Price"].append(price)
        data["Image"].append(image)
        data["Rating"].append(rating)
        data["Link"].append(link)

    df = pd.DataFrame(data)
    df['Source'] = 'Nykaa'
    return df
