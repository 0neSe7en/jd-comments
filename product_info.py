import random
import traceback
import time
import redis
from bs4 import BeautifulSoup
from datetime import datetime
import simplejson as json
from pymongo import MongoClient
import requests


from config import default

r = redis.StrictRedis()
mongo_client = MongoClient()
db = mongo_client.jd
host = 'http://item.jd.com/%s.html'
product_col = db['products']


def fetch_product(skuid):
    product_info = requests.get(host % skuid).text
    soup = BeautifulSoup(product_info, 'lxml')
    summary = soup.find_all('li', title=True)
    summary_desc = {}
    for s in summary:
        if s.string:
            summary_desc[s.string.split('：')[0]] = s.get('title')
    attrs = soup.find_all('td', class_='tdTitle')
    attrs_desc = {}
    for attr in attrs:
        attrs_desc[attr.string] = attr.parent.contents[1].string
    summary_desc.update(attrs_desc)
    product_col.update_one({'skuid': skuid}, {'$set': summary_desc}, upsert=True)


while True:
    sku = r.srandmember('product_list').decode('utf-8')
    print('SKUID:', sku)
    try:
        fetch_product(sku)
    except KeyboardInterrupt:
        print('Keyboard')
        r.hset('progress', sku, page)
        break
    except Exception as e:
        print('Someting happen', e)
        traceback.print_exc()
        # r.hset('progress', sku, page)
        time.sleep(180)
        continue
