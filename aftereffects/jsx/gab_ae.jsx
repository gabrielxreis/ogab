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
  if (app.project && app.project.file && app.project.file.parent.exists) {
    try { app.project.close(CloseOptions.SAVE_CHANGES); } catch (x) { app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); }
  } else if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
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
    var ls = GAB.criar(comp, spec.elementos[i]);
    for (var k = 0; k < ls.length; k++) criados.push(ls[k]);
  }
  // ordem de empilhamento: o primeiro da lista fica embaixo
  for (var m = 0; m < criados.length; m++) criados[m].moveToBeginning();
  if (spec.saida_geral) {      // saída do motion inteiro (como o out() do HyperFrames)
    for (var q = 0; q < criados.length; q++) if (!criados[q].parent && criados[q].enabled && criados[q].name.indexOf("BG ") !== 0) GAB.animar(criados[q], [spec.saida_geral]);
  }
  GAB.controles(comp, spec.cores || {}).moveToBeginning();
  app.endUndoGroup();
  var nomes = []; for (var z = 0; z < criados.length; z++) nomes.push(criados[z].name);
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

// ==================================================================================================================
// ACABAMENTO (12/10/2026): mesma linguagem dos motions do HyperFrames, para o AE ficar igual ao original.
// Animações no formato do GSAP:  "anim": [ {"de": {...}, "t": 0.6, "dur": 0.5, "ease": "out"},
//                                         {"para": {...}, "t": 5.6, "dur": 0.45, "ease": "in"} ]
// chaves: x, y (deslocamento em px), opacidade (0-100), escala (%), escalaX (%), rot (graus)
// ease: "out" (power3.out), "in" (power2.in), "inout" (power2.inOut), "back" (back.out, com passada), "linear", "calmo"
// ==================================================================================================================

GAB.EASES = { out: [8, 92], "in": [92, 8], inout: [62, 62], calmo: [80, 80], linear: [0.1, 0.1], back: [8, 70] };

GAB.dims = function (prop) {
  var t = prop.propertyValueType;
  return t === PropertyValueType.TwoD ? 2 : (t === PropertyValueType.ThreeD ? 3 : 1);
};

GAB.easeEntre = function (prop, k0, k1, tipo) {
  var e = GAB.EASES[tipo] || GAB.EASES.calmo, n = GAB.dims(prop), i;
  var saida = [], chegada = [];
  for (i = 0; i < n; i++) { saida.push(new KeyframeEase(0, e[0])); chegada.push(new KeyframeEase(0, e[1])); }
  try {
    prop.setTemporalEaseAtKey(k0, prop.keyInTemporalEase(k0), saida);
    prop.setTemporalEaseAtKey(k1, chegada, prop.keyOutTemporalEase(k1));
  } catch (x) {}
};

// Anima uma propriedade de v0 a v1 entre t e t+dur com a curva pedida ("back" passa do ponto e volta).
GAB.tween = function (prop, t, dur, v0, v1, tipo) {
  if (tipo === "back") {
    var over;
    if (v1 instanceof Array) { over = []; for (var i = 0; i < v1.length; i++) over.push(v1[i] + (v1[i] - v0[i]) * 0.12); }
    else over = v1 + (v1 - v0) * 0.12;
    prop.setValueAtTime(t, v0); prop.setValueAtTime(t + dur * 0.62, over); prop.setValueAtTime(t + dur, v1);
    GAB.easeEntre(prop, prop.nearestKeyIndex(t), prop.nearestKeyIndex(t + dur * 0.62), "out");
    GAB.easeEntre(prop, prop.nearestKeyIndex(t + dur * 0.62), prop.nearestKeyIndex(t + dur), "inout");
    return;
  }
  prop.setValueAtTime(t, v0); prop.setValueAtTime(t + dur, v1);
  GAB.easeEntre(prop, prop.nearestKeyIndex(t), prop.nearestKeyIndex(t + dur), tipo);
};

