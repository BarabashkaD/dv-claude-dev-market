// Parse every ```mermaid block in one or more Markdown files with the real Mermaid parser.
// Setup: place this file next to node_modules containing `mermaid` and `jsdom` (see scripts/README.md).
// Usage: node check_mermaid.mjs FILE.md [FILE2.md ...]     exit code 1 when any block fails to parse
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error('usage: node check_mermaid.mjs FILE.md [FILE2.md ...]');
  process.exit(2);
}

const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
for (const k of ['window', 'document', 'DOMParser', 'Element', 'HTMLElement', 'Node', 'SVGElement']) {
  const value = k === 'window' ? dom.window : k === 'document' ? dom.window.document : dom.window[k];
  try { Object.defineProperty(globalThis, k, { value, configurable: true, writable: true }); } catch { /* read-only */ }
}
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false });

let total = 0, bad = 0;
for (const file of files) {
  const md = readFileSync(file, 'utf8');
  const re = /```mermaid\r?\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(md)) !== null) {
    total++;
    const line = md.slice(0, m.index).split('\n').length;
    const first = m[1].split('\n')[0].trim();
    try {
      await mermaid.parse(m[1]);
      console.log(`OK    ${file}:${line} ${first}`);
    } catch (e) {
      bad++;
      console.log(`ERROR ${file}:${line} ${first}\n      ${String(e.message || e).split('\n').slice(0, 6).join('\n      ')}`);
    }
  }
}
console.log(`\n${total} mermaid blocks, ${bad} with errors`);
process.exit(bad ? 1 : 0);
