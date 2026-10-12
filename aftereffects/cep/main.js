// Gab Ponte AE: servidor HTTP local dentro do After Effects. O Python da skill (aftereffects/ae_lib.py) manda
// ExtendScript em POST /jsx; aqui ele roda no AE (evalScript) e a resposta volta como texto (JSON montado no JSX).
// Fica de propósito sem lógica de motion: tudo vive em aftereffects/jsx/gab_ae.jsx, então melhorar o Gab é só
// "git pull", sem reinstalar a extensão.
var http = require("http");
// Dentro do aerender (render em linha de comando) a extensão também sobe: aí não abre servidor.
var dentroDoAerender = false;
try { dentroDoAerender = /aerender/i.test(require("child_process").execSync("ps -o command= -p " + process.ppid).toString()); } catch (e) {}
var PORTA = 8766;
var fila = Promise.resolve();   // um script por vez (o AE é single-thread)

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
servidor.on("error", function (e) { console.log("[Gab Ponte AE] " + e); });
if (!dentroDoAerender) servidor.listen(PORTA, "127.0.0.1");
