from flask import Flask, request, Response
from flask import jsonify
from flask.ext.cors import CORS, cross_origin
from models.mongo import Mongo

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False
db = Mongo()


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


@app.route('/results')
def results():
    pass


@app.route('/marked')
@cross_origin()
def get_marked():
    return jsonify(contents=list(map(convert_contents, db.get_marked())))


def convert_contents(c):
    c['_id'] = str(c['_id'])
    return c


if __name__ == "__main__":
    app.run(debug=True)
