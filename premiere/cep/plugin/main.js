// Gab Ponte PPro: servidor HTTP local dentro do Premiere (CEP). O Python (premiere2019_lib.py) manda ExtendScript
// em POST /jsx; aqui ele roda no motor do Premiere (evalScript) e a resposta volta como texto (JSON montado no JSX).
// Sem lógica de edição: tudo vive em jsx/gab_ppro.jsx e no Python, então melhorar o Gab é só "git pull".
var http = require("http");
var PORTA = 8767;
var fila = Promise.resolve();   // um script por vez (o motor ExtendScript é single-thread)

function estado(t) { try { document.getElementById("estado").textContent = "Gab Ponte: " + t; } catch (e) {} }

function rodar(script) {
  return new Promise(function (ok) {
    window.__adobe_cep__.evalScript(script, function (r) { ok(r); });
  });
}

var servidor = http.createServer(function (req, res) {
  if (req.method === "GET" && req.url === "/ping") {
    res.writeHead(200, { "Content-Type": "text/plain" }); res.end("ok"); return;
  }
  if (req.method !== "POST" || req.url !== "/jsx") { res.writeHead(404); res.end(); return; }
  var corpo = [];
  req.on("data", function (c) { corpo.push(c); });
  req.on("end", function () {
    var script = Buffer.concat(corpo).toString("utf8");
    fila = fila.then(function () { return rodar(script); }).then(function (r) {
      res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
      res.end(r === undefined || r === null ? "" : String(r));
    }, function (e) {
      res.writeHead(500); res.end(String(e));
    });
  });
});
servidor.on("error", function (e) { estado(e.code === "EADDRINUSE" ? "conectado (servidor já ativo)" : String(e)); });
servidor.on("listening", function () { estado("conectado em 127.0.0.1:" + PORTA); });
servidor.listen(PORTA, "127.0.0.1");
