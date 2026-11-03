// Exemplo do preset igreja-moderna, arquétipo A (moldura quebrada), feed 1080x1350. Igreja e nomes fictícios.
// Variáveis: FOTO (pessoa, de preferência meio corpo ou corpo inteiro), SAIDA (pasta).
// python3 scripts/montar.py presets/igreja-moderna/exemplo/arte.jsx FOTO=/caminho/pastor.jpg SAIDA=/pasta
var W = 1080, H = 1350;
if (typeof CORTE === "undefined") var CORTE = "";
Y.doc(W, H, "igreja-moderna-dmngo");

var gFundo = Y.grupo("FUNDO");
Y.solido("#0C0B0B", "PRETO", gFundo);
Y.degrade([["#2A1410", 0, 100], ["#2A1410", 100, 0]], 270, "CALOR TOPO", gFundo, "screen", 60);

var gMold = Y.grupo("MOLDURA");
var ret = Y.retangulo({ x: 250, y: 330, w: 580, h: 700, cor: "#FFFFFF", nome: "MOLDURA" }, gMold);
Y.degrade([["#6E150D", 0], ["#C42E1E", 45], ["#F28A2E", 100]], 80, "DEGRADE QUENTE", gMold);
Y.recorte(gMold.layers[0]);

var gPes = Y.grupo("PESSOAS");
var p = Y.colocar(FOTO, "PREGADOR", gPes, { x: 40, y: -150, w: 1000, h: 1500 }, "altura", "topo");
Y.recortar(p);
Y.cortarAbaixo(p, CORTE ? Number(CORTE) : 968);   // foto atrás de púlpito: o recorte deixava o paletó solto à esquerda; corta abaixo das mãos, atrás do título
Y.efeitos(p, { sombra: { cor: "#000000", op: 55, dist: 0, desfoque: 70 } });

var gDeg = Y.grupo("DEGRADE");
Y.degrade([["#0C0B0B", 0, 100], ["#0C0B0B", 30, 0]], 90, "ESCURECE BASE", gDeg);

var gRab = Y.grupo("RABISCOS");
var r1 = Y.retangulo({ x: 860, y: 250, w: 3, h: 190, cor: "#FFFFFF", nome: "TRACO 1" }, gRab); r1.rotate(28);
var r2 = Y.retangulo({ x: 885, y: 300, w: 2, h: 120, cor: "#FFFFFF", nome: "TRACO 2" }, gRab); r2.rotate(-12);
var r3 = Y.retangulo({ x: 200, y: 520, w: 2, h: 150, cor: "#FFFFFF", nome: "TRACO 3" }, gRab); r3.rotate(40);

var gTit = Y.grupo("TITULO");
Y.texto({ txt: "DMNGO", nome: "TITULO", fonte: "Unbounded-Black", px: 196, cor: "#F4F1EC", tracking: -20, x: W / 2, y: 820, ancora: "tc" }, gTit);

var gServ = Y.grupo("SERVICO");
Y.texto({ txt: "CULTO DE\nCELEBRAÇÃO\nPR. LUCAS\nMENDES", nome: "CREDITO", fonte: "SpaceMono-Regular", px: 18, cor: "#F4F1EC", tracking: 300, entrelinha: 26, x: 70, y: 150 }, gServ);
Y.texto({ txt: "PRESENCIAL +\nONLINE\n10H + 18H", nome: "HORARIOS", fonte: "SpaceMono-Bold", px: 36, cor: "#F4F1EC", tracking: 60, entrelinha: 42, x: 70, y: 1080 }, gServ);
Y.texto({ txt: "AV. EXEMPLO, 123 · CENTRO", nome: "ENDERECO", fonte: "SpaceMono-Regular", px: 22, cor: "#F4F1EC", tracking: 60, x: 70, y: 1262 }, gServ);
Y.texto({ txt: "AO VIVO\n/IGREJAVIDANOVA", nome: "ONLINE", fonte: "SpaceMono-Bold", px: 22, cor: "#F4F1EC", tracking: 40, entrelinha: 30, x: 1010, y: 1080, ancora: "tr", alinh: "dir" }, gServ);

var gMarca = Y.grupo("MARCA");
Y.retangulo({ x: 640, y: 1160, w: 370, h: 130, raio: 18, cor: "#F4F1EC", contorno: { px: 2, cor: "#F4F1EC" }, so_contorno: true, nome: "CAIXA LOGO" }, gMarca);
Y.texto({ txt: "IVN©", nome: "SIGLA", fonte: "IvyPrestoDisplay-Regular", px: 58, cor: "#F4F1EC", x: 666, y: 1176 }, gMarca);
Y.texto({ txt: "IGREJA\nVIDA NOVA", nome: "NOME IGREJA", fonte: "SpaceMono-Bold", px: 15, cor: "#F4F1EC", tracking: 120, entrelinha: 19, x: 852, y: 1182 }, gMarca);
Y.retangulo({ x: 640, y: 1246, w: 370, h: 2, cor: "#F4F1EC", nome: "DIVISOR" }, gMarca);
Y.texto({ txt: "BEM-VINDO AO NOVO", nome: "SLOGAN", fonte: "SpaceMono-Regular", px: 15, cor: "#F4F1EC", tracking: 400, x: 825, y: 1268, ancora: "mc" }, gMarca);

var gAcab = Y.grupo("ACABAMENTO");
Y.curvas([[0, 10], [70, 58], [190, 205], [255, 250]], "CONTRASTE", gAcab, 70);
Y.grao(gAcab, 16, 38);

Y.salvar(SAIDA + "/igreja-moderna-dmngo.psd", SAIDA + "/igreja-moderna-dmngo.png");
"ok " + Y.bounds(p);
