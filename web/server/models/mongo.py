from pymongo import MongoClient
from bson import ObjectId
import copy

DEFAULT_PROJECTION = {
    'content': 1,
    'referenceName': 1,
    'creationTime': 1,
    'userLevelName': 1,
    'usefulVoteCount': 1,
    'uselessVoteCount': 1
}


class Mongo:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.jd
        self.product = self.db['products']
        self.tag = self.db['tags']
        self.user = self.db['users']
        self.comment = self.db['comments']
        self.marked = self.db['markedComments']

    def sample(self):
        return self.comment.aggregate([
            {
                '$project': DEFAULT_PROJECTION
            },
            {
                '$sample': {'size': 25}
            }
        ])

    def save(self, marked):
        for (comment_id, value) in marked.items():
            comment = self.comment.find_one({'_id': ObjectId(comment_id)})
            comment['mark'] = 1 if value else 0
            self.marked.insert_one(comment)

    def get_marked(self):
        projection = copy.copy(DEFAULT_PROJECTION)
        projection['mark'] = 1
        return self.marked.find(projection=projection)
