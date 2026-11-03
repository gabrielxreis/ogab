#!/usr/bin/env python3
"""Servidor local do painel do Gab: serve a pasta da skill só em 127.0.0.1.

Existe porque, aberto como arquivo (file://), o Chrome ignora o "baixar" dos links e abre o vídeo.
Pelo servidor, `?baixar=<nome>` responde com Content-Disposition: attachment e o arquivo vai para Downloads.

  python3 ~/.claude/skills/ogab/trafego/painel/servidor.py [--porta 47830]
O painel.py sobe este servidor sozinho em segundo plano quando ele não está rodando.
"""
import argparse
import io
import os
import re
import subprocess
import sys
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 47830


class Painel(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=SKILL, **k)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/zip":
            return self.zipar(parse_qs(u.query))
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_POST(self):
        """/receber?cliente=<pasta>&id=<id do anúncio>: grava o vídeo do criativo pedido (corpo = mp4) em criativos_concorrentes/."""
        u = urlparse(self.path)
        q = parse_qs(u.query)
        cliente = re.sub(r"[^A-Za-z0-9_-]", "", (q.get("cliente") or [""])[0])
        ida = (q.get("id") or [""])[0]
        n = int(self.headers.get("Content-Length") or 0)
        if u.path != "/receber" or not cliente or not ida.isdigit() or not (0 < n < 300 * 1024 * 1024):
            self.send_response(400); self.cors(); self.end_headers(); return
        pasta = os.path.join(SKILL, "clientes", cliente, "criativos_concorrentes")
        os.makedirs(pasta, exist_ok=True)
        dados = self.rfile.read(n)
        with open(os.path.join(pasta, f"concorrente_{ida}.mp4"), "wb") as f:
            f.write(dados)
        # refaz os dados do painel na hora: a aba aberta liga o ⬇ deste vídeo em poucos segundos
        subprocess.run([sys.executable, os.path.join(SKILL, "painel", "painel.py"), "--cliente", cliente, "--nao-abrir"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        self.send_response(200); self.cors(); self.end_headers()
        self.wfile.write(b"ok")

    def zipar(self, q):
        """/zip?cliente=<pasta>&ids=1,2,3&nome=<arquivo.zip>: junta os vídeos baixados num zip só (um download)."""
        cliente = re.sub(r"[^A-Za-z0-9_-]", "", (q.get("cliente") or [""])[0])
        pasta = os.path.join(SKILL, "clientes", cliente, "criativos_concorrentes")
        ids = [i for i in re.split(r"[,\s]+", (q.get("ids") or [""])[0]) if i.isdigit()]
        nomes = dict(zip(ids, (q.get("nomes") or [""])[0].split("|"))) if q.get("nomes") else {}
        arquivos = []
        if os.path.isdir(pasta):
            for f in sorted(os.listdir(pasta)):
                m = re.match(r"concorrente_(\d+)\.mp4$", f)
                if m and (not ids or m.group(1) in ids):
                    arquivos.append((os.path.join(pasta, f), nomes.get(m.group(1)) or f))
        if not arquivos:
            self.send_error(404, "Nenhum vídeo baixado ainda para este pedido")
            return
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
            for caminho, nome in arquivos:
                z.write(caminho, "".join(c for c in nome if c not in '\\/:*?"<>|'))
        dados = buf.getvalue()
        nome_zip = "".join(c for c in ((q.get("nome") or [""])[0] or "criativos_concorrentes.zip") if c not in '\\/:*?"<>|')
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(nome_zip))
        self.end_headers()
        self.wfile.write(dados)

    def end_headers(self):
        q = parse_qs(urlparse(self.path).query)
        nome = (q.get("baixar") or [None])[0]
        if nome:
            seguro = "".join(c for c in nome if c not in '\\/:*?"<>|').strip() or "video.mp4"
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(seguro))
        if self.path.split("?")[0].endswith((".js", ".html", ".json")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *a):
        try:
            with open(os.path.join(SKILL, "painel", ".servidor.log"), "a", encoding="utf-8") as f:
                f.write(self.log_date_time_string() + " " + (fmt % a) + "\n")
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=PORTA)
    a = ap.parse_args()
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", a.porta), Painel)
    except OSError:
        print(f"porta {a.porta} ocupada (o servidor provavelmente já está rodando)")
        return 1
    print(f"painel em http://127.0.0.1:{a.porta}/painel/index.html")
    sys.stdout.flush()
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