// Aplica as animações. `alvoOpacidade` permite animar o slider de um grupo em vez da opacidade da camada.
GAB.animar = function (layer, anims, alvoOpacidade) {
  if (!anims) return;
  var tr = layer.property("ADBE Transform Group");
  var pos = tr.property("ADBE Position"), sc = tr.property("ADBE Scale"), rot = tr.property("ADBE Rotate Z");
  var op = alvoOpacidade || tr.property("ADBE Opacity");
  var base = { pos: pos.value, sc: sc.value, rot: rot.value, op: op.value };
  for (var i = 0; i < anims.length; i++) {
    var a = anims[i], d = a.de || a.para, ida = !!a.de, t = a.t || 0, dur = a.dur || 0.5, tipo = a.ease || "calmo";
    var par = function (alt, normal) { return ida ? [alt, normal] : [normal, alt]; };
    if (d.x !== undefined || d.y !== undefined) {
      var p2 = [base.pos[0] + (d.x || 0), base.pos[1] + (d.y || 0)];
      var pp = par(p2, base.pos); GAB.tween(pos, t, dur, pp[0], pp[1], tipo === "back" ? "out" : tipo);
    }
    if (d.escala !== undefined || d.escalaX !== undefined || d.escalaY !== undefined) {
      var s2 = [d.escalaX !== undefined ? d.escalaX : (d.escala !== undefined ? d.escala : base.sc[0]),
                d.escalaY !== undefined ? d.escalaY : (d.escala !== undefined ? d.escala : base.sc[1]), base.sc[2]];
      var ps = par(s2, base.sc); GAB.tween(sc, t, dur, ps[0], ps[1], tipo);
    }
    if (d.rot !== undefined) { var pr = par(d.rot, base.rot); GAB.tween(rot, t, dur, pr[0], pr[1], tipo); }
    if (d.opacidade !== undefined) { var po = par(d.opacidade, base.op); GAB.tween(op, t, dur, po[0], po[1], tipo === "back" ? "out" : tipo); }
  }
};

// Fundo com acabamento: degradê radial na cor do fundo (CONTROLES), grade dourada que desliza, dois brilhos que se
// movem devagar e vinheta. Tudo editável (camadas "BG ...").
GAB.fundoRico = function (comp, e) {
  var W = comp.width, H = comp.height, ls = [];
  var base = comp.layers.addSolid([0.04, 0.12, 0.23], "BG degradê", W, H, 1, comp.duration);
  var rp = base.property("ADBE Effect Parade").addProperty("ADBE Ramp");
  rp = base.property("ADBE Effect Parade").property(1);
  rp.property("ADBE Ramp-0001").setValue([W / 2, H * 0.479]);
  rp.property("ADBE Ramp-0003").setValue([W / 2, H * 0.5 + 1300]);
  try { rp.property("ADBE Ramp-0005").setValue(2); } catch (x) {}
  rp.property("ADBE Ramp-0002").expression = 'var c = thisComp.layer("CONTROLES").effect("Cor do fundo")(1); [Math.min(1, c[0]*1.75), Math.min(1, c[1]*1.68), Math.min(1, c[2]*1.6), 1]';
  rp.property("ADBE Ramp-0004").expression = 'var c = thisComp.layer("CONTROLES").effect("Cor do fundo")(1); [c[0]*0.45, c[1]*0.48, c[2]*0.5, 1]';
  ls.push(base);
  if (e.grade !== false) {
    var g = comp.layers.addSolid([0, 0, 0], "BG grade", W, H, 1, comp.duration);
    var ge = g.property("ADBE Effect Parade").addProperty("ADBE Grid");
    ge = g.property("ADBE Effect Parade").property(1);
    try { ge.property("ADBE Grid-0002").setValue(2); } catch (x1) {}          // tamanho pela largura
    try { ge.property("ADBE Grid-0004").setValue(60); } catch (x2) {}         // largura da célula
    try { ge.property("ADBE Grid-0006").setValue(1); } catch (x3) {}          // espessura
    try { ge.property("ADBE Grid-0001").expression = "var o = (time*10) % 60; [o, o]"; } catch (x4) {}
    try { ge.property("ADBE Grid-0010").expression = 'thisComp.layer("CONTROLES").effect("Cor de destaque")(1)'; } catch (x5) {}
    g.property("ADBE Transform Group").property("ADBE Opacity").setValue(e.grade_opacidade || 6);
    ls.push(g);
  }
  // brilho = degradê radial dourado -> preto em modo Tela (o preto não soma nada): igual ao radialGradient do original
  var brilho = function (nome, x, y, r, opac, expr) {
    var b = comp.layers.addSolid([0, 0, 0], nome, W, H, 1, comp.duration);
    b.property("ADBE Effect Parade").addProperty("ADBE Ramp");
    var rp2 = b.property("ADBE Effect Parade").property(1);
    try { rp2.property("ADBE Ramp-0005").setValue(2); } catch (x0) {}
    rp2.property("ADBE Ramp-0001").expression = expr;
    rp2.property("ADBE Ramp-0003").expression = "var p = effect(1)(1); [p[0] + " + r + ", p[1]]";
    rp2.property("ADBE Ramp-0002").expression = 'thisComp.layer("CONTROLES").effect("Cor de destaque")(1)';
    rp2.property("ADBE Ramp-0004").setValue([0, 0, 0, 1]);
    b.blendingMode = BlendingMode.SCREEN;
    b.property("ADBE Transform Group").property("ADBE Opacity").setValue(opac);
    return b;
  };
  if (e.brilhos !== false) {
    ls.push(brilho("BG brilho 1", 220, 560, 560, 13, "[220 + 70*Math.sin(time*0.5), 560 + 50*Math.cos(time*0.4)]"));
    ls.push(brilho("BG brilho 2", 880, 1380, 600, 10, "[880 - 60*Math.sin(time*0.45), 1380 + 60*Math.sin(time*0.6)]"));
  }
  if (e.vinheta !== false) {
    var vi = comp.layers.addSolid([0, 0, 0], "BG vinheta", W, H, 1, comp.duration);
    var m = vi.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var sh = new Shape(), rx = 700, ry = 700, k = 0.5523, cx = W / 2, cy = H / 2;
    sh.vertices = [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]];
    sh.inTangents = [[-rx * k, 0], [0, -ry * k], [rx * k, 0], [0, ry * k]];
    sh.outTangents = [[rx * k, 0], [0, ry * k], [-rx * k, 0], [0, -ry * k]];
    sh.closed = true;
    m = vi.property("ADBE Mask Parade").property(1);
    m.property("ADBE Mask Shape").setValue(sh);
    m.inverted = true;
    m.property("ADBE Mask Feather").setValue([550, 550]);
    vi.property("ADBE Transform Group").property("ADBE Opacity").setValue(55);
    ls.push(vi);
  }
  for (var i = 0; i < ls.length; i++) { ls[i].label = 16; }
  return ls;
};

