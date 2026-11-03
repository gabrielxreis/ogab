// Adapta um PSD de feed (4:5 ou 1:1) para story 9:16 (1080x1920) sem esticar nada.
// Uso: python3 montar.py jsx/para_story.jsx ARQ=/caminho/post.psd
// 1) amplia a tela centralizada; 2) camadas de foto que não cobrem a tela nova ganham "FUNDO EXPANDIDO"
//    (sensível ao conteúdo, local); preenchimentos/ajustes se estendem sozinhos; 3) grupos de rodapé (BARRA, RODAPE,
//    MARCA, LOGO) descem para a zona segura de baixo (340 px livres) e grupos de topo (TOPO, CONTADOR) ficam a 250 px.
var d = app.open(new File(ARQ)); Y.usar(d); app.preferences.rulerUnits = Units.PIXELS;
var W = d.width.as("px"), H0 = d.height.as("px"), H = Math.round(W * 16 / 9), dy = (H - H0) / 2;
d.resizeCanvas(UnitValue(W, "px"), UnitValue(H, "px"), AnchorPosition.MIDDLECENTER);
var rel = [];
function percorre(c) {
  for (var i = 0; i < c.layers.length; i++) { var l = c.layers[i];
    if (l.typename === "LayerSet") { percorre(l); continue; }
    if (!l.visible || l.grouped) continue;
    var k = l.kind;
    if (k === LayerKind.SMARTOBJECT || k === LayerKind.NORMAL) { var bb = l.bounds, h = bb[3].as("px") - bb[1].as("px"), w = bb[2].as("px") - bb[0].as("px");
      // só foto que já cobria a altura antiga (fundo); objetos recortados no meio ficam como estão
      var falta = bb[1].as("px") > 1 || bb[3].as("px") < H - 1;
      if (/GRAN|GRAIN|RUIDO|NOISE|TEXTURA/i.test(l.name) && falta) { l.resize(100, H / h * 100, AnchorPosition.MIDDLECENTER); var b2 = l.bounds; l.translate(0, -b2[1].as("px")); rel.push("esticado: " + l.name); continue; }
      if (w >= W - 2 && h >= H0 - 2 && falta) { try { Y.expandirFundo(l); rel.push("expandido: " + l.name); } catch (e) { rel.push("falhou expandir " + l.name + ": " + e); } } } } }
percorre(d);
var BAIXO = /BARRA|RODAP|MARCA|LOGO|ASSINA/i, CIMA = /TOPO|CONTADOR|CABE/i;
for (var i = 0; i < d.layerSets.length; i++) { var g = d.layerSets[i], bb = g.bounds, y1 = bb[1].as("px"), y2 = bb[3].as("px");
  if (BAIXO.test(g.name) && y2 > H - dy - 5) { var alvo = H - 250 - (y2 - y1); g.translate(0, alvo - y1); rel.push("rodapé " + g.name + " -> y " + Math.round(alvo)); }
  else if (CIMA.test(g.name) && y1 < dy + 5) { g.translate(0, 250 - y1); rel.push("topo " + g.name + " -> y 250"); } }
var saida = ARQ.replace(/\.psd$/i, "-story");
var o = new PhotoshopSaveOptions(); o.layers = true; d.saveAs(new File(saida + ".psd"), o, false); d.saveAs(new File(saida + ".png"), new PNGSaveOptions(), true);
rel.join(" | ");
