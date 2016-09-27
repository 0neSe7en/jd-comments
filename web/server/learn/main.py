import sys
from pymongo import MongoClient
import numpy as np

import jieba
import jieba.analyse

from sklearn.svm import SVC
from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.grid_search import GridSearchCV

from model import model

mongo_client = MongoClient()
db = mongo_client.jd
cols = {
    'product': db['products'],
    'comment': db['comments'],
    'mobile_comment': db['comments_mobile'],
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


def generate_top():
    from collections import defaultdict
    import simplejson as json
    import operator
    from_product = defaultdict(lambda: 0)
    results = defaultdict(lambda: 0)
    for product in cols['product'].find().sort('_id', -1):
        for k in product.keys():
            from_product[k] += 1
    product_keys = dict(from_product)
    for w in list(product_keys.keys()):
        jieba.add_word(w, tag='nz')
    progress = 0
    for comment in cols['comment'].find(projection={'content': 1}):
        c = comment['content']
        words = jieba.analyse.extract_tags(c, topK=20, withWeight=False, allowPOS=('ns', 'n', 'nz'))
        for w in words:
            results[w] += 1
        progress += 1
        if progress % 100 == 0:
            print('Current Progress: ', progress)
    sorted_x = reversed(sorted(dict(results).items(), key=operator.itemgetter(1)))
    json.dump(
        list(sorted_x),
        open('sorted_mobile.json', mode='w', encoding='utf-8'),
        ensure_ascii=False,
        indent=2
    )
    # print(sorted_x)


if __name__ == '__main__':
    method = None
    if len(sys.argv) == 1:
        method = None
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
    # elif method == 'lstm':
    #     train = model.CommentModel(cols)
    #     train.init(to_train=False)
    #     train.lstm()
    elif method == 'save':
        train = model.CommentModel(cols)
        train.init()
        train.save()
    elif method == 'mobile':
        cols['product'] = db['products_mobile']
        train = model.CommentModel(cols)
        train.init(to_train=False, category='mobile')
        train.from_redis()
        pos = []
        neg = []
        for c in cols['mobile_comment'].aggregate([
            {'$sample': {'size': 100}}
        ]):
            prob = train.predict(c)
            if prob[1] > 0.6:
                neg.append(c['content'])
            else:
                pos.append(c['content'])
        print('Positive:')
        print('\n'.join(pos))
        print('\n\nNegitive:')
        print('\n'.join(neg))
    elif method == 'generate':
        cols['product'] = db['products_mobile']
        generate_top()
    else:
        print('''
        Usage:
        python main.py train       - train model and show output from marked comments.
        python main.py best        - find best parameters for svm.
        python main.py save        - save model to redis.
        python main.py generate    - generate top words.
        python main.py test report - show report results.
        python main.py test cross_validation - show cross_validation results.
        ''')
