from pymongo import MongoClient
from bson import ObjectId
import copy

DEFAULT_PROJECTION = {
    'content': 1,
    'referenceName': 1,
    'creationTime': 1,
    'userLevelName': 1,
    'usefulVoteCount': 1,
    'uselessVoteCount': 1,
    'imageCount': 1,
    'commentTags': 1
}

trained_model = None


def mapTag(c):
    if c.get('commentTags'):
        c['commentTags'] = list(map(lambda t: t['name'], c['commentTags']))
    return c


class Mongo:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.jd
        self.product = self.db['products']
        self.tag = self.db['tags']
        self.user = self.db['users']
        self.comment = self.db['comments']
        self.marked = self.db['markedComments']
        self.trained = None

    def init_model(self, model):
        self.trained = model

    def sample(self):
        comments = self.comment.aggregate([
            {
                '$project': DEFAULT_PROJECTION
            },
            {
                '$match': {'marked': {'$ne': True}}
            },
            {
                '$sample': {'size': 25}
            }
        ])

        return map(mapTag, comments)

    def save(self, marked):
        for (comment_id, value) in marked.items():
            comment = self.comment.find_one({'_id': ObjectId(comment_id)})
            comment['mark'] = 1 if value else 0
            try:
                self.marked.insert_one(comment)
                self.comment.update_one({'_id': ObjectId(comment_id)}, {'$set': {'marked': True}})
            except Exception:
                print('Exp', Exception)

    def predict(self, comment_id):
        c = self.comment.find_one({'_id': ObjectId(comment_id)})
        print(self.trained.predict(c))
        return self.trained.predict(c)

    def get_marked(self):
        projection = copy.copy(DEFAULT_PROJECTION)
        projection['mark'] = 1
        return map(mapTag, self.marked.find(projection=projection))

    def delete_marked(self, mark_id):
        self.marked.delete_one({'_id': ObjectId(mark_id)})
        self.comment.update_one({'_id': ObjectId(mark_id)}, {'$set': {'marked': False}})
