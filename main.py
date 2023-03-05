import re
import json
import time
import urllib.parse
import pandas as pd
import concurrent.futures
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from undetected_chromedriver import ChromeOptions

# Links for each store
pak_n_save = "https://www.paknsave.co.nz/shop/Search?q="
new_world = "https://www.newworld.co.nz/shop/Search?q="
countdown = "https://www.countdown.co.nz/shop/searchproducts?search="

# XPath for Pak n save, New world
path_pn = '/html/body/div[*]/section[2]/div[1]/div/div[1]/div[*]/div/div[3]'

# XPath for countdown product names
path_product_cd = '/html/body/wnz-content/div/wnz-search/div[1]/main/product-grid/cdx-card[*]/product-stamp-grid/a/h3'

# XPath for countdown product prices
path_price_cd = '/html/body/wnz-content/div/wnz-search/div[1]/main/product-grid/cdx-card[*]/product-stamp-grid/a/div[2]/product-price/h3'


# Gets all the information needed from different webpages
def crawler(identifier, link, path_name, path_price=None):
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 1
    })

    # Initialize the webdriver with options
    driver = uc.Chrome(options=options)

    try:
        # Get the webpage
        driver.get(link)
        time.sleep(3)

        # Countdown
        if path_price is not None:
            prod_details = driver.find_elements(by="xpath", value=path_name)
            price_details = driver.find_elements(by="xpath", value=path_price)
            price_per_unit = driver.find_elements(By.CLASS_NAME, value='size')

            # From prod_details and price_details, get the attributes (Product name, Price),
            # replace/ clean the output, then store in a dictionary those values
            return [{'storeID': identifier, 'productName': prod.get_attribute("aria-label").replace(".", ""),
                     'pricePerItem': re.compile(r'\d+\.\d+').search(price.get_attribute("aria-label")).group(),
                     'pricePerBaseUnitText': unit.text
                     } for prod, price, unit in zip(prod_details, price_details, price_per_unit)]

        # Pak n Save and New World
        prod_details = driver.find_elements(by="xpath", value=path_name)
        products = [json.loads(item.get_attribute("data-options")) for item in prod_details]

        # Take the items needed from the products, store in list of dictionaries
        pak_nw_dict = [{'storeID': identifier, 'productName': item['productName'],
                        'pricePerItem': item['ProductDetails']['PricePerItem'],
                        'pricePerBaseUnitText': item['ProductDetails']['PricePerBaseUnitText']}
                       for item in products]

        return pak_nw_dict

    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()


def search(query):
    links = [pak_n_save, new_world, countdown]
    return [f"{link}{urllib.parse.quote(q)}" for q in query.split(",") for link in links]


if __name__ == '__main__':
    # Search for products
    get_links = search(input("Search for groceries: "))

    # Organize the links
    pak_n_save = [item for item in get_links if "paknsave" in item]
    new_world = [item for item in get_links if "newworld" in item]
    countdown = [item for item in get_links if "countdown" in item]

    # Multi-threading to make the process faster
    # honey, cookie, salt, sugar, fish, meat, apples, oranges, bananas, plums (Test)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Structure of the args
        links_list_path = [(pak_n_save, path_pn), (new_world, path_pn),
                           (countdown, path_product_cd, path_price_cd)]

        # Use each of the values, 'x', and path to make new tuples to feed crawler()
        tuple_pak = [("pak", x, links_list_path[0][1]) for x in links_list_path[0][0]]
        tuple_new = [("new", x, links_list_path[1][1]) for x in links_list_path[1][0]]
        tuple_cd = [("cd", x, links_list_path[2][1], links_list_path[2][2]) for x in
                    links_list_path[2][0]]

        # Getting each of the items from the 3 lists then adding it to 'tuples'
        tuples = [item for sublist in [tuple_pak, tuple_new, tuple_cd] for item in sublist]

        # * Unpacks the tuple of args into separate 'arg'
        results = list(executor.map(lambda args: crawler(*args), tuples))

    pd.options.display.max_rows = None
    pd.options.display.max_columns = None

    # [[{}, {}], [{}, {}], [{}, {}], ...] -> [{}] Flattened out
    flat_results = [item for sublist in results for item in sublist]

    # Make a data frame of results and save it as csv file
    df_out = pd.DataFrame(flat_results, columns=["storeID", "productName", "pricePerItem", "pricePerBaseUnitText"])
    df_out.to_csv('output_all.csv', index=False, mode='w')
    print(df_out)
