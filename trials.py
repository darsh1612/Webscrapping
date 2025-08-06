# from bs4 import BeautifulSoup
# import requests
# import pandas as pd

# def get_title(soup):
#     try:
#         title=soup.find("span",attrs={"id":"productTitle"})
#         title_value=title.text
#         title_string=title_value.strip()        
#     except AttributeError:
#         title_string="No title found"
#     return title_string

# def get_price(soup):
#     try:
#         price=soup.find("span",attrs={"id":"priceblock_ourprice"})
#         price_value=price.text
#         price_string=price_value.strip()
#     except AttributeError:
#         price_string="No price found"
#     return price_string

# def get_image(soup):
#     try:
#         image=soup.find("img",attrs={"id":"landingImage"})
#         image_value=image["src"]
#     except TypeError:
#         image_value="No image found"
#     return image_value

# def get_rating(soup):
#     try:
#         rating=soup.find("span",attrs={"id":"acrPopover"})
#         rating_value=rating["title"]
#         rating_string=rating_value.strip()
#     except TypeError:
#         rating_string="No rating found"
#     return rating_string

# def get_reviews(soup):
#     try:
#         reviews=soup.find("span",attrs={"id":"acrCustomerReviewText"})
#         reviews_value=reviews.text
#         reviews_string=reviews_value.strip()
#     except AttributeError:
#         reviews_string="No reviews found"
#     return reviews_string

# def get_product_details(url):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }
    
#     response = requests.get(url, headers=headers)
    
#     if response.status_code != 200:
#         return None
    
#     soup = BeautifulSoup(response.content, 'html.parser')
    
#     product_details = {
#         "Title": get_title(soup),
#         "Price": get_price(soup),
#         "Image URL": get_image(soup),
#         "Rating": get_rating(soup),
#         "Reviews": get_reviews(soup)
#     }
    
#     return product_details


# if __name__ == "__main__":

#     HEADERS = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }
    
#     url = "https://www.amazon.in/s?k=black+tshirt&crid=TI7VNMUL04TH&sprefix=black+tshirt%2Caps%2C337&ref=nb_sb_noss_1"  # Example product URL

#     webpage=requests.get(url, headers=HEADERS)
#     soup=BeautifulSoup(webpage.content,'html.parser')

#     links = soup.find_all("a", attrs={"class": "a-link-normal s-line-clamp-2 s-line-clamp-3-for-col-12 s-link-style a-text-normal"})

#     links_list=[]

#     for link in links:
#         links.append( link.get("href"))

#     d={"title":[], "price":[], "image":[], "rating":[], "reviews":[]}

#     for link in links_list:
#         new_webpage=requests.get("https://www.amazon.in"+link, headers=HEADERS)
        
#         new_soup=BeautifulSoup(new_webpage.content,'html.parser')   

#         d["title"].append(get_title(new_soup))
#         d["price"].append(get_price(new_soup))
#         d["image"].append(get_image(new_soup))
#         d["rating"].append(get_rating(new_soup))
#         d["reviews"].append(get_reviews(new_soup))
#     df=pd.DataFrame(d)
#     df.to_csv("amazon_products.csv", index=False)
#     print("Data has been saved to amazon_products.csv")
#     print("Scraping completed successfully!")
#     print("Total products scraped:", len(df))
#     print("Sample data:")
#     print(df.head())
#     print("All product details have been successfully scraped and saved.")
#     print("You can find the data in the 'amazon_products.csv' file.")
#     print("Thank you for using the web scraping tool!")



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# Setup Chrome options
options = Options()
options.add_argument("--headless")  # run in background
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Load driver
driver = webdriver.Chrome(options=options)

# Target Amazon search page
search_url = "https://www.amazon.in/s?k=black+tshirt"
driver.get(search_url)
time.sleep(3)  # wait for page to load

# Scrape product elements
products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

data = {
    "title": [],
    "price": [],
    "image": [],
    "rating": [],
    "reviews": [],
}

for product in products[:20]:  # Limit to 20 for demo
    try:
        title = product.find_element(By.XPATH, ".//span[@class='a-size-medium a-color-base a-text-normal']").text
    except:
        title = "No title"
    
    try:
        price = product.find_element(By.XPATH, ".//span[@class='a-price-whole']").text
    except:
        price = "No price"
    
    try:
        image = product.find_element(By.TAG_NAME, "img").get_attribute("src")
    except:
        image = "No image"
    
    try:
        rating = product.find_element(By.XPATH, ".//span[@class='a-icon-alt']").text
    except:
        rating = "No rating"
    
    try:
        reviews = product.find_element(By.XPATH, ".//span[@class='a-size-base s-underline-text']").text
    except:
        reviews = "No reviews"

    data["title"].append(title)
    data["price"].append(price)
    data["image"].append(image)
    data["rating"].append(rating)
    data["reviews"].append(reviews)

# Close driver
driver.quit()

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("amazon_products.csv", index=False)

print("Scraping completed successfully!")
print("Total products scraped:", len(df))
print(df.head())
