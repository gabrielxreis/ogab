// Lista cada movimento (tween GSAP) de composições HyperFrames: node movimentos.mjs <pasta_motions> <id...>  (OUT=arquivo.json)
// Saída por id: [início s, duração s, alvo "texto", propriedades, ease, nº de alvos]. Base do desenho de som "cada movimento com som".
import { execSync } from 'child_process';
const pp = execSync('ls -d ~/.npm/_npx/*/node_modules/puppeteer-core | head -1', { shell: '/bin/zsh' }).toString().trim();
const { default: puppeteer } = await import(pp + '/lib/puppeteer/puppeteer-core.js');
import fs from 'fs';
const exe = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';  // o Chrome do cache do puppeteer vem quebrado (sem Framework)
const b = await puppeteer.launch({ executablePath: exe, headless: true, args: ['--allow-file-access-from-files','--no-sandbox'] });
const out = {};
const base = process.argv[2];
for (const id of process.argv.slice(3)) {
  const p = await b.newPage();
  await p.goto('file://' + base + '/' + id + '/index.html', { waitUntil: 'networkidle0' });
  out[id] = await p.evaluate(() => tl.getChildren(true, true, false).map(t => {
    const el = t.targets()[0]; const lab = el ? (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') + (el.textContent ? ' "' + el.textContent.trim().slice(0, 24) + '"' : '') : '?';
    const v = Object.keys(t.vars).filter(k => !['duration', 'ease', 'delay', 'immediateRender', 'stagger', 'repeat', 'yoyo', 'onComplete'].includes(k));
    return [+t.startTime().toFixed(2), +t.duration().toFixed(2), lab, v.join(','), String(t.vars.ease || ''), t.targets().length];
  }).sort((a, b) => a[0] - b[0]));
  await p.close();
}
await b.close();
fs.writeFileSync(process.env.OUT || 'movimentos.json', JSON.stringify(out, null, 1));
