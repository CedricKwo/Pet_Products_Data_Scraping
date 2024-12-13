import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import openpyxl


# Define the product categories and URLs
categories = {
    "Cat Dry Food": "https://www.homesalive.ca/cat/food/dry-and-kibble.html",
    "Cat Wet Food": "https://www.homesalive.ca/cat/food/wet-and-canned.html",
    "Dog Dry Food": "https://www.homesalive.ca/dog/food/dry-and-kibble.html",
    "Dog Wet Food": "https://www.homesalive.ca/dog/food/wet.html",
    "Cat Litter": "https://www.homesalive.ca/cat/litter-and-accessories.html",
    "Cat Toys": "https://www.homesalive.ca/cat/toys.html",
    "Dog Toys": "https://www.homesalive.ca/dog/toys.html"
}

def get_total_products(soup):
    """Extract the total number of products from the HTML."""
    total_text = soup.find('span', class_='toolbar-number').text.strip()
    total_products = int(total_text)
    return total_products


def get_product_data(driver, category, base_url):
    """Scrape product data for a specific category."""

    # Fetch the first page to get total products
    driver.get(base_url)
    time.sleep(5)  # 等待页面加载
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Get total products
    total_products = get_total_products(soup)
    print(f"Total products for {category}: {total_products}")

    product_data = []
    total_processed = 0
    page = 1

    while total_processed < total_products:
        url = f"{base_url}?p={page}"
        print(f"Fetching data from: {url}")

        # try:
        #     response = session.get(url, headers=headers, timeout=30)
        #     response.raise_for_status()
        # except requests.exceptions.RequestException as e:
        #     print(f"Error fetching data from {url}: {e}")
        #     break
        #
        # soup = BeautifulSoup(response.text, 'html.parser')

        # Fetch each page to get total products
        driver.get(url)
        time.sleep(5)  # 等待页面加载
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find product containers (adjust selectors as needed)
        products = soup.find_all('div', class_='product-item-info')
        print(f"Page {page} returned {len(products)} products.")

        for product in products:
            try:
                name_tag = product.find('a', class_='product-item-link')
                name = name_tag.text.strip()
                print(f"Product Name: {name}")
                link = name_tag['href']
                print(f"Product Link: {link}")

                price_section = product.find('div', class_='price-box price-final_price')

                # print(f"Price Section Info: {price_section}")

                if price_section:
                    # 查找 特价 格式的价格
                    price_special = price_section.find('span',
                                                     class_='special-price hidden-price')


                    # 查找 正常价 格式的价格
                    price_final = price_section.find('span',
                                                     class_='price-container price-final_price tax weee')

                    # 处理不同的价格情况
                    if price_special and not price_final:
                        price = price_special.find('span', class_='price').text.strip()
                    elif not price_special and price_final:
                        price = price_final.find('span', class_='price').text.strip()
                    elif price_special and price_final:
                        print(f"Both Price Format Found: {price_section}")
                        price = 0
                    else:
                        print(f"Irregular Price Format: {price_section}")
                        price = 0
                else:
                    print("Price section not found!")
                    price = 0
                # print(f"Price: {price}")

                review_tag = product.find('div', class_='yotpo-sr-bottom-line-text yotpo-sr-bottom-line-text--right-panel')
                review = int(review_tag.text.split('Review')[0].strip()) if review_tag else 0

                product_data.append({
                    'Category': category,
                    'Name': name,
                    'Link': link,
                    'Review': review,
                    'Price': price
                })

                total_processed += 1

            except AttributeError as e:
                print(f"Error parsing product data: {e}")
                continue

        if len(products) == 0:  # No more products found on the page
            print("No more products found. Ending pagination.")
            break

        page += 1

    # Sort by ratings in descending order and keep top 10
    sorted_products = sorted(product_data, key=lambda x: x['Review'], reverse=True)[:10]

    return sorted_products


def main():
    driver = webdriver.Chrome()  # 确保安装了 ChromeDriver
    all_products = []

    for category, url in categories.items():
        print(f"Scraping {category}...")
        products = get_product_data(driver, category, url)
        all_products.extend(products)

    driver.quit()

    if not all_products:
        print("No products found. Exiting...")
        return

    # Convert to DataFrame
    df = pd.DataFrame(all_products)

    # Save to Excel
    output_file = "homesalive_top_products.xlsx"
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

if __name__ == "__main__":
    main()
