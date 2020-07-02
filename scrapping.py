import requests
import re
from bs4 import BeautifulSoup
import cloudscraper
import json

file_path = 'known_sites_tags.json'

'''
- price regex = '^(?=.*\d)[\d, zł, грн, ₴, $, usd, pln, uah]+'
'''

def load_sites_tags():
    with open(file_path, 'r') as dt:
        data = json.load(dt)
        return data


def save_new_tag(data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


site_price_tags = load_sites_tags()
possible_tag_args = ['class', 'itemprop', 'id']
possible_tags = ['div', 'p', 'span']


def get_site_name(url):
    site_pattern = re.compile(f'://(.[^/]+)')
    site_name = site_pattern.search(url).group(1)
    site_name = site_name.replace('www.', '')
    return site_name


def get_site_price_tag(site_name):
    try:
        site_tag = site_price_tags[site_name]
        return site_tag
    except Exception:
        return None


def get_url(url):
    # headers = {
    #     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
    headers = {'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'}
    session = requests.Session()
    session.headers = headers
    scraper = cloudscraper.create_scraper(sess=session)

    contents = scraper.get(url, headers=headers, timeout=5)
    url = contents.text
    return url


def get_price(url):
    html = get_url(url)

    price_tag = get_site_price_tag(get_site_name(url))
    tag_name = price_tag[0]
    tag = price_tag[1]
    tag_arg = price_tag[2]
    try:
        json_key = price_tag[3]
    except:
        json_key = None
    soup = BeautifulSoup(html, 'html.parser')
    if tag_arg == 'class':
        price = soup.find(tag, class_=tag_name).text
    elif tag_arg == 'itemprop':
        price = soup.find(tag, itemprop=tag_name).text
    price = price.replace('\n', '')
    price = price.replace('  ', '')
    if json_key is not None:
        pattern = re.compile(f"{{{json_key} '(.[^']+)")
        finded_price = pattern.search(price)
        json_price = finded_price.group(1)
        return json_price
    return price


def get_price_js_content(js, price):
    pattern = "{+(\w+:) '" + price + "'"
    result = re.search(pattern, js)
    # print(result.group(1))
    return result.group(1)


def get_price_unknown(url, tagName, tagType, tagArg, js_price):
    html = get_url(url)

    html = html.replace(' ', ' ')
    tag_name = tagName
    tag = tagType
    tag_arg = tagArg
    soup = BeautifulSoup(html, 'html.parser')
    if tag_arg == 'class':
        price = soup.find(tag, class_=tag_name).text
    elif tag_arg == 'itemprop':
        price = soup.find(tag, itemprop=tag_name).text
    else:
        price = ""
    price = price.replace('\n', '')
    price = price.replace('  ', '')
    if len(price) > 30:
        print('JSON data')
        json_key = get_price_js_content(price, js_price)
        return price, json_key
    return price, None


def search_unknown_site_tag(url, price):
    html = get_url(url)
    # there is a rare posability, that some sites have another "space blank" code
    html = html.replace(' ', ' ')
    soup = BeautifulSoup(html, 'html.parser')
    scores = soup.find_all(text=re.compile(price))
    # with open('content.txt', 'w', encoding='utf8') as f:
    #     f.write(str(scores))
    for tag in possible_tags:
        tags_with_price = [score.findParent(
            tag) for score in scores if score.findParent(tag) is not None]
        tags_with_price = list(filter(None, tags_with_price))
        if tags_with_price != []:
            for tag_with_price in tags_with_price:
                tag = str(tag_with_price)
                parent_tag = str(tag_with_price.parent)
                for pta in possible_tag_args:  # example: pta = 'class'
                    for pt in possible_tags:  # example: pt = 'div'
                        print(f'pta: {pta}, pt: {pt}')
                        pattern = re.compile(f'<{pt} {pta}="([^"]+)')
                        tag_string = pattern.search(tag)
                        if tag_string is not None:
                            tag_name = tag_string.group(1)
                            context, json_key = get_price_unknown(url, tag_name, pt, pta, price)
                            if price in context:
                                print(pt, pta, tag_name, json_key)
                                return pt, pta, tag_name, json_key
                        # searh parent tag, if price tag was not found
                        tag_parent_string = pattern.search(parent_tag)
                        if tag_parent_string is not None:
                            tag_parent_name = tag_parent_string.group(1)
                            if price in get_price_unknown(url, tag_parent_name, pt, pta, price):
                                return pt, pta, tag_parent_name
    return None, None, None



# url = 'https://rozetka.com.ua/ua/xiaomi_mi_notebook_pro_156_core_i5_8_256gb_10504g/p64632925/'
url = 'https://www.lamoda.ua/p/mp002xu0334b/bags-nike-ryukzak/'

# print(search_unknown_site_tag(url,'949'))
# print(get_price(url))

site_name = get_site_name(url)

# sites_tags[site_name] = ["1", "2", "3"]

# save_new_tag(sites_tags)

# tag_type, tag_arg, tag_name, json_key = search_unknown_site_tag(url, '949')
# site_price_tags[site_name] = [tag_name, tag_type, tag_arg, json_key]
# save_new_tag(site_price_tags)
# print(tag_type, tag_arg, tag_name)



# js = get_price_unknown(url, tag_name, tag_type, tag_arg)
# get_price_js_content(js, '265')
