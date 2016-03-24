from collections import defaultdict
import simplejson as json
import jieba
import jieba.analyse
import logging
from sklearn import svm, cross_validation
from sklearn.cross_validation import train_test_split
from sklearn.metrics import classification_report
from tabulate import tabulate

logging.basicConfig(format='%(asctime)s - %(filename)s: %(name)s - %(message)s', level=logging.ERROR)

unused_words = ['commentCount', 'skuid', '材质/工艺', '_id', '功\u3000率（W）', '电\u3000压', 'scoreCount', 'productId', '品牌']
another_words = ['轻薄', '触摸屏', 'win', 'Win', 'windows', 'Windows',
                 '英雄联盟', '硬盘', '鲁大师', '无线网络', '系统', 'USB',
                 '更新', '卡顿', '噪声', '设备']
black_test = [
    '长度在5-200个字之间 填写您对此商品的使用心得，例如该商品或某功能为您带来的帮助，或使用过程中遇到的问题等。最多可输入200字',
    '机器性能如何？散热好么？配件质量如何？快把你的使用感受告诉大家吧！'
]

quantifying_methods = ['accuracy', 'f1_macro', 'log_loss', 'recall']


class CommentModel:
    def __init__(self, cols):
        self.cols = cols
        self.model = None
        self.keys = {
            'top': {},
            'product': {}
        }
        self.ready = False

    def init(self, to_train=True):
        logging.info('start init model...')
        logging.info('start generate keys...')
        self._gen_keys()
        logging.info('start add words to jieba')
        self._add_words(another_words)
        if to_train:
            logging.info('start to train the model...')
            self.train()
        self.ready = True
        logging.info('have fun.')

    def test(self, method='report'):
        X = []
        y = []
        contents = []
        for marked in self.cols['marked'].find():
            X.append(self.gen_feature(marked))
            y.append(marked['mark'])
            contents.append(marked['content'])
        if method == 'report':
            X_train, X_test, y_train, y_test, content_train, content_test = train_test_split(X, y, contents, test_size=0.33)
            clf = svm.SVC(C=10, gamma=0.1)
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            # for test, pred, content, feature in zip(y_test, y_pred, content_test, X_test):
            #     tags = jieba.analyse.extract_tags(content, topK=20, allowPOS=('ns', 'n', 'nz'))
            #     if test != pred:
                    # print(list(tags))
                    # print(feature)
                    # print('Test %d, Pred %d, Contents: %s\n' % (test, pred, content))
            print(classification_report(y_test, y_pred, target_names=['普通评论', '无效评论']))
        elif method == 'cross_validation':
            model = svm.SVC(C=10, gamma=0.1, probability=True)
            headers = ['#'] + ['K-Folder#' + str(i) for i in range(1, 11)] + ['avg']
            table = []
            for method in quantifying_methods:
                row = [method] + list(cross_validation.cross_val_score(model, X, y, cv=10, scoring=method))
                row.append(sum(row[1:])/10.)
                table.append(row)
            print(tabulate(table, headers=headers))

    def train(self):
        features = []
        marked = []
        for c in self.cols['marked'].find():
            features.append(self.gen_feature(c, output=False))
            marked.append(c['mark'])
        self.model = svm.SVC(C=10, gamma=0.1, probability=True)
        self.model.fit(features, marked)

    def predict(self, comment):
        return self.model.predict_proba([self.gen_feature(comment, output=False)])[0]

    def save(self):
        pass

    def _gen_keys(self):
        from_product = defaultdict(lambda: 0)
        for product in self.cols['product'].find().sort('_id', -1):
            for k in product.keys():
                from_product[k] += 1
        for unused in unused_words:
            del from_product[unused]
        self.keys['product'] = dict(from_product)
        for w in another_words:
            self.keys['product'][w] = 1

        top100 = {a[0]: a[1] for a in json.load(open('sorted_keys.json', mode='r', encoding='utf-8'))[:200]}
        del top100['总体']
        del top100['帮别人']
        del top100['京东']
        del top100['东西']
        del top100['发票']
        del top100['体验']
        self.keys['top'] = top100
        print(self.keys)

    def _add_words(self, words, pos='nz'):
        for w in words + list(self.keys['product'].keys()):
            jieba.add_word(w, tag=pos)

    def gen_feature(self, comment, output=False):
        comment_length = [80, 40, 15, 0]
        tags = jieba.analyse.extract_tags(comment['content'], topK=20, withWeight=True, allowPOS=('ns', 'n', 'nz'))
        if output:
            print(tags)
        comment_feature = [
            len(comment.get('commnetTags', [])),
            comment.get('imageCount', 0),
            comment.get('usefulVoteCount'),
            len(tags)
        ]

        # reply_count = comment.get('replyCount', 0)
        # if reply_count:
        #     for reply in comment.get('replies', []):
        #         if reply['userClient'] > 10:
        #             reply_count -= 1
        #
        # comment_feature.append(reply_count)

        for (i, l) in enumerate(comment_length):
            if len(comment.get('content')) > l:
                comment_feature.append(i)
                break
        else:
            comment_feature.append(3)
        product_count = 0
        top_count = 0
        for tag in tags:
            if tag[0] in self.keys['top']:
                top_count += 1
            if tag[0] in self.keys['product']:
                product_count += 1
        # print(tags, maybe)
        comment_feature.append(top_count)
        comment_feature.append(product_count)
        return comment_feature

