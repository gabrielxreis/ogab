// Funções de apoio do Gab no Premiere 2018-25.x (ExtendScript ES3: sem JSON nativo, sem let/const/arrow).
// Carregado uma vez por sessão do Premiere pelo premiere2019_lib.py ($.evalFile); recarrega se o arquivo mudar.
// Trilhas: índice 0 = V1/A1. Tempo em segundos (o Premiere usa ticks: 254016000000 por segundo).
// Sem "var": o arquivo roda num eval() dentro de função (envelope do Python) e o GAB precisa ficar global.
if (typeof GAB === "undefined") $.global.GAB = {};

GAB.TICKS = 254016000000;

// ---------------------------------------------------------------- JSON (ES3 não tem)
GAB.json = function (v) {
  var t = typeof v;
  if (v === null || v === undefined || t === "function") return "null";
  if (t === "number") return isFinite(v) ? String(v) : "null";
  if (t === "boolean") return String(v);
  if (t === "string") {
    // Laço em vez de regex: o ExtendScript dá "Syntax error" em regex com \u0000 ou U+2028.
    var s = '"';
    for (var n = 0; n < v.length; n++) {
      var c = v.charAt(n), cod = v.charCodeAt(n);
      if (c === "\\") s += "\\\\";
      else if (c === '"') s += '\\"';
      else if (cod < 32 || cod > 126) s += "\\u" + ("0000" + cod.toString(16)).slice(-4);
      else s += c;
    }
    return s + '"';
  }
  if (v instanceof Array) {
    var a = [];
    for (var i = 0; i < v.length; i++) a.push(GAB.json(v[i]));
    return "[" + a.join(",") + "]";
  }
  var o = [];
  for (var k in v) if (v.hasOwnProperty(k)) o.push(GAB.json(k) + ":" + GAB.json(v[k]));
  return "{" + o.join(",") + "}";
};

// ---------------------------------------------------------------- tempo
GAB.tempo = function (s) { var t = new Time(); t.seconds = Number(s); return t; };
GAB.ticks = function (s) { return String(Math.round(Number(s) * GAB.TICKS)); };

// ---------------------------------------------------------------- projeto, bins, itens
// Sem projeto aberto (tela Home), ler app.project.* gera exceção nativa que ESCAPA do try/catch ("Uncaught exception").
GAB.proj = function () { if (!app.isDocumentOpen()) throw new Error("nenhum projeto aberto no Premiere"); return app.project; };
GAB.norm = function (s) { return String(s || "").replace(/\\/g, "/").toLowerCase(); };

GAB.ehBin = function (it) { return it && it.type === ProjectItemType.BIN; };

GAB.itens = function (pasta, saida) {
  saida = saida || [];
  for (var i = 0; i < pasta.children.numItems; i++) {
    var it = pasta.children[i];
    if (GAB.ehBin(it)) GAB.itens(it, saida); else saida.push(it);
  }
  return saida;
};

GAB.itemPorCaminho = function (caminho) {
  var alvo = GAB.norm(caminho), todos = GAB.itens(GAB.proj().rootItem);
  for (var i = 0; i < todos.length; i++) {
    try { if (GAB.norm(todos[i].getMediaPath()) === alvo) return todos[i]; } catch (e) {}
  }
  return null;
};

GAB.itemPorNome = function (nome) {
  var todos = GAB.itens(GAB.proj().rootItem);
  for (var i = 0; i < todos.length; i++) if (todos[i].name === nome) return todos[i];
  return null;
};

GAB.bin = function (nome) {
  var raiz = GAB.proj().rootItem;
  if (!nome) return raiz;
  for (var i = 0; i < raiz.children.numItems; i++) {
    var it = raiz.children[i];
    if (GAB.ehBin(it) && it.name === nome) return it;
  }
  return raiz.createBin(nome);
};

GAB.importar = function (arquivos, nomeBin) {
  var faltam = [];
  for (var i = 0; i < arquivos.length; i++) if (!GAB.itemPorCaminho(arquivos[i])) faltam.push(arquivos[i]);
  if (faltam.length) GAB.proj().importFiles(faltam, true, GAB.bin(nomeBin), false);
  var r = [];
  for (var j = 0; j < arquivos.length; j++) {
    var it = GAB.itemPorCaminho(arquivos[j]);
    if (!it) throw new Error("não importou: " + arquivos[j]);
    r.push(it);
  }
  return r;
};

