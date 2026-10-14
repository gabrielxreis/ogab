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
  // Projeto do usuário é intocável: com alteração não salva, PARA e o Gab pergunta (o AE só tem um projeto aberto,
  // e fechar sem salvar já jogou fora o trabalho de um usuário). Sem alteração, fechar não perde nada.
  if (app.project && app.project.dirty) throw new Error("O projeto aberto no AE (" + (app.project.file ? app.project.file.name : "sem nome") + ") tem alterações não salvas. Pergunte ao usuário antes de abrir outro projeto.");
  if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
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
  // Âncora como o navegador: centro da LINHA da fonte (não do desenho das letras), para "g", "p", acentos não
  // deslocarem o texto. k = (ascendente - descendente) / 2 da fonte, em ems; à esquerda a âncora é a origem do texto.
  var k = { Inter: 0.3635, Cardo: 0.333, Poppins: 0.35, PlayfairDisplay: 0.4155, Lobster: 0.36 }[String(td.font).split("-")[0]] || 0.36;
  var ky = "-text.sourceText.style.fontSize * " + k;
  tr.property("ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width/2, " + ky + "]";
  if (e.alinhar === "esquerda") tr.property("ADBE Anchor Point").expression = "[0, " + ky + "]";
  if (e.alinhar === "direita") tr.property("ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width, " + ky + "]";
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
  if (spec.camera) GAB.camera(comp, spec.camera).moveToBeginning();
  if (spec.desfoque_movimento) { comp.motionBlur = true; for (var mb = 0; mb < criados.length; mb++) try { criados[mb].motionBlur = true; } catch (x4) {} }
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
GAB.fechar = function () {
  if (app.project && app.project.dirty && !app.project.file) throw new Error("Projeto sem nome com alterações não salvas no AE: pergunte ao usuário antes de fechar.");
  if (app.project && app.project.file) app.project.save();
  app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); app.quit(); return true;
};

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
    if (d.x !== undefined || d.y !== undefined || d.z !== undefined) {
      var p2 = [base.pos[0] + (d.x || 0), base.pos[1] + (d.y || 0)];
      if (base.pos.length > 2) p2.push(base.pos[2] + (d.z || 0));       // camada 3D
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
    var sh = new Shape(), rx = 975, ry = 975, k = 0.5523, cx = W / 2, cy = H / 2;
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
             grupo: GAB.grupo, linha_glow: GAB.linhaGlow, texto_esticar: GAB.textoEsticar, forma_morph: GAB.formaMorph }[e.tipo];
  if (!fn) throw new Error("tipo de elemento desconhecido: " + e.tipo);
  var r = fn(comp, e), ls = r instanceof Array ? r : [r];
  if (e.z !== undefined || e.rot3d) {        // camada 3D: profundidade e giros em X/Y (para a câmera e o parallax)
    for (var z = 0; z < ls.length; z++) {
      if (ls[z].nullLayer && e.tipo !== "grupo") continue;
      if (e.tipo === "grupo" && z > 0) { try { ls[z].threeDLayer = true; } catch (xg) {} continue; }   // filhos: 3D, z herdado do null
      try {
        ls[z].threeDLayer = true;
        var pz = ls[z].property("ADBE Transform Group").property("ADBE Position"), v0 = pz.value;
        if (!pz.numKeys) pz.setValue([v0[0], v0[1], e.z || 0]);
        if (e.rot3d) { ls[z].property("ADBE Transform Group").property("ADBE Rotate Y").setValue(e.rot3d[1] || 0);
                       ls[z].property("ADBE Transform Group").property("ADBE Rotate X").setValue(e.rot3d[0] || 0); }
      } catch (x3) {}
    }
  }
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

// ------------------------------------------------------------------ acabamento fino (2ª passada, 12/10/2026)
// Máscara de retângulo arredondado (para sólidos com degradê: vidro, círculo do check).
GAB.mascaraArredondada = function (layer, w, h, r) {
  var k = 0.5523 * r, x0 = 0, y0 = 0, x1 = w, y1 = h, sh = new Shape();
  sh.vertices = [[x0 + r, y0], [x1 - r, y0], [x1, y0 + r], [x1, y1 - r], [x1 - r, y1], [x0 + r, y1], [x0, y1 - r], [x0, y0 + r]];
  sh.inTangents = [[-k, 0], [0, 0], [0, -k], [0, 0], [k, 0], [0, 0], [0, k], [0, 0]];
  sh.outTangents = [[0, 0], [k, 0], [0, 0], [0, k], [0, 0], [-k, 0], [0, 0], [0, -k]];
  sh.closed = true;
  layer.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
  layer.property("ADBE Mask Parade").property(1).property("ADBE Mask Shape").setValue(sh);
};

// Sólido com degradê linear (cores em hex ou expressão) e máscara arredondada.
GAB.solidoDegrade = function (comp, nome, w, h, r, x, y, c0, c1, p0, p1, expr0, expr1) {
  var l = comp.layers.addSolid([0, 0, 0], nome, Math.round(w), Math.round(h), 1, comp.duration);
  GAB.mascaraArredondada(l, w, h, r);
  l.property("ADBE Effect Parade").addProperty("ADBE Ramp");
  var rp = l.property("ADBE Effect Parade").property(1);
  rp.property("ADBE Ramp-0001").setValue(p0); rp.property("ADBE Ramp-0003").setValue(p1);
  try { rp.property("ADBE Ramp-0005").setValue(1); } catch (x0) {}
  if (expr0) rp.property("ADBE Ramp-0002").expression = expr0; else rp.property("ADBE Ramp-0002").setValue(GAB.rgb(c0));
  if (expr1) rp.property("ADBE Ramp-0004").expression = expr1; else rp.property("ADBE Ramp-0004").setValue(GAB.rgb(c1));
  l.property("ADBE Transform Group").property("ADBE Position").setValue([x, y]);
  return l;
};

// Vidro do HyperFrames: linear-gradient(160deg, rgba(18,48,90,.92), rgba(11,31,58,.94)) + borda rgba(201,166,87,.45)
// + sombra 0 30px 70px rgba(0,0,0,.55). Preenchimento = sólido com degradê; borda = forma só com traço por cima.
GAB.cartao = function (comp, e) {
  var w = e.w, h = e.h, r = e.raio === undefined ? 26 : e.raio, nome = e.nome || "CARTAO";
  var dx = Math.tan(20 * Math.PI / 180) * h / 2;   // 160deg = quase vertical, puxado 20° para a direita
  var fill = GAB.solidoDegrade(comp, nome + " vidro", w, h, r, e.x, e.y, e.cor_topo || "#12305A", e.cor_base || "#0B1F3A",
                               [w / 2 - dx, 0], [w / 2 + dx, h]);
  fill.property("ADBE Transform Group").property("ADBE Opacity").setValue(e.opacidade_fill === undefined ? 93 : e.opacidade_fill);
  var ds = fill.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
  ds = fill.property("ADBE Effect Parade").property(2);
  ds.property("ADBE Drop Shadow-0002").setValue(140); ds.property("ADBE Drop Shadow-0003").setValue(180);
  ds.property("ADBE Drop Shadow-0004").setValue(30); ds.property("ADBE Drop Shadow-0005").setValue(70);
  var borda = comp.layers.addShape(); borda.name = nome + " borda";
  borda.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Borda";
  var v = borda.property("ADBE Root Vectors Group").property("Borda").property("ADBE Vectors Group");
  var rr = v.addProperty("ADBE Vector Shape - Rect");
  rr.property("ADBE Vector Rect Size").setValue([w - 1.5, h - 1.5]); rr.property("ADBE Vector Rect Roundness").setValue(r);
  var s = borda.property("ADBE Root Vectors Group").property("Borda").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
  GAB.corDe(s.property("ADBE Vector Stroke Color"), e.borda || "destaque");
  s.property("ADBE Vector Stroke Width").setValue(e.borda_largura || 1.5);
  s.property("ADBE Vector Stroke Opacity").setValue(e.borda_opacidade === undefined ? 45 : e.borda_opacidade);
  // filete de luz no topo (inset 0 1px rgba(255,255,255,.08))
  borda.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Luz";
  var vl = borda.property("ADBE Root Vectors Group").property("Luz").property("ADBE Vectors Group");
  vl.addProperty("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").setValue([w - 2 * r, 1]);
  var fl = borda.property("ADBE Root Vectors Group").property("Luz").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
  fl.property("ADBE Vector Fill Color").setValue([1, 1, 1]); fl.property("ADBE Vector Fill Opacity").setValue(8);
  borda.property("ADBE Root Vectors Group").property("Luz").property("ADBE Vector Transform Group").property("ADBE Vector Position").setValue([0, -h / 2 + 2]);
  borda.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  var out = [fill, borda];
  if (e.brilho) {
    var matte = fill.duplicate(); matte.name = nome + " (máscara do brilho)";
    try { matte.property("ADBE Effect Parade").property(2).remove(); } catch (x2) {}
    matte.enabled = false;
    var sh = comp.layers.addShape(); sh.name = nome + " brilho";
    sh.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Faixa";
    var vf = sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vectors Group");
    vf.addProperty("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").setValue([e.brilho.largura || 48, h * 1.4]);
    var ff = sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    ff.property("ADBE Vector Fill Color").setValue(GAB.rgb("#FFF0C8"));
    ff.property("ADBE Vector Fill Opacity").setValue(e.brilho.opacidade || 36);
    try { sh.property("ADBE Root Vectors Group").property("Faixa").property("ADBE Vector Transform Group").property("ADBE Vector Skew").setValue(20); } catch (x3) {}
    sh.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
    sh.property("ADBE Effect Parade").property(1).property(1).setValue(38);
    try { sh.property("ADBE Effect Parade").property(1).property("ADBE Gaussian Blur 2-0002").setValue(2); } catch (x4) {}
    var x0 = e.x - w / 2 - 160, x1 = x0 + 1500, pos = sh.property("ADBE Transform Group").property("ADBE Position");
    pos.setValue([x0, e.y]);
    GAB.tween(pos, e.brilho.t, e.brilho.dur || 1.0, [x0, e.y], [x1, e.y], "inout");
    try { sh.setTrackMatte(matte, TrackMatteType.ALPHA); } catch (x5) { GAB.avisos.push("track matte do brilho: " + x5); }
    out.push(matte); out.push(sh);
  }
  return out;
};

// Check: círculo em degradê dourado (linear-gradient 135deg #f1dfa6 -> #c9a657 -> #a8853a) + visto.
// estilo_visto: "cunha" (preenchido, como sai no HyperFrames dos motions da Calverstone) ou "traco".
GAB.checkRico = function (comp, e) {
  var t = e.tamanho || 54, pad = e.pad === undefined ? 12 : e.pad, k = (t - 2 * pad) / 24;
  var c = GAB.solidoDegrade(comp, (e.nome || "CHECK") + " círculo", t, t, t / 2, e.x, e.y, null, null, [0, 0], [t, t],
    'var c = thisComp.layer("CONTROLES").effect("Cor de destaque")(1); [Math.min(1, c[0]*1.2), Math.min(1, c[1]*1.33), Math.min(1, c[2]*1.88), 1]',
    'var c = thisComp.layer("CONTROLES").effect("Cor de destaque")(1); [c[0]*0.84, c[1]*0.80, c[2]*0.67, 1]');
  var l = comp.layers.addShape(); l.name = e.nome || "CHECK";
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Visto";
  var vv = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group");
  var pth = vv.addProperty("ADBE Vector Shape - Group");
  var sh = new Shape(), pts = [[5, 12.5], [9.5, 17], [19, 7.5]];
  for (var i = 0; i < pts.length; i++) pts[i] = [(pts[i][0] - 12) * k, (pts[i][1] - 12) * k];
  sh.vertices = pts;
  if ((e.estilo_visto || "cunha") === "cunha") {
    sh.closed = true; pth.property("ADBE Vector Shape").setValue(sh);
    var f = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    f.property("ADBE Vector Fill Color").setValue(GAB.rgb(e.cor_visto || "#000000"));
  } else {
    sh.closed = false; pth.property("ADBE Vector Shape").setValue(sh);
    var stk = l.property("ADBE Root Vectors Group").property("Visto").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
    GAB.corDe(stk.property("ADBE Vector Stroke Color"), e.cor_visto || "principal");
    stk.property("ADBE Vector Stroke Width").setValue(3 * k);
    stk.property("ADBE Vector Stroke Line Cap").setValue(2); stk.property("ADBE Vector Stroke Line Join").setValue(2);
  }
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  return [c, l];
};

// ==================================================================================================================
// TÉCNICAS DE MOTION (12/10/2026): glow lines, letter stretch, kinetic type, morphing shapes, 3D e câmera fluida.
// ==================================================================================================================

// Linha de luz: caminho que se desenha (Trim Paths) com brilho (Glow). "cometa": a cauda some atrás da ponta.
// e = {tipo:"linha_glow", pontos:[[x,y],...], curva:true, cor, largura, t, dur, cometa:true, glow:{raio, intensidade}}
GAB.linhaGlow = function (comp, e) {
  var l = comp.layers.addShape(); l.name = e.nome || "LINHA GLOW";
  l.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0]);   // pontos em coordenadas da comp (a forma conta a partir da posição da camada)
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Linha";
  var v = l.property("ADBE Root Vectors Group").property("Linha").property("ADBE Vectors Group");
  var pth = v.addProperty("ADBE Vector Shape - Group"), sh = new Shape(), pts = e.pontos, tin = [], tout = [];
  for (var i = 0; i < pts.length; i++) {
    if (e.curva !== false && i > 0 && i < pts.length - 1) {
      var dx = (pts[i + 1][0] - pts[i - 1][0]) / 4, dy = (pts[i + 1][1] - pts[i - 1][1]) / 4;
      tin.push([-dx, -dy]); tout.push([dx, dy]);
    } else { tin.push([0, 0]); tout.push([0, 0]); }
  }
  sh.vertices = pts; sh.inTangents = tin; sh.outTangents = tout; sh.closed = false;
  pth.property("ADBE Vector Shape").setValue(sh);
  var stk = l.property("ADBE Root Vectors Group").property("Linha").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
  GAB.corDe(stk.property("ADBE Vector Stroke Color"), e.cor || "destaque");
  stk.property("ADBE Vector Stroke Width").setValue(e.largura || 6);
  stk.property("ADBE Vector Stroke Line Cap").setValue(2);
  l.property("ADBE Root Vectors Group").property("Linha").property("ADBE Vectors Group").addProperty("ADBE Vector Filter - Trim");
  var trim = l.property("ADBE Root Vectors Group").property("Linha").property("ADBE Vectors Group").property("ADBE Vector Filter - Trim");
  var t = e.t || 0, dur = e.dur || 1.2;
  GAB.tween(trim.property("ADBE Vector Trim End"), t, dur, 0, 100, e.ease || "inout");
  if (e.cometa) GAB.tween(trim.property("ADBE Vector Trim Start"), t + dur * 0.35, dur, 0, 100, e.ease || "inout");
  l.property("ADBE Effect Parade").addProperty("ADBE Glo2");
  var g = l.property("ADBE Effect Parade").property(1), gl = e.glow || {};
  try { g.property("ADBE Glo2-0002").setValue(gl.limiar === undefined ? 55 : gl.limiar); } catch (x1) {}   // limite
  try { g.property("ADBE Glo2-0003").setValue(gl.raio || 28); } catch (x2) {}                              // raio
  try { g.property("ADBE Glo2-0004").setValue(gl.intensidade || 1.3); } catch (x3) {}                      // intensidade (alto estoura para branco)
  return l;
};

