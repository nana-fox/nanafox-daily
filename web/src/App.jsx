import { useEffect, useMemo, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ArrowSquareOut, CalendarBlank, CaretLeft, CaretRight, Check, DownloadSimple, FileCode, FileImage, Images, List, X } from '@phosphor-icons/react';
import { normalizeDigest } from './data.js';
import { clean, formats, renderPages, downloadBlob, downloadPages } from './export';

const defaults = { format: 'long', theme: 'white', signature: 'NanaFox', sources: true };
function loadSettings() { try { const saved = JSON.parse(localStorage.getItem('daily-export-v1')); return { ...defaults, signature: typeof saved?.signature === 'string' ? saved.signature.slice(0, 32) : defaults.signature, sources: typeof saved?.sources === 'boolean' ? saved.sources : true, theme: saved?.theme === 'paper' ? 'paper' : 'white', format: formats.some(f => f.id === saved?.format) ? saved.format : 'long' }; } catch { return defaults; } }
const shortDate = day => `${day.slice(5, 7)} 月 ${day.slice(8)} 日`;

function ExportDialog({ issue, open, setOpen, settings, setSettings }) {
  const [page, setPage] = useState(0); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState('');
  const [title, setTitle] = useState(issue.data.title);
  useEffect(() => { setTitle(issue.data.title); setNotice(''); }, [issue]);
  const result = useMemo(() => {
    if (!open) return { pages: [], error: '' };
    try { return { pages: renderPages(issue, { ...settings, title }), error: '' }; } catch (error) { return { pages: [], error: error.message }; }
  }, [open, issue, settings, title]);
  const { pages, error } = result;
  useEffect(() => () => { pages.forEach(page => { page.canvas.width = 0; page.canvas.height = 0; }); }, [pages]);
  const templatePreviews = useMemo(() => {
    if (!open) return {};
    const coverIssue = { ...issue, data: { ...issue.data, sections: [] } };
    return Object.fromEntries(['white', 'paper'].map(theme => {
      const page = renderPages(coverIssue, { ...settings, format: 'xhs', theme, title }, true)[0];
      const url = page?.url;
      if (page) { page.canvas.width = 0; page.canvas.height = 0; }
      return [theme, url];
    }));
  }, [open, issue, title, settings.signature]);
  useEffect(() => { setPage(0); setNotice(''); }, [issue, settings, title]);
  const current = pages[Math.min(page, pages.length - 1)];
  const set = patch => setSettings(value => ({ ...value, ...patch }));
  async function save(single = false) {
    setBusy(true); setNotice('');
    try {
      if (settings.format === 'json') downloadBlob(new Blob([JSON.stringify(issue.raw, null, 2)], { type: 'application/json;charset=utf-8' }), `${issue.day}.json`);
      else await downloadPages(pages, issue, settings.format, single ? page : undefined);
      setNotice('文件已生成，下载已开始。');
    } catch (error) { setNotice(error.message); } finally { setBusy(false); }
  }
  const isJson = settings.format === 'json';
  return <Dialog.Root open={open} onOpenChange={setOpen}><Dialog.Portal><Dialog.Overlay className="overlay" /><Dialog.Content className="export-dialog">
    <header className="dialog-head"><div><Dialog.Title>导出当前日报</Dialog.Title><Dialog.Description>{issue.data.title} <span>·</span> {issue.day}</Dialog.Description></div><Dialog.Close asChild><button className="icon-button" aria-label="关闭导出"><X size={20} /></button></Dialog.Close></header>
    <div className="export-types" aria-label="导出类型">{formats.map((format, i) => { const Icon = [FileImage, Images, Images, FileCode][i]; return <button key={format.id} className={settings.format === format.id ? 'selected' : ''} aria-pressed={settings.format === format.id} onClick={() => set({ format: format.id })}><Icon size={18} />{format.label}</button>; })}</div>
    {isJson ? <div className="json-panel"><div className="json-caption"><FileCode size={22} /><div><strong>完整结构化数据</strong><p>保留当前日报的标题、要点、正文和来源字段。</p></div></div><pre>{JSON.stringify(issue.raw, null, 2)}</pre></div> : <div className="export-body"><aside className="export-settings">
      <label className="field-title">样式模板</label><div className="template-options">{[['white', '清爽白底'], ['paper', '暖色纸张']].map(([theme, label]) => <button key={theme} className={`template-option ${settings.theme === theme ? 'selected' : ''}`} onClick={() => set({ theme })} aria-pressed={settings.theme === theme}><span className={`template-sample ${theme}`}><img src={templatePreviews[theme]} alt={`${label}模板封面预览`} /></span><span className="template-label">{label}{settings.theme === theme && <Check size={14} weight="bold" />}</span></button>)}</div>
      <label className="field-title" htmlFor="export-title">图片标题</label><input id="export-title" value={title} maxLength={48} onChange={event => setTitle(event.target.value)} />
      <label className="field-title" htmlFor="signature">署名</label><input id="signature" value={settings.signature} maxLength={32} onChange={event => set({ signature: event.target.value })} />
      <label className="toggle-row"><span>显示来源</span><input type="checkbox" checked={settings.sources} onChange={event => set({ sources: event.target.checked })} /><span className="switch" aria-hidden="true" /></label>
      <div className="format-note"><strong>{formats.find(f => f.id === settings.format).description}</strong><p>{settings.format === 'wechat' ? '按分类拆图，内容较多时继续分页，方便插入公众号正文。' : settings.format === 'xhs' ? '1080 × 1440，封面与内容页按阅读顺序打包。' : '1080 像素宽，图片高度随完整内容自动延伸。'}</p><span>使用当前日报完整内容</span></div>
    </aside><section className="preview-area"><div className="preview-heading"><strong>{formats.find(f => f.id === settings.format).label}预览</strong><span>{pages.length ? `${pages.length} 张图片` : ''}</span></div>
      {error ? <div className="error-state" role="alert">{error}</div> : current && <><div className={`preview-stage ${settings.format === 'long' ? 'long-preview' : ''}`}><img src={current.url} alt={`${current.label}，第 ${page + 1} 张导出图片`} /></div><div className="pagination"><button className="icon-button" aria-label="上一张图片" disabled={page === 0} onClick={() => setPage(value => value - 1)}><CaretLeft size={16} /></button><span>{current.label} <b>{page + 1} / {pages.length}</b></span><button className="icon-button" aria-label="下一张图片" disabled={page === pages.length - 1} onClick={() => setPage(value => value + 1)}><CaretRight size={16} /></button></div>{pages.length > 1 && <div className="page-thumbnails">{pages.map((item, i) => <button key={i} className={page === i ? 'selected' : ''} aria-label={`预览第 ${i + 1} 张：${item.label}`} aria-pressed={page === i} onClick={() => setPage(i)}><img src={item.url} alt="" /><span>{i + 1}</span></button>)}</div>}</>}
    </section></div>}
    <footer className="dialog-footer"><span className="download-notice" role="status">{notice || (isJson ? 'JSON 直接下载，无需图片设置' : pages.length > 1 ? '组图将按页码顺序打包为 ZIP' : '下载 PNG 图片')}</span><div>{!isJson && pages.length > 1 && <button className="button secondary" disabled={busy || !!error} onClick={() => save(true)}>下载当前图片</button>}<button className="button primary" disabled={busy || (!isJson && !pages.length)} onClick={() => save()}><DownloadSimple size={17} />{busy ? '正在生成…' : isJson ? '下载 JSON' : pages.length > 1 ? '下载全部组图' : '下载长图'}</button></div></footer>
  </Dialog.Content></Dialog.Portal></Dialog.Root>;
}

