// HTML port of Grok Bot's render.py. No image pixels or pre-generated PNG input.
export const SECTION_ACCENTS = ['#f97316','#10b981','#3b82f6','#8b5cf6','#0ea5e9','#ef4444','#ec4899'];
const TAG_COLORS = {'模型发布':['#ede9fe','#6d28d9'],'产品':['#dbeafe','#1d4ed8'],'研究':['#dcfce7','#15803d'],'论文':['#d1fae5','#047857'],'文章':['#fef3c7','#b45309'],'观点':['#ffe4e6','#be123c'],'工程':['#e0f2fe','#0369a1'],'开源':['#fce7f3','#be185d'],'融资':['#f1f5f9','#334155'],'Agent':['#d1fae5','#047857'],'政策':['#fee2e2','#b91c1c'],'市场':['#e0e7ff','#4338ca'],'标准':['#ccfbf1','#0f766e'],'芯片':['#fef9c3','#a16207']};
export const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
export const accentFor = (section, index) => /^#[\da-f]{6}$/i.test(section.accent || '') ? section.accent : SECTION_ACCENTS[index % 7];
const tint = hex => `rgba(${[1,3,5].map(start => parseInt(hex.slice(start,start+2),16)).join(',')},0.09)`;
export function itemHTML(item, number, accent, settings, continued = false, bullets = false) {
  const [bg,fg] = TAG_COLORS[item.tag] || ['#f1f5f9','#475569'];
  const tag = item.tag ? `<span class="tag" style="background:${bg};color:${fg}">${esc(item.tag)}</span>` : '';
  const source = settings.sources && item.source ? `<span class="source inline">${esc(item.source)}</span>` : '';
  const related = settings.sources && item.related?.length ? `<div class="related"><span class="rl">🔗 另见</span>${item.related.map(esc).join(' · ')}</div>` : '';
  const summary = item.summary && item.summary !== item.detail ? `<div class="summary">${esc(item.summary)}</div>` : '';
  const detail = item.detail ? `<div class="detail">${esc(item.detail)} ${source}</div>` : source;
  const why = item.why ? `<div class="why" style="background:${tint(accent)};color:#1e293b"><span class="label" style="color:${accent}">💡 看点</span><span>${esc(item.why)}</span></div>` : '';
  const continuation = continued ? '<span class="continuation"> · 接上页</span>' : '';
  if (bullets) return `<div class="bullets"><div class="bullet"><span class="dot" style="background:${accent}"></span><div class="txt"><span class="bt">${esc(item.title)}${continuation}</span>${summary && item.detail ? summary : ''}${esc(item.detail || item.summary)}${source}${why}${related}</div></div></div>`;
  return `<div class="item"><div class="idx" style="background:${accent}">${number}</div><div class="content"><div class="row1"><div class="title">${esc(item.title)}${continuation}</div>${tag}</div>${summary}${detail}${why}${related}</div></div>`;
}
export function sectionHeadHTML(section, continuation = false) {
  return `<h2><span class="bar" style="background:${section.color}"></span>${esc(section.heading)}${continuation ? ' · 续' : ''}<span class="count">${section.items.length} 条</span></h2>${section.note ? `<div class="sec-note">${esc(section.note)}</div>` : ''}`;
}
export function highlightsHTML(issue, rows = issue.data.tldr) {
  if (!rows.length) return '';
  return `<div class="tldr"><div class="th">${esc(issue.data.tldr_heading || '⚡ 今日要点')}</div>${rows.map((item,index) => `<div class="tl"><span class="tn">${index+1}</span><div class="tt">${typeof item === 'string' ? esc(item) : `<b>${esc(item.title)}</b>　${esc(item.text)}`}</div></div>`).join('')}</div>`;
}
export function headerHTML(issue, settings) {
  return `<div class="header"><div class="grid-deco"></div><div class="eyebrow">${esc(issue.data.eyebrow || 'DAILY AI BRIEFING')}</div><h1>${esc(settings.title || issue.data.title)}</h1><div class="meta"><span class="pill date">${esc(issue.data.date || issue.day)}</span><span class="signature">${esc(settings.signature)}</span></div></div>`;
}
export function longHTML(issue,settings) {
  return `${headerHTML(issue,settings)}${highlightsHTML(issue)}<div class="body">${issue.data.sections.map((section,index) => {
    const color=accentFor(section,index);
    return `<div class="section">${sectionHeadHTML({...section,color})}${section.style==='bullets' ? '<div class="bullets">'+section.items.map((item,i)=>itemHTML(item,i+1,color,settings,false,true).replace(/^<div class="bullets">|<\/div>$/g,'')).join('')+'</div>' : section.items.map((item,i)=>itemHTML(item,i+1,color,settings)).join('')}</div>`;
  }).join('')}</div><div class="footer"><span>原文链接见日报网站</span><span>${esc(settings.signature || issue.data.brand)}</span></div>`;
}

export function mainHTML(issue, settings) {
  return `${headerHTML(issue, settings)}${highlightsHTML(issue).replaceAll('</b>　', '</b>') || '<div class="tldr"><div class="th">今日要点</div><div class="tt">今日暂无要点</div></div>'}<div class="footer"><span>每日 AI 动态 · nanafox.com/daily</span><span>${esc(settings.signature || issue.data.brand)}</span></div>`;
}
