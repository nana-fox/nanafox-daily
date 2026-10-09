import JSZip from 'jszip';

export const formats = [
  { id: 'long', label: '长图', description: '完整日报，一张长图' },
  { id: 'wechat', label: '公众号组图', description: '封面与分类配图，插入公众号正文' },
  { id: 'xhs', label: '小红书组图', description: '3:4 封面与内容页，自动分页' },
  { id: 'json', label: 'JSON', description: '当前日报的完整结构化数据' },
];
const font = '"PingFang SC", "Microsoft YaHei", system-ui, sans-serif';
export const clean = value => String(value || '').replace(/[\p{Extended_Pictographic}\p{Regional_Indicator}\uFE0F\u200D]/gu, '').trim();
export function wrap(ctx, text, maxWidth) {
  const lines = [];
  for (const paragraph of String(text || '').split('\n')) {
    let line = '';
    const tokens = paragraph.match(/[A-Za-z0-9][A-Za-z0-9._+\/-]*|\s+|./gu) || [];
    for (const token of tokens) {
      if (ctx.measureText(token).width > maxWidth) {
        for (const char of token) {
          if (line && ctx.measureText(line + char).width > maxWidth) { lines.push(line.trimEnd()); line = char; }
          else line += char;
        }
      } else if (line && ctx.measureText(line + token).width > maxWidth) { lines.push(line.trimEnd()); line = token.trimStart(); }
      else line += token;
    }
    if (line) lines.push(line);
  }
  return lines;
}
function linesOf(ctx, text, size, weight = 400, color = 'body', space = 12) {
  ctx.font = `${weight} ${size}px ${font}`;
  const result = wrap(ctx, text, 928).map(text => ({ text, size, weight, color, height: Math.ceil(size * 1.65) }));
  if (result.length) result[result.length - 1].space = space;
  return result;
}
function sectionLines(ctx, section, settings) {
  const larger = settings.format === 'xhs';
  const lines = linesOf(ctx, clean(section.heading), larger ? 44 : 40, 650, 'accent', 24);
  if (section.note) lines.push(...linesOf(ctx, section.note, 26, 400, 'muted', 26));
  lines.forEach(line => { line.group = 'intro'; });
  section.items.forEach((item, index) => {
    const start = lines.length;
    const titleLines = linesOf(ctx, `${String(index + 1).padStart(2, '0')}  ${item.title}`, larger ? 42 : 34, 650, 'ink', 12);
    titleLines.forEach(line => { line.articleHeading = true; });
    lines.push(...titleLines);
    if (item.detail) lines.push(...linesOf(ctx, item.detail, larger ? 38 : 32, 400, 'body', 12));
    if (item.why) lines.push(...linesOf(ctx, `关注点：${item.why}`, larger ? 34 : 30, 500, 'body', 12));
    if (settings.sources && item.source) lines.push(...linesOf(ctx, `来源：${item.source}`, 23, 400, 'muted', 8));
    if (settings.sources && item.url) lines.push(...linesOf(ctx, item.url, 19, 400, 'muted', 8));
    if (settings.sources) (item.related_urls || []).forEach((url, i) => { if (url) lines.push(...linesOf(ctx, `${item.related?.[i] || '相关来源'}：${url}`, 19, 400, 'muted', 6)); });
    lines.push({ height: 28, rule: true });
    lines.slice(start).forEach(line => { line.group = `item-${index}`; });
  });
  return lines;
}
export const lineHeight = line => line.height + (line.space || 0);
export function paginate(lines, maxHeight) {
  const pages = []; let current = []; let used = 0;
  const groups = [];
  for (const line of lines) {
    if (!groups.length || groups.at(-1)[0].group !== line.group) groups.push([]);
    groups.at(-1).push(line);
  }
  const flush = () => { if (current.length) pages.push(current); current = []; used = 0; };
  for (const group of groups) {
    const height = group.reduce((sum, line) => sum + lineHeight(line), 0);
    // Keep complete articles together when they fit. Long articles repeat their
    // headline after a page break, rather than starting the next image mid-sentence.
    if (height <= maxHeight && used + height > maxHeight && current.some(line => line.group !== 'intro')) flush();
    const title = group.filter(line => line.articleHeading);
    const titleHeight = title.reduce((sum, line) => sum + lineHeight(line), 0);
    if (titleHeight > maxHeight - 160) throw new Error('单条标题过长，组图无法清晰分页，请使用长图或 JSON 导出。');
    if (height > maxHeight && used + titleHeight + 160 > maxHeight) flush();
    for (const line of group) {
      if (line.rule && used + lineHeight(line) > maxHeight) continue;
      if (used + lineHeight(line) > maxHeight && current.length) {
        flush();
        if (title.length && !line.articleHeading && !line.rule) {
          const continuation = { text: '接上页', size: 22, weight: 400, color: 'muted', height: 38, space: 8 };
          current.push(continuation, ...title); used = lineHeight(continuation) + titleHeight;
        }
      }
      current.push(line); used += lineHeight(line);
    }
  }
  if (current.length) pages.push(current);
  return pages;
}
function canvasPage({ label, lines, height, cover = false }, issue, settings, page, count) {
  const canvas = document.createElement('canvas'); canvas.width = 1080; canvas.height = height;
  const ctx = canvas.getContext('2d');
  const colors = settings.theme === 'paper'
    ? { bg: '#faf6ee', ink: '#282520', body: '#544f45', muted: '#857e70', accent: '#a46030', rule: '#ded7c9' }
    : { bg: '#ffffff', ink: '#22272d', body: '#4d5663', muted: '#83909e', accent: '#dd682c', rule: '#e7e9ec' };
  ctx.fillStyle = colors.bg; ctx.fillRect(0, 0, 1080, height);
  const text = (value, x, y, size, weight, color) => { ctx.font = `${weight} ${size}px ${font}`; ctx.fillStyle = colors[color]; ctx.textBaseline = 'top'; ctx.fillText(value, x, y); };
  text(settings.signature || 'NanaFox', 76, 48, 26, 650, 'accent');
  ctx.textAlign = 'right'; text(issue.day, 1004, 50, 24, 400, 'muted'); ctx.textAlign = 'left';
  let y = 112;
  for (const line of lines) {
    if (line.rule) { ctx.fillStyle = colors.rule; ctx.fillRect(76, y + 10, 928, 1); }
    else text(line.text, 76, y, line.size, line.weight, line.color);
    y += lineHeight(line);
  }
  const footer = height - 70;
  ctx.fillStyle = colors.rule; ctx.fillRect(76, footer - 18, 928, 1);
  text(`${issue.data.brand || 'AI 前沿日报'} · nanafox.com/daily`, 76, footer, 21, 400, 'muted');
  ctx.textAlign = 'right'; text(`${page + 1} / ${count}`, 1004, footer, 21, 400, 'muted');
  return { label, canvas, url: canvas.toDataURL('image/png'), cover };
}
export function renderPages(issue, settings, coverOnly = false) {
  if (settings.format === 'json') return [];
  const ctx = document.createElement('canvas').getContext('2d');
  const heading = linesOf(ctx, settings.title || issue.data.title, 56, 700, 'ink', 24);
  const highlights = linesOf(ctx, '今日要点', 38, 650, 'accent', 18);
  (issue.data.tldr || []).forEach((item, index) => {
    if (typeof item === 'string') highlights.push(...linesOf(ctx, `${index + 1}. ${item}`, 28, 400, 'body', 18));
    else { highlights.push(...linesOf(ctx, `${index + 1}. ${item.title}`, 32, 650, 'ink', 8)); highlights.push(...linesOf(ctx, item.text, 28, 400, 'body', 22)); }
  });
  let specs = [];
  if (settings.format === 'long') {
    const lines = [...heading, ...highlights];
    issue.data.sections.forEach(section => lines.push(...sectionLines(ctx, section, settings)));
    const height = 240 + lines.reduce((sum, line) => sum + lineHeight(line), 0);
    if (height > 30000) throw new Error('这期内容超出了单张长图的尺寸范围，请使用组图导出。');
    specs = [{ label: '完整日报', lines, height }];
  } else if (settings.format === 'wechat') {
    const coverLines = [...heading, ...linesOf(ctx, '今天的 AI 动态，按分类读清楚。', 30, 400, 'muted', 32), ...linesOf(ctx, `${issue.data.sections.length} 个栏目 · ${issue.data.sections.reduce((sum, section) => sum + section.items.length, 0)} 条动态`, 28, 500, 'accent', 0)];
    specs.push({ label: '封面', lines: coverLines, height: Math.max(608, 240 + coverLines.reduce((sum, line) => sum + lineHeight(line), 0)), cover: true });
    for (const [label, lines] of [['今日要点', highlights], ...issue.data.sections.map(section => [clean(section.heading), sectionLines(ctx, section, settings)])]) {
      paginate(lines, 1400).forEach((chunk, index) => {
        const content = index ? [...linesOf(ctx, `${label} · 续`, 36, 650, 'accent', 20), ...chunk] : chunk;
        specs.push({ label: `${label}${index ? ` ${index + 1}` : ''}`, lines: content, height: 240 + content.reduce((sum, line) => sum + lineHeight(line), 0) });
      });
    }
  } else {
    const coverLines = [...heading, ...linesOf(ctx, '今日要点', 38, 650, 'accent', 24)];
    (issue.data.tldr || []).forEach((item, i) => coverLines.push(...linesOf(ctx, `${String(i + 1).padStart(2, '0')}  ${typeof item === 'string' ? item : item.title}`, 38, 600, 'ink', 38)));
    paginate(coverLines, 1200).forEach((lines, index) => specs.push({ label: index ? '封面续页' : '封面', lines, height: 1440, cover: index === 0 }));
    paginate(highlights, 1115).forEach((lines, index) => specs.push({ label: `今日要点${index ? ` ${index + 1}` : ''}`, lines, height: 1440 }));
    for (const section of issue.data.sections) {
      const continuation = linesOf(ctx, `${clean(section.heading)} · 续`, 36, 650, 'accent', 16);
      const available = 1200 - continuation.reduce((sum, line) => sum + lineHeight(line), 0);
      if (available < 300) throw new Error('栏目标题过长，请使用长图或 JSON 导出。');
      paginate(sectionLines(ctx, section, settings), available).forEach((chunk, index) => specs.push({ label: `${clean(section.heading)}${index ? ` ${index + 1}` : ''}`, lines: index ? [...continuation, ...chunk] : chunk, height: 1440 }));
    }
  }
  const output = coverOnly ? specs.slice(0, 1) : specs;
  return output.map((spec, i) => canvasPage(spec, issue, settings, i, output.length));
}
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 60000);
}
export async function downloadPages(pages, issue, format, onlyPage) {
  if (onlyPage !== undefined || pages.length === 1) {
    const i = onlyPage ?? 0; const blob = await new Promise(resolve => pages[i].canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('图片生成失败，请重试。');
    downloadBlob(blob, `${issue.day}-${format}-${String(i + 1).padStart(2, '0')}.png`); return;
  }
  const zip = new JSZip();
  const blobs = await Promise.all(pages.map(async (page) => {
    const blob = await new Promise(resolve => page.canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('图片生成失败，请重试。');
    return blob;
  }));
  blobs.forEach((blob, index) => zip.file(`${String(index + 1).padStart(2, '0')}-${pages[index].label.replace(/[/\\:*?"<>|]/g, '')}.png`, blob));
  downloadBlob(await zip.generateAsync({ type: 'blob' }), `${issue.day}-${format}.zip`);
}
