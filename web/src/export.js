import JSZip from 'jszip';
import { toCanvas } from 'html-to-image';
import { mainHTML, longHTML } from './bot-template.js';
import { exportFonts } from './export-fonts.js';
import '@fontsource-variable/noto-sans-sc';
import './bot-template.css';

export const clean = value => String(value || '').replace(/[\p{Extended_Pictographic}\p{Regional_Indicator}\uFE0F\u200D]/gu, '').trim();
const release = pages => pages.forEach(page => { page.canvas.width = 0; page.canvas.height = 0; });

export async function renderPages(issue, signal) {
  const host = document.createElement('div');
  host.setAttribute('aria-hidden', 'true'); host.inert = true;
  Object.assign(host.style, { position: 'fixed', left: '-16000px', top: '0', width: '1080px', pointerEvents: 'none' });
  document.body.append(host);
  const pages = [];
  const check = () => { if (signal?.aborted) throw new DOMException('Canceled', 'AbortError'); };
  try {
    const settings = { title: issue.data.title, signature: 'NanaFox', sources: true };
    const fontEmbedCSS = await exportFonts(JSON.stringify(issue.data) + '今日要点 今日暂无要点 每日 AI 动态 原文链接见日报网站 看点 另见 NanaFox nanafox.com/daily 0123456789');
    check();
    const specs = [
      { label: '主图', html: mainHTML(issue, settings), className: 'digest-main' },
      { label: '长图', html: longHTML(issue, settings), className: '' },
    ];
    for (const spec of specs) {
      check();
      const node = document.createElement('div');
      node.className = `bot-export card ${spec.className}`; node.innerHTML = spec.html; host.append(node);
      const height = Math.ceil(node.getBoundingClientRect().height);
      if (height > 30000) throw new Error('本期内容过长，超出浏览器图片范围。请下载 Bot 原始长图。');
      const canvas = await toCanvas(node, { pixelRatio: 1, width: 1080, height, fontEmbedCSS, skipAutoScale: true });
      if (signal?.aborted) { canvas.width = 0; canvas.height = 0; check(); }
      pages.push({ label: spec.label, canvas, url: canvas.toDataURL('image/png') });
      node.remove();
    }
    return pages;
  } catch (error) { release(pages); throw error; }
  finally { host.remove(); }
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
export async function downloadPages(pages, issue) {
  if (pages.length !== 2) throw new Error('请等待两张图片生成完成。');
  const zip = new JSZip();
  for (const [index, page] of pages.entries()) {
    const blob = await new Promise(resolve => page.canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('图片生成失败，请重试。');
    zip.file(`${String(index + 1).padStart(2, '0')}-${page.label}.png`, blob);
  }
  downloadBlob(await zip.generateAsync({ type: 'blob' }), `${issue.day}-images.zip`);
}
