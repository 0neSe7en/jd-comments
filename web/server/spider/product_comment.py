import random
import sys
import time
import traceback
from datetime import datetime

import redis
import requests
import simplejson as json
from pymongo import MongoClient

from config import default

r = redis.StrictRedis()
mongo_client = MongoClient()
db = mongo_client.jd
product_col = db['products_mobile']
tag_col = db['tags_mobile']
user_col = db['users']
comment_col = db['comments_mobile']

user_agents_file = open('uas.txt', mode='r')
ua_list = [x.strip() for x in user_agents_file.readlines()]


class Spider:
    def __init__(self, skuid=None, page=0):
        self.skuid = skuid
        self.retry = 0
        self.page = page
        self.host = default['comment_host']
        self.changed = False
        # if skuid:
        #     self.comment_count = product_col.find_one({'skuid': skuid})['commentCount']

    def get_header(self, ua):
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': ':zh-CN,zh;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': '_tp=QXX9VtyNdwlHMCZRrP4eAXfaOke9ixA6K2cQRnUQa8g%3D; unick=wsy19940107; _pst=jd_65f66868daac7; TrackID=1wJIUeky-S2F1BmbGMNBAcmCZXhkBK0GEkQk4QugLa6989QQXZp1LfT7R__IVFad62ifr1fWkggzX3-XCoev2Pntew-Qk8iPiyDnsBfbFXtbi6Msv057rwpV7bIPec34V; pinId=8p65jm9RD1L7kd0WGay4WrV9-x-f3wj7; pin=jd_65f66868daac7; user-key=ba93466b-1457-48c3-8d3e-cfa5f3d26e2b; cn=0; unpl=V2_ZzNtbUFRQhR2CU4HKB0OAWIEEVxLURQVIQ5EVn1MXVJgBhdeclRCFXIUR1ZnGFoUZwUZXkZcRhJFCHZUehhdBGcDFl5KZ3Mldgl2UEsZWAZiAxBeRlRKJUUPdmRLGGwEVwIiFixWDhVxC0NUeRpYBm4zEw%3d%3d; __jdv=122270672|www.mengfeikeji.com|t_1000011529_|tuiguang|2700209bb5c5462087f1e7337d0f6442-p_388224673; mt_subsite=122%252C1457401429%7C125%2C1457342746%7C; mt_xid=V2_52007VwMWUVhYUFkbShBsVm9TFlJbW1dGSh5OCBliAxNWQQgHD0hVGl9VZAEUUwlYBlsceRpdBWAfE1BBWVtLHkESWQBsABtiX2hSahlPG1wCZQMiUl5bVw%3D%3D; sid=97c36eaa415ed131fbbc27e2d0dd33d4; mba_muid=1457401428540-78797cc1d0d81e5644; thor=CD904FCD5483F6F5B50B37D11A41A436257E94B3172BFE0A8DD81D542EECAAB0909232D7E5C1A367DB7E04BBC1EBF1FD6AD8EAEFF975DB59A6AF71C8BF7F686C5F346A97F9123173A2B508A58A655D57C2AEFA2C46F8FDAB671F04E6001877AB8CA6E35A664B07B2A0AAA7BAE0A961D14994D2F10C285CD7A717931BDD514E260824D1BFBCAD1A1673DDCCEAC03E8718AA8746183B268C342450B164A9E9148B; __jda=122270672.1524132528.1457098599.1457408627.1457411961.13; __jdb=122270672.3.1524132528|13.1457411961; __jdc=122270672; ipLocation=%u5317%u4EAC; areaId=1; ipLoc-djd=1-72-2799-0; __jdu=1524132528'
        }

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

    def fetch_single(self, url):
        ua = random.choice(ua_list)
        comments_json = requests.get(url, headers=self.get_header(ua))
        comments = json.loads(comments_json.text)
        return self.save_to_mongo(comments)

    def fetch_comments(self, exhaustive=False):
        while True:
            sec = random.randint(8, 15)
            time.sleep(sec)
            ua = random.choice(ua_list)
            url = self.host % (self.skuid, self.page)
            print('Start fetch:', url)
            comments_json = requests.get(url, headers=self.get_header(ua))
            print('Fetch Done:', url)

            if exhaustive:
                if not comments_json.text:
                    self.retry += 1
                    if self.retry > 5:
                        time.sleep(20)
                    continue
                comments = json.loads(comments_json.text)
                self.retry = 0
                if len(comments['comments']):
                    self.save_to_mongo(comments)
                    self.page += 1
                    print('INFO: Progress Sku=%s, Comment Page=%d' % (self.skuid, self.page))
                else:
                    count = comment_col.count({'skuid': self.skuid})
                    print('Current Count %d, Max Count %d' % (count, self.comment_count))
                    if count + 500 > self.comment_count:
                        break
                    else:
                        continue
            else:
                if not comments_json.text:
                    if self.do_retry():
                        continue
                    else:
                        r.hset('progress', self.skuid, self.page)
                        break
                comments = json.loads(comments_json.text)
                if len(comments['comments']):
                    self.clear_retry()
                    self.save_to_mongo(comments)
                    self.page += 1
                    print('INFO: Progress Sku=%s, Comment Page=%d' % (self.skuid, self.page))
                else:
                    print('INFO: SKU=%s finished, Page=%d' % (self.skuid, self.page))
                    break

    def save_to_mongo(self, comments):
        print('Save...')
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
        inserted_ids = []
        for comment in comments['comments']:
            exists = comment_col.find_one({'guid': comment['guid']})
            if exists:
                inserted_ids.append(exists['_id'])
                print('SKUID=%s Exists, Jump' % self.skuid)
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
            oid = comment_col.insert_one(comment).inserted_id
            inserted_ids.append(oid)
        return inserted_ids


def from_progress():
    sku_list = r.hgetall('progress')
    for (sku, page) in sku_list.items():
        print('SKUID:', sku.decode('utf-8'), int(page))
        spider = Spider(sku.decode('utf-8'), int(page))
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


def basic():
    while True:
        sku = r.spop('comment_list')
        print('SKUID... start', sku)
        spider = Spider(sku.decode('utf-8'))
        print('SKUID:', sku)
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


if __name__ == '__main__':
    basic()
    # skuid_list = ['1378538', '2123282', '1664594', '1664592', '1466274',
    #               '1730595', '1946272', '1999938', '1309456', '1956794',
    #               '2024548', '1852822', '2232248', '1579645', '1331785']
    #
    # print(sys.argv[1])
    # number = int(sys.argv[1])
    # print('Start...', number)
    #
    # s = Spider(skuid_list[number])
    # while True:
    #     try:
    #         s.fetch_comments(exhaustive=True)
    #     except Exception as e:
    #         time.sleep(240)
    #         continue
