import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# Define the product categories and URLs
categories = {
    "Cat Dry Food": "https://www.petsmart.ca/cat/food-and-treats/dry-food/",
    "Cat Wet Food": "https://www.petsmart.ca/cat/food-and-treats/wet-food/",
    "Dog Dry Food": "https://www.petsmart.ca/dog/food/dry-food/",
    "Dog Wet Food": "https://www.petsmart.ca/dog/food/canned-food/",
    "Cat Litter": "https://www.petsmart.ca/cat/litter-and-waste-disposal/litter/",
    "Cat Toys": "https://www.petsmart.ca/cat/toys/",
    "Dog Toys": "https://www.petsmart.ca/dog/toys/"
}

def click_next_button(driver):
    """Click the Next button on the page."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'li[data-testid="paginate-last-item"] > a')
        parent_li = next_button.find_element(By.XPATH, "..")
        if "disabled" in parent_li.get_attribute("class"):
            print("Reached the last page. Stopping.")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(3)
    except Exception as e:
        print(f"Failed to click 'Next' button: {e}")
        return False
    return True

# def remove_duplicates(products):
#     """Remove duplicate products based on the 'Link'."""
#     unique_products = {product['Link']: product for product in products}
#     return list(unique_products.values())

def remove_duplicates(products):
    """Remove duplicate products based on all fields."""
    seen = set()
    unique_products = []
    for product in products:
        product_tuple = tuple(product.items())  # Convert the product dict to a tuple of items
        if product_tuple not in seen:
            seen.add(product_tuple)
            unique_products.append(product)
    return unique_products

def scrape_category(driver, url, category):
    """Scrape all pages for a single category."""
    driver.get(url)
    time.sleep(3)

    all_products = []
    page_number = 1

    while True:
        print(f"Scraping page {page_number} of {category}...")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = soup.find_all('div', class_='sparky-l-grid__item')
        print(f"Page {page_number} returned {len(products)} products.")

        for product in products:
            try:
                name = product.find('a', class_='sparky-c-text-link sparky-c-product-card__text-link').text.strip()
                link = product.find('a', class_='sparky-c-text-link sparky-c-product-card__text-link')['href']
                full_link = f"https://www.petsmart.com{link}"

                review_tag = product.find('div', class_='sparky-c-star-rating__rating-after')
                review = int(review_tag.text.strip('()')) if review_tag else 0

                rating_tag = product.find('div', class_='sparky-c-star-rating__icons')['aria-label']
                rating = float(rating_tag.split("out of")[0].strip()) if rating_tag else 0

                price_tag = product.find('div', class_='sparky-c-price sparky-c-product-card__price-group sparky-c-price--lg')
                price = price_tag.text.strip() if price_tag else "N/A"

                all_products.append({
                    'Category': category,
                    'Name': name,
                    'Link': full_link,
                    'Review': review,
                    'Rating': rating,
                    'Price': price
                })

            except AttributeError:
                continue

        # Click the next page
        if not click_next_button(driver):
            break

        page_number += 1

    # Remove duplicates
    all_products = remove_duplicates(all_products)
    print("----Product Detail----")
    print(f"Category: {category}, Count: {len(all_products)}")
    # Sort by reviews in descending order and keep top 10
    sorted_products = sorted(all_products, key=lambda x: x['Review'], reverse=True)[:10]
    return sorted_products

def main():
    driver = webdriver.Chrome()
    all_products = []

    for category, url in categories.items():
        print(f"Scraping {category}...")
        products = scrape_category(driver, url, category)
        all_products.extend(products)

    driver.quit()

    # Save data to Excel
    df = pd.DataFrame(all_products)
    output_file = "petsmart_top_products.xlsx"
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

if __name__ == "__main__":
    main()

