'use strict';

var re = /(http:\/\/club.jd.com\/productpage\/p-.+?.html)/;
var current_comment = null;
var already = false;

function genDom(text) {
	var template = '<div><a href="javascript:;">' + text + '</div>';
	return $(template);
}

function addHref() {
	var doms = document.querySelectorAll('.column.column3');
	console.log('add...');
	for (var i = 0; i < doms.length; i++ ) {
		var d1 = genDom('这是无效评论');
		d1.click(function(i) {
			$.ajax({
				type: 'POST',
				url: 'http://localhost:5000/plugin/marked',
				data: JSON.stringify({
					url: current_comment,
					pos: i,
					type: 1
				}),
				dataType: 'json',
				contentType: 'application/json;charset=utf-8'
			}).done(function(data) {
				console.log(data);
			})
		}.bind(null, i));
		var d2 = genDom('这是有价值的评论');
		d2.click(function(i) {
			console.log('click on 有效评论', i)
		}.bind(null, i));
		$(doms[i]).append(d1).append(d2);
	}
}

if (window.location.host === 'item.jd.com') {
	console.log('Call ');
	document.head.addEventListener('DOMSubtreeModified', function(e) {
		var dom = e.target;
		$(dom).children('script').each(function(index, dom) {
			var url = re.exec(dom.src);
			if (url && url.length == 2) {
				if (current_comment !== url[1]) {
					current_comment = url[1];
					already = false;
				}
				if (!already) {
					already = true;
					setTimeout(addHref, 1500)
				}
			}
		});
	});
}