// Cartão "vidro": cor com transparência, borda dourada fina, sombra longa e brilho que atravessa (track matte).
GAB.cartao = function (comp, e) {
  var card = GAB.caixa(comp, { nome: e.nome || "CARTAO", w: e.w, h: e.h, x: e.x, y: e.y, raio: e.raio === undefined ? 26 : e.raio,
                               cor: e.cor || "#0F284C", borda: e.borda || "destaque", borda_largura: e.borda_largura || 1.5,
                               opacidade_fill: e.opacidade_fill === undefined ? 93 : e.opacidade_fill });
  try {
    var s = card.property("ADBE Root Vectors Group").property("Caixa").property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke");
    s.property("ADBE Vector Stroke Opacity").setValue(e.borda_opacidade === undefined ? 45 : e.borda_opacidade);
  } catch (x) {}
  var ds = card.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
  ds = card.property("ADBE Effect Parade").property(1);
  ds.property("ADBE Drop Shadow-0002").setValue(140);   // opacidade (0-255) ~55%
  ds.property("ADBE Drop Shadow-0003").setValue(180);   // direção: para baixo
  ds.property("ADBE Drop Shadow-0004").setValue(30);    // distância
  ds.property("ADBE Drop Shadow-0005").setValue(70);    // suavidade
  var out = [card];
  if (e.brilho) {
    var matte = card.duplicate(); matte.name = card.name + " (máscara do brilho)";
    try { matte.property("ADBE Effect Parade").property(1).remove(); } catch (x2) {}
    matte.enabled = false;
    var sh = comp.layers.addShape(); sh.name = card.name + " brilho";
    sh.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Faixa";
    var v = sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vectors Group");
    v.addProperty("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").setValue([120, e.h * 1.4]);
    var f = sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    f.property("ADBE Vector Fill Color").setValue(GAB.rgb("#FFF0C8"));
    f.property("ADBE Vector Fill Opacity").setValue(35);
    try { sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vector Transform Group").property("ADBE Vector Skew").setValue(20); } catch (x3) {}
    var bl = sh.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
    sh.property("ADBE Effect Parade").property(1).property(1).setValue(40);
    try { sh.property("ADBE Effect Parade").property(1).property("ADBE Gaussian Blur 2-0002").setValue(2); } catch (x4) {}   // só horizontal
    var x0 = e.x - e.w / 2 - 160, x1 = x0 + 1500;
    var pos = sh.property("ADBE Transform Group").property("ADBE Position");
    pos.setValue([x0, e.y]);
    GAB.tween(pos, e.brilho.t, e.brilho.dur || 1.0, [x0, e.y], [x1, e.y], "inout");
    try { sh.setTrackMatte(matte, TrackMatteType.ALPHA); } catch (x5) { GAB.avisos.push("track matte do brilho: " + x5); }
    out.push(matte); out.push(sh);
  }
  return out;
};

// Divisor dourado: duas linhas e um losango no meio (o losango da logo).
GAB.divisor = function (comp, e) {
  var l = comp.layers.addShape(); l.name = e.nome || "DIVISOR";
  var raiz = l.property("ADBE Root Vectors Group"), lin = e.linha || 90, gap = e.gap || 14, d = e.losango || 12;
  var peca = function (nome, w, h, x, rot) {
    l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = nome;
    var g = l.property("ADBE Root Vectors Group").property(nome);
    g.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").setValue([w, h]);
    var f = l.property("ADBE Root Vectors Group").property(nome).property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    GAB.corDe(f.property("ADBE Vector Fill Color"), e.cor || "destaque");
    var tg = l.property("ADBE Root Vectors Group").property(nome).property("ADBE Vector Transform Group");
    tg.property("ADBE Vector Position").setValue([x, 0]);
    if (rot) tg.property("ADBE Vector Rotation").setValue(rot);
  };
  var off = gap + d * 0.7 + lin / 2;
  peca("Linha esq", lin, 2, -off, 0); peca("Losango", d, d, 0, 45); peca("Linha dir", lin, 2, off, 0);
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  return l;
};

// Check do HyperFrames: círculo dourado e o visto (path do SVG 24x24) em navy, aparece girando com passada.
GAB.checkRico = function (comp, e) {
  var t = e.tamanho || 54, pad = e.pad === undefined ? 12 : e.pad, k = (t - 2 * pad) / 24;
  var l = comp.layers.addShape(); l.name = e.nome || "CHECK";
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Visto";
  var vv = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group");
  var pth = vv.addProperty("ADBE Vector Shape - Group");
  var sh = new Shape(), pts = [[5, 12.5], [9.5, 17], [19, 7.5]];
  for (var i = 0; i < pts.length; i++) pts[i] = [(pts[i][0] - 12) * k, (pts[i][1] - 12) * k];
  sh.vertices = pts; sh.closed = false;
  pth.property("ADBE Vector Shape").setValue(sh);
  var stk = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
  GAB.corDe(stk.property("ADBE Vector Stroke Color"), e.cor_visto || "principal");
  stk.property("ADBE Vector Stroke Width").setValue(3 * k);
  stk.property("ADBE Vector Stroke Line Cap").setValue(2); stk.property("ADBE Vector Stroke Line Join").setValue(2);
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Circulo";
  var vc = l.property("ADBE Root Vectors Group").property("Circulo").property("ADBE Vectors Group");
  vc.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([t, t]);
  var fc = l.property("ADBE Root Vectors Group").property("Circulo").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
  GAB.corDe(fc.property("ADBE Vector Fill Color"), e.cor || "destaque");
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  return l;
};

// Grupo: um null no centro (posição/escala/rotação animadas) e uma "Opacidade do grupo" que multiplica a de cada filho.
GAB.grupo = function (comp, e) {
  var n = comp.layers.addNull(comp.duration);
  n.name = e.nome || "GRUPO"; n.label = 11;
  n.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  n.property("ADBE Effect Parade").addProperty("ADBE Slider Control").name = "Opacidade do grupo";
  var slider = n.property("ADBE Effect Parade").property("Opacidade do grupo").property(1);
  slider.setValue(100);
  var filhos = [];
  for (var i = 0; i < e.elementos.length; i++) {
    var ls = GAB.criar(comp, e.elementos[i]);
    for (var j = 0; j < ls.length; j++) {
      ls[j].parent = n;
      var op = ls[j].property("ADBE Transform Group").property("ADBE Opacity");
      if (ls[j].enabled) op.expression = 'value * thisComp.layer("' + n.name + '").effect("Opacidade do grupo")(1) / 100';
      filhos.push(ls[j]);
    }
  }
  GAB.animar(n, e.anim, slider);
  return [n].concat(filhos);
};

// Cria um elemento de qualquer tipo e aplica as animações dele. Devolve as camadas criadas.
GAB.criar = function (comp, e) {
  if (e.x === undefined) e.x = comp.width / 2;
  if (e.y === undefined) e.y = comp.height / 2;
  var fn = { texto: GAB.texto, caixa: GAB.caixa, check: GAB.check, barra: GAB.barra, contador: GAB.contador, imagem: GAB.imagem,
             fundo: GAB.fundo, fundo_rico: GAB.fundoRico, cartao: GAB.cartao, divisor: GAB.divisor, check_rico: GAB.checkRico,
             grupo: GAB.grupo }[e.tipo];
  if (!fn) throw new Error("tipo de elemento desconhecido: " + e.tipo);
  var r = fn(comp, e), ls = r instanceof Array ? r : [r];
  if (e.tipo !== "grupo") {
    for (var k = 0; k < ls.length; k++) {
      if (!ls[k].enabled && !ls[k].hasVideo) continue;
      if (e.anim) GAB.animar(ls[k], e.anim);
      else {      // formato antigo (entrada/saida_em)
        if (e.tipo !== "check" && e.tipo !== "barra" && e.entrada) GAB.entrada(ls[k], e.entrada, e.inicio || 0, e.dur_entrada);
        if (e.saida_em !== undefined) GAB.saida(ls[k], e.saida || "fade", e.saida_em, e.dur_saida);
      }
    }
  }
  return ls;
};
