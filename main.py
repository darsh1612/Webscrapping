import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

def scrape_amazon(query):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    search_url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    driver.get(search_url)
    time.sleep(3)

    products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

    data = {"Title": [], "Price": [], "Image": [], "Rating": [], "Reviews": [], "Link": []}

    for product in products[:20]:
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

        try:
            link = product.find_element(By.XPATH, ".//a[@class='a-link-normal s-no-outline']").get_attribute("href")
        except:
            link = "No link"

        data["Title"].append(title)
        data["Price"].append(price)
        data["Image"].append(image)
        data["Rating"].append(rating)
        data["Reviews"].append(reviews)
        data["Link"].append(link)

    driver.quit()
    return pd.DataFrame(data)

# Streamlit UI
st.set_page_config(page_title="Amazon Scraper", layout="wide")
st.title("Amazon Product Scraper")
query = st.text_input("Enter product to search:", placeholder="e.g. black t-shirt")

if st.button("Search"):
    with st.spinner("Scraping Amazon... Please wait."):
        df = scrape_amazon(query)

    st.success("Scraping complete! Showing results below:")
    for i in range(len(df)):
        col1, col2 = st.columns([1, 4])
        with col1:
            if df["Image"][i] != "No image":
                st.image(df["Image"][i], width=120)
        with col2:
            st.markdown(f"### {df['Title'][i]}")
            st.markdown(f" **Price:** ₹{df['Price'][i]}")
            st.markdown(f"**Rating:** {df['Rating'][i]}")
            st.markdown(f" **Reviews:** {df['Reviews'][i]}")
            st.markdown(f"[ View on Amazon]({df['Link'][i]})", unsafe_allow_html=True)
        st.markdown("---")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download as CSV", data=csv, file_name="amazon_products.csv", mime="text/csv")
