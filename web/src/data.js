export function safeUrl(value) {
  if (typeof value !== 'string') return '';
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : ''; } catch { return ''; }
}
export function normalizeDigest(raw = {}) {
  return {
    ...raw,
    title: raw.title || 'AI 前沿日报',
    tldr: (Array.isArray(raw.tldr) ? raw.tldr : []).filter(item => typeof item === 'string' || item && typeof item === 'object'),
    sections: (Array.isArray(raw.sections) ? raw.sections : []).filter(section => section && typeof section === 'object').map(section => ({
      ...section,
      heading: section.heading || '动态',
      items: (Array.isArray(section.items) ? section.items : []).filter(item => item && typeof item === 'object').map(item => ({
        ...item,
        title: item.title || '动态',
        detail: item.detail || item.summary || '',
        url: safeUrl(item.url),
        related: Array.isArray(item.related) ? item.related : [],
        related_urls: (Array.isArray(item.related_urls) ? item.related_urls : []).map(safeUrl),
      })),
    })),
  };
}