// ---------------------------------------------------------------- sequências e trilhas
GAB.seq = function (nome) {
  var p = GAB.proj();
  if (!nome) { if (!p.activeSequence) throw new Error("nenhuma sequência ativa"); return p.activeSequence; }
  for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].name === nome) return p.sequences[i];
  throw new Error("sequência não encontrada: " + nome);
};

// QE (API interna, sem documentação): mesma sequência no mundo QE. Ativa a sequência antes.
GAB.qeSeq = function (s) {
  app.enableQE();
  if (s && GAB.proj().activeSequence.sequenceID !== s.sequenceID) GAB.proj().activeSequence = s;
  return qe.project.getActiveSequence();
};

GAB.garantirTrilhas = function (s, nV, nA) {
  var faltaV = Math.max(0, nV - s.videoTracks.numTracks), faltaA = Math.max(0, nA - s.audioTracks.numTracks);
  if (faltaV || faltaA) GAB.qeSeq(s).addTracks(faltaV, s.videoTracks.numTracks, faltaA, 1, s.audioTracks.numTracks, 0, 0);
};

GAB.clipeEm = function (trilha, seg, tol) {
  tol = tol === undefined ? 0.05 : tol;
  for (var i = 0; i < trilha.clips.numItems; i++) {
    var c = trilha.clips[i];
    if (Math.abs(c.start.seconds - seg) < tol) return c;
  }
  return null;
};

GAB.retrato = function (s) {
  var r = { nome: s.name, video: [], audio: [] };
  var lado = function (trilhas, saida) {
    for (var t = 0; t < trilhas.numTracks; t++) {
      var tr = trilhas[t], l = [];
      for (var i = 0; i < tr.clips.numItems; i++) {
        var c = tr.clips[i];
        l.push({ nome: c.name, inicio: c.start.seconds, fim: c.end.seconds, in_: c.inPoint.seconds });
      }
      saida.push(l);
    }
  };
  lado(s.videoTracks, r.video); lado(s.audioTracks, r.audio);
  return r;
};

