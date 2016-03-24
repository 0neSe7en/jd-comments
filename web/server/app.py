from flask import Flask, request, Response
from flask import jsonify
from flask.ext.cors import CORS, cross_origin
from models.mongo import Mongo
from learn.model.model import CommentModel
from spider.product_comment import Spider

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False
db = Mongo()
spider = Spider()


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
