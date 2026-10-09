// Bundle only font subsets containing this issue's text in the SVG capture.
// All WOFF2 files are served with the site; export never needs a Google Fonts request.
const cached = new Map();
function intersects(range, points) {
  return range.split(',').some(part => {
    const match=part.trim().match(/^U\+([\da-f]+)(?:-([\da-f]+))?$/i);
    if (!match) return false;
    const lo=parseInt(match[1],16),hi=parseInt(match[2] || match[1],16);
    return points.some(point=>point>=lo && point<=hi);
  });
}
async function dataURL(url) {
  if (!cached.has(url)) cached.set(url,fetch(url).then(response=>{
    if (!response.ok) throw new Error('导出字体未加载成功，请刷新后重试。');
    return response.blob();
  }).then(blob=>new Promise((resolve,reject)=>{ const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob); })).catch(error=>{cached.delete(url);throw error;}));
  return cached.get(url);
}
export async function exportFonts(text) {
  const points=[...new Set(Array.from(text).map(char=>char.codePointAt(0)))];
  const rules=[];
  for (const sheet of document.styleSheets) {
    for (const rule of sheet.cssRules) {
      if (rule.type!==CSSRule.FONT_FACE_RULE || !rule.style.fontFamily.includes('Noto Sans SC Variable')) continue;
      if (!intersects(rule.style.getPropertyValue('unicode-range'),points)) continue;
      const src=rule.style.getPropertyValue('src').match(/url\(["']?([^"')]+)["']?\)/)?.[1];
      if (!src) continue;
      const url=new URL(src,sheet.href || document.baseURI).href;
      rules.push({rule,url});
    }
  }
  const css=await Promise.all(rules.map(async ({rule,url})=>rule.cssText.replace(/url\([^)]+\)/,`url("${await dataURL(url)}")`)));
  await document.fonts.load('400 25px "Noto Sans SC Variable"',text);
  await document.fonts.load('800 31px "Noto Sans SC Variable"',text);
  await document.fonts.ready;
  return css.join('\n');
}