// Letter stretch: a palavra estica (escala horizontal por letra) numa onda que atravessa as letras e assenta.
// e = {tipo:"texto_esticar", texto, ..., t, dur, esticar: 320 (% de largura no pico), base: 1 letras | 3 palavras}
GAB.textoEsticar = function (comp, e) {
  var l = GAB.texto(comp, e);
  var anims = l.property("ADBE Text Properties").property("ADBE Text Animators");
  anims.addProperty("ADBE Text Animator").name = "Esticar";
  var an = function () { return l.property("ADBE Text Properties").property("ADBE Text Animators").property("Esticar"); };
  an().property("ADBE Text Animator Properties").addProperty("ADBE Text Scale 3D");
  an().property("ADBE Text Animator Properties").property("ADBE Text Scale 3D").setValue([e.esticar || 320, e.achatar || 70, 100]);
  an().property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity");
  an().property("ADBE Text Animator Properties").property("ADBE Text Opacity").setValue(0);
  an().property("ADBE Text Selectors").addProperty("ADBE Text Selector");
  var sel = an().property("ADBE Text Selectors").property(1);
  try { sel.property("ADBE Text Range Advanced").property("ADBE Text Range Type2").setValue(e.base || 1); } catch (x) {}
  try { sel.property("ADBE Text Range Advanced").property("ADBE Text Range Shape").setValue(2); } catch (x2) {}   // rampa: letras já passadas assentam
  try { sel.property("ADBE Text Range Advanced").property("ADBE Text Levels Max Ease").setValue(60); } catch (x3) {}
  var t = e.t || 0, dur = e.dur || 0.9;
  GAB.tween(sel.property("ADBE Text Percent Offset"), t, dur, -100, 100, e.ease || "out");
  return l;
};

