import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import openpyxl


# Define the product categories and URLs
categories = {
    "Cat Dry Food": "https://www.renspets.com/categories/cat-food-dry",
    "Cat Wet Food": "https://www.renspets.com/categories/cat-food-wet",
    "Dog Dry Food": "https://www.renspets.com/categories/dog-food-dry",
    "Dog Wet Food": "https://www.renspets.com/categories/dog-food-wet",
    "Cat Litter": "https://www.renspets.com/categories/cat-cleaning-waste-management-litter",
    "Cat Toys": "https://www.renspets.com/categories/cat-toys",
    "Dog Toys": "https://www.renspets.com/categories/dog-toys"
}

def get_total_products(soup):
    """Extract the total number of products from the HTML."""
    total_text = soup.find('span', class_='browse-controls__total-products').text.strip()
    total_products = int(total_text.split('of')[1].split('results')[0].strip())
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
        url = f"{base_url}?page={page}"
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
        products = soup.find_all('div', class_='product-summary')
        print(f"Page {page} returned {len(products)} products.")

        for product in products:
            try:
                name = product.find('div', class_='product-summary__name').text.strip()
                link = product.find('a', class_='product-summary__link')['href']
                full_link = f"https://www.renspets.com{link}"

                price_section = product.find('div', class_='product-prices__section')

                if price_section:
                    # 查找 autoship 格式的价格
                    price_range = price_section.find('div',
                                                     class_='product-prices__price product-prices__price--autoship')

                    # 查找普通价格
                    price_single = None
                    for div in price_section.find_all('div', class_='product-prices__price'):
                        if 'product-prices__price--autoship' not in div[
                            'class'] and 'product-prices__price--small' not in div['class']:
                            price_single = div
                            break

                    # 查找 small 格式的价格
                    price_small = price_section.find('div', class_='product-prices__price product-prices__price--small')

                    # 处理不同的价格情况
                    if price_range and not price_single and not price_small:
                        prices = price_range.find_all('span')
                        price = ''.join(p.get_text(strip=True) for p in prices) if prices else "N/A"
                    elif not price_range and price_single and not price_small:
                        price = price_single.find('span').text.strip()
                    elif not price_range and not price_single and price_small:
                        # 处理 small 格式价格
                        prices = price_small.find_all('s')
                        price = ''.join(p.get_text(strip=True) for p in prices) if prices else "N/A"
                    elif price_range and price_single and price_range != price_single:
                        print(f"Both price_range and price_single exist: {price_section}")
                        price = "Conflict in price data"
                    else:
                        print(f"Irregular Price Format: {price_section}")
                        price = 0
                else:
                    print("Price section not found!")
                    price = 0
                # print(f"Price: {price}")

                rating_tag = product.find('div', class_='product-summary__rating').find('div', class_='bv_averageRating_component_container').find('div', class_='bv_text')
                rating = float(rating_tag.text.strip()) if rating_tag else 0
                review_tag = product.find('div', class_='product-summary__rating').find('div', class_='bv_numReviews_component_container').find('div', class_='bv_text')
                review = int(review_tag.text.strip('()')) if review_tag else 0

                product_data.append({
                    'Category': category,
                    'Name': name,
                    'Link': full_link,
                    'Review': review,
                    'Rating': rating,
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
    output_file = "renspets_top_products.xlsx"
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

if __name__ == "__main__":
    main()
