from flask import Flask, request, Response
from flask import jsonify
from flask.ext.cors import CORS, cross_origin
from models.mongo import Mongo
from learn.model.model import CommentModel
from spider.product_comment import Spider
from learn.model import model

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False
spider = Spider()
db = Mongo()
trained_model = model.CommentModel({
    'product': db.product,
    'comment': db.comment,
    'marked': db.marked,
    'user': db.user,
    'tag': db.tag
})
trained_model.init(to_train=False)
trained_model.from_redis()
db.init_model(trained_model)


@app.route('/')
@cross_origin()
def hello():
    return jsonify({'msg': 'Hello World'})


@app.route('/sample', methods=['GET', 'POST'])
@cross_origin()
def sample():
    if request.method == 'GET':
        sample_comments = map(convert_contents, db.sample())
        return jsonify(contents=list(sample_comments))
    elif request.method == 'POST':
        db.save(request.get_json())
        return jsonify({'msg': 'success'})


@app.route('/plugin/marked', methods=['POST'])
@cross_origin()
def plugin_marked():
    user_marked = request.get_json()
    url = user_marked['url']
    comment_ids = spider.fetch_single(url)
    single_marked = {str(comment_ids[user_marked['pos']]): user_marked['type']}
    db.save(single_marked)
    return jsonify({'msg': 'success'})


@app.route('/plugin/init', methods=['POST'])
@cross_origin()
def plugin_init():
    user_marked = request.get_json()
    url = user_marked['url']
    comment_ids = spider.fetch_single(url)
    predict_results = [db.predict(single) for single in comment_ids]
    if predict_results[0] is None:
        return jsonify({
            'msg': 'no model'
        })
    return jsonify({
        'msg': 'success',
        'results': [1 if prob[1] > 0.6 else 0 for prob in predict_results]
    })


@app.route('/results')
def results():
    pass


@app.route('/marked', methods=['GET'])
@cross_origin()
def get_marked():
    return jsonify(contents=list(map(convert_contents, db.get_marked())))


@app.route('/marked/<mark_id>', methods=['DELETE'])
@cross_origin()
def delete_marked(mark_id):
    db.delete_marked(mark_id)
    return jsonify({'msg': 'success'})


def convert_contents(c):
    c['_id'] = str(c['_id'])
    return c


if __name__ == "__main__":
    print('app start...')
    app.run(debug=True)
