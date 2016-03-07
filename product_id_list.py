import random
import requests
import redis
import re

from config import default

r = redis.StrictRedis()
p = re.compile(r'fp-text.+?<i>(\d+)</i>', re.MULTILINE | re.IGNORECASE)
sku_re = re.compile(r'data-sku="(\d+)"', re.MULTILINE | re.IGNORECASE)
user_agents_file = open('uas.txt', mode='r')
ua_list = [x.strip() for x in user_agents_file.readlines()]
max_page = None


def page_url(page):
    return default['list_host'] % (default['category'], page)


def get_max_page():
    global max_page
    ua = random.choice(ua_list)
    list_page = requests.get(page_url(1), headers={'User-Agent': ua})
    print(list_page.text)
    max_page = int(p.search(list_page.text).group(1))
    print(max_page)


def fetch_skuid_list():
    for current_page in range(1, max_page):
        ua = random.choice(ua_list)
        print('INFO: fetch ', page_url(current_page))
        page = requests.get(page_url(current_page), headers={'User-Agent': ua})
        id_list = sku_re.findall(page.text)
        print('Page: ', current_page, id_list)
        r.sadd('product_list', *id_list)
        r.sadd('comment_list', *id_list)

get_max_page()
fetch_skuid_list()