export function App({ bootstrap }) {
  const { issues, base, view } = bootstrap;
  const day = bootstrap.day;
  const issue = useMemo(() => bootstrap.data ? { day, raw: bootstrap.data, data: normalizeDigest(bootstrap.data) } : null, [bootstrap, day]);
  const [open, setOpen] = useState(false); const [historyOpen, setHistoryOpen] = useState(false); const [active, setActive] = useState('all');
  const [settings, setSettings] = useState(loadSettings);
  useEffect(() => { try { localStorage.setItem('daily-export-v1', JSON.stringify(settings)); } catch { /* Downloads still work when storage is unavailable. */ } }, [settings]);
  useEffect(() => {
    if (!historyOpen) return;
    const onKey = event => {
      if (event.key === 'Escape') { setHistoryOpen(false); document.getElementById('history-toggle')?.focus(); }
      if (event.key === 'Tab') {
        const controls = [...document.querySelectorAll('.history-sidebar button, .history-sidebar a')];
        const first = controls[0], last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.querySelector('.history-sidebar button')?.focus();
    window.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = previous; window.removeEventListener('keydown', onKey); document.getElementById('history-toggle')?.focus(); };
  }, [historyOpen]);
  const total = issue?.data.sections.reduce((sum, section) => sum + section.items.length, 0) || 0;
  const months = [...new Set(issues.map(item => item.day.slice(0, 7)))];
  function jump(value) { setActive(value); document.getElementById(value === 'all' ? 'sections' : `section-${value}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  return <><header className="topbar" inert={historyOpen || undefined}><a className="brand" href={`${base}/`}><span>NanaFox</span><i />AI 日报</a><a href="https://nanafox.com/" className="home-link">返回官网<ArrowSquareOut size={15} /></a></header>
    {historyOpen && <button className="sidebar-scrim" aria-label="关闭历史日期" onClick={() => setHistoryOpen(false)} />}
    <aside role={historyOpen ? 'dialog' : undefined} aria-modal={historyOpen || undefined} aria-label="历史日报" className={`history-sidebar ${historyOpen ? 'mobile-open' : ''}`}><div className="sidebar-title"><CalendarBlank size={19} weight="duotone" /><strong>历史日报</strong><button className="icon-button mobile-only" onClick={() => setHistoryOpen(false)} aria-label="关闭历史日期"><X size={18} /></button></div><div className="history-scroll"><nav aria-label="历史日报日期">{months.map(month => <div key={month}><p className="month-label">{month.slice(0, 4)} 年 {Number(month.slice(5))} 月</p>{issues.filter(item => item.day.startsWith(month)).map(item => <a key={item.day} href={item.url} className={view !== 'archive' && item.day === day ? 'active' : ''} aria-current={view !== 'archive' && item.day === day ? 'page' : undefined}><span>{shortDate(item.day)}</span>{item.day === issues[0].day && <small>最新</small>}</a>)}</div>)}</nav>{!issues.length && <p className="month-label">暂无日报</p>}</div><div className="sidebar-bottom"><a href={`${base}/archive/`}>查看全部历史 · {issues.length} 期</a></div></aside>
    <main className="reader" inert={historyOpen || undefined}><button id="history-toggle" className="history-mobile-button mobile-only button secondary" aria-expanded={historyOpen} onClick={() => setHistoryOpen(true)}><List size={18} />历史日报</button>
    {view === 'archive' ? <><div className="page-heading"><div><p className="eyebrow">DAILY AI BRIEFING</p><h1>历史日报</h1><p className="date-meta">共 {issues.length} 期 · 按日期倒序</p></div></div><div className="issue-list">{issues.map(item => <a className="issue-card" href={item.url} key={item.day}><span>{item.day}</span><h2>{item.title}</h2><p>{item.summary}</p><span className="issue-card-footer">{item.count} 条动态 <CaretRight size={16} /></span></a>)}</div>{!issues.length && <p className="empty-state">还没有日报，请稍后再来。</p>}</> : issue ? <>
    <div className="page-heading"><div><p className="eyebrow">{issue.data.eyebrow || 'DAILY AI BRIEFING'}</p><h1>{issue.data.title}</h1><p className="date-meta">{issue.data.date || day}<span>·</span>{total} 条动态</p></div><button className="button primary" onClick={() => setOpen(true)}><DownloadSimple size={18} />导出</button></div>
    {!!issue.data.tldr.length && <section className="highlights" aria-labelledby="highlights-title"><div className="section-caption"><h2 id="highlights-title">{clean(issue.data.tldr_heading) || '今日要点'}</h2><span>先读这 {issue.data.tldr.length} 件事</span></div><ol>{issue.data.tldr.map((item, i) => <li key={i}><span className="highlight-index">{String(i + 1).padStart(2, '0')}</span><div><strong>{typeof item === 'string' ? item : item.title}</strong>{typeof item !== 'string' && <p>{item.text}</p>}</div></li>)}</ol></section>}
    <nav className="section-tabs" aria-label="日报分类"><button className={active === 'all' ? 'active' : ''} onClick={() => jump('all')}>全部</button>{issue.data.sections.map((section, i) => <button key={i} className={active === i ? 'active' : ''} onClick={() => jump(i)}>{clean(section.heading).replace('与 AI 编程', '').replace('行业 · 投融资 · 政策', '行业').replace('模型发布与评测', '模型').replace('论文与研究', '研究').replace('产品与应用', '产品')}</button>)}</nav>
    <div id="sections">{issue.data.sections.map((section, i) => <section key={`${day}-${i}`} id={`section-${i}`} className="article-section"><div className="article-section-head"><h2>{clean(section.heading)}</h2><span>{section.items.length} 条</span></div>{section.note && <p className="section-note">{section.note}</p>}{section.items.map((item, index) => <article className="news-item" key={index}><div className="article-title-row"><h3>{item.url ? <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a> : item.title}</h3>{item.tag && <span className="badge">{item.tag}</span>}</div>{item.detail && <p className="article-detail">{item.detail}</p>}{item.why && <p className="article-why"><span>关注点</span>{item.why}</p>}<div className="article-bottom"><span>{item.source || ''}</span>{item.url && <a href={item.url} target="_blank" rel="noreferrer">阅读原文<ArrowSquareOut size={13} /></a>}</div>{item.related_urls.some(Boolean) && <div className="related-links">{item.related_urls.map((url, j) => url && <a href={url} target="_blank" rel="noreferrer" key={j}>{item.related[j] || `相关来源 ${j + 1}`}</a>)}</div>}</article>)}{!section.items.length && <p className="section-note">暂无条目</p>}</section>)}</div><footer className="reader-footer">NanaFox <span>·</span> AI 前沿日报<button className="button secondary" onClick={() => setOpen(true)}><DownloadSimple size={16} />导出本期</button></footer>
    <details className="original-poster"><summary>查看 Bot 原始长图</summary><a href={`${base}/assets/${day}.png`} download={`${day}.png`} className="button secondary">下载原始长图</a><img src={`${base}/assets/${day}.png`} alt={`${day} Bot 原始长图`} loading="lazy" /></details></> : <div className="empty-state"><h1>AI 前沿日报</h1><p>还没有日报，请稍后再来。</p></div>}
    </main>{issue && view !== 'archive' && <ExportDialog issue={issue} open={open} setOpen={setOpen} settings={settings} setSettings={setSettings} />}</>;
}
