const m = require('mithril');

m.route.mode = 'hash';
m.route(document.getElementById('mainContent'), '/train', {
	'/train': require('./src/components/train.js'),
	'/marked': require('./src/components/marked.js'),
	'/show': require('./src/components/show.js')
});

