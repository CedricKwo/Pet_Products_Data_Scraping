import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl


# Define the product categories and URLs
categories = {
    "Cat Dry Food": "https://www.petvalu.ca/category/cat/dry-food/21001",
    "Cat Wet Food": "https://www.petvalu.ca/category/cat/wet-food/21002",
    "Dog Dry Food": "https://www.petvalu.ca/category/dog/dry-food/11001",
    "Dog Wet Food": "https://www.petvalu.ca/category/dog/wet-food/11002",
    "Cat Litter": "https://www.petvalu.ca/category/cat/litter/22001",
    "Cat Toys": "https://www.petvalu.ca/category/cat/toys/23001",
    "Dog Toys": "https://www.petvalu.ca/category/dog/toys/13046"
}

def get_total_products(soup):
    """Extract the total number of products from the HTML."""
    total_text = soup.find('div', class_='filters-sort-order-wrapper show').find('p', class_='P1 semi-bold').text.strip()
    total_products = int(total_text.split('of')[1].split('Products')[0].strip())
    return total_products

def get_product_data(category, base_url):
    """Scrape product data for a specific category."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"}
    session = requests.Session()

    # Fetch the first page to get total products
    try:
        response = session.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {base_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Get total products
    total_products = get_total_products(soup)
    print(f"Total products for {category}: {total_products}")

    product_data = []
    total_processed = 0
    page = 1

    while total_processed < total_products:
        url = f"{base_url}?page={page}"
        print(f"Fetching data from: {url}")

        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find product containers (adjust selectors as needed)
        products = soup.find_all('div', class_='product-tile__details')
        print(f"Page {page} returned {len(products)} products.")

        for product in products:
            try:
                name_tag = product.find('div', class_='title')
                names = name_tag.find_all('p')
                if names:
                    name = ' '.join(n.get_text(strip=True) for n in names)
                    # print(f"Name: {name}")
                link = name_tag.find('a')['href']
                full_link = f"https://www.petvalu.ca{link}"
                price_tag = product.find('div', class_='price')
                price = price_tag.find('p').text.strip() if price_tag else "N/A"
                # print(f"Price: {price}")
                review_tag = product.find('div', class_='reviews__information')
                if review_tag:
                    rating_tag = review_tag.find('p')
                    if rating_tag:
                        rating = float(rating_tag.text.strip())
                    else:
                        rating = 0

                    reviews = review_tag.find_all('p')
                    if reviews:
                        review_text = ' '.join(r.get_text(strip=True) for r in reviews).split('(')[1].split(')')[0]
                        review = int(review_text)
                    else:
                        review = 0
                else:
                    review = 0
                # print(f"Review: {review}")

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
    all_products = []

    for category, url in categories.items():
        print(f"Scraping {category}...")
        products = get_product_data(category, url)
        all_products.extend(products)

    if not all_products:
        print("No products found. Exiting...")
        return

    # Convert to DataFrame
    df = pd.DataFrame(all_products)

    # Save to Excel
    output_file = "petvalu_top_products.xlsx"
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

if __name__ == "__main__":
    main()
