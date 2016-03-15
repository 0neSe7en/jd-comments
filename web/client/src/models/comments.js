const m = require('mithril');
const host = 'http://localhost:5000/';

const xhrConfig = function(xhr) {
	xhr.setRequestHeader('Access-Control-Allow-Origin', '*');
};

let comments = module.exports = {};

comments.sample = function() {
	return m.request({
		url: host + 'sample',
		method: 'GET',
		config: xhrConfig
	})
};

comments.train = function(trained) {
	return m.request({
		url: host + 'sample',
		method: 'POST',
		data: trained,
		config: xhrConfig
	})
};

comments.marked = function() {
	return m.request({
		url: host + 'marked',
		method: 'GET',
		config: xhrConfig
	})
};

comments.deleteMark = function(_id) {
	return m.request({
		url: host + 'marked/' + _id,
		method: 'DELETE',
		config:xhrConfig
	})
};
