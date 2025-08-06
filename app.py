import streamlit as st
import pandas as pd
from scrapers import (
    scrape_amazon, 
    scrape_myntra, 
    scrape_nykaa, 
    scrape_flipkart, 
    scrape_zara, 
    scrape_hnm, 
    scrape_levis, 
    scrape_lifestyle,
    scrape_ajio,    
   
)

from savana import (
    scrape_westside,
    scrape_urbanic
)

from libass import (
    scrape_libas
)
from montecarlo import (
    scrape_monte_carlo
)
from souledstore import (
    scrape_souled_store
)

# --- Streamlit UI ---
st.set_page_config(page_title="🛍️ Product Price Comparator", layout="wide")
st.title("🛍️ Multi-Site Product Price Comparator")

query = st.text_input("Enter product to search:", placeholder="e.g., blue jeans or iphone 15")

# List of all supported sites
sites_list = ["Amazon", "Flipkart", "Zara", "H&M", "Levi's", "Lifestyle", "Ajio", "Urbanic", "Westside", "Libas", "Monte Carlo", "Souled Store", "Myntra"]
site = st.selectbox("Choose website to search:", sites_list)

if st.button("Search") and query:
    df = None  # Initialize df to None
    scraper_functions = {
        "Amazon": scrape_amazon,
        "Myntra": scrape_myntra,
        "Nykaa": scrape_nykaa,
        "Flipkart": scrape_flipkart,
        "Zara": scrape_zara,
        "H&M": scrape_hnm,
        "Levi's": scrape_levis,
        "Lifestyle": scrape_lifestyle,
        "Ajio": scrape_ajio,
        "Urbanic": scrape_urbanic,
        "Westside": scrape_westside,
        "Libas": scrape_libas,
        "Monte Carlo": scrape_monte_carlo,
        "Souled Store": scrape_souled_store
    }

    if site in scraper_functions:
        with st.spinner(f"Scraping {site} for '{query}'... this might take a moment."):
            try:
                df = scraper_functions[site](query)
            except Exception as e:
                st.error(f"An error occurred while scraping {site}: {e}")
                print(f"Error scraping {site}: {e}")
    # --- Display Results ---
    if df is not None and not df.empty:
        st.success(f"Found a total of {len(df)} products!")

        # The Matrix Display
        num_columns = 3  # Adjust the number of columns for the matrix
        cols = st.columns(num_columns)

        for i, row in df.iterrows():
            # Place each product in the next available column, wrapping around
            col = cols[i % num_columns]
            
            with col:
                # Use .get() for safer dictionary access
                title = row.get('Title', 'No Title Provided')
                price = row.get('Price', 'N/A')
                image_url = row.get("Image")
                product_link = row.get('Link', '#')
                source_site = row.get('Source', site if site != "All" else "N/A")

                st.markdown(f"##### {title}")
                st.markdown(f"**Sold by:** {source_site}")
                
                if image_url and image_url != "No image":
                    st.image(image_url)
                
                st.markdown(f"**Price:** ₹{price}")
                st.markdown(f"[🔗 View Product]({product_link})", unsafe_allow_html=True)
                st.markdown("---")
        
        # Download button for the combined CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Results as CSV", 
            csv, 
            f"{query.replace(' ','_')}_{site.lower()}.csv", 
            "text/csv"
        )
    elif query:
        st.warning("No products found for your query. The scrapers might have been blocked, or the product is not available. Please try a different query or website.")
    