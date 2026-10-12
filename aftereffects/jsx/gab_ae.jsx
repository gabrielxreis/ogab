/* Gab (/ogab) no After Effects: monta motions como camadas NATIVAS e editáveis (texto, formas, checks, contadores,
   barras, imagens), com keyframes suaves e uma camada CONTROLES (cores da marca num lugar só).
   Carregado a cada comando pelo aftereffects/ae_lib.py ($.evalFile), então atualizar é só "git pull".
   ExtendScript = ES3: sem let/const, arrow, forEach, template string ou JSON nativo. */

var GAB = GAB || {};
GAB.avisos = [];

// ---------------------------------------------------------------- JSON (ExtendScript não tem)
GAB.json = function (v) {
  var t = typeof v, i, out;
  if (v === null || v === undefined) return "null";
  if (t === "number") return isFinite(v) ? String(v) : "null";
  if (t === "boolean") return v ? "true" : "false";
  if (t === "string") {
    return '"' + v.replace(/[\\"\u0000-\u001f\u007f-￿]/g, function (c) {
      var m = { '"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t" };
      return m[c] || "\\u" + ("0000" + c.charCodeAt(0).toString(16)).slice(-4);
    }) + '"';
  }
  if (v instanceof Array) { out = []; for (i = 0; i < v.length; i++) out.push(GAB.json(v[i])); return "[" + out.join(",") + "]"; }
  if (t === "object") { out = []; for (i in v) if (v.hasOwnProperty(i) && typeof v[i] !== "function") out.push(GAB.json(String(i)) + ":" + GAB.json(v[i])); return "{" + out.join(",") + "}"; }
  return "null";
};

// Todo comando roda com os diálogos do AE suprimidos: uma janela modal trava a ponte e ninguém está na frente
// do Mac para clicar (aprendido no teste de 12/10/2026).
GAB.rodar = function (fn, args) {
  GAB.avisos = [];
  try { app.beginSuppressDialogs(); } catch (x) {}
  try { return GAB.json({ ok: true, r: fn(args), avisos: GAB.avisos }); }
  catch (e) { return GAB.json({ ok: false, erro: String(e) + (e.line ? " (linha " + e.line + ")" : "") }); }
  finally { try { app.endSuppressDialogs(false); } catch (y) {} }
};

// ---------------------------------------------------------------- utilidades
GAB.rgb = function (hex) {
  hex = String(hex).replace("#", "");
  if (hex.length === 3) hex = hex.charAt(0) + hex.charAt(0) + hex.charAt(1) + hex.charAt(1) + hex.charAt(2) + hex.charAt(2);
  return [parseInt(hex.substr(0, 2), 16) / 255, parseInt(hex.substr(2, 2), 16) / 255, parseInt(hex.substr(4, 2), 16) / 255];
};

GAB.comp = function (nome) {
  for (var i = 1; i <= app.project.numItems; i++) {
    var it = app.project.item(i);
    if (it instanceof CompItem && it.name === nome) return it;
  }
  return null;
};

GAB.pasta = function (nome) {
  for (var i = 1; i <= app.project.numItems; i++) {
    var it = app.project.item(i);
    if (it instanceof FolderItem && it.name === nome) return it;
  }
  return app.project.items.addFolder(nome);
};

GAB.projeto = function (caminho) {
  var f = new File(caminho);
  if (app.project && app.project.file && app.project.file.fsName === f.fsName) return app.project.file.fsName;
  // salva o projeto aberto antes de trocar (senão o AE pergunta "salvar alterações?" e trava)
  if (app.project && app.project.file) app.project.close(CloseOptions.SAVE_CHANGES);
  else if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
  if (f.exists) app.open(f);
  else { app.newProject(); app.project.save(f); }
  return app.project.file ? app.project.file.fsName : null;
};

// Curva "calma" do Gab: sai devagar e chega devagar (influência alta), sem tranco.
GAB.suavizar = function (prop, influencia) {
  influencia = influencia || 80;
  var dims = 1, t = prop.propertyValueType;
  if (t === PropertyValueType.TwoD) dims = 2;
  else if (t === PropertyValueType.ThreeD) dims = 3;
  var e = [], i;
  for (i = 0; i < dims; i++) e.push(new KeyframeEase(0, influencia));
  for (i = 1; i <= prop.numKeys; i++) {
    try { prop.setTemporalEaseAtKey(i, e, e); } catch (x) {}
  }
};

GAB.chaves = function (prop, pares, influencia) {
  for (var i = 0; i < pares.length; i++) prop.setValueAtTime(pares[i][0], pares[i][1]);
  GAB.suavizar(prop, influencia);
};

// Liga uma cor ao controle da camada CONTROLES (o usuário troca a cor da marca uma vez só).
GAB.corDe = function (prop, cor) {
  if (cor === "principal" || cor === "destaque" || cor === "texto" || cor === "fundo") {
    var nomes = { principal: "Cor principal", destaque: "Cor de destaque", texto: "Cor do texto", fundo: "Cor do fundo" };
    prop.expression = 'thisComp.layer("CONTROLES").effect("' + nomes[cor] + '")(1)';
  } else if (cor) {
    prop.setValue(GAB.rgb(cor));
  }
};

GAB.controles = function (comp, cores) {
  var n = comp.layers.addNull(comp.duration);
  n.name = "CONTROLES"; n.guideLayer = true; n.enabled = false; n.label = 9;
  var lista = [["Cor principal", cores.principal || "#0B2545"], ["Cor de destaque", cores.destaque || "#C9A227"],
               ["Cor do texto", cores.texto || "#FFFFFF"], ["Cor do fundo", cores.fundo || "#0B2545"]];
  for (var i = lista.length - 1; i >= 0; i--) {
    var ef = n.property("ADBE Effect Parade").addProperty("ADBE Color Control");
    ef.name = lista[i][0];
    ef.property(1).setValue(GAB.rgb(lista[i][1]));
  }
  return n;
};

// ---------------------------------------------------------------- entradas e saídas
// Efeitos: fade, fade_up, fade_down, pop, blur_in, slide_esq, slide_dir, digitando (letras), palavras (palavra por palavra)
GAB.entrada = function (layer, ef, ini, dur, y, x) {
  if (!ef) return;
  dur = dur || 0.6;
  var tr = layer.property("ADBE Transform Group"), op = tr.property("ADBE Opacity"), pos = tr.property("ADBE Position");
  var p0 = pos.value;
  if (ef === "digitando" || ef === "palavras") { GAB.revelarTexto(layer, ini, dur, ef === "palavras" ? 3 : 1); return; }
  GAB.chaves(op, [[ini, 0], [ini + dur * 0.7, 100]]);
  if (ef === "fade_up") GAB.chaves(pos, [[ini, [p0[0], p0[1] + 70]], [ini + dur, p0]]);
  if (ef === "fade_down") GAB.chaves(pos, [[ini, [p0[0], p0[1] - 70]], [ini + dur, p0]]);
  if (ef === "slide_esq") GAB.chaves(pos, [[ini, [p0[0] + 220, p0[1]]], [ini + dur, p0]]);
  if (ef === "slide_dir") GAB.chaves(pos, [[ini, [p0[0] - 220, p0[1]]], [ini + dur, p0]]);
  if (ef === "pop") {
    var sc = tr.property("ADBE Scale");
    GAB.chaves(sc, [[ini, [0, 0, 100]], [ini + dur * 0.65, [106, 106, 100]], [ini + dur, [100, 100, 100]]], 70);
  }
  if (ef === "blur_in") {
    var bl = layer.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
    bl.name = "Blur de entrada";
    GAB.chaves(layer.property("ADBE Effect Parade").property("Blur de entrada").property(1), [[ini, 45], [ini + dur, 0]]);
  }
};

GAB.saida = function (layer, ef, ini, dur) {
  if (!ef) return;
  dur = dur || 0.5;
  var tr = layer.property("ADBE Transform Group"), op = tr.property("ADBE Opacity"), pos = tr.property("ADBE Position");
  var p0 = pos.valueAtTime(ini, false);
  GAB.chaves(op, [[ini, 100], [ini + dur, 0]]);
  if (ef === "fade_down") GAB.chaves(pos, [[ini, p0], [ini + dur, [p0[0], p0[1] + 60]]]);
  if (ef === "fade_up") GAB.chaves(pos, [[ini, p0], [ini + dur, [p0[0], p0[1] - 60]]]);
};

// Revela o texto por letra (1) ou por palavra (3) com um animador de texto (fica editável no AE).
GAB.revelarTexto = function (layer, ini, dur, base) {
  var anims = layer.property("ADBE Text Properties").property("ADBE Text Animators");
  var an = anims.addProperty("ADBE Text Animator");
  an.name = "Revelar";
  an = layer.property("ADBE Text Properties").property("ADBE Text Animators").property("Revelar");
  an.property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity");
  an = layer.property("ADBE Text Properties").property("ADBE Text Animators").property("Revelar");
  an.property("ADBE Text Animator Properties").property("ADBE Text Opacity").setValue(0);
  an.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D");
  an = layer.property("ADBE Text Properties").property("ADBE Text Animators").property("Revelar");
  an.property("ADBE Text Animator Properties").property("ADBE Text Position 3D").setValue([0, 30, 0]);
  var sel = an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
  sel = layer.property("ADBE Text Properties").property("ADBE Text Animators").property("Revelar").property("ADBE Text Selectors").property(1);
  try { sel.property("ADBE Text Range Advanced").property("ADBE Text Range Type2").setValue(base); } catch (e) {}
  try { sel.property("ADBE Text Range Advanced").property("ADBE Text Selector Smoothness").setValue(100); } catch (e2) {}
  GAB.chaves(sel.property("ADBE Text Percent Start"), [[ini, 0], [ini + dur, 100]], 60);
};

// ---------------------------------------------------------------- elementos
GAB.texto = function (comp, e) {
  var l = comp.layers.addText(e.caixa_alta ? String(e.texto).toUpperCase() : String(e.texto));
  l.name = e.nome || ("TXT " + String(e.texto).substr(0, 24));
  var st = l.property("ADBE Text Properties").property("ADBE Text Document");
  var td = st.value;
  td.resetCharStyle(); td.resetParagraphStyle();
  td.font = e.fonte || "Poppins-Bold";
  td.fontSize = e.tamanho || 72;
  td.applyFill = true;
  td.fillColor = GAB.rgb(e.cor && e.cor.charAt(0) === "#" ? e.cor : "#FFFFFF");
  td.justification = e.alinhar === "esquerda" ? ParagraphJustification.LEFT_JUSTIFY : (e.alinhar === "direita" ? ParagraphJustification.RIGHT_JUSTIFY : ParagraphJustification.CENTER_JUSTIFY);
  if (e.tracking !== undefined) td.tracking = e.tracking;
  st.setValue(td);
  try {   // o AE aceita qualquer nome calado (fica "fonte ausente"): conferir na lista de fontes instaladas
    var fs = app.fonts.getFontsByPostScriptName(td.font);
    if (!fs.length || fs[0].isSubstitute)
      GAB.avisos.push("fonte '" + td.font + "' não está instalada nesta máquina (camada " + l.name + ")");
  } catch (ef) {}
  if (e.cor && e.cor.charAt(0) !== "#") {   // cor ligada ao CONTROLES: efeito Preenchimento com expressão
    var fx = l.property("ADBE Effect Parade").addProperty("ADBE Fill");
    fx.name = "Cor";
    GAB.corDe(l.property("ADBE Effect Parade").property("Cor").property("ADBE Fill-0002"), e.cor);
  }
  var tr = l.property("ADBE Transform Group");
  // âncora no centro do texto (continua certa se o usuário trocar o texto no AE)
  tr.property("ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width/2, r.top + r.height/2]";
  if (e.alinhar === "esquerda") tr.property("ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left, r.top + r.height/2]";
  tr.property("ADBE Position").setValue([e.x, e.y]);
  return l;
};

GAB.caixa = function (comp, e) {
  var l = comp.layers.addShape();
  l.name = e.nome || "CAIXA";
  var g = l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
  g.name = "Caixa";
  var v = l.property("ADBE Root Vectors Group").property("Caixa").property("ADBE Vectors Group");
  var r = v.addProperty("ADBE Vector Shape - Rect");
  r.property("ADBE Vector Rect Size").setValue([e.w, e.h]);
  r.property("ADBE Vector Rect Roundness").setValue(e.raio === undefined ? 24 : e.raio);
  if (e.borda) {
    var s = l.property("ADBE Root Vectors Group").property("Caixa").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
    GAB.corDe(s.property("ADBE Vector Stroke Color"), e.borda);
    s.property("ADBE Vector Stroke Width").setValue(e.borda_largura || 3);
  }
  var f = l.property("ADBE Root Vectors Group").property("Caixa").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
  GAB.corDe(f.property("ADBE Vector Fill Color"), e.cor || "principal");
  if (e.opacidade_fill !== undefined) f.property("ADBE Vector Fill Opacity").setValue(e.opacidade_fill);
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  if (e.sombra) {
    var ds = l.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
    ds.property("ADBE Drop Shadow-0002").setValue(35);   // opacidade
    ds.property("ADBE Drop Shadow-0004").setValue(18);   // distância
    ds.property("ADBE Drop Shadow-0005").setValue(40);   // suavidade
  }
  return l;
};

GAB.fundo = function (comp, e) {
  var l = GAB.caixa(comp, { nome: "FUNDO", w: comp.width + 40, h: comp.height + 40, x: comp.width / 2, y: comp.height / 2, raio: 0, cor: e.cor || "fundo" });
  return l;
};

GAB.check = function (comp, e) {
  var t = e.tamanho || 56;
  var l = comp.layers.addShape();
  l.name = e.nome || "CHECK";
  var raiz = l.property("ADBE Root Vectors Group");
  if (e.circulo !== false) {
    raiz.addProperty("ADBE Vector Group").name = "Circulo";
    var vc = l.property("ADBE Root Vectors Group").property("Circulo").property("ADBE Vectors Group");
    vc.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([t, t]);
    var fc = l.property("ADBE Root Vectors Group").property("Circulo").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    GAB.corDe(fc.property("ADBE Vector Fill Color"), e.cor || "destaque");
  }
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Visto";
  var vv = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group");
  var pth = vv.addProperty("ADBE Vector Shape - Group");
  var sh = new Shape();
  sh.vertices = [[-t * 0.22, 0], [-t * 0.05, t * 0.17], [t * 0.24, -t * 0.16]];
  sh.closed = false;
  pth.property("ADBE Vector Shape").setValue(sh);
  var stk = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
  GAB.corDe(stk.property("ADBE Vector Stroke Color"), e.cor_visto || "principal");
  stk.property("ADBE Vector Stroke Width").setValue(Math.max(4, t * 0.1));
  stk.property("ADBE Vector Stroke Line Cap").setValue(2);
  stk.property("ADBE Vector Stroke Line Join").setValue(2);
  var trim = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").addProperty("ADBE Vector Filter - Trim");
  var ini = e.inicio || 0;
  GAB.chaves(l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").property("ADBE Vector Filter - Trim").property("ADBE Vector Trim End"), [[ini + 0.15, 0], [ini + 0.55, 100]], 70);
  // no AE o 1º grupo da lista fica na FRENTE: o visto vai para cima do círculo
  l.property("ADBE Root Vectors Group").property("Visto").moveTo(1);
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  GAB.entrada(l, "pop", ini, 0.45);
  return l;
};

GAB.barra = function (comp, e) {
  var fundo = GAB.caixa(comp, { nome: (e.nome || "BARRA") + " trilho", w: e.w, h: e.h || 14, x: e.x, y: e.y, raio: (e.h || 14) / 2, cor: e.cor_trilho || "#FFFFFF", opacidade_fill: 18 });
  var l = GAB.caixa(comp, { nome: e.nome || "BARRA", w: e.w, h: e.h || 14, x: e.x, y: e.y, raio: (e.h || 14) / 2, cor: e.cor || "destaque" });
  var tr = l.property("ADBE Transform Group");
  tr.property("ADBE Anchor Point").setValue([-e.w / 2, 0]);
  tr.property("ADBE Position").setValue([e.x - e.w / 2, e.y]);
  var ini = e.inicio || 0, fim = (e.ate === undefined ? 100 : e.ate);
  GAB.chaves(tr.property("ADBE Scale"), [[ini, [0, 100, 100]], [ini + (e.dur || 1.2), [fim, 100, 100]]], 75);
  return [fundo, l];
};

// Contador: o número sobe de "Valor inicial" a "Valor final" (controles deslizantes na própria camada, editáveis no
// Controles de efeito do AE, sem mexer em expressão). Separador de milhar, prefixo e sufixo no próprio texto.
GAB.contador = function (comp, e) {
  var l = GAB.texto(comp, e);
  var ini = e.inicio || 0, dur = e.dur || 1.5;
  var fx = l.property("ADBE Effect Parade");
  fx.addProperty("ADBE Slider Control").name = "Valor inicial";
  l.property("ADBE Effect Parade").property("Valor inicial").property(1).setValue(e.de || 0);
  l.property("ADBE Effect Parade").addProperty("ADBE Slider Control").name = "Valor final";
  l.property("ADBE Effect Parade").property("Valor final").property(1).setValue(e.ate);
  var pre = (e.prefixo || "").replace(/"/g, '\\"'), suf = (e.sufixo || "").replace(/"/g, '\\"');
  var sep = e.separador === undefined ? "." : e.separador;
  l.property("ADBE Text Properties").property("ADBE Text Document").expression =
    "var a = effect(\"Valor inicial\")(1), b = effect(\"Valor final\")(1);\n" +
    "var v = ease(time, " + ini + ", " + (ini + dur) + ", a, b);\n" +
    "var n = Math.round(v).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, \"" + sep + "\");\n" +
    "\"" + pre + "\" + n + \"" + suf + "\";";
  return l;
};

GAB.imagem = function (comp, e) {
  var io = new ImportOptions(new File(e.arquivo));
  var item = app.project.importFile(io);
  item.parentFolder = GAB.pasta("Gab - midia");
  var l = comp.layers.add(item);
  l.name = e.nome || item.name;
  var tr = l.property("ADBE Transform Group");
  if (e.largura) { var s = 100 * e.largura / item.width; tr.property("ADBE Scale").setValue([s, s, 100]); }
  tr.property("ADBE Position").setValue([e.x, e.y]);
  return l;
};

// ---------------------------------------------------------------- motion a partir do plano (spec)
/* spec = { nome, w, h, fps, dur, transparente, cores: {principal, destaque, texto, fundo},
            elementos: [ { tipo: "texto"|"caixa"|"check"|"barra"|"contador"|"imagem"|"fundo", ...,
                           inicio, entrada, dur_entrada, saida_em, saida } ] }
   Ordem da lista = de baixo para cima (o primeiro fica no fundo). */
GAB.motion = function (spec) {
  app.beginUndoGroup("Gab: motion " + spec.nome);
  var antigo = GAB.comp(spec.nome);
  if (antigo) antigo.remove();
  var comp = app.project.items.addComp(spec.nome, spec.w || 1080, spec.h || 1920, 1, spec.dur || 5, spec.fps || 30);
  comp.parentFolder = GAB.pasta("Gab - motions");
  comp.bgColor = GAB.rgb((spec.cores && spec.cores.fundo) || "#000000");
  var criados = [];
  for (var i = 0; i < spec.elementos.length; i++) {
    var e = spec.elementos[i];
    if (e.x === undefined) e.x = comp.width / 2;
    if (e.y === undefined) e.y = comp.height / 2;
    var fn = { texto: GAB.texto, caixa: GAB.caixa, check: GAB.check, barra: GAB.barra, contador: GAB.contador, imagem: GAB.imagem, fundo: GAB.fundo }[e.tipo];
    if (!fn) throw new Error("tipo de elemento desconhecido: " + e.tipo);
    var r = fn(comp, e);
    var ls = r instanceof Array ? r : [r];
    for (var k = 0; k < ls.length; k++) {
      if (e.tipo !== "check" && e.tipo !== "barra") GAB.entrada(ls[k], e.entrada, e.inicio || 0, e.dur_entrada);
      if (e.saida_em !== undefined) GAB.saida(ls[k], e.saida || "fade", e.saida_em, e.dur_saida);
      ls[k].moveToBeginning();
      criados.push(ls[k].name);
    }
  }
  GAB.controles(comp, spec.cores || {}).moveToBeginning();
  app.endUndoGroup();
  return { comp: comp.name, camadas: criados.length, duracao: comp.duration };
};

// ---------------------------------------------------------------- saída: quadro, render, MOGRT, salvar
GAB.quadro = function (nome, t, arquivo) {
  var c = GAB.comp(nome);
  if (!c) throw new Error("comp não encontrada: " + nome);
  c.saveFrameToPng(t, new File(arquivo));
  return arquivo;
};

GAB.salvar = function () { app.project.save(); return app.project.file ? app.project.file.fsName : null; };

// Salva e fecha o AE sem nenhuma pergunta.
GAB.fechar = function () { if (app.project && app.project.file) app.project.save(); app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); app.quit(); return true; };

// Nome do modelo de saída com alfa (os nomes mudam com o idioma do AE).
GAB.modeloAlfa = function () {
  var rq = app.project.renderQueue, c = app.project.items.addComp("_gab_tmp", 16, 16, 1, 1, 30);
  var it = rq.items.add(c), om = it.outputModule(1), ts = om.templates, achado = null, i;
  for (i = 0; i < ts.length && !achado; i++) if (/alpha|alfa/i.test(ts[i]) && /(high|alta)/i.test(ts[i])) achado = ts[i];
  for (i = 0; i < ts.length && !achado; i++) if (/alpha|alfa/i.test(ts[i])) achado = ts[i];
  it.remove(); c.remove();
  return { modelo: achado, todos: ts };
};

// Render pela fila do AE. NUNCA renderizar dentro da chamada da ponte (rq.render() dentro do evalScript trava o AE,
// teste de 12/10/2026): a chamada só prepara a fila e AGENDA o render (app.scheduleTask), que roda depois que a
// resposta volta. O Python acompanha o arquivo e o status em GAB.statusRender().
GAB.render = function (nome, arquivo) {
  var c = GAB.comp(nome);
  if (!c) throw new Error("comp não encontrada: " + nome);
  var modelo = GAB.modeloAlfa().modelo;
  if (!modelo) throw new Error("nenhum modelo de saída com alfa neste AE");
  var rq = app.project.renderQueue, i;
  for (i = rq.numItems; i >= 1; i--) if (rq.item(i).status !== RQItemStatus.RENDERING) rq.item(i).remove();
  var it = rq.items.add(c), om = it.outputModule(1);
  om.applyTemplate(modelo);
  om.file = new File(arquivo);
  app.scheduleTask("app.project.renderQueue.render();", 300, false);
  return { arquivo: om.file.fsName, modelo: modelo };
};

GAB.statusRender = function () {
  var rq = app.project.renderQueue;
  if (!rq.numItems) return { estado: "vazio" };
  var it = rq.item(rq.numItems), m = { 2615: "pronto", 2614: "renderizando", 2613: "na fila", 2612: "parado", 2611: "erro", 2616: "falhou", 2617: "usuário parou" };
  return { estado: m[it.status] || String(it.status), rendering: rq.rendering, arquivo: it.outputModule(1).file ? it.outputModule(1).file.fsName : null };
};

// Expõe os textos no Essential Graphics e exporta .mogrt (para o Premiere: o texto fica editável lá).
GAB.mogrt = function (nome, arquivo) {
  var c = GAB.comp(nome);
  if (!c) throw new Error("comp não encontrada: " + nome);
  c.motionGraphicsTemplateName = nome;
  var n = 0;
  for (var i = 1; i <= c.numLayers; i++) {
    var l = c.layer(i);
    if (l instanceof TextLayer && !l.property("ADBE Text Properties").property("ADBE Text Document").expressionEnabled) {
      try { l.property("ADBE Text Properties").property("ADBE Text Document").addToMotionGraphicsTemplateAs(c, l.name); n++; } catch (e) {}
    }
  }
  var ctl = c.layer("CONTROLES");
  if (ctl) for (var j = 1; j <= ctl.property("ADBE Effect Parade").numProperties; j++) {
    var ef = ctl.property("ADBE Effect Parade").property(j);
    try { ef.property(1).addToMotionGraphicsTemplateAs(c, ef.name); n++; } catch (e2) {}
  }
  // `arquivo` é a PASTA de destino (o AE grava "<nome da comp>.mogrt" dentro dela). Exporta direto: o agendamento
  // (app.scheduleTask) não roda com o AE em segundo plano.
  c.exportAsMotionGraphicsTemplate(true, arquivo);
  return { pasta: arquivo, campos: n };
};

GAB.listar = function () {
  var r = [];
  for (var i = 1; i <= app.project.numItems; i++) {
    var it = app.project.item(i);
    if (it instanceof CompItem) r.push({ nome: it.name, dur: it.duration, w: it.width, h: it.height, camadas: it.numLayers });
  }
  return r;
};
