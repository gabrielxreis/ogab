// rick.jsx: funções de montagem do Rick (ExtendScript + Action Manager), testadas no Photoshop 2026.
// Uso: $.evalFile(".../rick.jsx"); Y.doc(1080,1440,"nome"); var g=Y.grupo("FUNDO"); Y.solido("#0B1F3A","COR",g); ...
// Coordenadas sempre em pixels do documento. Grupos: criar de BAIXO para CIMA (cada grupo novo vai para o topo).
var Y = (function () {
  function s(x) { return stringIDToTypeID(x); }
  var D = null;
  function rgb(hex) { var c = new SolidColor(); c.rgb.hexValue = hex.replace("#", ""); return c; }
  function rgbDesc(hex) { var c = rgb(hex), d = new ActionDescriptor(); d.putDouble(s("red"), c.rgb.red); d.putDouble(s("green"), c.rgb.green); d.putDouble(s("blue"), c.rgb.blue); return d; }
  function refAtiva() { var r = new ActionReference(); r.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); return r; }
  function px(v) { return Number(v); }
  function b(l) { var bb = l.bounds; return { x: bb[0].as("px"), y: bb[1].as("px"), w: bb[2].as("px") - bb[0].as("px"), h: bb[3].as("px") - bb[1].as("px") }; }
  function nomeia(l, nome) { if (nome) l.name = nome; return l; }
  function entra(l, g) { if (g) l.move(g, ElementPlacement.PLACEATBEGINNING); D.activeLayer = l; return l; }
  var MODOS = { normal: BlendMode.NORMAL, multiply: BlendMode.MULTIPLY, screen: BlendMode.SCREEN, overlay: BlendMode.OVERLAY,
    softLight: BlendMode.SOFTLIGHT, hardLight: BlendMode.HARDLIGHT, color: BlendMode.COLORBLEND, colorDodge: BlendMode.COLORDODGE,
    linearDodge: BlendMode.LINEARDODGE, linearLight: BlendMode.LINEARLIGHT, lighten: BlendMode.LIGHTEN, darken: BlendMode.DARKEN,
    luminosity: BlendMode.LUMINOSITY, difference: BlendMode.DIFFERENCE, vividLight: BlendMode.VIVIDLIGHT };

  var Y = {};
  Y.doc = function (w, h, nome, fundo) {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS; app.preferences.typeUnits = TypeUnits.PIXELS;
    D = app.documents.add(w, h, 72, nome || "rick", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
    D.activeLayer.name = "base";
    return D;
  };
  Y.usar = function (doc) { D = doc || app.activeDocument; app.preferences.rulerUnits = Units.PIXELS; app.preferences.typeUnits = TypeUnits.PIXELS; return D; };
  Y.grupo = function (nome, pai) {
    var g = pai ? pai.layerSets.add() : D.layerSets.add(); g.name = nome;
    if (!pai) g.move(D, ElementPlacement.PLACEATBEGINNING);
    return g;
  };
  Y.misturar = function (l, modo, opacidade) { if (modo) l.blendMode = MODOS[modo]; if (opacidade !== undefined) l.opacity = opacidade; return l; };

  // ---------- cor ----------
  Y.solido = function (hex, nome, g, modo, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(hex));
    u.putObject(s("type"), s("solidColorLayer"), f); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome); Y.misturar(l, modo, op); return entra(l, g);
  };
  // paradas: [["#000000",0,100],["#000000",100,0]] (cor, posição %, opacidade %). angulo: 90 = de baixo para cima.
  Y.degrade = function (paradas, angulo, nome, g, modo, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), gd = new ActionDescriptor();
    gd.putUnitDouble(s("angle"), s("angleUnit"), angulo === undefined ? 90 : angulo); gd.putEnumerated(s("type"), s("gradientType"), s("linear"));
    var gr = new ActionDescriptor(); gr.putString(s("name"), "rick"); gr.putEnumerated(s("gradientForm"), s("gradientForm"), s("customStops")); gr.putDouble(s("interfaceIconFrameDimmed"), 4096);
    var cl = new ActionList(), tl = new ActionList();
    for (var i = 0; i < paradas.length; i++) {
      var p = paradas[i], loc = Math.round(p[1] / 100 * 4096);
      var c = new ActionDescriptor(); c.putObject(s("color"), s("RGBColor"), rgbDesc(p[0])); c.putEnumerated(s("type"), s("colorStopType"), s("userStop"));
      c.putInteger(s("location"), loc); c.putInteger(s("midpoint"), 50); cl.putObject(s("colorStop"), c);
      var t = new ActionDescriptor(); t.putUnitDouble(s("opacity"), s("percentUnit"), p.length > 2 ? p[2] : 100); t.putInteger(s("location"), loc); t.putInteger(s("midpoint"), 50); tl.putObject(s("transferSpec"), t);
    }
    gr.putList(s("colors"), cl); gr.putList(s("transparency"), tl); gd.putObject(s("gradient"), s("gradientClassEvent"), gr);
    u.putObject(s("type"), s("gradientLayer"), gd); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome); Y.misturar(l, modo, op); return entra(l, g);
  };

  // ---------- imagem ----------
  // caixa {x,y,w,h}; ajuste: "cobrir" (preenche a caixa, corta), "conter" (cabe inteira), "largura", "altura".
  // alinhar: "centro" (padrão), "base" (encosta embaixo), "topo".
  Y.colocar = function (caminho, nome, g, caixa, ajuste, alinhar) {
    var a = new ActionDescriptor(); a.putPath(s("null"), new File(caminho));
    a.putEnumerated(s("freeTransformCenterState"), s("quadCenterState"), s("QCSAverage")); executeAction(s("placeEvent"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome);
    if (caixa) Y.encaixar(l, caixa, ajuste || "cobrir", alinhar || "centro");
    return entra(l, g);
  };
  Y.encaixar = function (l, c, ajuste, alinhar) {
    var bb = b(l), sx = c.w / bb.w, sy = c.h / bb.h, e;
    if (ajuste === "conter") e = Math.min(sx, sy); else if (ajuste === "largura") e = sx; else if (ajuste === "altura") e = sy; else e = Math.max(sx, sy);
    l.resize(e * 100, e * 100, AnchorPosition.MIDDLECENTER);
    bb = b(l);
    var dx = c.x + (c.w - bb.w) / 2 - bb.x, dy;
    if (alinhar === "base") dy = c.y + c.h - bb.h - bb.y; else if (alinhar === "topo") dy = c.y - bb.y; else dy = c.y + (c.h - bb.h) / 2 - bb.y;
    l.translate(dx, dy); return l;
  };
  // Caixa do que APARECE da camada (máscara aplicada): layer.bounds ignora a máscara, então um objeto recortado
  // "mede" a foto inteira. Carrega a máscara (ou a transparência) como seleção e lê a caixa.
  Y.caixaVisivel = function (l) {
    D.activeLayer = l; var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("channel"), s("selection")); a.putReference(s("null"), r);
    var c = new ActionReference();
    try { c.putEnumerated(s("channel"), s("channel"), s("mask")); a.putReference(s("to"), c); executeAction(s("set"), a, DialogModes.NO); }
    catch (e) { a = new ActionDescriptor(); a.putReference(s("null"), r); c = new ActionReference(); c.putEnumerated(s("channel"), s("channel"), s("transparencyEnum")); a.putReference(s("to"), c); executeAction(s("set"), a, DialogModes.NO); }
    var bb = D.selection.bounds; D.selection.deselect();
    var x = bb[0].as("px"), y = bb[1].as("px"); return { x: x, y: y, w: bb[2].as("px") - x, h: bb[3].as("px") - y };
  };
  // Encaixa pelo que aparece (objeto recortado) numa caixa medida na referência (medir_objeto.py --ps).
  Y.encaixarVisivel = function (l, c, ajuste, alinhar) {
    var v = Y.caixaVisivel(l), sx = c.w / v.w, sy = c.h / v.h, e;
    if (ajuste === "largura") e = sx; else if (ajuste === "altura") e = sy; else if (ajuste === "cobrir") e = Math.max(sx, sy); else e = Math.min(sx, sy);
    l.resize(e * 100, e * 100, AnchorPosition.MIDDLECENTER); v = Y.caixaVisivel(l);
    var dy = alinhar === "base" ? c.y + c.h - v.h - v.y : (alinhar === "topo" ? c.y - v.y : c.y + (c.h - v.h) / 2 - v.y);
    l.translate(c.x + (c.w - v.w) / 2 - v.x, dy); return l;
  };
  // Alinha um OBJETO da foto com o da referência: gira pela diferença de ângulo, escala pela altura da caixa e
  // centraliza. ref = saída do medir_objeto.py --ps na referência {x,y,w,h,angulo}; anguloFoto = mesmo comando
  // rodado no arquivo da foto. Mede a caixa por seleção de IA na própria camada (prompt em inglês).
  Y.alinharObjeto = function (l, prompt, ref, anguloFoto) {
    var giro = (ref.angulo || 0) - (anguloFoto || 0);
    if (Math.abs(giro) > 0.2) l.rotate(giro, AnchorPosition.MIDDLECENTER);
    function caixa() { Y.selecionarPorPrompt(l, prompt); var bb = D.selection.bounds; D.selection.deselect();
      var x = bb[0].as("px"), y = bb[1].as("px"); return { x: x, y: y, w: bb[2].as("px") - x, h: bb[3].as("px") - y }; }
    var c = caixa(), e = ref.h / c.h;
    if (Math.abs(e - 1) > 0.003) { l.resize(e * 100, e * 100, AnchorPosition.MIDDLECENTER); c = caixa(); }
    l.translate(ref.x + ref.w / 2 - (c.x + c.w / 2), ref.y + ref.h / 2 - (c.y + c.h / 2));
    return l;
  };
  // Objeto RETANGULAR (celular, tela, quadro): leva o centro da borda de cima do objeto da foto ao ponto da
  // referência, com o mesmo ângulo e a mesma largura. foto/ref = "retangulo" do medir_objeto.py --ps ... --retangulo
  // (foto medida no arquivo original, em pixels nativos: passar --largura <largura nativa>); larguraNativa = px da foto.
  Y.alinharRetangulo = function (l, foto, ref, larguraNativa) {
    var bb = b(l), s0 = bb.w / larguraNativa, s = ref.largura / foto.largura;
    l.resize(s / s0 * 100, s / s0 * 100, AnchorPosition.MIDDLECENTER); bb = b(l);
    var px = bb.x + foto.topo[0] * s, py = bb.y + foto.topo[1] * s, cx = bb.x + bb.w / 2, cy = bb.y + bb.h / 2;
    var d = ref.angulo - foto.angulo, r = d * Math.PI / 180;
    if (Math.abs(d) > 0.05) l.rotate(d, AnchorPosition.MIDDLECENTER);
    var qx = cx + (px - cx) * Math.cos(r) - (py - cy) * Math.sin(r), qy = cy + (px - cx) * Math.sin(r) + (py - cy) * Math.cos(r);
    l.translate(ref.topo[0] - qx, ref.topo[1] - qy); return l;
  };
  // Retângulo arredondado girado (celular/tela desenhados em vetor). c = centro {x,y}; ang em graus (horário).
  Y.retanguloGirado = function (c, w, h, raio, cor, ang, nome, g) {
    var l = Y.retangulo({ x: c.x - w / 2, y: c.y - h / 2, w: w, h: h, raio: raio, cor: cor, nome: nome }, g);
    if (ang) l.rotate(ang, AnchorPosition.MIDDLECENTER); return l;
  };
  // Recorta a pessoa/objeto principal (Selecionar assunto, IA local) e cria máscara na camada.
  Y.recortar = function (l) {
    D.activeLayer = l; var a = new ActionDescriptor(); a.putBoolean(s("sampleAllLayers"), false); executeAction(s("autoCutout"), a, DialogModes.NO);
    Y.refinarSelecao(Y.REFINO);
    var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask"));
    m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealSelection")); executeAction(s("make"), m, DialogModes.NO);
    D.selection.deselect(); return l;
  };
  // "Pessoa na frente do título": duplica a foto já recortada para outro grupo (acima do texto).
  Y.duplicarPara = function (l, nome, g) { var c = l.duplicate(); c.name = nome; return entra(c, g); };
  // Corta seco a camada abaixo de y (na máscara): recorte de pessoa atrás de púlpito/mesa leva o resto do corpo
  // sem o móvel e sobra um pedaço solto. Ponha y logo abaixo das mãos, de preferência escondido atrás do título.
  Y.cortarAbaixo = function (l, y, x1, x2) {
    var W_ = D.width.as("px"), H_ = D.height.as("px"); x1 = x1 || 0; x2 = x2 || W_;
    D.activeLayer = l; var tem = false;
    try { var r0 = new ActionReference(); r0.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); tem = executeActionGet(r0).getBoolean(s("hasUserMask")); } catch (e) {}
    if (!tem) { var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask")); m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealAll")); executeAction(s("make"), m, DialogModes.NO); }
    var a = new ActionDescriptor(), rm = new ActionReference(); rm.putEnumerated(s("channel"), s("channel"), s("mask")); a.putReference(s("null"), rm); a.putBoolean(s("makeVisible"), false); executeAction(s("select"), a, DialogModes.NO);
    D.selection.select([[x1, y], [x2, y], [x2, H_], [x1, H_]]); D.selection.fill(rgb("#000000")); D.selection.deselect();
    var b2 = new ActionDescriptor(), rc = new ActionReference(); rc.putEnumerated(s("channel"), s("channel"), s("RGB")); b2.putReference(s("null"), rc); executeAction(s("select"), b2, DialogModes.NO);
    return l;
  };
  // Esconde a parte de baixo de uma camada com máscara de degradê (para a foto "sumir" no fundo). de/ate em px de y.
  Y.sumirEmbaixo = function (l, yInicio, yFim) {
    D.activeLayer = l;
    var temMascara = false; try { var r0 = new ActionReference(); r0.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); temMascara = executeActionGet(r0).getBoolean(s("hasUserMask")); } catch (e) {}
    if (!temMascara) { var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask")); m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealAll")); executeAction(s("make"), m, DialogModes.NO); }
    // seleciona o canal da máscara e pinta um degradê branco->preto multiplicando (intersecção) via seleção com difusão
    var sel = [[0, yFim], [D.width.as("px"), yFim], [D.width.as("px"), D.height.as("px")], [0, D.height.as("px")]];
    D.selection.select(sel, SelectionType.REPLACE, (yFim - yInicio) / 2, false);
    var rc = new ActionReference(); rc.putEnumerated(s("channel"), s("channel"), s("mask")); var sc = new ActionDescriptor(); sc.putReference(s("null"), rc); sc.putBoolean(s("makeVisible"), false); executeAction(s("select"), sc, DialogModes.NO);
    D.selection.fill(rgb("#000000")); D.selection.deselect();
    var rl = new ActionReference(); rl.putEnumerated(s("channel"), s("channel"), s("RGB")); var sl = new ActionDescriptor(); sl.putReference(s("null"), rl); executeAction(s("select"), sl, DialogModes.NO);
    return l;
  };

  // ---------- texto ----------
  // o: {txt, fonte, px, cor, x, y, ancora:"tl|tc|tr|bl|bc", tracking, entrelinha, caixa:{w,h}, alinh:"esq|centro|dir", caps,
  //     faixas:[{de,ate,fonte,px,cor}]}  (faixas = trechos com estilo diferente dentro da mesma camada)
  Y.texto = function (o, g) {
    var l = D.artLayers.add(); l.kind = LayerKind.TEXT;   // (dentro de prancheta isto falha: montar em grupo e converter no fim, Y.virarPrancheta)
    var ti = l.textItem;
    if (o.caixa) { ti.kind = TextType.PARAGRAPHTEXT; ti.width = o.caixa.w; ti.height = o.caixa.h; }
    ti.contents = o.txt.replace(/\n/g, "\r"); ti.font = o.fonte; ti.size = o.px; ti.color = rgb(o.cor || "#FFFFFF");
    ti.justification = o.alinh === "centro" ? Justification.CENTER : (o.alinh === "dir" ? Justification.RIGHT : Justification.LEFT);
    if (o.tracking !== undefined) ti.tracking = o.tracking;
    if (o.entrelinha) { ti.useAutoLeading = false; ti.leading = o.entrelinha; }
    if (o.caps) ti.capitalization = TextCase.ALLCAPS;
    ti.antiAliasMethod = AntiAlias.SMOOTH; try { ti.autoKerning = AutoKernType.OPTICAL; } catch (e) {}
    nomeia(l, o.nome || o.txt.split("\n")[0].substr(0, 30));
    if (o.faixas) Y.faixas(l, o.faixas);
    if (o.caixa) { ti.position = [o.x, o.y]; }
    else if (o.alvo) {
      Y.encaixarTexto(l, o.alvo);
      // fonte errada = espaçamento absurdo para caber na largura medida (letras grudadas ou espalhadas): testa as
      // alternativas (o.fontes) e fica com a que pede o espaçamento mais natural
      var trk = l.textItem.tracking;
      // bloco medido pelo corpo da maiúscula (alvo.ch1): tracking largo é do design (créditos espaçados), só letra grudada conta
      if (o.fontes && o.fontes.length && (trk < -40 || (trk > 160 && !o.alvo.ch1))) {
        var melhor = { f: o.fonte, t: trk };
        for (var q = 0; q < o.fontes.length; q++) { if (o.fontes[q] === o.fonte) continue;
          try { l.textItem.font = o.fontes[q]; l.textItem.tracking = 0; if (o.faixas) Y.faixas(l, o.faixas); Y.encaixarTexto(l, o.alvo);
            var tq = l.textItem.tracking; if (Math.abs(tq - 40) < Math.abs(melhor.t - 40)) melhor = { f: o.fontes[q], t: tq }; } catch (eF) {} }
        l.textItem.font = melhor.f; l.textItem.tracking = 0; if (o.faixas) Y.faixas(l, o.faixas); Y.encaixarTexto(l, o.alvo);
        Y.TROCAS = (Y.TROCAS || []).concat([o.nome + ": " + o.fonte + " -> " + melhor.f + " (tracking " + Math.round(trk) + " -> " + Math.round(l.textItem.tracking) + ")"]);
      }
    }
    else Y.ancorar(l, o.x, o.y, o.ancora || "tl");
    return entra(l, g);
  };
  // Encaixa um texto numa caixa medida na referência (medir_texto.py): ajusta o tamanho até a LARGURA (ou altura,
  // com alvo.por:"altura") bater e coloca a caixa dos pixels exatamente em x,y. Não distorce a fonte.
  // Encaixa um texto numa caixa medida na referência (medir_texto.py) para ficar IDÊNTICO:
  //  1) tamanho pela ALTURA da caixa; 2) tracking calculado para a LARGURA bater; 3) posiciona a caixa dos pixels em x,y.
  // alvo.por: "largura" = só tamanho pela largura (sem mexer no tracking), "altura" = só tamanho pela altura.
  Y.encaixarTexto = function (l, alvo) {
    var ti = l.textItem, i, bb, f;
    function px() { return ti.size.as ? ti.size.as("px") : Number(ti.size); }
    var porLarg = alvo.por === "largura";
    // CAIXA ALTA com corpo medido (cy/ch): mede pela altura do "H" numa cópia, sem acento/cedilha atrapalhar
    // minúsculas com xh medido: mede pelo "x" (acento, cedilha, ascendente e descendente não atrapalham)
    var temMin = /[a-zà-ÿ]/.test(ti.contents), caps = alvo.h >= 34 && ((alvo.ch && !temMin) || (alvo.xh && temMin)), sonda = null;   // < 22 px: caixa inteira
    var letra = temMin ? "x" : "H", altAlvo = temMin ? alvo.xh : alvo.ch, topoAlvo = temMin ? alvo.xy : alvo.cy;
    function altura() {
      if (!caps) return b(l);
      if (sonda) sonda.remove();
      sonda = l.duplicate(); sonda.textItem.contents = letra; return b(sonda);
    }
    if (alvo.ch1) {   // bloco de várias linhas em caixa alta: tamanho pelo "H" da 1ª linha, largura pelo tracking (linha mais longa)
      var sd = l.duplicate(); sd.textItem.contents = "H";
      for (i = 0; i < 5; i++) { f = alvo.ch1 / b(sd).h; if (Math.abs(f - 1) < 0.002) break; ti.size = px() * f; sd.textItem.size = ti.size; }
      sd.remove();
      var lns = ti.contents.split(/[\r\n]/), nm = 1; for (i = 0; i < lns.length; i++) nm = Math.max(nm, lns[i].length - 1);
      for (i = 0; i < 4; i++) { bb = b(l); var dw2 = alvo.w - bb.w; if (Math.abs(dw2) < 1) break; ti.tracking = Math.round(ti.tracking + dw2 / (nm * px() / 1000)); }
      porLarg = true; i = 99;
    }
    for (i = (alvo.ch1 ? 99 : 0); i < 5; i++) {
      bb = altura(); f = porLarg ? alvo.w / b(l).w : (caps ? altAlvo : alvo.h) / bb.h;
      if (Math.abs(f - 1) < 0.002) break;
      ti.size = px() * f;
      if (ti.useAutoLeading === false) { try { ti.leading = ti.leading.as("px") * f; } catch (e) {} }
    }
    if (!porLarg && alvo.por !== "altura" && alvo.w) {
      var n = Math.max(1, ti.contents.replace(/[\r\n]/g, "").length - 1);
      for (i = 0; i < 4; i++) {
        bb = b(l); var dw = alvo.w - bb.w; if (Math.abs(dw) < 1) break;
        ti.tracking = Math.round(ti.tracking + dw / (n * px() / 1000));
      }
    }
    // alvo.passo = distância medida entre o topo de linhas iguais (ex.: 1ª e 3ª linha / 2) -> entrelinha exata
    if (alvo.passo) {
      ti.useAutoLeading = false; ti.leading = alvo.passo;
      var linhas = ti.contents.split(/[\r\n]/);
      if (linhas.length > 1) for (i = 0; i < 4; i++) {  // mede o passo real: fundo do bloco - fundo da última linha sozinha
        var so = l.duplicate(); so.textItem.contents = linhas[linhas.length - 1];
        var real = (b(l).y + b(l).h - (b(so).y + b(so).h)) / (linhas.length - 1); so.remove();
        if (Math.abs(real - alvo.passo) < 0.3) break;
        ti.leading = ti.leading.as("px") * alvo.passo / real;
      }
    }
    bb = b(l); var topo = caps ? altura().y : bb.y, alvoY = caps ? topoAlvo : alvo.y;
    if (sonda) sonda.remove();
    l.translate(alvo.x - bb.x, alvoY - topo); return l;
  };
  Y.ancorar = function (l, x, y, anc) {
    var bb = b(l), tx = x - bb.x, ty = y - bb.y;
    if (anc.charAt(1) === "c") tx = x - bb.w / 2 - bb.x; if (anc.charAt(1) === "r") tx = x - bb.w - bb.x;
    if (anc.charAt(0) === "b") ty = y - bb.h - bb.y; if (anc.charAt(0) === "m") ty = y - bb.h / 2 - bb.y;
    l.translate(tx, ty); return l;
  };
  Y.faixas = function (l, fx) {
    D.activeLayer = l;
    var tk = executeActionGet(refAtiva()).getObjectValue(s("textKey")), base = tk.getList(s("textStyleRange")).getObjectValue(0).getObjectValue(s("textStyle"));
    var total = l.textItem.contents.length, nl = new ActionList(), marc = [], i, k, fonteBase = l.textItem.font;
    // preenche os buracos entre faixas com o estilo base
    var lista = [], pos = 0; fx.sort(function (a, c) { return a.de - c.de; });
    for (i = 0; i < fx.length; i++) { if (fx[i].de > pos) lista.push({ de: pos, ate: fx[i].de }); lista.push(fx[i]); pos = fx[i].ate; }
    if (pos < total) lista.push({ de: pos, ate: total });
    for (i = 0; i < lista.length; i++) {
      var f = lista[i], r = new ActionDescriptor(); r.putInteger(s("from"), f.de); r.putInteger(s("to"), f.ate);
      var st = new ActionDescriptor();
      for (k = 0; k < base.count; k++) { var key = base.getKey(k); try { var t = base.getType(key);
        if (t == DescValueType.STRINGTYPE) st.putString(key, base.getString(key)); else if (t == DescValueType.UNITDOUBLE) st.putUnitDouble(key, base.getUnitDoubleType(key), base.getUnitDoubleValue(key));
        else if (t == DescValueType.DOUBLETYPE) st.putDouble(key, base.getDouble(key)); else if (t == DescValueType.INTEGERTYPE) st.putInteger(key, base.getInteger(key));
        else if (t == DescValueType.BOOLEANTYPE) st.putBoolean(key, base.getBoolean(key)); else if (t == DescValueType.ENUMERATEDTYPE) st.putEnumerated(key, base.getEnumerationType(key), base.getEnumerationValue(key));
        else if (t == DescValueType.OBJECTTYPE) st.putObject(key, base.getObjectType(key), base.getObjectValue(key)); } catch (e) {} }
      // trecho sem fonte própria (vão entre faixas) leva a fonte da camada: sem isso o Photoshop caía na Myriad Pro
      st.putString(s("fontPostScriptName"), f.fonte || fonteBase);
      if (f.px) { st.putUnitDouble(s("size"), s("pixelsUnit"), f.px); }
      if (f.cor) st.putObject(s("color"), s("RGBColor"), rgbDesc(f.cor));
      if (f.tracking !== undefined) st.putInteger(s("tracking"), f.tracking);
      r.putObject(s("textStyle"), s("textStyle"), st); nl.putObject(s("textStyleRange"), r);
    }
    tk.putList(s("textStyleRange"), nl);
    var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); a.putObject(s("to"), s("textLayer"), tk); executeAction(s("set"), a, DialogModes.NO);
    return l;
  };

  // ---------- formas ----------
  // o: {x,y,w,h,cor,raio,nome, contorno:{px,cor}, so_contorno:true}
  Y.retangulo = function (o, g) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#FFFFFF")); u.putObject(s("type"), s("solidColorLayer"), f);
    var sh = new ActionDescriptor(); sh.putInteger(s("unitValueQuadVersion"), 1);
    sh.putUnitDouble(s("top"), s("pixelsUnit"), o.y); sh.putUnitDouble(s("left"), s("pixelsUnit"), o.x); sh.putUnitDouble(s("bottom"), s("pixelsUnit"), o.y + o.h); sh.putUnitDouble(s("right"), s("pixelsUnit"), o.x + o.w);
    var rr = o.raio || 0; sh.putUnitDouble(s("topRight"), s("pixelsUnit"), rr); sh.putUnitDouble(s("topLeft"), s("pixelsUnit"), rr); sh.putUnitDouble(s("bottomLeft"), s("pixelsUnit"), rr); sh.putUnitDouble(s("bottomRight"), s("pixelsUnit"), rr);
    u.putObject(s("shape"), s("rectangle"), sh); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, o.nome || "RETANGULO");
    if (o.contorno) Y.efeitos(l, { traco: { px: o.contorno.px, cor: o.contorno.cor, posicao: "inside" } });
    if (o.so_contorno) l.fillOpacity = 0;
    if (o.opacidade !== undefined) l.opacity = o.opacidade;
    return entra(l, g);
  };
  Y.elipse = function (o, g) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#FFFFFF")); u.putObject(s("type"), s("solidColorLayer"), f);
    var sh = new ActionDescriptor(); sh.putUnitDouble(s("top"), s("pixelsUnit"), o.y); sh.putUnitDouble(s("left"), s("pixelsUnit"), o.x); sh.putUnitDouble(s("bottom"), s("pixelsUnit"), o.y + o.h); sh.putUnitDouble(s("right"), s("pixelsUnit"), o.x + o.w);
    u.putObject(s("shape"), s("ellipse"), sh); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, o.nome || "ELIPSE");
    if (o.contorno) Y.efeitos(l, { traco: { px: o.contorno.px, cor: o.contorno.cor, posicao: "inside" } });
    if (o.so_contorno) l.fillOpacity = 0;
    return entra(l, g);
  };

  // ---------- estilos de camada ----------
  // fx: {sombra:{cor,op,dist,desfoque,angulo}, traco:{px,cor,posicao:"outside|inside|center"}, cor:{cor,op}, brilho:{cor,op,tam},
  //      brilhoInterno:{cor,op,tam,contrair,centro,modo}, sombraInterna:{cor,op,dist,desfoque,angulo}, chanfro:{estilo,tecnica,prof,tam,suave,angulo,altitude,luz,sombra},
  //      degrade:{paradas:[[hex,loc]],angulo,tipo:"linear|radial",escala,modo,op}, cetim:{cor,op,angulo,dist,desfoque,inverter,modo}}
  Y.efeitos = function (l, fx) {
    D.activeLayer = l;
    var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("property"), s("layerEffects")); r.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); a.putReference(s("null"), r);
    var e = new ActionDescriptor(); e.putUnitDouble(s("scale"), s("percentUnit"), 100);
    if (fx.sombra) { var o = fx.sombra, d = new ActionDescriptor(); d.putBoolean(s("enabled"), true); d.putEnumerated(s("mode"), s("blendMode"), s("multiply"));
      d.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#000000")); d.putUnitDouble(s("opacity"), s("percentUnit"), o.op || 50);
      d.putUnitDouble(s("distance"), s("pixelsUnit"), o.dist || 10); d.putUnitDouble(s("blur"), s("pixelsUnit"), o.desfoque || 30); d.putUnitDouble(s("localLightingAngle"), s("angleUnit"), o.angulo || 90); d.putBoolean(s("useGlobalAngle"), false);
      e.putObject(s("dropShadow"), s("dropShadow"), d); }
    if (fx.traco) { var t = fx.traco, st = new ActionDescriptor(); st.putBoolean(s("enabled"), true);
      st.putEnumerated(s("style"), s("frameStyle"), s(t.posicao === "inside" ? "insetFrame" : (t.posicao === "center" ? "centeredFrame" : "outsetFrame")));
      st.putEnumerated(s("paintType"), s("frameFill"), s("solidColor")); st.putEnumerated(s("mode"), s("blendMode"), s("normal"));
      st.putUnitDouble(s("opacity"), s("percentUnit"), 100); st.putUnitDouble(s("size"), s("pixelsUnit"), t.px || 2); st.putObject(s("color"), s("RGBColor"), rgbDesc(t.cor || "#FFFFFF"));
      e.putObject(s("frameFX"), s("frameFX"), st); }
    if (fx.cor) { var c = new ActionDescriptor(); c.putBoolean(s("enabled"), true); c.putEnumerated(s("mode"), s("blendMode"), s("normal"));
      c.putObject(s("color"), s("RGBColor"), rgbDesc(fx.cor.cor)); c.putUnitDouble(s("opacity"), s("percentUnit"), fx.cor.op || 100); e.putObject(s("solidFill"), s("solidFill"), c); }
    if (fx.brilho) { var gl = new ActionDescriptor(); gl.putBoolean(s("enabled"), true); gl.putEnumerated(s("mode"), s("blendMode"), s("screen"));
      gl.putObject(s("color"), s("RGBColor"), rgbDesc(fx.brilho.cor)); gl.putUnitDouble(s("opacity"), s("percentUnit"), fx.brilho.op || 60);
      gl.putUnitDouble(s("blur"), s("pixelsUnit"), fx.brilho.tam || 40); gl.putUnitDouble(s("chokeMatte"), s("percentUnit"), 0); e.putObject(s("outerGlow"), s("outerGlow"), gl); }
    // novos (16/10, chaves tiradas do dicionário de terminologia do binário)
    if (fx.brilhoInterno) { var ig = fx.brilhoInterno, di = new ActionDescriptor(); di.putBoolean(s("enabled"), true); di.putEnumerated(s("mode"), s("blendMode"), s(ig.modo || "screen"));
      di.putObject(s("color"), s("RGBColor"), rgbDesc(ig.cor)); di.putUnitDouble(s("opacity"), s("percentUnit"), ig.op || 75); di.putUnitDouble(s("chokeMatte"), s("pixelsUnit"), ig.contrair || 0);
      di.putUnitDouble(s("blur"), s("pixelsUnit"), ig.tam || 10); di.putEnumerated(s("innerGlowSource"), s("innerGlowSourceType"), s(ig.centro ? "centerGlow" : "edgeGlow")); e.putObject(s("innerGlow"), s("innerGlow"), di); }
    if (fx.sombraInterna) { var is_ = fx.sombraInterna, ds = new ActionDescriptor(); ds.putBoolean(s("enabled"), true); ds.putEnumerated(s("mode"), s("blendMode"), s(is_.modo || "multiply"));
      ds.putObject(s("color"), s("RGBColor"), rgbDesc(is_.cor || "#000000")); ds.putUnitDouble(s("opacity"), s("percentUnit"), is_.op || 50); ds.putBoolean(s("useGlobalAngle"), false);
      ds.putUnitDouble(s("localLightingAngle"), s("angleUnit"), is_.angulo === undefined ? 90 : is_.angulo); ds.putUnitDouble(s("distance"), s("pixelsUnit"), is_.dist || 5);
      ds.putUnitDouble(s("chokeMatte"), s("pixelsUnit"), 0); ds.putUnitDouble(s("blur"), s("pixelsUnit"), is_.desfoque || 10); e.putObject(s("innerShadow"), s("innerShadow"), ds); }
    if (fx.chanfro) { var bv = fx.chanfro, db = new ActionDescriptor(); db.putBoolean(s("enabled"), true);
      db.putEnumerated(s("bevelStyle"), s("bevelEmbossStyle"), s(bv.estilo || "innerBevel")); db.putEnumerated(s("bevelTechnique"), s("bevelTechnique"), s(bv.tecnica || "softMatte"));
      db.putUnitDouble(s("strengthRatio"), s("percentUnit"), bv.prof || 100); db.putEnumerated(s("bevelDirection"), s("bevelEmbossStampStyle"), s("stampIn"));
      db.putUnitDouble(s("blur"), s("pixelsUnit"), bv.tam || 8); db.putUnitDouble(s("softness"), s("pixelsUnit"), bv.suave || 0);
      db.putBoolean(s("useGlobalAngle"), false); db.putUnitDouble(s("localLightingAngle"), s("angleUnit"), bv.angulo || 120); db.putUnitDouble(s("localLightingAltitude"), s("angleUnit"), bv.altitude || 30);
      db.putEnumerated(s("highlightMode"), s("blendMode"), s("screen")); db.putObject(s("highlightColor"), s("RGBColor"), rgbDesc(bv.luz || "#FFFFFF")); db.putUnitDouble(s("highlightOpacity"), s("percentUnit"), bv.opLuz || 75);
      db.putEnumerated(s("shadowMode"), s("blendMode"), s("multiply")); db.putObject(s("shadowColor"), s("RGBColor"), rgbDesc(bv.sombra || "#000000")); db.putUnitDouble(s("shadowOpacity"), s("percentUnit"), bv.opSombra || 75);
      db.putBoolean(s("antialiasGloss"), true); e.putObject(s("bevelEmboss"), s("bevelEmboss"), db); }
    if (fx.degrade) { var gf = fx.degrade, dg = new ActionDescriptor(); dg.putBoolean(s("enabled"), true); dg.putEnumerated(s("mode"), s("blendMode"), s(gf.modo || "normal"));
      dg.putUnitDouble(s("opacity"), s("percentUnit"), gf.op || 100); dg.putObject(s("gradient"), s("gradientClassEvent"), gradDesc(gf.paradas));
      dg.putUnitDouble(s("angle"), s("angleUnit"), gf.angulo === undefined ? 90 : gf.angulo); dg.putEnumerated(s("type"), s("gradientType"), s(gf.tipo || "linear"));
      dg.putBoolean(s("reverse"), false); dg.putBoolean(s("align"), true); dg.putUnitDouble(s("scale"), s("percentUnit"), gf.escala || 100); e.putObject(s("gradientFill"), s("gradientFill"), dg); }
    if (fx.cetim) { var ct = fx.cetim, dc = new ActionDescriptor(); dc.putBoolean(s("enabled"), true); dc.putEnumerated(s("mode"), s("blendMode"), s(ct.modo || "multiply"));
      dc.putObject(s("color"), s("RGBColor"), rgbDesc(ct.cor || "#000000")); dc.putUnitDouble(s("opacity"), s("percentUnit"), ct.op || 50); dc.putUnitDouble(s("localLightingAngle"), s("angleUnit"), ct.angulo || 19);
      dc.putUnitDouble(s("distance"), s("pixelsUnit"), ct.dist || 11); dc.putUnitDouble(s("blur"), s("pixelsUnit"), ct.desfoque || 14); dc.putBoolean(s("invert"), !!ct.inverter); e.putObject(s("chromeFX"), s("chromeFX"), dc); }
    a.putObject(s("to"), s("layerEffects"), e); executeAction(s("set"), a, DialogModes.NO); return l;
  };

  // ---------- acabamento ----------
  Y.grao = function (g, quantidade, opacidade) {
    var l = D.artLayers.add(); l.name = "GRANULACAO"; D.selection.selectAll(); D.selection.fill(rgb("#808080")); D.selection.deselect();
    l.applyAddNoise(quantidade || 12, NoiseDistribution.GAUSSIAN, true); l.blendMode = BlendMode.OVERLAY; l.opacity = opacidade === undefined ? 35 : opacidade;
    return entra(l, g);
  };
  // pontos: [[0,0],[64,50],[192,205],[255,255]] (canal composto) OU por canal {rgb:[..], r:[..], g:[..], b:[..]}
  // (saída do casar_cor.py: casa a cor de uma foto/objeto com a referência).
  Y.curvas = function (pontos, nome, g, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("adjustmentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), cv = new ActionDescriptor(); cv.putEnumerated(s("presetKind"), s("presetKindType"), s("presetKindCustom"));
    var lst = new ActionList(), canais = (pontos instanceof Array) ? { rgb: pontos } : pontos;
    var nomes = { rgb: "composite", r: "red", g: "green", b: "blue" };
    for (var k in nomes) { if (!canais[k]) continue;
      var ch = new ActionDescriptor(), rc = new ActionReference(); rc.putEnumerated(s("channel"), s("channel"), s(nomes[k])); ch.putReference(s("channel"), rc);
      var pl = new ActionList(), pts = canais[k];
      for (var i = 0; i < pts.length; i++) { var p = new ActionDescriptor(); p.putDouble(s("horizontal"), pts[i][0]); p.putDouble(s("vertical"), pts[i][1]); pl.putObject(s("paint"), p); }
      ch.putList(s("curve"), pl); lst.putObject(s("curvesAdjustment"), ch); }
    cv.putList(s("adjustment"), lst);
    u.putObject(s("type"), s("curves"), cv); a.putObject(s("using"), s("adjustmentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome || "CURVAS"); if (op !== undefined) l.opacity = op; return entra(l, g);
  };
  // Mapa de degradê (unifica a cor da peça inteira). paradas: [["#0B0710",0],["#C9A04A",100]] (sombras -> luzes)
  function gradDesc(paradas) {   // paradas: [["#hex", local 0-100], ...]
    var gr = new ActionDescriptor(); gr.putString(s("name"), "rick"); gr.putEnumerated(s("gradientForm"), s("gradientForm"), s("customStops")); gr.putDouble(s("interfaceIconFrameDimmed"), 4096);
    var cl = new ActionList(), tl = new ActionList();
    for (var i = 0; i < paradas.length; i++) { var p = paradas[i], loc = Math.round(p[1] / 100 * 4096);
      var c = new ActionDescriptor(); c.putObject(s("color"), s("RGBColor"), rgbDesc(p[0])); c.putEnumerated(s("type"), s("colorStopType"), s("userStop")); c.putInteger(s("location"), loc); c.putInteger(s("midpoint"), 50); cl.putObject(s("colorStop"), c);
      var tt = new ActionDescriptor(); tt.putUnitDouble(s("opacity"), s("percentUnit"), 100); tt.putInteger(s("location"), loc); tt.putInteger(s("midpoint"), 50); tl.putObject(s("transferSpec"), tt); }
    gr.putList(s("colors"), cl); gr.putList(s("transparency"), tl); return gr;
  }
  Y.mapaDegrade = function (paradas, nome, g, modo, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("adjustmentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), gm = new ActionDescriptor(), gr = new ActionDescriptor();
    gr.putString(s("name"), "rick"); gr.putEnumerated(s("gradientForm"), s("gradientForm"), s("customStops")); gr.putDouble(s("interfaceIconFrameDimmed"), 4096);
    var cl = new ActionList(), tl = new ActionList();
    for (var i = 0; i < paradas.length; i++) { var p = paradas[i], loc = Math.round(p[1] / 100 * 4096);
      var c = new ActionDescriptor(); c.putObject(s("color"), s("RGBColor"), rgbDesc(p[0])); c.putEnumerated(s("type"), s("colorStopType"), s("userStop")); c.putInteger(s("location"), loc); c.putInteger(s("midpoint"), 50); cl.putObject(s("colorStop"), c);
      var t = new ActionDescriptor(); t.putUnitDouble(s("opacity"), s("percentUnit"), 100); t.putInteger(s("location"), loc); t.putInteger(s("midpoint"), 50); tl.putObject(s("transferSpec"), t); }
    gr.putList(s("colors"), cl); gr.putList(s("transparency"), tl); gm.putObject(s("gradient"), s("gradientClassEvent"), gr);
    u.putObject(s("type"), s("gradientMapClass"), gm); a.putObject(s("using"), s("adjustmentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome || "MAPA DE DEGRADE"); Y.misturar(l, modo, op); return entra(l, g);
  };
  // Desfoque gaussiano em smart object (vira filtro inteligente, editável). Bom para fundo com profundidade.
  Y.desfocar = function (l, raio) { D.activeLayer = l; l.applyGaussianBlur(raio); return l; };
  // Vinheta: degradê radial escuro nas bordas (camada de preenchimento editável)
  Y.vinheta = function (hex, op, g) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), gd = new ActionDescriptor(); gd.putEnumerated(s("type"), s("gradientType"), s("radial")); gd.putUnitDouble(s("scale"), s("percentUnit"), 150);
    var gr = new ActionDescriptor(); gr.putString(s("name"), "vinheta"); gr.putEnumerated(s("gradientForm"), s("gradientForm"), s("customStops")); gr.putDouble(s("interfaceIconFrameDimmed"), 4096);
    var cl = new ActionList(), tl = new ActionList(), pp = [[0, 0], [55, 0], [100, 100]];
    for (var i = 0; i < pp.length; i++) { var loc = Math.round(pp[i][0] / 100 * 4096);
      var c = new ActionDescriptor(); c.putObject(s("color"), s("RGBColor"), rgbDesc(hex || "#000000")); c.putEnumerated(s("type"), s("colorStopType"), s("userStop")); c.putInteger(s("location"), loc); c.putInteger(s("midpoint"), 50); cl.putObject(s("colorStop"), c);
      var t = new ActionDescriptor(); t.putUnitDouble(s("opacity"), s("percentUnit"), pp[i][1]); t.putInteger(s("location"), loc); t.putInteger(s("midpoint"), 50); tl.putObject(s("transferSpec"), t); }
    gr.putList(s("colors"), cl); gr.putList(s("transparency"), tl); gd.putObject(s("gradient"), s("gradientClassEvent"), gr);
    u.putObject(s("type"), s("gradientLayer"), gd); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; l.name = "VINHETA"; l.opacity = op === undefined ? 70 : op; return entra(l, g);
  };
  // Integra a pessoa ao ambiente: cor do ambiente na pele (Luz suave) + luz de borda (Tela) recortadas na foto.
  // lado: "esq"|"dir" = de onde vem a luz de borda.
  Y.integrar = function (foto, g, corAmbiente, corLuz, lado) {
    var amb = Y.solido(corAmbiente, "COR DO AMBIENTE (" + foto.name + ")", g, "softLight", 45); amb.move(foto, ElementPlacement.PLACEBEFORE); Y.recorte(amb);
    var bb = b(foto), ang = lado === "esq" ? 0 : 180;
    var luz = Y.degrade([[corLuz, 0, 100], [corLuz, 35, 0]], ang, "LUZ DE BORDA (" + foto.name + ")", g, "screen", 55); luz.move(amb, ElementPlacement.PLACEBEFORE); Y.recorte(luz);
    return foto;
  };
  // Linha com trechos MARCADOS (caixa colorida atrás de palavras), estilo "SEU [CURRÍCULO MÉDICO]".
  // partes: [{t:"SEU ", fonte:"Owners-Light"}, {t:"CURRÍCULO MÉDICO", fonte:"Owners-Bold", marca:"#FF5A12"}]
  // o: {px, cor, x (centro ou esquerda), y (topo), alinh:"centro"|"esq", pad:[horizontal, vertical], tracking}
  Y.linhaMarcada = function (partes, o, g) {
    var gl = g ? g.layerSets.add() : D.layerSets.add(); gl.name = o.nome || "LINHA";
    var camadas = [], larg = 0, alt = 0, i, pad = o.pad || [12, 6];
    for (i = 0; i < partes.length; i++) {
      var p = partes[i];
      var l = Y.texto({ txt: p.t.replace(/ $/, " "), nome: p.t, fonte: p.fonte || o.fonte, px: o.px, cor: p.cor || o.cor || "#FFFFFF", tracking: o.tracking || 0, x: 0, y: 0 }, gl);
      var bb = b(l); camadas.push({ l: l, w: bb.w, h: bb.h, p: p }); larg += bb.w + (p.marca ? 2 * pad[0] : 0); alt = Math.max(alt, bb.h);
    }
    var x0 = o.alinh === "esq" ? o.x : o.x - larg / 2;
    for (i = 0; i < camadas.length; i++) {
      var c = camadas[i], dx = c.p.marca ? pad[0] : 0;
      Y.ancorar(c.l, x0 + dx, o.y + (alt - c.h), "tl");
      if (c.p.marca) {
        var r = Y.retangulo({ x: x0, y: o.y - pad[1], w: c.w + 2 * pad[0], h: alt + 2 * pad[1], cor: c.p.marca, nome: "MARCA " + c.p.t }, gl);
        r.move(c.l, ElementPlacement.PLACEAFTER);
      }
      x0 += c.w + 2 * dx;
    }
    return gl;
  };
  // Caminho (linha poligonal) com traço e brilho: conectores de infográfico. pts: [[x,y],[x,y],...]
  Y.caminho = function (pts, hex, largura, g, brilho, nome) {
    var l = D.artLayers.add(); l.name = nome || "LINHA";
    var arr = [];
    for (var i = 0; i < pts.length; i++) { var p = new PathPointInfo(); p.kind = PointKind.CORNERPOINT; p.anchor = [pts[i][0], pts[i][1]]; p.leftDirection = p.anchor; p.rightDirection = p.anchor; arr.push(p); }
    var sp = new SubPathInfo(); sp.closed = false; sp.operation = ShapeOperation.SHAPEXOR; sp.entireSubPath = arr;
    var path = D.pathItems.add("rick_tmp", [sp]);
    app.foregroundColor = rgb(hex);
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("paintbrushTool")); a.putReference(s("null"), r); executeAction(s("select"), a, DialogModes.NO);
    var b1 = new ActionDescriptor(), r1 = new ActionReference(); r1.putEnumerated(s("brush"), s("ordinal"), s("targetEnum")); b1.putReference(s("null"), r1);
    var bd = new ActionDescriptor(); bd.putUnitDouble(s("diameter"), s("pixelsUnit"), largura || 3); bd.putUnitDouble(s("hardness"), s("percentUnit"), 100); b1.putObject(s("to"), s("brush"), bd); executeAction(s("set"), b1, DialogModes.NO);
    D.activeLayer = l; path.strokePath(ToolType.BRUSH, false); path.remove();
    if (brilho !== false) Y.efeitos(l, { brilho: { cor: hex, op: 85, tam: 14 } });
    return entra(l, g);
  };
  // Círculo cheio com brilho (ponto de conexão do infográfico)
  Y.ponto = function (cx, cy, r, hex, g) { var e = Y.elipse({ x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, cor: hex, nome: "PONTO" }, g); Y.efeitos(e, { brilho: { cor: hex, op: 90, tam: 12 } }); return e; };
  // Brilho radial suave (luz atrás do objeto/pessoa): elipse com difusão grande em camada própria.
  Y.brilho = function (cx, cy, rx, ry, hex, op, g, modo) {
    var l = D.artLayers.add(); l.name = "BRILHO " + hex;
    D.selection.select([[cx - rx, cy - ry], [cx + rx, cy - ry], [cx + rx, cy + ry], [cx - rx, cy + ry]], SelectionType.REPLACE, 0, true);
    var a = new ActionDescriptor(); var r = new ActionReference(); r.putProperty(s("channel"), s("selection")); a.putReference(s("null"), r);
    var e = new ActionDescriptor(); e.putUnitDouble(s("top"), s("pixelsUnit"), cy - ry); e.putUnitDouble(s("left"), s("pixelsUnit"), cx - rx); e.putUnitDouble(s("bottom"), s("pixelsUnit"), cy + ry); e.putUnitDouble(s("right"), s("pixelsUnit"), cx + rx);
    a.putObject(s("to"), s("ellipse"), e); a.putBoolean(s("antiAlias"), true); executeAction(s("set"), a, DialogModes.NO);
    D.selection.feather(Math.min(rx, ry) * 0.6); D.selection.fill(rgb(hex)); D.selection.deselect();
    l.blendMode = MODOS[modo || "screen"]; l.opacity = op === undefined ? 80 : op; return entra(l, g);
  };
  // Partículas de brilho (pontinhos com glow) numa área, semente fixa para repetir igual.
  Y.particulas = function (n, area, hex, g, semente) {
    var l = D.artLayers.add(); l.name = "PARTICULAS"; var sd = semente || 7;
    function rnd() { sd = (sd * 9301 + 49297) % 233280; return sd / 233280; }
    for (var i = 0; i < n; i++) {
      var x = area.x + rnd() * area.w, y = area.y + rnd() * area.h, r = 1.2 + rnd() * 2.8;
      D.selection.select([[x - r, y - r], [x + r, y - r], [x + r, y + r], [x - r, y + r]], i ? SelectionType.EXTEND : SelectionType.REPLACE, 0, true);
    }
    D.selection.fill(rgb(hex)); D.selection.deselect();
    Y.efeitos(l, { brilho: { cor: hex, op: 75, tam: 10 } }); l.opacity = 70; return entra(l, g);
  };
  // ---------- máscaras e "texto atrás" ----------
  // Ferramenta nativa do agente do Photoshop (precisa de jsx/agente_lib.jsx na mesma pasta).
  function agente(nome, params) {
    if (typeof ferramenta === "undefined") $.evalFile(File($.fileName).path + "/agente_lib.jsx");
    return eval("(" + ferramenta(nome, params) + ")");
  }
  // Seleciona por descrição ("o celular", "a pessoa da esquerda", "o céu") só na camada ativa.
  // prompt pode ser lista: ["o celular", "a mão"] = soma as seleções (um objeto composto raramente vem inteiro num prompt só).
  Y.selecionarPorPrompt = function (l, prompt) {
    D.activeLayer = l;
    var doc = agente("application_list_open_documents", {}).data.front_doc_id;
    var lista = (prompt instanceof Array) ? prompt : [prompt];
    for (var i = 0; i < lista.length; i++) {
      var r = agente("selection_select_by_prompt", { doc_id: doc, prompt: lista[i], sample_all_layers: false, selection_mode: i ? "add" : "replace" });
      if (r.status !== "success") throw new Error("seleção por prompt falhou (" + lista[i] + "): " + r.data);
    }
    return true;
  };
  // Máscara a partir da seleção atual (ou cria seleção por prompt antes). inverter: esconde o objeto em vez de mostrar.
  // Máscara por IA. prompt: texto ou lista (inglês funciona melhor); vazio = Selecionar assunto.
  // o (opcional): {inverter:true, fonte:<camada onde SELECIONAR (ex.: a foto) quando a máscara vai em outra camada>,
  //                estrito:true (não cai no Selecionar assunto se o prompt falhar), contrair:px, refino:{...}|false}
  Y.mascara = function (l, prompt, o) {
    if (o === true) o = { inverter: true }; o = o || {};
    var fonte = o.fonte || l, ok = false;
    if (prompt) { try { Y.selecionarPorPrompt(fonte, prompt); ok = true; } catch (e) { if (o.estrito || o.fonte) throw e; $.writeln("prompt falhou, usando Selecionar assunto: " + e); } }
    if (!ok) { D.activeLayer = fonte; var a = new ActionDescriptor(); a.putBoolean(s("sampleAllLayers"), false); executeAction(s("autoCutout"), a, DialogModes.NO); }
    if (o.refino !== false) Y.refinarSelecao(o.refino || Y.REFINO);
    if (o.contrair) D.selection.contract(o.contrair);
    if (o.inverter) D.selection.invert();
    D.activeLayer = l; Y.tirarMascara(l);
    var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask"));
    m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealSelection")); executeAction(s("make"), m, DialogModes.NO);
    D.selection.deselect(); return l;
  };
  // Camadas de preenchimento (degradê, cor sólida) já nascem com máscara: apaga a existente antes de criar outra.
  Y.tirarMascara = function (l) {
    D.activeLayer = l; var tem = false;
    try { var r0 = new ActionReference(); r0.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); tem = executeActionGet(r0).getBoolean(s("hasUserMask")); } catch (e) {}
    if (!tem) return l;
    var sel = null; try { sel = D.selection.bounds; } catch (e) {}
    if (sel) D.selection.store(D.channels.add()); // guarda a seleção (delete pode limpar)
    var a = new ActionDescriptor(), r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask")); a.putReference(s("null"), r); a.putBoolean(s("apply"), false);
    executeAction(s("delete"), a, DialogModes.NO);
    if (sel) { var ch = D.channels[D.channels.length - 1]; D.selection.load(ch); ch.remove(); D.activeLayer = l; }
    return l;
  };
  // Selecionar e Mascarar sobre a seleção atual: borda limpa (sem franja da cor do fundo, sem serrilhado).
  // r: {raio:3, suavizar:2, difusao:0.6, contraste:15, deslocar:-20 (% para dentro), profundo:true}
  Y.REFINO = { raio: 3, suavizar: 2, difusao: 0.6, contraste: 15, deslocar: -20, profundo: true };
  Y.refinarSelecao = function (r) {
    r = r || Y.REFINO;
    try {
      var a = new ActionDescriptor();
      a.putBoolean(s("smartBrushUseSmartRadius"), true); a.putBoolean(s("smartBrushUseDeepMatte"), r.profundo !== false);
      a.putUnitDouble(s("smartBrushRadius"), s("pixelsUnit"), r.raio); a.putInteger(s("smartBrushSmooth"), r.suavizar);
      a.putUnitDouble(s("smartBrushFeather"), s("pixelsUnit"), r.difusao); a.putUnitDouble(s("smartBrushContrast"), s("percentUnit"), r.contraste);
      a.putUnitDouble(s("smartBrushShiftEdge"), s("percentUnit"), r.deslocar); a.putBoolean(s("sampleAllLayers"), false);
      a.putBoolean(s("smartBrushDecontaminate"), false);
      a.putEnumerated(s("refineEdgeOutput"), s("refineEdgeOutput"), s("selectionOutputToSelection"));
      executeAction(s("smartBrushWorkspace"), a, DialogModes.NO);
    } catch (e) { $.writeln("refino falhou: " + e); }
  };
  // TEXTO ATRÁS: copia a camada da foto para um grupo ACIMA do texto e deixa só a pessoa/objeto (máscara por IA).
  // prompt vazio = pessoa principal (Selecionar assunto); prompt = objeto ("o celular na mão"). A foto original fica embaixo, inteira.
  Y.naFrente = function (foto, grupoAcima, prompt, nome) {
    var c = foto.duplicate(); c.name = nome || ("NA FRENTE: " + (prompt || "pessoa"));
    c.move(grupoAcima, ElementPlacement.PLACEATBEGINNING);
    try { D.activeLayer = c; executeAction(s("deleteUserMask") , (function(){ var a = new ActionDescriptor(); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask")); a.putReference(s("null"), r); a.putBoolean(s("apply"), false); return a; })(), DialogModes.NO); } catch (e) {}
    Y.mascara(c, prompt, false);
    return c;
  };
  // Contorno do texto visível POR CIMA do objeto (o trecho que fica atrás aparece só em linha): cópia do texto sem preenchimento
  // com traço, recortada (máscara de corte) na camada "na frente".
  Y.contornoSobre = function (texto, naFrente, hex, px) {
    var c = texto.duplicate(); c.name = texto.name + " (contorno sobre o objeto)";
    c.move(naFrente, ElementPlacement.PLACEBEFORE);
    Y.efeitos(c, { traco: { px: px || 2, cor: hex || "#FFFFFF", posicao: "center" } }); c.fillOpacity = 0; Y.recorte(c); return c;
  };
  Y.recorte = function (l) { if (l.grouped) return l; D.activeLayer = l; var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); executeAction(s("groupEvent"), a, DialogModes.NO); return l; };

  // ---------- saída ----------
  Y.salvar = function (psd, png) {
    try { D.artLayers.getByName("base").remove(); } catch (e) {}
    if (psd) { var o = new PhotoshopSaveOptions(); o.layers = true; o.embedColorProfile = true; D.saveAs(new File(psd), o, false); }
    if (png) { D.saveAs(new File(png), new PNGSaveOptions(), true); }
    return psd || png;
  };
  // Carrossel panorâmico: exporta n fatias de largura w (PNG) a partir do documento inteiro. prefixo + "-01.png"...
  Y.fatiar = function (prefixo, n, w) {
    var orig = D, h = D.height.as("px");
    for (var i = 0; i < n; i++) {
      var c = orig.duplicate("fatia", true); // achatada
      c.crop([i * w, 0, (i + 1) * w, h]);
      c.saveAs(new File(prefixo + "-" + (i < 9 ? "0" : "") + (i + 1) + ".png"), new PNGSaveOptions(), true);
      c.close(SaveOptions.DONOTSAVECHANGES);
    }
    app.activeDocument = orig; D = orig; return n;
  };
  Y.bounds = function (l) { var bb = b(l); return bb.x + "," + bb.y + "," + bb.w + "," + bb.h; };
  // ---------- técnicas do laboratório (engenharia reversa 16/10/2026, docs/tecnicas.md) ----------
  function setCamada(l, chave, tipo, v) { D.activeLayer = l; var lay = new ActionDescriptor();
    if (tipo === "lista") lay.putList(s(chave), v); var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); a.putObject(s("to"), s("layer"), lay); executeAction(s("set"), a, DialogModes.NO); }
  Y.inteligente = function (l) { D.activeLayer = l; executeAction(s("newPlacedLayer"), new ActionDescriptor(), DialogModes.NO); return D.activeLayer; };
  // EXPERIMENTAL (resultado depende de onde a camada nasceu; para mockup use scripts/perspectiva.py, exato).
  // Distorção por 4 cantos (perspectiva/mockup): cantos = [[x,y] sup-esq, sup-dir, inf-dir, inf-esq]. Converte em objeto
  // inteligente (continua editável: duplo clique troca a arte). USAR A CAMADA DEVOLVIDA (a antiga fica dentro do novo SO). Malha Bézier 4x4 por homografia = perspectiva real.
  // Formato descoberto lendo smartObjectMore.warp: warpCustom + bounds classFloatRect + customEnvelopeWarp.meshPoints.
  Y.perspectiva = function (l, c, manterPixels) {
    // 1) encaixa na caixa do quadrilátero (o warp erra muito quando a camada está longe/maior que o destino)
    var qx = Math.min(c[0][0], c[1][0], c[2][0], c[3][0]), qy = Math.min(c[0][1], c[1][1], c[2][1], c[3][1]);
    var qw = Math.max(c[0][0], c[1][0], c[2][0], c[3][0]) - qx, qh = Math.max(c[0][1], c[1][1], c[2][1], c[3][1]) - qy;
    var bb = b(l); l.resize(qw / bb.w * 100, qh / bb.h * 100, AnchorPosition.MIDDLECENTER); bb = b(l); l.translate(qx - bb.x, qy - bb.y);
    if (!manterPixels) l = Y.inteligente(l);
    aplicarMalha(l, c); return l;
  };
  Y._malha = function (l, c) { aplicarMalha(l, c); return l; };
  // Malha Bézier 4x4 por homografia (quadrado -> quadrilátero). Formato lido de smartObjectMore.warp:
  // warpCustom + bounds classFloatRect + customEnvelopeWarp.meshPoints (rationalPoint em pixels).
  function aplicarMalha(l, c) {
    D.activeLayer = l; var bb = b(l);
    var x0 = c[0][0], y0 = c[0][1], x1 = c[1][0], y1 = c[1][1], x2 = c[2][0], y2 = c[2][1], x3 = c[3][0], y3 = c[3][1];
    var dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2, sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
    var den = dx1 * dy2 - dx2 * dy1, g = (sx * dy2 - dx2 * sy) / den, h = (dx1 * sy - sx * dy1) / den;
    var A = x1 - x0 + g * x1, B = x3 - x0 + h * x3, C = y1 - y0 + g * y1, E = y3 - y0 + h * y3;
    function H(u, v) { var w = g * u + h * v + 1; return [(A * u + B * v + x0) / w, (C * u + E * v + y0) / w]; }
    var lst = new ActionList();
    for (var j = 0; j < 4; j++) for (var i = 0; i < 4; i++) { var p = H(i / 3, j / 3), pt = new ActionDescriptor();
      pt.putUnitDouble(s("horizontal"), s("pixelsUnit"), p[0]); pt.putUnitDouble(s("vertical"), s("pixelsUnit"), p[1]); lst.putObject(s("rationalPoint"), pt); }
    var env = new ActionDescriptor(); env.putList(s("meshPoints"), lst);
    var rc = new ActionDescriptor(); rc.putDouble(s("top"), bb.y); rc.putDouble(s("left"), bb.x); rc.putDouble(s("bottom"), bb.y + bb.h); rc.putDouble(s("right"), bb.x + bb.w);
    var w = new ActionDescriptor(); w.putEnumerated(s("warpStyle"), s("warpStyle"), s("warpCustom")); w.putDouble(s("warpValue"), 0); w.putDouble(s("warpPerspective"), 0); w.putDouble(s("warpPerspectiveOther"), 0);
    w.putEnumerated(s("warpRotate"), s("orientation"), s("horizontal")); w.putObject(s("bounds"), s("classFloatRect"), rc); w.putInteger(s("uOrder"), 4); w.putInteger(s("vOrder"), 4);
    w.putObject(s("customEnvelopeWarp"), s("customEnvelopeWarp"), env);
    var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); a.putEnumerated(s("freeTransformCenterState"), s("quadCenterState"), s("QCSAverage")); a.putObject(s("warp"), s("warp"), w);
    executeAction(s("transform"), a, DialogModes.NO);
  }
  // Mesclar se (Blend If): esta = [pretoA, pretoB, brancoA, brancoB] da própria camada; baixo = idem da camada de baixo.
  // Ex.: texto que some nas luzes da foto: Y.mesclarSe(t, null, [0, 0, 60, 140]). Valores divididos = transição suave.
  Y.mesclarSe = function (l, esta, baixo) {
    esta = esta || [0, 0, 255, 255]; baixo = baixo || [0, 0, 255, 255];
    var br = new ActionDescriptor(), cr = new ActionReference(); cr.putEnumerated(s("channel"), s("channel"), s("gray")); br.putReference(s("channel"), cr);
    var k = ["srcBlackMin", "srcBlackMax", "srcWhiteMin", "srcWhiteMax", "destBlackMin", "destBlackMax", "destWhiteMin", "destWhiteMax"], v = esta.concat(baixo);
    for (var i = 0; i < 8; i++) br.putInteger(s(k[i]), v[i]);
    var lst = new ActionList(); lst.putObject(s("blendRange"), br); setCamada(l, "blendRange", "lista", lst); return l;
  };
  // Restrição de canais (Opções de mesclagem > Canais): glitch RGB = cópias só no R / só no G-B, deslocadas.
  Y.canais = function (l, lista) { var lst = new ActionList(); for (var i = 0; i < lista.length; i++) lst.putEnumerated(s("channel"), s(lista[i])); setCamada(l, "channelRestrictions", "lista", lst); return l; };
  Y.glitch = function (l, dx, g) {
    var r = l.duplicate(); r.name = "GLITCH R"; Y.canais(r, ["red"]); r.translate(dx, 0);
    var c = l.duplicate(); c.name = "GLITCH GB"; Y.canais(c, ["green", "blue"]); c.translate(-dx, 0); return [r, c];
  };
  // LUT de cor (camada de ajuste Pesquisa de cores) a partir de .cube/.3dl/.look. Os do Photoshop: Y.LUTS + "Candlelight.CUBE".
  Y.LUTS = "/Applications/Adobe Photoshop 2026/Presets/3DLUTs/";
  Y.lut = function (arquivo, nome, g, op) {
    var a = new ActionDescriptor(); a.putPath(s("from"), new File(arquivo.indexOf("/") < 0 ? Y.LUTS + arquivo : arquivo)); a.putString(s("name"), nome || "LUT");
    executeAction(s("makerColorLookupLayerFromFile"), a, DialogModes.NO); var l = D.activeLayer; nomeia(l, nome || "LUT"); if (op !== undefined) l.opacity = op; return entra(l, g);
  };
  // Mapa de deslocamento a partir de uma imagem (tecido, parede, água): cinza + desfoque, salvo como PSD.
  Y.criarMapa = function (imagem, saidaPsd, desfoque) {
    var orig = D, m = app.open(new File(imagem)); m.flatten(); m.changeMode(ChangeMode.GRAYSCALE); m.activeLayer.applyGaussianBlur(desfoque || 4);
    var f = new File(saidaPsd); m.saveAs(f, new PhotoshopSaveOptions(), true); m.close(SaveOptions.DONOTSAVECHANGES); app.activeDocument = orig; D = orig; return f;
  };
  // Deslocamento (filtro inteligente): texto/arte acompanha as dobras do mapa. escala 10-40.
  Y.deslocar = function (l, mapa, eh, ev) {
    if (l.kind !== LayerKind.SMARTOBJECT) l = Y.inteligente(l); D.activeLayer = l;
    var a = new ActionDescriptor(); a.putInteger(s("horizontalScale"), eh); a.putInteger(s("verticalScale"), ev === undefined ? eh : ev);
    a.putEnumerated(s("displacementMap"), s("displacementMap"), s("stretchToFit")); a.putEnumerated(s("undefinedArea"), s("undefinedArea"), s("repeatEdgePixels"));
    a.putPath(s("displaceFile"), mapa instanceof File ? mapa : new File(mapa)); executeAction(s("displace"), a, DialogModes.NO); return l;
  };
  // Texto em arco (deformação de texto, continua editável). valor -100..100.
  Y.arco = function (l, valor, estilo) { l.textItem.warpStyle = estilo || WarpStyle.ARC; l.textItem.warpBend = valor; return l; };
  // ---------- técnicas de design (lote 2, 16/10/2026) ----------
  function rasterizar(l) { D.activeLayer = l; var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); executeAction(s("rasterizeLayer"), a, DialogModes.NO); return D.activeLayer; }
  function copiaSolida(l, cor) {   // cópia da silhueta em cor chapada, rasterizada (base para sombras e extrusão)
    var c = l.duplicate(); c = rasterizar(c); D.activeLayer = c; c.fillOpacity = 100;
    var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); executeAction(s("rasterizeLayer"), a, DialogModes.NO);
    c.blendMode = BlendMode.NORMAL; c.opacity = 100; D.activeLayer = c;
    // trava transparência e pinta
    D.selection.selectAll(); D.selection.fill(rgb(cor), ColorBlendMode.NORMAL, 100, true); D.selection.deselect();   // 4º arg = preservar transparência
    return c;
  }
  // Repete uma camada deslocando 1 px por passo até `comp` (dobrando: log2 passos). ang em graus (0 = direita, 90 = baixo).
  function arrastar(c, ang, comp) {
    var r = ang * Math.PI / 180, dx = Math.cos(r), dy = Math.sin(r), feito = 1;
    while (feito < comp) { var passo = Math.min(feito, comp - feito); var d = c.duplicate(); d.translate(dx * passo, dy * passo); D.activeLayer = d; c = d.merge(); feito += passo; }
    return c;
  }
  // Sombra longa (flat design): silhueta arrastada na diagonal, abaixo da camada.
  Y.sombraLonga = function (l, ang, comp, cor, op) {
    var c = copiaSolida(l, cor || "#000000"); c = arrastar(c, ang === undefined ? 45 : ang, comp || 1500);   // padrão passa da borda (sombra longa não termina dentro da peça)
    c.move(l, ElementPlacement.PLACEAFTER); c.name = "SOMBRA LONGA"; c.opacity = op === undefined ? 35 : op; return c;
  };
  // Extrusão 3D de texto/forma: cópias empilhadas mais escuras atrás + chanfro leve na frente.
  Y.extrusao = function (l, prof, cor, ang) {
    var c = copiaSolida(l, cor || "#333333"); c = arrastar(c, ang === undefined ? 60 : ang, prof || 24);
    c.move(l, ElementPlacement.PLACEAFTER); c.name = "EXTRUSAO 3D";
    Y.efeitos(c, { sombra: { cor: "#000000", op: 45, dist: 10, desfoque: 25, angulo: -(ang === undefined ? 60 : ang) + 180 } });
    Y.efeitos(l, { chanfro: { tam: 3, prof: 120, altitude: 40, opLuz: 45, opSombra: 30 } }); return c;
  };
  // Neon: núcleo claro + brilho interno da cor + brilho externo forte + halo desfocado atrás.
  Y.neon = function (l, cor) {
    if (l.kind === LayerKind.TEXT) l.textItem.color = rgb("#FFFFFF");
    Y.efeitos(l, { brilhoInterno: { cor: cor, op: 90, tam: 6 }, brilho: { cor: cor, op: 95, tam: 28 } });
    var h = copiaSolida(l, cor); h.move(l, ElementPlacement.PLACEAFTER); h.applyGaussianBlur(45); h.blendMode = BlendMode.SCREEN; h.opacity = 70; h.name = "HALO NEON"; return l;
  };
  // Cromado: degradê metálico + chanfro brilhante + cetim + traço fino escuro.
  Y.cromado = function (l) {
    return Y.efeitos(l, { degrade: { paradas: [["#2B2B2B", 0], ["#FFFFFF", 45], ["#5A5A5A", 52], ["#E6E6E6", 75], ["#8C8C8C", 100]], angulo: 90 },
      chanfro: { tecnica: "preciseMatte", tam: 6, prof: 300, altitude: 55, opLuz: 90, opSombra: 60 }, cetim: { cor: "#000000", op: 35, dist: 12, desfoque: 10 },
      traco: { px: 2, cor: "#1A1A1A", posicao: "outside" } });
  };
  // Texto vazado: a foto aparece só dentro das letras (máscara de recorte).
  Y.textoVazado = function (texto, foto) { foto.move(texto, ElementPlacement.PLACEBEFORE); Y.recorte(foto); return foto; };
  // Retícula (halftone de jornal/pôster) como filtro inteligente. raio 4-20 px.
  Y.reticula = function (l, raio) {
    if (l.kind !== LayerKind.SMARTOBJECT) l = Y.inteligente(l); D.activeLayer = l;
    var a = new ActionDescriptor(); a.putInteger(charIDToTypeID("Rds "), raio || 8);
    a.putInteger(charIDToTypeID("Ang1"), 108); a.putInteger(charIDToTypeID("Ang2"), 162); a.putInteger(charIDToTypeID("Ang3"), 90); a.putInteger(charIDToTypeID("Ang4"), 45);
    executeAction(charIDToTypeID("ClrH"), a, DialogModes.NO); return l;
  };
  // Sombra de contato: elipse escura desfocada sob a base do objeto (pé, produto em mesa).
  Y.sombraContato = function (obj, g, forca) {
    var v = Y.caixaVisivel(obj), w = v.w * 0.8, h = Math.max(10, v.w * 0.07);
    var e = Y.elipse({ x: v.x + (v.w - w) / 2, y: v.y + v.h - h * 0.6, w: w, h: h, cor: "#000000", nome: "SOMBRA CONTATO" }, g);
    e = rasterizar(e); e.applyGaussianBlur(h * 0.6); e.blendMode = BlendMode.MULTIPLY; e.opacity = forca || 70; e.move(obj, ElementPlacement.PLACEAFTER); return e;
  };
  // Luz de recorte (rim light): faixa de luz na borda do lado da fonte de luz (dx,dy = de onde vem a luz, ex.: -6,-4).
  Y.luzRecorte = function (obj, cor, dx, dy, op) {
    D.activeLayer = obj; var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("channel"), s("selection")); a.putReference(s("null"), r);
    var c = new ActionReference(); try { c.putEnumerated(s("channel"), s("channel"), s("mask")); a.putReference(s("to"), c); executeAction(s("set"), a, DialogModes.NO); }
    catch (e) { a = new ActionDescriptor(); a.putReference(s("null"), r); c = new ActionReference(); c.putEnumerated(s("channel"), s("channel"), s("transparencyEnum")); a.putReference(s("to"), c); executeAction(s("set"), a, DialogModes.NO); }
    var l = D.artLayers.add(); l.name = "LUZ DE RECORTE"; D.selection.fill(rgb(cor || "#FFFFFF"));
    D.selection.translateBoundary(UnitValue(-(dx || -6), "px"), UnitValue(-(dy || -4), "px")); D.selection.clear(); D.selection.deselect();
    l.applyGaussianBlur(2.5); l.blendMode = BlendMode.SCREEN; l.opacity = op || 85; l.move(obj, ElementPlacement.PLACEBEFORE); Y.recorte(l); return l;
  };
  // ---------- produção e retoque (lote 3, 16/10/2026) ----------
  // Troca o conteúdo de um objeto inteligente (template de marca: mesma moldura/efeitos, foto ou arte nova).
  Y.trocarConteudo = function (l, arquivo) { D.activeLayer = l; var a = new ActionDescriptor(); a.putPath(s("null"), new File(arquivo));
    executeAction(s("placedLayerReplaceContents"), a, DialogModes.NO); return D.activeLayer; };
  // Expande o fundo da foto para cobrir o documento inteiro com Preenchimento Sensível ao Conteúdo (LOCAL, sem crédito
  // generativo): adaptar feed 4:5 -> story 9:16 sem esticar. Cria cópia rasterizada "FUNDO EXPANDIDO" abaixo da foto.
  Y.expandirFundo = function (foto, margem) {
    var c = foto.duplicate(); c = rasterizar(c); c.name = "FUNDO EXPANDIDO"; c.move(foto, ElementPlacement.PLACEAFTER); D.activeLayer = c;
    var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("channel"), s("selection")); a.putReference(s("null"), r);
    var t2 = new ActionReference(); t2.putEnumerated(s("channel"), s("channel"), s("transparencyEnum")); a.putReference(s("to"), t2); executeAction(s("set"), a, DialogModes.NO);
    D.selection.invert(); D.selection.expand(UnitValue(margem || 6, "px"));
    var f = new ActionDescriptor(); f.putEnumerated(s("using"), s("fillContents"), s("contentAware")); f.putBoolean(s("contentAwareColorAdaptationFill"), true);
    f.putUnitDouble(s("opacity"), s("percentUnit"), 100); f.putEnumerated(s("mode"), s("blendMode"), s("normal")); executeAction(s("fill"), f, DialogModes.NO);
    D.selection.deselect(); return c;
  };
  // Separação de frequência (retoque de pele): BAIXA = cor/tom (desfoque), ALTA = textura (Aplicar Imagem: subtrair,
  // escala 2, deslocamento 128, modo Luz Linear). Mais uma camada cinza 50% em Luz Suave para esquivar/queimar.
  Y.separacaoFrequencia = function (foto, raio, g) {
    var base = foto.kind === LayerKind.SMARTOBJECT ? rasterizar(foto.duplicate()) : foto.duplicate();
    var baixa = base; baixa.name = "BAIXA FREQUENCIA (tom)"; baixa.applyGaussianBlur(raio || 6);
    var alta = rasterizar(foto.duplicate()); alta.name = "ALTA FREQUENCIA (textura)"; alta.move(baixa, ElementPlacement.PLACEBEFORE); D.activeLayer = alta;
    var calc = new ActionDescriptor(), rr = new ActionReference(); rr.putEnumerated(s("channel"), s("channel"), s("RGB")); rr.putName(s("layer"), baixa.name);
    calc.putReference(s("to"), rr); calc.putEnumerated(s("calculation"), s("calculationType"), s("subtract")); calc.putDouble(s("scale"), 2); calc.putInteger(s("offset"), 128);
    var a = new ActionDescriptor(); a.putObject(s("with"), s("calculation"), calc); executeAction(s("applyImageEvent"), a, DialogModes.NO);
    alta.blendMode = BlendMode.LINEARLIGHT;
    var db = D.artLayers.add(); db.name = "ESQUIVAR E QUEIMAR (pincel branco/preto 5-10%)"; D.selection.selectAll(); D.selection.fill(rgb("#808080")); D.selection.deselect();
    db.blendMode = BlendMode.SOFTLIGHT; db.move(alta, ElementPlacement.PLACEBEFORE);
    return { baixa: baixa, alta: alta, db: db };
  };
  // Dupla exposição (receita clássica): pessoa recortada em P&B contrastada sobre fundo claro; paisagem recortada na
  // pessoa em MULTIPLICAÇÃO; o rosto fica limpo por uma máscara elíptica esfumada (rosto = metade de cima da caixa).
  // rosto opcional {x,y,w,h}; sem ele estima pelo topo da silhueta. Tela (screen) só serve com pessoa escura.
  Y.duplaExposicao = function (pessoa, paisagem, op, rosto, modo) {
    paisagem.move(pessoa, ElementPlacement.PLACEBEFORE); Y.recorte(paisagem); paisagem.blendMode = modo === "tela" ? BlendMode.SCREEN : BlendMode.MULTIPLY; paisagem.opacity = op || 100;
    var v = Y.caixaVisivel(pessoa), r = rosto || { x: v.x + v.w * 0.25, y: v.y, w: v.w * 0.5, h: v.h * 0.32 };
    D.selection.select([[r.x, r.y], [r.x + r.w, r.y], [r.x + r.w, r.y + r.h], [r.x, r.y + r.h]]);
    var e = new ActionDescriptor(); var rr = new ActionReference(); rr.putProperty(s("channel"), s("selection")); e.putReference(s("null"), rr);
    var el = new ActionDescriptor(); el.putUnitDouble(s("top"), s("pixelsUnit"), r.y); el.putUnitDouble(s("left"), s("pixelsUnit"), r.x); el.putUnitDouble(s("bottom"), s("pixelsUnit"), r.y + r.h); el.putUnitDouble(s("right"), s("pixelsUnit"), r.x + r.w);
    e.putObject(s("to"), s("ellipse"), el); e.putBoolean(s("antiAlias"), true); executeAction(s("set"), e, DialogModes.NO);
    D.selection.feather(UnitValue(Math.round(r.w * 0.35), "px"));
    D.activeLayer = paisagem; var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var mr = new ActionReference(); mr.putEnumerated(s("channel"), s("channel"), s("mask"));
    m.putReference(s("at"), mr); m.putEnumerated(s("using"), s("userMaskEnabled"), s("hideSelection")); executeAction(s("make"), m, DialogModes.NO); D.selection.deselect();
    return paisagem;
  };
  // ---------- pranchetas (carrossel num PSD só) ----------
  // Texto NÃO pode ser criado por script dentro de prancheta (erro "camada não pode conter texto"). Fluxo: montar cada
  // slide como GRUPO normal (Y.slides) e no fim converter com Y.virarPrancheta (artboardFromLayerGroupEvent).
  Y.PRANCHETAS = [];
  Y.slides = function (n, w, h, prefixo) { var lst = []; for (var i = 0; i < n; i++) { var g = D.layerSets.add(); g.name = (prefixo || "SLIDE ") + (i < 9 ? "0" : "") + (i + 1);
    lst.push({ g: g, x: i * (w + 100), y: 0, w: w, h: h }); } return lst; };
  // Converte o grupo do slide em prancheta pelas ferramentas NATIVAS do agente (o evento AM artboardFromLayerGroup
  // não fica disponível por script): cria a prancheta vazia no retângulo e move o grupo para dentro.
  Y.virarPrancheta = function (sl) {
    var doc = agente("application_list_open_documents", {}).data.front_doc_id;
    var ab = agente("document_create_artboard", { doc_id: doc, anchor: { x: sl.x, y: sl.y }, size: { width: sl.w, height: sl.h }, name: sl.g.name });
    if (ab.status !== "success") throw new Error("prancheta: " + ab.data);
    D.activeLayer = sl.g; var gid = agente("document_get_layer_selection", { doc_id: doc }).data.selected_layer_ids[0];
    var mv = agente("layer_reorder", { doc_id: doc, layer_id: gid, position: "inside", relative_to_layer_id: ab.data.layer_id });
    if (mv.status !== "success") throw new Error("mover para prancheta: " + mv.data);
    Y.PRANCHETAS.push({ nome: sl.g.name, r: sl }); return ab.data.layer_id;
  };
  // Exporta cada prancheta em PNG (prefixo-01.png ...): cópia do documento, recorta no retângulo da prancheta.
  Y.exportarPranchetas = function (prefixo) {
    var orig = D, out = [];
    for (var i = 0; i < Y.PRANCHETAS.length; i++) { var p = Y.PRANCHETAS[i], dup = orig.duplicate("exp", true);
      dup.crop([UnitValue(p.r.x, "px"), UnitValue(p.r.y, "px"), UnitValue(p.r.x + p.r.w, "px"), UnitValue(p.r.y + p.r.h, "px")]);
      var f = new File(prefixo + "-" + (i < 9 ? "0" : "") + (i + 1) + ".png"); dup.saveAs(f, new PNGSaveOptions(), true); dup.close(SaveOptions.DONOTSAVECHANGES); out.push(f.fsName); }
    app.activeDocument = orig; D = orig; return out;
  };
  // Apaga áreas (texto da referência) com Preenchimento Sensível ao Conteúdo numa cópia rasterizada: vira "fundo limpo".
  // caixas: [[x1,y1,x2,y2], ...] em px do documento. Local, sem crédito generativo.
  Y.apagarAreas = function (l, caixas, expandir) {
    l = rasterizar(l); D.activeLayer = l; D.selection.deselect();
    for (var i = 0; i < caixas.length; i++) { var c = caixas[i];
      D.selection.select([[c[0], c[1]], [c[2], c[1]], [c[2], c[3]], [c[0], c[3]]], i ? SelectionType.EXTEND : SelectionType.REPLACE); }
    D.selection.expand(UnitValue(expandir || 4, "px"));
    var f = new ActionDescriptor(); f.putEnumerated(s("using"), s("fillContents"), s("contentAware")); f.putBoolean(s("contentAwareColorAdaptationFill"), true);
    f.putUnitDouble(s("opacity"), s("percentUnit"), 100); f.putEnumerated(s("mode"), s("blendMode"), s("normal")); executeAction(s("fill"), f, DialogModes.NO);
    D.selection.deselect(); return l;
  };
  Y.mesclar = function (a, b) { var o = {}, k; for (k in a) o[k] = a[k]; for (k in b) o[k] = b[k]; return o; };
  // Marcação de destaque no texto: **negrito** e {{cor}} -> {txt sem marcas, faixas para o Y.texto}
  Y.marcacao = function (txt, fonteNeg, corDest) {
    var out = "", fx = [], i = 0, modo = null, ini = 0;
    while (i < txt.length) {
      if (txt.substr(i, 2) === "**" || txt.substr(i, 2) === "{{" || txt.substr(i, 2) === "}}") {
        var tok = txt.substr(i, 2);
        if (!modo && tok !== "}}") { modo = tok; ini = out.length; }
        else if (modo) { var f = { de: ini, ate: out.length };
          if (modo === "**" && fonteNeg) f.fonte = fonteNeg; if (modo === "{{" && corDest) f.cor = corDest;
          if (f.fonte || f.cor) fx.push(f); modo = null; }
        i += 2; continue; }
      out += txt.charAt(i); i++; }
    return { txt: out, faixas: fx };
  };
  // Máscara de camada a partir de um PNG (alfa = visível). Procura a camada cujo nome começa com `prefixo`.
  // Cópia só-contorno do texto, visível onde o objeto cobre a letra (efeito "letra fantasma" sobre a tela/objeto).
  Y.contornoOculto = function (prefixo, png, cor) {
    function acha(c) { for (var i = 0; i < c.layers.length; i++) { var l = c.layers[i];
      if (l.typename === "LayerSet") { var r = acha(l); if (r) return r; } else if (l.name.indexOf(prefixo) === 0) return l; } return null; }
    var base = acha(D); if (!base) return null;
    var c = base.duplicate(); c.name = base.name.split(" ")[0] + " CONTORNO (sobre o objeto)"; c.move(base, ElementPlacement.PLACEBEFORE);
    c.fillOpacity = 0; Y.efeitos(c, { traco: { px: 1.5, cor: cor || "#FFFFFF", posicao: "inside" } }); c.opacity = 80;
    Y.mascaraDeImagem(c.name, png); return c;
  };
  Y.mascaraDeImagem = function (prefixo, png) {
    function acha(c) { for (var i = 0; i < c.layers.length; i++) { var l = c.layers[i];
      if (l.typename === "LayerSet") { var r = acha(l); if (r) return r; }
      else if (l.name.indexOf(prefixo) === 0 && (prefixo.indexOf("CONTORNO") >= 0 || l.name.indexOf("CONTORNO") < 0)) return l; } return null; }
    var alvo = acha(D); if (!alvo) return null;
    var tmp = Y.colocar(png, "tmp mascara", null); tmp = rasterizar(tmp); D.activeLayer = tmp;
    var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("channel"), s("selection")); a.putReference(s("null"), r);
    var c = new ActionReference(); c.putEnumerated(s("channel"), s("channel"), s("transparencyEnum")); a.putReference(s("to"), c); executeAction(s("set"), a, DialogModes.NO);
    tmp.remove(); D.activeLayer = alvo; Y.tirarMascara(alvo);
    var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var mr = new ActionReference(); mr.putEnumerated(s("channel"), s("channel"), s("mask"));
    m.putReference(s("at"), mr); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealSelection")); executeAction(s("make"), m, DialogModes.NO);
    D.selection.deselect(); return alvo;
  };
  Y.D = function () { return D; };
  // Lê um JSON (alvos.json do ciclo.py, preset.json da marca). ExtendScript não tem JSON nativo confiável.
  Y.lerJSON = function (caminho) { var f = new File(caminho); f.encoding = "UTF-8"; if (!f.exists) return {}; f.open("r"); var t = f.read(); f.close(); return eval("(" + t + ")"); };
  return Y;
})();