// Arquivo da instalação do Premiere (app.path já termina com \). A QE só aceita caminho com \ no Windows:
// com / o qe.project.newSequence devolve false sem erro.
GAB.instalacao = function (rel) { return app.path.replace(/[\\\/]+$/, "") + "\\" + rel.replace(/\//g, "\\"); };

// ---------------------------------------------------------------- edição (comportamentos medidos no 13.1.5)

// Timecode "HH;MM;SS;FF" que a QE aceita (razor, exportFramePNG), pelo fps da sequência.
GAB.tc = function (s, seg) {
  var fps = Math.round(GAB.TICKS / Number(s.timebase)), q = Math.round(Number(seg) * fps);
  var d2 = function (n) { return (n < 10 ? "0" : "") + n; };
  return d2(Math.floor(q / (3600 * fps))) + ";" + d2(Math.floor(q / (60 * fps)) % 60) + ";" + d2(Math.floor(q / fps) % 60) + ";" + d2(q % fps);
};

// In/out no item do projeto (mediaType 4 = tudo). Limpa antes: o subclipe e o overwrite herdam o que estiver marcado.
GAB.marcarInOut = function (it, de, ate) {
  it.clearInPoint(4); it.clearOutPoint(4);
  if (de !== null && de !== undefined) it.setInPoint(GAB.tempo(de), 4);
  if (ate !== null && ate !== undefined) it.setOutPoint(GAB.tempo(ate), 4);
};

// Subclipe só de vídeo (createSubClip takeAudio=0), reaproveitado pelo nome. Overwrite do item cru numa trilha de
// vídeo leva o áudio junto para a trilha de áudio de MESMO índice; overwriteClip(item, t, v, -1) dá "Bad argument".
GAB.soVideo = function (it) {
  var nome = it.name + " (video)", sub = GAB.itemPorNome(nome);
  if (sub) return sub;
  it.clearInPoint(4); it.clearOutPoint(4);
  try { it.createSubClip(nome, GAB.tempo(0), it.getOutPoint(4), 0, 1, 0); } catch (e) { return it; }   // sem áudio: o próprio item
  return GAB.itemPorNome(nome) || it;
};

// Tamanho da fonte: o TrackItem não expõe; vem da metadata do projeto ("1920 x 1080 (1,0)").
GAB.tamanho = function (it) {
  var m = it.getProjectMetadata().match(/Column\.Intrinsic\.VideoInfo>(\d+) x (\d+)/);
  return m ? [Number(m[1]), Number(m[2])] : null;
};

// Escala para cobrir o quadro (Motion > Scale, componente 1, parâmetro 1).
GAB.preencher = function (s, c) {
  var t = GAB.tamanho(c.projectItem);
  if (!t) return null;
  var esc = Math.max(s.frameSizeHorizontal / t[0], s.frameSizeVertical / t[1]) * 100;
  c.components[1].properties[1].setValue(esc, true);
  return esc;
};

// Volume > Level do clipe de áudio. Escala do 13.x: 0,5 = 0 dB, teto 1,0 = +6 dB (medido com render e ffmpeg).
GAB.nivel = function (c) {
  for (var i = 0; i < c.components.numItems; i++) {
    var comp = c.components[i];
    for (var j = 0; j < comp.properties.numItems; j++) if (/^(level|n.vel)$/i.test(comp.properties[j].displayName)) return comp.properties[j];
  }
  throw new Error("parâmetro Level não encontrado em " + c.name);
};
GAB.lin = function (db) { return Math.min(1, 0.5 * Math.pow(10, Number(db) / 20)); };

// Clipe da QE que começa em `seg` na trilha de vídeo. A QE conta os VÃOS como itens (type "Empty") e o objeto fica
// inválido depois de qualquer edição ("Object is invalid"): buscar de novo a cada operação.
GAB.qeClipe = function (s, v, seg) {
  var tr = GAB.qeSeq(s).getVideoTrackAt(v);
  for (var i = 0; i < tr.numItems; i++) {
    var x = tr.getItemAt(i);
    if (x.type === "Clip" && Math.abs(x.start.secs - seg) < 0.05) return x;
  }
  throw new Error("clipe QE não encontrado em " + seg + " s na V" + (v + 1));
};

// Componente Lumetri do clipe; criar=true põe um (pela QE) se não houver.
GAB.lumetri = function (c, criar) {
  var achar = function (x) { for (var i = 0; i < x.components.numItems; i++) if (x.components[i].matchName === "AE.ADBE Lumetri") return x.components[i]; return null; };
  var l = achar(c);
  if (l || !criar) { if (!l) throw new Error("sem Lumetri em " + c.name); return l; }
  var s = GAB.proj().activeSequence, ini = c.start.seconds, v = null;
  for (var t = 0; t < s.videoTracks.numTracks && v === null; t++) if (GAB.clipeEm(s.videoTracks[t], ini) && GAB.clipeEm(s.videoTracks[t], ini).nodeId === c.nodeId) v = t;
  GAB.qeClipe(s, v, ini).addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color"));
  return achar(GAB.clipeEm(s.videoTracks[v], ini));
};

// ---------------------------------------------------------------- reflexão (engenharia reversa da API)
GAB.descrever = function (obj) {
  var r = { classe: "", metodos: [], props: [] };
  try { r.classe = obj.reflect.name; } catch (e) {}
  try {
    var m = obj.reflect.methods;
    for (var i = 0; i < m.length; i++) {
      var args = [];
      try { for (var j = 0; j < m[i].arguments.length; j++) args.push(m[i].arguments[j].name + ":" + m[i].arguments[j].dataType); } catch (e2) {}
      r.metodos.push(m[i].name + "(" + args.join(", ") + ")");
    }
    var p = obj.reflect.properties;
    for (var k = 0; k < p.length; k++) r.props.push(p[k].name);
  } catch (e3) { r.erro = String(e3); }
  return r;
};

GAB.carregado = true;
