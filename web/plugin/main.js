'use strict';

var re = /(http:\/\/sclub.jd.com\/productpage\/p-.+?.html)/;
var current_comment = null;
var already = false;

function genDom(text) {
	var template = '<div><a href="javascript:;">' + text + '</div>';
	return $(template);
}

function addHref() {
	var doms = document.querySelectorAll('.column.column3');
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
				if (data && data.msg === 'success') {
					$($('.comments-item')[i]).hide('fast');
				}
			})
		}.bind(d1, i));
		var d2 = genDom('这是有价值的评论');
		d2.click(function(i) {
			$.ajax({
				type: 'POST',
				url: 'http://localhost:5000/plugin/marked',
				data: JSON.stringify({url: current_comment, pos: i, type: 0}),
				dataType: 'json',
				contentType: 'application/json;charset=utf-8'
			}).done(function(data) {
				console.log(data)
			})
		}.bind(null, i));
		$(doms[i]).append(d1).append(d2);
	}
}

function getPredict() {
	$.ajax({
		type: 'POST',
		url: 'http://localhost:5000/plugin/init',
		data: JSON.stringify({
			url: current_comment
		}),
		dataType: 'json',
		contentType: 'application/json;charset=utf-8'
	}).done(function(data) {
		var comments = document.querySelectorAll('.comments-item');
		for (var i = 0; i < comments.length; i++) {
			if (data.results[i]) {
				$(comments[i]).css('opacity', 0.5)
			}
		}
	})
}

if (window.location.host === 'item.jd.com' || window.location.host === 'sclub.jd.com') {
	document.head.addEventListener('DOMSubtreeModified', function(e) {
		var dom = e.target;
		$(dom).children('script').each(function(index, dom) {
			var url = re.exec(dom.src);
			if (url && url.length == 2) {
				if (current_comment !== url[1]) {
					current_comment = url[1];
					already = false;
					getPredict();
				}
				if (!already) {
					already = true;
					setTimeout(addHref, 1500)
				}
			}
		});
	});
}

