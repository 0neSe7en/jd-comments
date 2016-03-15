const m = require('mithril');
const _ = require('lodash');
const commentModel = require('../models/comments.js');
module.exports = {
	controller() {
		this.comments = commentModel.marked();
	},
	view(ctrl) {
		console.log('render...');
		function generateTable(type) {
			let filter_key = type === '无用评论' ? 1 : 0;
			let comments_td = _(ctrl.comments().contents).filter((c) => c.mark === filter_key).map((c) => {
				return m('tr', [
					m('td.mdl-data-table__cell--non-numeric', {style: {'max-width': '60px'}}, c.userLevelName),
					m('td', {style: {'max-width': '60px'}}, c.usefulVoteCount),
					m('td', {style: {'max-width': '60px'}}, c.uselessVoteCount),
					m('td.mdl-data-table__cell--non-numeric.td-wrap', {style: {'max-width': '200px'}}, c.referenceName.slice(0, 20)),
					m('td.mdl-data-table__cell--non-numeric.td-wrap', {style: {'max-width': '500px'}}, c.content),
					m('td.mdl-data-table__cell--non-numeric', c._id)
				])
			});
			return m('table.mdl-data-table.mdl-js-data-table.mdl-shadow--2dp.mdl-cell--12-col', {config: (ele, inited) => {if (!inited) new MaterialDataTable(ele)}}, [
				m('thead', m('tr', [
					m('th.mdl-data-table__cell--non-numeric', {style: {'max-width': '60px'}}, '用户等级'),
					m('th', {style: {'max-width': '60px'}}, '有用评价'),
					m('th', {style: {'max-width': '60px'}}, '无用评价'),
					m('th.mdl-data-table__cell--non-numeric', '产品名'),
					m('th.mdl-data-table__cell--non-numeric', '评论内容'),
					m('th.mdl-data-table__cell--non-numeric', 'id')
				])),
				m('tbody', comments_td.valueOf())
			])
		}

		return m('.mdl-grid', [
			m('.mdl-tabs.mdl-js-tabs.mdl-js-ripple-effect.mdl-cell--12-col', {config: (ele, inited) => {if (!inited) new MaterialTabs(ele)}}, [
				m('.mdl-tabs__tab-bar', [
					m('a.mdl-tabs__tab.is-active[href="#spam"]', '无用评论'),
					m('a.mdl-tabs__tab[href="#normal"]', '普通评论')
				]),
				m('.mdl-tabs__panel.is-active#spam', generateTable('无用评论')),
				m('.mdl-tabs__panel#normal', generateTable('普通评论'))
			])
		])
	}
};