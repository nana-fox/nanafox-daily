import { useEffect, useMemo, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ArrowSquareOut, CalendarBlank, CaretRight, DownloadSimple, List, X } from '@phosphor-icons/react';
import { normalizeDigest } from './data.js';
import { clean, renderPages, downloadPages } from './export';

const shortDate = day => `${day.slice(5, 7)} 月 ${day.slice(8)} 日`;

function ExportDialog({ issue, open, setOpen }) {
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [result, setResult] = useState({ pages: [], error: '', rendering: false });
  const { pages, error, rendering } = result;
  useEffect(() => {
    setNotice('');
    if (!open) { setResult({ pages: [], error: '', rendering: false }); return; }
    const controller = new AbortController();
    setResult({ pages: [], error: '', rendering: true });
    renderPages(issue, controller.signal).then(pages => {
      if (controller.signal.aborted) { pages.forEach(page => { page.canvas.width = 0; page.canvas.height = 0; }); return; }
      setResult({ pages, error: '', rendering: false });
    }).catch(error => { if (!controller.signal.aborted) setResult({ pages: [], error: error.message, rendering: false }); });
    return () => controller.abort();
  }, [open, issue]);
  useEffect(() => () => { pages.forEach(page => { page.canvas.width = 0; page.canvas.height = 0; }); }, [pages]);
  async function save() {
    setBusy(true); setNotice('');
    try { await downloadPages(pages, issue); setNotice('下载已开始，解压即可使用。'); }
    catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }
  return <Dialog.Root open={open} onOpenChange={setOpen}><Dialog.Portal><Dialog.Overlay className="overlay" /><Dialog.Content className="export-dialog">
    <header className="dialog-head"><div><Dialog.Title>导出本期图片</Dialog.Title><Dialog.Description>{issue.day} <span>·</span> 一张主图，一张完整长图</Dialog.Description></div><Dialog.Close asChild><button className="icon-button" aria-label="关闭导出"><X size={20} /></button></Dialog.Close></header>
    {rendering ? <div className="export-state" role="status">正在生成两张图片…</div> : error ? <div className="export-state" role="alert">{error}</div> : <div className="image-pair">{pages.map((page, index) => <section className="image-card" key={page.label}><div className="image-card-heading"><div><h3>{page.label}</h3><p>{index === 0 ? `当天全部 ${issue.data.tldr.length} 条要点` : '完整正文、看点与来源'}</p></div><span>{page.canvas.width} × {page.canvas.height}</span></div><div className={`image-stage ${index === 0 ? 'main-image-stage' : ''}`} tabIndex={0} aria-label={`${page.label}预览，可滚动查看`}><img src={page.url} alt={`${issue.day} ${page.label}`} /></div></section>)}</div>}
    <footer className="dialog-footer"><span className="download-notice" role="status">{notice || '两张无网址 PNG 图片，打包为 ZIP'}</span><button className="button primary" disabled={busy || rendering || !!error || pages.length !== 2} onClick={save}><DownloadSimple size={17} />{busy ? '正在打包…' : rendering ? '正在生成…' : '下载两张图片'}</button></footer>
  </Dialog.Content></Dialog.Portal></Dialog.Root>;
}

export function App({ bootstrap }) {
  const { issues, base, view } = bootstrap;
  const day = bootstrap.day;
  const issue = useMemo(() => bootstrap.data ? { day, raw: bootstrap.data, data: normalizeDigest(bootstrap.data) } : null, [bootstrap, day]);
  const [open, setOpen] = useState(false); const [historyOpen, setHistoryOpen] = useState(false); const [active, setActive] = useState('all');
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
    </main>{issue && view !== 'archive' && <ExportDialog issue={issue} open={open} setOpen={setOpen} />}</>;
}
