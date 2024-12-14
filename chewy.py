import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
from playwright.sync_api import sync_playwright


# Define the product categories and URLs
categories = {
    "Cat Dry Food": "https://www.chewy.com/ca/b/dry-food-388",
    "Cat Wet Food": "https://www.chewy.com/ca/b/wet-food-389",
    "Dog Dry Food": "https://www.chewy.com/ca/b/dry-food-294",
    "Dog Wet Food": "https://www.chewy.com/ca/b/wet-food-293",
    "Cat Litter": "https://www.chewy.com/ca/b/litter-411",
    "Cat Toys": "https://www.chewy.com/ca/b/toys-326",
    "Dog Toys": "https://www.chewy.com/ca/b/toys-315"
}

def click_next_button(driver):
    """Click the Next button on the page."""
    try:
        next_li = driver.find_element(By.CSS_SELECTOR, "li.kib-pagination-new__list-item--next")
        print(f"Next button HTML: {next_li.get_attribute('outerHTML')}")  # 打印 HTML 结构

        try:
            next_button = next_li.find_element(By.CSS_SELECTOR, "a")  # 优先查找 <a>
        except Exception:
            try:
                next_button = next_li.find_element(By.CSS_SELECTOR, "button")  # 查找 <button>
            except Exception:
                print("No clickable element in Next button. Reached the last page.")
                return False

        if "disabled" in next_button.get_attribute("class") or next_button.get_attribute("aria-disabled") == "true":
            print("Next button is disabled. Reached the last page.")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        next_button.click()
        time.sleep(3)
    except Exception as e:
        print(f"Failed to click 'Next' button: {e}")
        return False

    return True


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
    # print(f"Page Source: {driver.page_source}")
    time.sleep(random.uniform(20, 50))

    all_products = []
    page_number = 1

    while True:
        print(f"Scraping page {page_number} of {category}...")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = soup.find_all('div', class_='kib-product-card__content')
        print(f"Page {page_number} returned {len(products)} products.")

        for product in products:
            try:
                name = product.find('div', class_='kib-product-title__text').text.strip()
                link = product.find('a', class_='kib-product-title')['href']
                if "https" not in link:
                    link = f"https://www.chewy.com{link}"

                review_tag = product.find('span', class_='kib-product-rating__count')
                if review_tag:
                    review_text = review_tag.text
                    if "Review" in review_text:
                        review = int(review_text.split("Review")[0].strip())
                    else:
                        review = int(review_tag.text.replace(",", "").strip())
                else:
                    print("No Review Data Found")
                    review = 0

                rating_tag = product.find('div', class_='kib-product-rating__rating-display')
                rating = float(rating_tag.text) if rating_tag else 0

                price_tag = product.find('div', class_='kib-product-price kib-product-price--deal kib-product-price--md')
                price = price_tag.text.strip() if price_tag else "N/A"

                if rating != 0:
                    all_products.append({
                        'Category': category,
                        'Name': name,
                        'Link': link,
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

    # with sync_playwright() as p:
    #     browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    #     context = browser.contexts[0]  # 使用现有的上下文
    #     page = context.new_page()
    #     page.goto("https://www.chewy.com/ca/b/dry-food-388")
    #     print(f"Page Title: {page.title()}")

    # 首先在终端中使用命令启一个chrome进程 #
    # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/Users/apolloguo/selenium/chrome-profile" #
    # 配置 ChromeOptions
    options = Options()
    options.debugger_address = "127.0.0.1:9222"  # 连接到远程调试端口

    # 连接到现有的 Chrome 实例
    driver = webdriver.Chrome(options=options)

    all_products = []

    for category, url in categories.items():
        print(f"Scraping {category}...")
        products = scrape_category(driver, url, category)
        all_products.extend(products)

    driver.quit()

    # Save data to Excel
    df = pd.DataFrame(all_products)
    output_file = "chewy_top_products.xlsx"
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

if __name__ == "__main__":
    main()

