#!/usr/bin/env python3
"""Criativos do cliente no painel: capa em alta e player de cada anúncio, montados sozinhos.

  python3 ~/.claude/skills/ogab/trafego/painel/criativos.py --cliente xtrader

Lê clientes/<cliente>/criativos/lista.json (escrita pelo Gab a cada leitura da conta, ver painel/LEIA.md):
  {"pagina_fb": "<id da página>", "conta": "<conta de anúncio>", "criativos": [
     {"id": "<video_id ou creative_id>", "tipo": "video|imagem", "nome", "campanha", "gasto", "impressoes", "status",
      "ad_id"?, "imagem_url"? (só imagem, vem do ads_get_creatives)}]}
Para cada vídeo, abre a página pública do vídeo no Facebook e grava a capa (og:image) em criativos/<id>.jpg; o painel
toca pelo player embutido do Facebook. Vídeo que não é público (post do Instagram impulsionado) fica com o botão que
abre o anúncio no Gerenciador. Imagem: baixa a imagem do anúncio uma vez. Escreve a lista pronta em painel.json
("criativos") e roda o painel.py. Capa já baixada não é baixada de novo.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CLIENTES = os.path.join(os.path.dirname(AQUI), "clientes")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def baixar(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def capa_video(pagina, vid):
    """Capa em alta da página pública do vídeo; None se o vídeo não é público."""
    try:
        h = baixar(f"https://www.facebook.com/{pagina}/videos/{vid}/").decode("utf-8", "ignore")
    except Exception:
        return None
    m = re.search(r'og:image" content="([^"]+)"', h)
    return html.unescape(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--nao-abrir", action="store_true")
    a = ap.parse_args()
    base = os.path.join(CLIENTES, a.cliente)
    pasta = os.path.join(base, "criativos")
    lista = json.load(open(os.path.join(pasta, "lista.json"), encoding="utf-8"))
    pagina, conta = lista.get("pagina_fb", ""), lista.get("conta", "")
    saida, sem = [], []
    todos = lista.get("criativos", [])
    for n, c in enumerate(todos, 1):
        subprocess.run([sys.executable, os.path.join(AQUI, "progresso.py"), "item", str(n), str(len(todos)), c.get("nome", "")], check=False)
        cid = str(c["id"]); arq = os.path.join(pasta, f"{cid}.jpg")
        item = {k: c.get(k) for k in ("id", "tipo", "nome", "campanha", "gasto", "impressoes", "status", "nota")}
        if c["tipo"] == "video":
            publico = os.path.isfile(arq) or bool(c.get("publico"))
            if not os.path.isfile(arq):
                url = capa_video(pagina, cid)
                if url:
                    try:
                        open(arq, "wb").write(baixar(url)); publico = True
                    except Exception as e:
                        print(f"CAPA_FALHOU {cid}: {e}")
            if publico:
                href = f"https://www.facebook.com/{pagina}/videos/{cid}/"
                item["player"] = "https://www.facebook.com/plugins/video.php?href=" + urllib.parse.quote(href, safe="") + "&show_text=false&autoplay=true&width=560"
                item["link"] = href
        elif c.get("imagem_url") and not os.path.isfile(arq):
            try:
                open(arq, "wb").write(baixar(c["imagem_url"]))
            except Exception as e:
                print(f"IMAGEM_FALHOU {cid}: {e} (o endereço da imagem expira: puxar de novo pelo ads_get_creatives)")
        if os.path.isfile(arq):
            item["capa"] = f"../clientes/{a.cliente}/criativos/{cid}.jpg"
        else:
            sem.append(cid)
        if c.get("ad_id") and conta:
            item["gerenciador"] = f"https://www.facebook.com/adsmanager/manage/ads/edit?act={conta}&selected_ad_ids={c['ad_id']}"
        saida.append(item)
    pj = os.path.join(base, "painel.json")
    d = json.load(open(pj, encoding="utf-8"))
    d["criativos"] = sorted(saida, key=lambda x: -(x.get("gasto") or 0))
    d["criativos_fonte"] = lista.get("fonte", "")
    json.dump(d, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"CRIATIVOS_PRONTOS: {len(saida)} ({len(saida) - len(sem)} com capa)" + (f" | SEM_CAPA: {', '.join(sem)}" if sem else ""))
    cmd = [sys.executable, os.path.join(AQUI, "painel.py"), "--cliente", a.cliente] + (["--nao-abrir"] if a.nao_abrir else [])
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
