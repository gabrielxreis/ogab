#!/usr/bin/env python3
"""Miniaturas dos criativos da concorrência (capa do vídeo ou imagem do anúncio; o vídeo NÃO é baixado).

  python3 ~/.claude/skills/ogab/trafego/painel/miniaturas.py --cliente xtrader --faltam
      lista, em JSON, os anúncios do painel.json sem miniatura e a página da Biblioteca que mostra cada grupo
  echo '[{"id": "123", "capa": "https://scontent...jpg"}]' | python3 ~/.claude/skills/ogab/trafego/painel/miniaturas.py --cliente xtrader
      grava clientes/<cliente>/miniaturas/<id>.jpg (o JSON sai do painel/capas.js rodado na página da Biblioteca)

Só grava a capa de anúncio que está no painel.json do cliente (campeões e concorrentes); as outras do JSON são ignoradas.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CLIENTES = os.path.join(os.path.dirname(AQUI), "clientes")


def anuncios(d):
    """[(id, anúncio, página da Biblioteca que mostra ele)] de tudo que o painel desenha com miniatura."""
    out = []
    for p in d.get("concorrentes_principais", []):
        for c in p.get("campeoes", []):
            out.append((str(c["id"]), c, p.get("pagina_biblioteca") or c.get("link")))
    for c in d.get("concorrentes", []):
        out.append((str(c["id"]), c, c.get("link") or f"https://www.facebook.com/ads/library/?id={c['id']}"))
    return out


def faltam(nome, d):
    pasta = os.path.join(CLIENTES, nome, "miniaturas")
    vistos, lista = set(), []
    for i, c, pag in anuncios(d):
        if i not in vistos and not c.get("fora_do_ar") and not os.path.isfile(os.path.join(pasta, f"{i}.jpg")):
            vistos.add(i)
            lista.append({"id": i, "pagina": pag})
    return lista


def gravar(nome, d, capas):
    pasta = os.path.join(CLIENTES, nome, "miniaturas")
    os.makedirs(pasta, exist_ok=True)
    validos = {i for i, _, _ in anuncios(d)}
    ok, erro = [], []
    for c in capas:
        i, url = str(c.get("id") or ""), c.get("capa") or ""
        if i not in validos:
            continue
        if not url.startswith("https://"):
            erro.append(f"{i}: sem capa na página")
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                dados = r.read()
        except Exception as e:  # noqa: BLE001
            erro.append(f"{i}: {e}")
            continue
        destino = os.path.join(pasta, f"{i}.jpg")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".img") as t:
            t.write(dados)
        # sips (macOS) converte webp/png em jpg e reduz para 480 px; sem ele, grava como veio (o navegador abre igual)
        if shutil.which("sips") and subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "480", t.name, "--out", destino],
                                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            os.unlink(t.name)
        else:
            shutil.move(t.name, destino)
        ok.append(i)
    return ok, erro


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--faltam", action="store_true", help="só lista o que está sem miniatura")
    ap.add_argument("--fora-do-ar", help="IDs (vírgula) que a Biblioteca não mostra mais: marca fora_do_ar no painel.json")
    a = ap.parse_args()
    caminho = os.path.join(CLIENTES, a.cliente, "painel.json")
    if not os.path.isfile(caminho):
        print(f"SEM_PAINEL: {caminho}")
        return 1
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    if a.faltam:
        print(json.dumps(faltam(a.cliente, d), ensure_ascii=False, indent=1))
        return 0
    if a.fora_do_ar:
        ids = {i for i in a.fora_do_ar.replace(" ", "").split(",") if i}
        for i, c, _ in anuncios(d):
            if i in ids:
                c["fora_do_ar"] = True
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(f"FORA_DO_AR_MARCADOS: {len(ids)}")
        return 0
    entrada = json.load(sys.stdin)
    if isinstance(entrada, str):  # o javascript devolve o JSON como texto
        entrada = json.loads(entrada)
    if isinstance(entrada, dict):  # {capas: [...], nao_achou: [...]} do capas.js
        entrada = entrada.get("capas", [])
    ok, erro = gravar(a.cliente, d, entrada)
    print(f"MINIATURAS_GRAVADAS: {len(ok)}")
    for e in erro:
        print("FALHOU:", e)
    resto = faltam(a.cliente, d)
    print(f"FALTAM_MINIATURAS: {len(resto)}" + (" (" + ", ".join(x["id"] for x in resto) + ")" if resto else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
