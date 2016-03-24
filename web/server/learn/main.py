import sys
from pymongo import MongoClient
import numpy as np

from sklearn.svm import SVC
from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.grid_search import GridSearchCV

from model import model

mongo_client = MongoClient()
db = mongo_client.jd
cols = {
    'product': db['products'],
    'comment': db['comments'],
    'marked': db['markedComments'],
    'user': db['users'],
    'tag': db['tags']
}


def find_best():
    train = model.CommentModel(cols)
    train.init(to_train=False)
    features = []
    marked = []
    contents = []
    for c in cols['marked'].find():
        feature = train.gen_feature(c, output=False)
        features.append(feature)
        marked.append(c['mark'])
        contents.append(c['content'])
    features = np.asarray(features)
    marked = np.asarray(marked)
    print('Start...', len(features))
    c_range = np.logspace(-2, 5, 8)
    gamma_range = np.logspace(-5, 2, 8)
    param_grid = dict(gamma=gamma_range, C=c_range)
    print(gamma_range, c_range, param_grid)
    cv = StratifiedShuffleSplit(marked, n_iter=2, test_size=0.2, random_state=42)
    print(cv)
    grid = GridSearchCV(SVC(), param_grid=param_grid, cv=cv)
    grid.fit(features, marked)
    print("The best parameters are %s with a score of %0.2f" % (grid.best_params_, grid.best_score_))
    print(grid.grid_scores_)


if __name__ == '__main__':
    method = None
    if len(sys.argv) == 1:
        method = 'train'
    else:
        method = sys.argv[1]

    if method == 'train':
        train = model.CommentModel(cols)
        train.init()
        for c in cols['comment'].find()[:100]:
            prob = train.predict(c)
            if prob[1] > 0.5:
                print(c['content'])
    elif method == 'best':
        find_best()
    elif method == 'test':
        train = model.CommentModel(cols)
        train.init(to_train=False)
        train.test(sys.argv[2])
    else:
        print('wrong input.')
