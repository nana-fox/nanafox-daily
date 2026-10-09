import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeDigest, safeUrl } from '../src/data.js';
import { paginate, lineHeight } from '../src/export.js';

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

test('long article pagination preserves body lines and image height limits', () => {
  const lines = [{ text: '标题', group: 'item-0', articleHeading: true, height: 65, size: 40 }, ...Array.from({ length: 40 }, (_, i) => ({ text: `正文 ${i}`, group: 'item-0', height: 70, size: 38 }))];
  const pages = paginate(lines, 600);
  assert.ok(pages.length > 1);
  assert.deepEqual(pages.flat().filter(line => line.text.startsWith('正文')).map(line => line.text), lines.slice(1).map(line => line.text));
  for (const page of pages) {
    assert.ok(page.reduce((sum, line) => sum + lineHeight(line), 0) <= 600);
    assert.ok(page.some(line => line.articleHeading));
    assert.ok(page.some(line => line.text.startsWith('正文')));
  }
});

test('unrenderable headlines give an explicit alternative instead of overflowing', () => {
  assert.throws(() => paginate(Array.from({ length: 12 }, () => ({ text: '很长的标题', articleHeading: true, group: 'item-0', height: 80 })), 600), /标题过长/);
});
