// Versão Windows de scripts/movimentos.mjs (a do Mac usa zsh + ls e o Chrome de /Applications).
// Lista cada movimento (tween GSAP) de composições HyperFrames: node movimentos.mjs <pasta_motions> <id...>  (OUT=arquivo.json)
// Saída por id: [início s, duração s, alvo "texto", propriedades, ease, nº de alvos]. Base do desenho de som "cada movimento com som".
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

function acharPuppeteer() {
  const caches = [
    process.env.npm_config_cache,
    path.join(process.env.LOCALAPPDATA || '', 'npm-cache'),
    path.join(process.env.APPDATA || '', 'npm-cache'),
  ].filter(Boolean).map(c => path.join(c, '_npx'));
  for (const c of caches) {
    if (!fs.existsSync(c)) continue;
    for (const d of fs.readdirSync(c)) {
      const p = path.join(c, d, 'node_modules', 'puppeteer-core');
      if (fs.existsSync(p)) return p;
    }
  }
  throw new Error('puppeteer-core não encontrado no cache do npx: rode "npx hyperframes doctor" uma vez e tente de novo');
}

function acharChrome() {
  if (process.env.CHROME) return process.env.CHROME;
  const cands = [
    path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
  ];
  const ok = cands.find(c => fs.existsSync(c));
  if (!ok) throw new Error('Chrome não encontrado: defina a variável CHROME com o caminho do chrome.exe');
  return ok;
}

const pp = acharPuppeteer();
const { default: puppeteer } = await import(pathToFileURL(path.join(pp, 'lib', 'puppeteer', 'puppeteer-core.js')).href);
const b = await puppeteer.launch({ executablePath: acharChrome(), headless: true, args: ['--allow-file-access-from-files', '--no-sandbox'] });
const out = {};
const base = path.resolve(process.argv[2]);
for (const id of process.argv.slice(3)) {
  const p = await b.newPage();
  await p.goto(pathToFileURL(path.join(base, id, 'index.html')).href, { waitUntil: 'networkidle0' });
  out[id] = await p.evaluate(() => tl.getChildren(true, true, false).map(t => {
    const el = t.targets()[0]; const lab = el ? (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') + (el.textContent ? ' "' + el.textContent.trim().slice(0, 24) + '"' : '') : '?';
    const v = Object.keys(t.vars).filter(k => !['duration', 'ease', 'delay', 'immediateRender', 'stagger', 'repeat', 'yoyo', 'onComplete'].includes(k));
    return [+t.startTime().toFixed(2), +t.duration().toFixed(2), lab, v.join(','), String(t.vars.ease || ''), t.targets().length];
  }).sort((a, b) => a[0] - b[0]));
  await p.close();
}
await b.close();
fs.writeFileSync(process.env.OUT || 'movimentos.json', JSON.stringify(out, null, 1));
