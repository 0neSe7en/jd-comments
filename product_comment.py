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

user_agents_file = open('uas.txt', mode='r')
ua_list = [x.strip() for x in user_agents_file.readlines()]


class Spider:
    def __init__(self, skuid):
        self.skuid = skuid
        self.retry = 0
        self.page = 0
        self.host = default['comment_host']
        self.changed = False

    def do_retry(self):
        if self.retry > 3 and self.changed:
            return False
        if self.changed:
            self.retry += 1
        else:
            if self.host == default['comment_host']:
                self.host = default['another_host']
            else:
                self.host = default['comment_host']
            self.changed = True
        return True

    def clear_retry(self):
        self.retry = 0
        self.changed = False

    def fetch_comments(self):
        while True:
            sec = random.randint(1, 3)
            time.sleep(sec)
            ua = random.choice(ua_list)
            url = self.host % (self.skuid, self.page)
            print('Start fetch:', url)
            comments_json = requests.get(url, headers={'User-Agent': ua})
            print('fetch Done:', url)
            if not comments_json.text:
                if self.do_retry():
                    continue
                else:
                    break
            comments = json.loads(comments_json.text)
            if len(comments['comments']):
                self.clear_retry()
                self.save_to_mange(comments)
                self.page += 1
                print('INFO: Progress Sku=%s, Comment Page=%d' % (self.skuid, self.page))
            else:
                print('INFO: SKU=%s finished, Page=%d' % (self.skuid, self.page))
                break

    def save_to_mange(self, comments):
        print('Save to mongo')
        if self.page == 0:
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
            product_col.update_one({'skuid': self.skuid}, {'$set': save_to_summary}, upsert=True)
            for tag in tags:
                tag['tag_id'] = tag['id']
                del tag['id']
                tag_col.update_one({'tag_id': tag['tag_id']}, {'$set': tag}, upsert=True)

        for comment in comments['comments']:
            exists = comment_col.find_one({'id': comment['id']})
            if exists:
                continue
            save_to_user = {
                'nickname': comment.get('nickname'),
                'levelId': comment.get('userLevelId'),
                'province': comment.get('userProvince'),
                'registerTime': datetime.strptime(comment.get('userRegisterTime'), '%Y-%m-%d %H:%M:%S'),
                'levelName': comment.get('userLevelName')
            }
            if comment.get('anonymousFlag') == 1:
                user_exists = user_col.find_one({'registerTime': save_to_user['registerTime']})
                if not user_exists:
                    user_col.insert_one(save_to_user)
            else:
                user_col.update_one({'registerTime': save_to_user['registerTime']}, {'$set': save_to_user}, upsert=True)
            comment['skuid'] = self.skuid
            print('Insert', comment['id'])
            comment_col.insert_one(comment)


while True:
    sku = r.spop('comment_list').decode('utf-8')
    print('SKUID:', sku)
    spider = Spider(sku)
    try:
        spider.fetch_comments()
    except KeyboardInterrupt:
        print('Keyboard')
        r.hset('progress', spider.skuid, spider.page)
        break
    except Exception as e:
        print('Someting happen', e)
        traceback.print_exc()
        time.sleep(180)
        continue
