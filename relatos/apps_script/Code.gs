/**
 * Receptor dos relatos de erro do Gab (/ogab). Roda na conta Google do dono, grava numa planilha dele.
 * Publicado como app da Web ("executar como: eu", "acesso: qualquer pessoa"). Ver relatos/LEIA.md.
 *
 * POST (instalações):  {chave_envio:"ogab-relato-v1", titulo, erro, causa, correcao, diff, assinatura, versao, ...}
 *   -> nova linha; mesmo erro (assinatura) ainda aberto só soma +1 em "vezes" e guarda a instalação.
 * GET  ?acao=chave                 -> devolve a chave de administrador UMA vez (o /ogab do dono guarda no config dele)
 * GET  ?acao=listar&chave=K[&todos=1][&diff=1]  -> relatos (abertos por padrão)
 * POST {acao:"resolver", chave:K, assinatura, commit, nota, status}  -> marca como resolvido
 */
var MAX_CORPO = 30000;
var COLUNAS = ['recebido', 'assinatura', 'titulo', 'erro', 'causa', 'correcao', 'diff', 'versao', 'sistema', 'python',
               'editor', 'motion', 'instalacoes', 'vezes', 'status', 'commit', 'nota', 'atualizado'];

function props_() { return PropertiesService.getScriptProperties(); }

function planilha_() {
  var id = props_().getProperty('SHEET_ID');
  if (id) return SpreadsheetApp.openById(id).getSheets()[0];
  var ss = SpreadsheetApp.create('Relatos do Gab (/ogab)');
  var sh = ss.getSheets()[0];
  sh.setName('relatos'); sh.appendRow(COLUNAS); sh.setFrozenRows(1);
  props_().setProperty('SHEET_ID', ss.getId());
  return sh;
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function txt_(v, lim) {   // texto limpo: sem fórmula (evita injeção na planilha) e com limite de tamanho
  var s = String(v == null ? '' : v).slice(0, lim || 3000);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function admin_(k) { var a = props_().getProperty('ADMIN_KEY'); return a && k && k === a; }

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.acao === 'ping') return json_({ ok: true });
  if (p.acao === 'chave') {   // só na primeira vez (logo depois de publicar, feito pelo /ogab do dono)
    if (props_().getProperty('ADMIN_KEY')) return json_({ ok: false, erro: 'chave ja entregue' });
    var k = Utilities.getUuid() + Utilities.getUuid().slice(0, 8);
    props_().setProperty('ADMIN_KEY', k); planilha_();
    return json_({ ok: true, chave: k, planilha: SpreadsheetApp.openById(props_().getProperty('SHEET_ID')).getUrl() });
  }
  if (p.acao === 'listar') {
    if (!admin_(p.chave)) return json_({ ok: false, erro: 'chave' });
    var v = planilha_().getDataRange().getValues(), out = [];
    for (var i = 1; i < v.length; i++) {
      var o = {}; for (var c = 0; c < COLUNAS.length; c++) o[COLUNAS[c]] = v[i][c];
      if (!p.diff) delete o.diff;
      o.linha = i + 1;
      if (p.todos || o.status !== 'resolvido') out.push(o);
    }
    return json_({ ok: true, relatos: out });
  }
  return json_({ ok: false });
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '';
    if (raw.length > MAX_CORPO) return json_({ ok: false, erro: 'grande' });
    var d = JSON.parse(raw);
    if (d.acao === 'resolver') return resolver_(d);
    if (d.chave_envio !== 'ogab-relato-v1' || !d.titulo || !d.erro) return json_({ ok: false, erro: 'formato' });
    var cache = CacheService.getScriptCache(), n = Number(cache.get('n') || 0);
    if (n > 500) return json_({ ok: false, erro: 'limite diario' });
    cache.put('n', String(n + 1), 21600);
    var lock = LockService.getScriptLock(); lock.waitLock(15000);
    try {
      var sh = planilha_(), v = sh.getDataRange().getValues(), agora = new Date();
      for (var i = 1; i < v.length; i++) {
        if (v[i][1] === d.assinatura && v[i][14] !== 'resolvido') {
          var inst = String(v[i][12] || ''), id = txt_(d.instalacao, 20);
          if (inst.indexOf(id) < 0) inst = inst ? inst + ',' + id : id;
          sh.getRange(i + 1, 13, 1, 2).setValues([[inst, Number(v[i][13] || 1) + 1]]);
          sh.getRange(i + 1, 18).setValue(agora);
          return json_({ ok: true, repetido: true });
        }
      }
      sh.appendRow([agora, txt_(d.assinatura, 20), txt_(d.titulo, 200), txt_(d.erro, 3000), txt_(d.causa, 2000),
                    txt_(d.correcao, 3000), txt_(d.diff, 15000), txt_(d.versao, 40), txt_(d.sistema, 80), txt_(d.python, 20),
                    txt_(d.editor, 20), txt_(d.motion, 20), txt_(d.instalacao, 20), 1, 'novo', '', '', agora]);
    } finally { lock.releaseLock(); }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, erro: String(err).slice(0, 200) });
  }
}

function resolver_(d) {
  if (!admin_(d.chave)) return json_({ ok: false, erro: 'chave' });
  var sh = planilha_(), v = sh.getDataRange().getValues(), n = 0;
  for (var i = 1; i < v.length; i++) {
    if (v[i][1] === d.assinatura && v[i][14] !== 'resolvido') {
      sh.getRange(i + 1, 15, 1, 4).setValues([[d.status || 'resolvido', txt_(d.commit, 60), txt_(d.nota, 500), new Date()]]); n++;
    }
  }
  return json_({ ok: true, marcados: n });
}
