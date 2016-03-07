import random
import traceback
import time
import redis
from datetime import datetime
import simplejson as json
from pymongo import MongoClient
import requests

from config import default

r = redis.StrictRedis()
mongo_client = MongoClient()
db = mongo_client.jd
product_col = db['products']
tag_col = db['tags']
user_col = db['users']
comment_col = db['comments']
page = 0

user_agents_file = open('uas.txt', mode='r')
ua_list = [x.strip() for x in user_agents_file.readlines()]


def fetch_comments(skuid):
    global page
    page = 0
    while True:
        sec = random.randint(1, 3)
        time.sleep(sec)
        ua = random.choice(ua_list)
        url = default['comment_host'] % (skuid, page)
        print('Start fetch:', url)
        comments_json = requests.get(url, headers={'User-Agent': ua})
        print('Fetch Done:', url)
        if not comments_json.text:
            break
        comments = json.loads(comments_json.text)
        if len(comments['comments']):
            save_to_mongo(skuid, comments, page)
            page += 1
            print('INFO: Progress Sku=%s, Comment Page=%d' % (skuid, page))
        else:
            print('INFO: Finish Sku=%s' % skuid)
            break


def save_to_mongo(skuid, comments, page):
    print('Save to mongo')
    if page == 0:
        summary = comments['productCommentSummary']
        save_to_summary = {
            'productId': summary.get('productId'),
            'scoreCount': [
                summary.get('score1Count'),
                summary.get('score2Count'),
                summary.get('score3Count'),
                summary.get('score4Count'),
                summary.get('score5Count'),
            ],
            'commentCount': summary.get('commentCount'),
            'rates': {
                'good': summary.get('goodRate'),
                'general': summary.get('general'),
                'poor': summary.get('poor')
            }
        }
        tags = comments['hotCommentTagStatistics']
        print('Update product')
        product_col.update_one({'skuid': skuid}, {'$set': save_to_summary}, upsert=True)
        print('Start update tags')
        for tag in tags:
            tag['tag_id'] = tag['id']
            del tag['id']
            tag_col.update_one({'tag_id': tag['tag_id']}, {'$set': tag}, upsert=True)

    for comment in comments['comments']:
        save_to_user = {
            'nickname': comment.get('nickname'),
            'levelId': comment.get('userLevelId'),
            'province': comment.get('userProvince'),
            'registerTime': datetime.strptime(comment.get('userRegisterTime'), '%Y-%m-%d %H:%M:%S'),
            'levelName': comment.get('userLevelName')
        }
        if comment.get('anonymousFlag') == 1:
            print('Update users by regex')
            user_col.insert_one(save_to_user)
        else:
            print('Update users by nickname directly')
            user_col.update_one({
                'nickname': save_to_user['nickname'],
                'registerTime': save_to_user['registerTime']
            }, {'$set': save_to_user}, upsert=True)
        exists = comment_col.find_one({'id': comment['id']})
        if not exists:
            print('Insert', comment['id'])
            comment_col.insert_one(comment)


while True:
    sku = r.spop('comment_list').decode('utf-8')
    print('SKUID:', sku)
    try:
        fetch_comments(sku)
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
