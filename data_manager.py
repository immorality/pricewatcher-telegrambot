# -*- coding: utf-8 -*-
import json
from scrapping import get_price, get_site_name, load_sites_tags

file_path = 'data.json'


def getJsonData():
    with open(file_path, 'r', encoding='utf-8') as dt:
        data = json.load(dt)
        return data


info = getJsonData()


def save(data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def add_item(user_id, item, url):
    if user_id in info:
        if item not in info[user_id]['items']:
            if get_site_name(url) not in load_sites_tags():
                return None
            try:
                price = get_price(url)
            except Exception:
                return None
            info[user_id]['items'][item] = {'https': url, 'price': price}
            save(info)
            print('Item added')
            return True
        else:
            return False
            print('Item already exist!')
    else:
        return False
        print('User not exist!')


def delete_item(user_id, item):
    if user_id in info:
        if item in info[user_id]['items']:
            del info[user_id]['items'][item]
            save(info)
            print('Item deleted')
            return True
        else:
            print('Item not exist!')
            return False
    else:
        return False
        print('User not exist!')


def delete_all_item(user_id):
    if user_id in info:
        if bool(info[user_id]['items']):
            for item in list(info[user_id]['items']):
                del info[user_id]['items'][item]
            save(info)
            print('Items deleted')
            return True
        else:
            print('Your have no items!')
            return False
    else:
        return False
        print('User not exist!')


def get_sites_list():
    sites = load_sites_tags()
    sites = sites.keys()
    return list(sites)

def get_user_items(user_id):
    if user_id in info:
        if info[user_id]['items']:
            list_of_items = [[item, f"[{get_site_name(info[user_id]['items'][item]['https'])}]({info[user_id]['items'][item]['https']})", f"*{info[user_id]['items'][item]['price']}*"] for item in info[user_id]['items']]
            return list_of_items
    else:
        print('No user')
        return False

def add_new_user(user_id, user_name):
    info[user_id] = {"name": user_name,
                     "items": {}}
    save(info)

def get_saved_price(user_id, item_name):
    return info[user_id]['items'][item_name]['price']

def check_user_exist(user_id):
    if user_id in info:
        return True
    return False
