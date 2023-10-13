from cachecontrol.caches import FileCache
from cachecontrol import CacheControl
from bs4 import BeautifulSoup
from threading import Thread
from base64 import b64encode
from queue import Queue
import requests
import random


# u = UserAgent()

cache = CacheControl(requests.Session(), cache=FileCache('.web_cache'))


User_Agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
]

Header = {
    'User-Agent': random.choice(User_Agents),
    'Accept-Language': 'en-US, en;q=0.5',
}


# Make the soup (The source code) of the product page
def make_soup(barcode):
    url_amz = "https://www.amazon.com/dp/" + barcode + "?th=1"

    webpage = cache.get(url_amz, headers=Header)
    webpage_txt = webpage.text

    if "sure you're not a robot" in webpage_txt:
        webpage.close()
        Header['User-Agent'] = random.choice(User_Agents)
        return make_soup(barcode)

    if webpage.status_code == 404:
        return None

    soup = BeautifulSoup(webpage_txt, 'html.parser')

    return soup


def get_image(soup: BeautifulSoup):
    try:
        link = soup.find('div', attrs={'id': 'imgTagWrapperId'}).find('img').get('src')
    except:
        return None

    link_content = requests.get(link).content
    link_b64 = b64encode(link_content)

    return link_b64


def get_title(soup: BeautifulSoup):
    try:
        title = soup.find('span',
                          attrs={'id': 'productTitle'}).text.strip()
        return title
    except:
        return None


price_places = [
    'a-price aok-align-center',
    'a-price a-text-price a-size-medium apexPriceToPay',
    'a-price aok-align-center reinventPricePriceToPayMargin priceToPay',
]


def get_price(soup: BeautifulSoup):
    try:
        for price_place in price_places:
            price_pos = soup.find('span', attrs={'class': price_place})
            if price_pos:
                price = price_pos.text
                if price.count("$") != 1:
                    price = price[:price.find("$", 2)]

                return price.strip()
    except:
        return None


def get_rating(soup: BeautifulSoup):
    try:
        rating = soup.find('span', attrs={'id': 'acrPopover'}).get('title')
        rating = float(rating.split()[0])
        return rating
    except:
        return None


def get_reviews(soup: BeautifulSoup):
    try:
        reviews = soup.find('span', attrs={'id': 'acrCustomerReviewText'}).text
        reviews = reviews.split()[0].replace(',', '')
        return int(reviews)
    except:
        return None


def get_availability(soup: BeautifulSoup):
    try:
        available = soup.find("div", attrs={'id': 'availability'})
        available = available.find("span").string.strip()

    except:
        available = "Not Available"

    return available


def get_seller(soup: BeautifulSoup):
    try:
        seller = soup.find('div', id='tabular-buybox')
        seller = seller.find('div',
                             attrs={'tabular-attribute-name': 'Sold by', 'class': 'tabular-buybox-text'}).text.strip()
        return seller
    except:
        pass
    try:
        seller = soup.find('div', id='shipFromSoldByAbbreviatedODF_feature_div')
        seller = seller.find_all('span', attrs={'class': 'a-size-small'})[-1].text.strip()
        return seller
    except:
        pass
    try:
        seller = soup.find('div', id='merchantInfoFeature_feature_div')
        seller = seller.find('div', attrs={'class': 'offer-display-feature-text'}).text.strip()
        return seller
    except:
        pass

    return None



def get_all_data(soup: BeautifulSoup):
    product_soup = soup

    name = get_title(product_soup)
    product = {
        'name': name,
        'short_title': name[:38] + "..." if len(name) > 38 else name,
        'price': get_price(product_soup),
        'image': get_image(product_soup),
        'rating': get_rating(product_soup),
        'reviews': get_reviews(product_soup),
        'status': get_availability(product_soup),
        'seller': get_seller(product_soup),
    }

    return product


def generate_data_products(queue: Queue, asins_num):
    products = list()

    def append_data_product():
        while not queue.empty():
            asin = queue.get()

            if type(asin) == str:
                soup = make_soup(asin)
                values = {
                    'asin': asin,
                }

            else:
                soup = make_soup(asin[1])
                values = {
                    'id': asin[0],
                    'asin': asin[1],
                }

            if not soup:
                products.append(values)
                queue.task_done()
                continue

            product_data = get_all_data(soup)

            for key, value in product_data.items():
                values[key] = value

            products.append(values)

            queue.task_done()

    if asins_num <= 2:
        threads_num = 1
    else:
        threads_num = round(asins_num / 2)

    for i in range(threads_num):
        t = Thread(target=append_data_product)
        t.start()
    queue.join()

    return products
