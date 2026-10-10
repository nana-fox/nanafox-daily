import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeDigest, safeUrl } from '../src/data.js';
import { itemHTML, accentFor, mainHTML, longHTML } from '../src/bot-template.js';

test('legacy and incomplete fields remain readable without modifying original JSON', () => {
  const raw = { tldr: ['旧摘要', null], sections: [{ items: [{ summary: '旧正文', url: 'javascript:alert(1)', related_urls: ['https://example.com', 'data:text/html,bad'] }] }, {}] };
  const snapshot = JSON.stringify(raw);
  const data = normalizeDigest(raw);
  assert.equal(data.sections[0].items[0].detail, '旧正文');
  assert.equal(data.sections[0].items[0].url, '');
  assert.deepEqual(data.sections[0].items[0].related_urls, ['https://example.com/', '']);
  assert.deepEqual(data.sections[1].items, []);
  assert.equal(data.tldr.length, 1);
  assert.equal(JSON.stringify(raw), snapshot);
  assert.equal(safeUrl('javascript:alert(1)'), '');
});

test('Bot template preserves full body, insight and source with escaped text', () => {
  const item = {title:'<script>标题</script>', detail:'完整正文'.repeat(300), why:'完整看点', source:'官方来源', tag:'产品', related:['相关报道']};
  const html = itemHTML(item, 2, '#3b82f6', {sources:true});
  assert.ok(html.includes(item.detail));
  assert.ok(html.includes(item.why));
  assert.ok(html.includes(item.source));
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('background:#3b82f6'));
  const hidden = itemHTML(item, 2, '#3b82f6', {sources:false});
  assert.ok(!hidden.includes(item.source));
  assert.ok(!hidden.includes('相关报道'));
  assert.equal(accentFor({accent:'red; color:evil'}, 2),'#3b82f6');
});


test('main image retains every highlight while the long image retains all stories', () => {
  const raw = { title: 'AI 日报', tldr: Array.from({length:4}, (_,i) => ({title:`要点 ${i+1}`,text:`完整要点 ${i+1} ` + '详细说明🦊'.repeat(40)})), sections:[{heading:'新闻',items:[{title:'正文标题',summary:'独立摘要',detail:'完整正文'.repeat(300),why:'完整看点',source:'官方来源'}]}] };
  const snapshot = JSON.stringify(raw);
  const issue = {day:'2026-10-09',data:normalizeDigest(raw)};
  const settings = {signature:'NanaFox',sources:true};
  const main = mainHTML(issue,settings), long = longHTML(issue,settings);
  for (const row of raw.tldr) { assert.ok(main.includes(row.title)); assert.ok(main.includes(row.text)); assert.ok(long.includes(row.text)); }
  assert.ok(!main.includes('正文标题'));
  for (const field of ['title','summary','detail','why','source']) assert.ok(long.includes(raw.sections[0].items[0][field]));
  assert.equal(JSON.stringify(raw),snapshot);
  assert.ok(mainHTML({...issue,data:{...issue.data,tldr:[]}},settings).includes('今日暂无要点'));
});


test('export omits visible addresses while keeping dates, stories, source names and original JSON', () => {
  const raw = { title:'AI 日报', date:'2026-10-10 周六',
    tldr:[{title:'今日要点',text:'重要事实 https://example.com/story 继续正文'}],
    sections:[{heading:'新闻',items:[{title:'独立标题',detail:'完整正文 www.example.org/report 后续事实',why:'完整看点',source:'官方机构 https://example.com',related:['相关机构 example.cn/reference'],url:'https://example.com/story'}]}] };
  const original = JSON.stringify(raw);
  const issue = {day:'2026-10-10',data:normalizeDigest(raw)};
  const settings = {signature:'NanaFox',sources:true};
  const main = mainHTML(issue,settings), long = longHTML(issue,settings);
  for (const html of [main,long]) {
    assert.ok(html.includes(raw.date));
    assert.ok(html.includes('重要事实'));
    assert.ok(html.includes('继续正文'));
    assert.ok(!/https?:|www\.|example\.|nanafox\.com|原文链接/.test(html));
    assert.ok(!/<a\b|href=/.test(html));
  }
  for (const text of ['独立标题','完整正文','后续事实','完整看点','官方机构','相关机构']) assert.ok(long.includes(text));
  assert.equal(JSON.stringify(raw),original);
  assert.equal(issue.data.sections[0].items[0].url,raw.sections[0].items[0].url);
});