// Morphing shape: uma forma que vira outra (círculo, quadrado, losango, estrela, triângulo), mesma contagem de pontos.
// e = {tipo:"forma_morph", formas:["circulo","quadrado","losango","estrela"], tempos:[0,0.8,1.6,2.4], raio, cor, girar}
GAB.verticesForma = function (forma, r, n) {
  var pts = [], i, a;
  for (i = 0; i < n; i++) {
    a = -Math.PI / 2 + 2 * Math.PI * i / n;
    var c = Math.cos(a), s = Math.sin(a), k = 1;
    if (forma === "quadrado") k = 1 / Math.max(Math.abs(c), Math.abs(s)) * 0.86;
    else if (forma === "losango") k = 1 / (Math.abs(c) + Math.abs(s)) * 1.15;
    else if (forma === "estrela") k = (i % 2 === 0) ? 1.15 : 0.5;
    else if (forma === "triangulo") { var seg = 2 * Math.PI / 3, ang = ((a + Math.PI / 2) % seg + seg) % seg - seg / 2; k = 0.62 / Math.cos(ang); }
    pts.push([c * r * k, s * r * k]);
  }
  return pts;
};
GAB.formaMorph = function (comp, e) {
  var n = 40, r = e.raio || 160;
  var l = comp.layers.addShape(); l.name = e.nome || "FORMA MORPH";
  l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").name = "Forma";
  var v = l.property("ADBE Root Vectors Group").property("Forma").property("ADBE Vectors Group");
  var pth = v.addProperty("ADBE Vector Shape - Group").property("ADBE Vector Shape");
  for (var i = 0; i < e.formas.length; i++) {
    var sh = new Shape(); sh.vertices = GAB.verticesForma(e.formas[i], r, n); sh.closed = true;
    pth.setValueAtTime(e.tempos[i], sh);
  }
  for (var k = 1; k < pth.numKeys; k++) GAB.easeEntre(pth, k, k + 1, e.ease || "inout");
  var f = l.property("ADBE Root Vectors Group").property("Forma").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
  GAB.corDe(f.property("ADBE Vector Fill Color"), e.cor || "destaque");
  if (e.contorno) {
    var st = l.property("ADBE Root Vectors Group").property("Forma").property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
    GAB.corDe(st.property("ADBE Vector Stroke Color"), e.contorno); st.property("ADBE Vector Stroke Width").setValue(4);
  }
  l.property("ADBE Transform Group").property("ADBE Position").setValue([e.x, e.y]);
  if (e.girar) {
    var rot = l.property("ADBE Transform Group").property("ADBE Rotate Z");
    GAB.tween(rot, e.tempos[0], e.tempos[e.tempos.length - 1] - e.tempos[0], 0, e.girar, "inout");
  }
  return l;
};

