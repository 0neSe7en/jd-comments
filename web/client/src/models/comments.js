const m = require('mithril');

const xhrConfig = function(xhr) {
	xhr.setRequestHeader('Access-Control-Allow-Origin', '*');
};

let comments = module.exports = {};

comments.sample = function() {
	return m.request({
		url: 'http://localhost:5000/sample',
		method: 'GET',
		config: xhrConfig
	})
};

comments.train = function(trained) {
	return m.request({
		url: 'http://localhost:5000/sample',
		method: 'POST',
		data: trained,
		config: xhrConfig
	})
};

comments.marked = function() {
	return m.request({
		url: 'http://localhost:5000/marked',
		method: 'GET',
		config: xhrConfig
	})
};
