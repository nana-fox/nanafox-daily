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
export const footerHTML = (issue,settings,page,count) => `<div class="page-footer"><span>${esc(settings.signature || issue.data.brand || 'AI 前沿日报')} · nanafox.com/daily</span><span>${page+1} / ${count}</span></div>`;
export function longHTML(issue,settings) {
  return `${headerHTML(issue,settings)}${highlightsHTML(issue)}<div class="body">${issue.data.sections.map((section,index) => {
    const color=accentFor(section,index);
    return `<div class="section">${sectionHeadHTML({...section,color})}${section.style==='bullets' ? '<div class="bullets">'+section.items.map((item,i)=>itemHTML(item,i+1,color,settings,false,true).replace(/^<div class="bullets">|<\/div>$/g,'')).join('')+'</div>' : section.items.map((item,i)=>itemHTML(item,i+1,color,settings)).join('')}</div>`;
  }).join('')}</div><div class="footer"><span>原文链接见日报网站</span><span>${esc(settings.signature || issue.data.brand)}</span></div>`;
}
// Whole cards stay together. Oversized cards are split before calling this helper.
export function packCards(cards, available, gap = 18) {
  const pages=[]; let page=[]; let used=0;
  for (const card of cards) {
    if (card.height > available) throw new Error('单条内容无法放入组图，请使用长图或 JSON 导出。');
    const next=card.height+(page.length ? gap : 0);
    if (used+next > available && page.length) { pages.push(page); page=[]; used=0; }
    used+=card.height+(page.length ? gap : 0); page.push(card);
  }
  if (page.length) pages.push(page);
  return pages;
}

// A single very long story repeats its heading, but never loses any body text.
export function splitOversized(item,number,accent,settings,bullets,available,measure) {
  const fields=['summary','detail','why'];
  const remaining={...item,summary:item.summary===item.detail ? '' : item.summary};
  const output=[]; let continued=false;
  if (!fields.some(field=>remaining[field])) throw new Error('单条标题或来源过长，请使用长图或 JSON 导出。');
  while (fields.some(field=>remaining[field])) {
    // Reserve the source block during fitting so it stays with the final body fragment.
    const part={...item,summary:'',detail:'',why:''};
    let progress=false;
    for (const field of fields) {
      const value=remaining[field] || '';
      if (!value) continue;
      const chars=Array.from(value); let low=0,high=chars.length;
      while (low<high) {
        const mid=Math.ceil((low+high)/2);part[field]=chars.slice(0,mid).join('');
        if (measure(itemHTML(part,number,accent,settings,continued,bullets))<=available) low=mid; else high=mid-1;
      }
      part[field]=chars.slice(0,low).join('');remaining[field]=chars.slice(low).join('');progress ||= low>0;
      if (low<chars.length) break;
    }
    if (!progress) throw new Error('单条标题或来源过长，无法清晰分页，请使用长图或 JSON 导出。');
    part.source='';part.related=[];part.related_urls=[];
    output.push(part);continued=true;
  }
  // Sources and related labels are kept in a trailing card if they do not fit.
  const last=output.at(-1);
  if (last) { last.source=item.source;last.related=item.related;last.related_urls=item.related_urls; }
  if (last && measure(itemHTML(last,number,accent,settings,output.length>1,bullets))>available) {
    last.source='';last.related=[];last.related_urls=[];
    output.push({...item,summary:'',detail:'',why:''});
  }
  return output.map((part,index)=>{
    const html=itemHTML(part,number,accent,settings,index>0,bullets);const height=measure(html);
    if (height>available) throw new Error('单条标题或来源过长，请使用长图或 JSON 导出。');
    return {html,height};
  });
}
