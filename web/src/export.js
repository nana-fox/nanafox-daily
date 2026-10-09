import JSZip from 'jszip';
import { toCanvas } from 'html-to-image';
import { accentFor, esc, headerHTML, highlightsHTML, itemHTML, sectionHeadHTML, footerHTML, longHTML, packCards, splitOversized } from './bot-template.js';
import { exportFonts } from './export-fonts.js';
import '@fontsource-variable/noto-sans-sc';
import './bot-template.css';

export const formats = [
  { id:'long',label:'长图',description:'Bot 原版排版，完整一期长图' },
  { id:'wechat',label:'公众号组图',description:'公众号封面与完整分类配图' },
  { id:'xhs',label:'小红书组图',description:'沿用 Bot 模板，3:4 自动分页' },
  { id:'json',label:'JSON',description:'当前日报的完整结构化数据' },
];
export const clean = value => String(value || '').replace(/[\p{Extended_Pictographic}\p{Regional_Indicator}\uFE0F\u200D]/gu,'').trim();
const release = pages => pages.forEach(page=>{page.canvas.width=0;page.canvas.height=0;});
function surface(host,settings,html,classes='',height) {
  const node=document.createElement('div'); node.className=`bot-export card ${settings.theme==='paper' ? 'paper' : ''} ${classes}`;
  if (height) node.style.height=`${height}px`;
  node.innerHTML=html;host.append(node);return node;
}
const measured = node => Math.ceil(node.getBoundingClientRect().height);
const channelHeader = (issue,settings) => `<div class="channel-header"><strong>${esc(settings.title || issue.data.title)}</strong><span>${esc(issue.data.date || issue.day)}</span></div>`;
const coverPoint = (row,index) => `<div class="cover-point"><b><span class="tn">${index+1}</span>${esc(typeof row==='string' ? '今日要点' : row.title)}</b><p>${esc(typeof row==='string' ? row : row.text)}</p></div>`;
export async function renderPages(issue,settings,coverOnly=false,signal) {
  if (settings.format==='json') return [];
  const host=document.createElement('div');
  host.setAttribute('aria-hidden','true');host.inert=true;
  Object.assign(host.style,{position:'fixed',left:'-16000px',top:'0',width:'1080px',pointerEvents:'none'});
  document.body.append(host);
  const pages=[];
  const check=()=>{if(signal?.aborted) throw new DOMException('Canceled','AbortError');};
  try {
    const text=JSON.stringify(issue.data)+String(settings.title)+String(settings.signature)+'今日要点 看点 另见 原文链接见日报网站 接上页 续 NanaFox nanafox.com/daily 0123456789 /';
    const fontEmbedCSS=await exportFonts(text);check();
    const specs=[];
    if (settings.format==='long') {
      specs.push({label:'完整日报',node:surface(host,settings,longHTML(issue,settings))});
    } else {
      if (settings.format==='wechat') {
        const cover=surface(host,settings,`<div class="wechat-cover">${headerHTML(issue,settings).replace('</h1>','</h1><div class="cover-topics">'+issue.data.tldr.slice(0,3).map(row=>`<span>${esc(typeof row==='string' ? row : row.title)}</span>`).join('')+'</div>')}</div>`,'page wechat-cover-page',460);
        cover.querySelector('h1').style.fontSize=`${Array.from(settings.title || issue.data.title).length>28?40:Array.from(settings.title || issue.data.title).length>16?48:60}px`;
        specs.push({label:'公众号封面',node:cover});
        if (!coverOnly && issue.data.tldr.length) specs.push({label:'今日要点',node:surface(host,settings,channelHeader(issue,settings)+`<div class="channel-body">${highlightsHTML(issue)}</div>`,'page')});
      } else {
        const shell=surface(host,settings,headerHTML(issue,settings)+`<div class="cover-blocks"></div>`+footerHTML(issue,settings,0,1),'page xhs-cover',1440);
        const blocks=shell.querySelector('.cover-blocks');
        const available=1440-measured(shell.querySelector('.header'))-measured(shell.querySelector('.page-footer'))-48;
        const rows=issue.data.tldr.map((row,index)=>{blocks.innerHTML=coverPoint(row,index);return {html:blocks.innerHTML,height:measured(blocks.firstElementChild)};});
        const chunks=packCards(rows,available,24);
        shell.remove();
        (chunks.length?chunks:[[]]).forEach((chunk,index)=>specs.push({label:index?'今日要点 · 续':'封面',node:surface(host,settings,headerHTML(issue,settings)+`<div class="cover-blocks">${chunk.map(row=>row.html).join('')}</div>`,'page xhs-cover',1440)}));
      }
      if (!coverOnly) for (const [si,section] of issue.data.sections.entries()) {
        check();
        const color=accentFor(section,si),sec={...section,color};
        const baseClass=settings.format==='xhs'?'page xhs':'page';
        const probe=surface(host,settings,channelHeader(issue,settings)+`<div class="channel-body"><div class="section">${sectionHeadHTML(sec,true)}<div class="measure-cards"></div></div></div>`+footerHTML(issue,settings,0,1),baseClass);
        const box=probe.querySelector('.measure-cards');
        const measure=html=>{box.innerHTML=html;return measured(box.firstElementChild);};
        const overhead=measured(probe)-measured(box);
        const available=settings.format==='xhs'?1440-overhead-4:2000-overhead;
        if (available<200) throw new Error('栏目标题或说明过长，请使用长图或 JSON 导出。');
        const cards=section.items.flatMap((item,index)=>{
          const html=itemHTML(item,index+1,color,settings,false,section.style==='bullets');
          const height=measure(html);
          return height<=available?[{html,height}]:splitOversized(item,index+1,color,settings,section.style==='bullets',available,measure);
        });
        const chunks=packCards(cards,available,18);probe.remove();
        (chunks.length?chunks:[[]]).forEach((chunk,index)=>specs.push({label:`${clean(section.heading)}${index?' · 续 '+(index+1):''}`,node:surface(host,settings,channelHeader(issue,settings)+`<div class="channel-body"><div class="section">${sectionHeadHTML(sec,index>0)}${chunk.map(card=>card.html).join('')}</div></div>`,baseClass,settings.format==='xhs'?1440:undefined)}));
      }
    }
    const output=coverOnly?specs.slice(0,1):specs;
    for (const [index,spec] of output.entries()) {
      check();
      if (settings.format!=='long') spec.node.insertAdjacentHTML('beforeend',footerHTML(issue,settings,index,output.length));
      const height=measured(spec.node);
      if (height>30000 || (['xhs','wechat'].includes(settings.format) && spec.node.style.height && spec.node.scrollHeight>height)) throw new Error('内容超出了图片范围，请使用长图或 JSON 导出。');
      const canvas=await toCanvas(spec.node,{pixelRatio:1,width:1080,height,fontEmbedCSS,skipAutoScale:true});
      if(signal?.aborted) {canvas.width=0;canvas.height=0;check();}
      pages.push({label:spec.label,canvas,url:canvas.toDataURL('image/png'),cover:index===0});
      spec.node.remove();
    }
    return pages;
  } catch(error) {release(pages);throw error;} finally {host.remove();}
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