// 3D + câmera: elementos com "z" viram camadas 3D; a câmera desliza/orbita com curva suave (fluid camera / glide).
// spec.camera = {de: {x, y, z, ax, ay, az}, para: {...}, t, dur, ease, foco: true}  (a = ponto de interesse)
GAB.camera = function (comp, cam) {
  var W = comp.width, H = comp.height;
  var c = comp.layers.addCamera("CAMERA", [W / 2, H / 2]); c.label = 14;
  var zoom = cam.zoom || 1800;     // com a câmera em z = -zoom, o que está em z = 0 aparece em tamanho real
  try { c.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(zoom); } catch (xz) {}
  var de = cam.de || {}, para = cam.para || {};
  var p0 = [de.x === undefined ? W / 2 : de.x, de.y === undefined ? H / 2 : de.y, de.z === undefined ? -zoom : de.z];
  var p1 = [para.x === undefined ? p0[0] : para.x, para.y === undefined ? p0[1] : para.y, para.z === undefined ? p0[2] : para.z];
  var a0 = [de.ax === undefined ? W / 2 : de.ax, de.ay === undefined ? H / 2 : de.ay, de.az || 0];
  var a1 = [para.ax === undefined ? a0[0] : para.ax, para.ay === undefined ? a0[1] : para.ay, para.az === undefined ? a0[2] : para.az];
  var tr = c.property("ADBE Transform Group");
  GAB.tween(tr.property("ADBE Position"), cam.t || 0, cam.dur || comp.duration, p0, p1, cam.ease || "inout");
  GAB.tween(tr.property("ADBE Anchor Point"), cam.t || 0, cam.dur || comp.duration, a0, a1, cam.ease || "inout");
  if (cam.foco) {
    try {
      var op = c.property("ADBE Camera Options Group");
      op.property("ADBE Camera Depth of Field").setValue(1);
      op.property("ADBE Camera Focus Distance").expression = "length(transform.position, transform.pointOfInterest)";
      op.property("ADBE Camera Aperture").setValue(cam.abertura || 60);
    } catch (x) {}
  }
  return c;
};
