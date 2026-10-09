import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
const root = resolve('..');
function sources(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const path = resolve(dir, entry.name);
    return entry.isDirectory() ? sources(path) : [path];
  });
}
const files = [...sources(resolve('src')), ...['package.json', 'package-lock.json', 'vite.config.mjs', 'scripts/build-meta.mjs'].map(path => resolve(path))].sort();
const hashes = Object.fromEntries(files.map(path => [relative(root, path), createHash('sha256').update(readFileSync(path)).digest('hex')]));
writeFileSync('../site/reader/build-meta.json', JSON.stringify({ sources: hashes }, null, 2) + '\n');
