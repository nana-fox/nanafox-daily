import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeDigest, safeUrl } from '../src/data.js';
import { packCards, itemHTML, accentFor, splitOversized } from '../src/bot-template.js';

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

test('whole cards paginate in order without dropped or split entries', () => {
  const cards = [420, 310, 510, 190, 150].map((height, id) => ({ height, id }));
  const pages = packCards(cards, 850, 18);
  assert.deepEqual(pages.flat(), cards);
  for (const page of pages) assert.ok(page.reduce((sum, card) => sum + card.height, 0) + (page.length - 1) * 18 <= 850);
  assert.throws(() => packCards([{ height: 900 }], 850), /单条内容/);
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


test('oversized stories preserve every field and keep sources on the final continuation', () => {
  const item={title:'一个长标题',summary:'摘要！'.repeat(17),detail:'正文🦊。'.repeat(100),why:'看点？'.repeat(26),source:'官方',related:['相关一','相关二']};
  const measure=html=>Array.from(html.replace(/<[^>]*>/g,'')).length;
  for(const bullets of [false,true]) {
    const parts=splitOversized(item,1,'#3b82f6',{sources:true},bullets,130,measure);
    assert.ok(parts.length>1);
    const joined=parts.map(part=>part.html.replace(/<[^>]*>/g,'')).join('').replace(/一个长标题| · 接上页|💡 看点|🔗 另见|相关一 · 相关二|官方|1/g,'');
    for(const field of ['summary','detail','why']) {
      const chars=Array.from(item[field]);
      // Remove each field's unique alphabet and verify the total is retained even across pages.
      for(const char of new Set(chars)) assert.equal(Array.from(joined).filter(x=>x===char).length,chars.filter(x=>x===char).length);
    }
    assert.equal(parts.filter(part=>part.html.includes('官方')).length,1);
    assert.ok(parts.at(-1).html.includes('相关二'));
    assert.ok(parts.every(part=>part.height<=130));
  }
  assert.throws(()=>splitOversized({title:'过长标题'},1,'#3b82f6',{sources:true},false,1,measure),/标题/);
});
