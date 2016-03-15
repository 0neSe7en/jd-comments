const m = require('mithril');
const _ = require('lodash');
const commentModel = require('../models/comments.js');
module.exports = {
	controller() {
		var self = this;
		self.comments = m.prop([]);
		self.selectData = m.prop({});
		self.comments = m.prop([]);
		self.dataTable = m.prop({});
		self.selectAll = (v) => {
			_.forEach(self.selectData(), (value) => {
				if (v) {
					value.dom.check();
				} else {
					value.dom.uncheck();
				}
			});
		};

		self.save = () => {
			commentModel.train(_.reduce(self.selectData(), (results, v, cid) => {
				results[cid] = v.checked();
				return results;
			}, {})).then(function() {
				m.redraw.strategy('all');
				return init()
			})
		};

		init();

		function init() {
			return commentModel.sample().then((comments) => {
				self.comments(comments);
				self.selectData(_.reduce(comments.contents, (results, comment) => {
					results[comment._id] = {
						checked: m.prop(false),
						dom: null
					};
					return results;
				}, {}));
			})
		}
	},
	view(ctrl) {
		return m('.mdl-grid', [
			m('button.mdl-button.mdl-js-button.mdl-button--raised.mdl-js-ripple-effect.mdl-button--accent.float-button', {onclick: ctrl.save}, '保存'),
			m('table.mdl-data-table.mdl-js-data-table.mdl-shadow--2dp.mdl-cell--12-col', { config: newDataTable },
				[
					m('thead', m('tr', [
						m('th',
							m('label.mdl-checkbox.mdl-js-checkbox.mdl-js-ripple-effect.mdl-data-table__select[for="table-header"]',
								{config: newCheckbox},
								m('input.mdl-checkbox__input#table-header[type="checkbox"]', {onclick: m.withAttr('checked', ctrl.selectAll)})
							)
						),
						m('th.mdl-data-table__cell--non-numeric', {style: {'max-width': '60px'}}, '用户等级'),
						m('th', {style: {'max-width': '60px'}}, '有用评价'),
						m('th', {style: {'max-width': '60px'}}, '无用评价'),
						m('th.mdl-data-table__cell--non-numeric', '产品名'),
						m('th.mdl-data-table__cell--non-numeric', '标签'),
						m('th', {style: {'max-width': '60px'}}, '图片数量'),
						m('th.mdl-data-table__cell--non-numeric', '评论内容'),
						m('th', {style: {'max-width': '60px'}}, '评论长度'),
						m('th.mdl-data-table__cell--non-numeric', 'id')
					])),
					m('tbody', ctrl.comments().contents.map(comment => {
						return m('tr', [
							m('td',
								m('label.mdl-checkbox.mdl-js-checkbox.mdl-js-ripple-effect.mdl-data-table__select',
									{for: comment._id, config: newCheckbox},
									m('input.mdl-checkbox__input[type="checkbox"]', {
										id: comment._id,
										onclick: m.withAttr('checked', ctrl.selectData()[comment._id].checked)
									})
								)
							),
							m('td.mdl-data-table__cell--non-numeric', {style: {'max-width': '60px'}}, comment.userLevelName),
							m('td', {style: {'max-width': '60px'}}, comment.usefulVoteCount),
							m('td', {style: {'max-width': '60px'}}, comment.uselessVoteCount),
							m('td.mdl-data-table__cell--non-numeric.td-wrap', {style: {'max-width': '200px'}}, comment.referenceName.slice(0, 20)),
							m('td.mdl-data-table__cell--non-numeric.td-wrap', {style: {'max-width': '100px'}}, comment.commentTags ? comment.commentTags.join(', ') : ''),
							m('td', {style: {'max-width': '60px'}}, comment.imageCount || 0),
							m('td.mdl-data-table__cell--non-numeric.td-wrap', {style: {'max-width': '500px'}}, comment.content),
							m('td', {style: {'max-width': '60px'}}, comment.content.length),
							m('td.mdl-data-table__cell--non-numeric', comment._id)
						])
					}))
				])]
		);


		function newDataTable(ele, inited) {
			if (!inited) {
				new MaterialDataTable(ele);
			}
		}

		function newCheckbox(ele, inited) {
			if (!inited) {
				let comment = ctrl.selectData()[ele.getAttribute('for')];
				if (comment) {
					comment.dom = new MaterialCheckbox(ele);
				} else {
					new MaterialCheckbox(ele);
				}
			}
		}

	}
};


