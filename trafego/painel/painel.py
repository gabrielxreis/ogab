#!/usr/bin/env python3
"""Painel do Gab (tráfego): junta clientes/*/painel.json em painel/dados.js e abre o painel no navegador.

Uso:
  python3 ~/.claude/skills/ogab/trafego/painel/painel.py --cliente xtrader      # atualiza; abre só se não abriu nas últimas 6 h
  python3 ~/.claude/skills/ogab/trafego/painel/painel.py --cliente xtrader --abrir   # força abrir uma aba
  python3 ~/.claude/skills/ogab/trafego/painel/painel.py --cliente xtrader --nao-abrir
  python3 ~/.claude/skills/ogab/trafego/painel/painel.py --checar                # só valida os painel.json

O formato do painel.json está em painel/LEIA.md. dados.js e os painel.json ficam fora do git.
"""
import argparse
import hashlib
import json
import time
import os
import socket
import subprocess
import sys
import webbrowser

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
CLIENTES = os.path.join(SKILL, "clientes")
OBRIGATORIOS = ["cliente", "atualizado", "resumo", "campanhas", "parecer"]
PORTA = 47830
URL = f"http://127.0.0.1:{PORTA}/painel/index.html"


def servidor_no_ar():
    try:
        with socket.create_connection(("127.0.0.1", PORTA), timeout=0.5):
            return True
    except OSError:
        return False


def subir_servidor():
    """Servidor local (servidor.py) para o botão de baixar funcionar; sobe em segundo plano se não estiver rodando."""
    if servidor_no_ar():
        return True
    subprocess.Popen([sys.executable, os.path.join(AQUI, "servidor.py"), "--porta", str(PORTA)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(20):
        time.sleep(0.15)
        if servidor_no_ar():
            return True
    return False


def marcar_videos(nome, d):
    """Liga o botão de baixar a todo vídeo de concorrente que já está em clientes/<nome>/criativos_concorrentes/."""
    pasta = os.path.join(CLIENTES, nome, "criativos_concorrentes")
    tem = set()
    if os.path.isdir(pasta):
        tem = {f[len("concorrente_"):-4] for f in os.listdir(pasta) if f.startswith("concorrente_") and f.endswith(".mp4")}
    itens = [c for p in d.get("concorrentes_principais", []) for c in p.get("campeoes", [])] + d.get("concorrentes", [])
    for c in itens:
        if str(c.get("id")) in tem:
            c["video_local"] = f"../clientes/{nome}/criativos_concorrentes/concorrente_{c['id']}.mp4"
        else:
            c.pop("video_local", None)


def marcar_miniaturas(nome, d):
    """Liga a miniatura de todo campeão/anúncio que tem clientes/<nome>/miniaturas/<id>.jpg; devolve os IDs sem miniatura."""
    pasta = os.path.join(CLIENTES, nome, "miniaturas")
    itens = [c for p in d.get("concorrentes_principais", []) for c in p.get("campeoes", [])] + d.get("concorrentes", [])
    faltam = []
    for c in itens:
        if os.path.isfile(os.path.join(pasta, f"{c.get('id')}.jpg")):
            c["miniatura"] = f"../clientes/{nome}/miniaturas/{c['id']}.jpg"
        else:
            c.pop("miniatura", None)
            if not c.get("fora_do_ar") and str(c.get("id")) not in faltam:
                faltam.append(str(c.get("id")))
    return faltam


# conector oficial do Meta para o Claude ler a conta de anúncios (sem ele o painel fica sem campanhas)
CONECTOR_META = "https://mcp.facebook.com/ads"

def carregar():
    dados, erros = {}, []
    if not os.path.isdir(CLIENTES):
        return dados, erros
    for nome in sorted(os.listdir(CLIENTES)):
        caminho = os.path.join(CLIENTES, nome, "painel.json")
        if nome.startswith("_") or not os.path.isfile(caminho):
            continue
        try:
            with open(caminho, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:  # noqa: BLE001
            erros.append(f"{nome}: painel.json inválido ({e})")
            continue
        marcar_videos(nome, d)
        sem_mini = marcar_miniaturas(nome, d)
        falta = [k for k in OBRIGATORIOS if k not in d]
        if falta:
            erros.append(f"{nome}: falta {', '.join(falta)}")
        if (d.get("concorrentes") or d.get("concorrentes_principais")) and not d.get("concorrentes_principais"):
            erros.append(f"CAMPEOES_FALTANDO: {nome} tem concorrentes sem concorrentes_principais/campeoes (puxar pela Biblioteca agora)")
        if not d.get("campanhas"):
            erros.append(f"SEM_META_ADS: {nome}: sem campanhas lidas. Oriente: no Claude, Configurações > Conectores > "
                         f"Adicionar conector personalizado com {CONECTOR_META}; entrar com o Facebook, autorizar e escolher "
                         f"a conta de anúncios do ativo (a do negócio do cliente); depois /ogab trafego painel {nome}")
        if sem_mini:
            erros.append(f"FALTAM_MINIATURAS: {nome}: {len(sem_mini)} ({', '.join(sem_mini)}) -> painel/miniaturas.py --cliente {nome} --faltam")
        dados[nome] = d
    return dados, erros


def abrir(arquivo):
    url = URL if subir_servidor() else "file://" + arquivo
    if sys.platform == "darwin":
        subprocess.run(["open", url], check=False)
    elif os.name == "nt":
        os.startfile(url)  # type: ignore[attr-defined]
    else:
        webbrowser.open(url)
    return url


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", help="pasta do cliente em clientes/ que abre primeiro")
    ap.add_argument("--nao-abrir", action="store_true", help="só gera o dados.js")
    ap.add_argument("--abrir", action="store_true", help="abre uma aba mesmo que já tenha aberto há pouco")
    ap.add_argument("--checar", action="store_true", help="só valida os painel.json")
    ap.add_argument("--idioma", choices=["pt", "en"], help="idioma do painel: o da conversa (fica gravado em painel/.idioma)")
    a = ap.parse_args()

    dados, erros = carregar()
    for e in erros:
        print("AVISO:", e)
    if a.checar:
        print(f"{len(dados)} painel(is) lido(s)")
        return 1 if erros else 0
    if not dados:
        print("SEM_DADOS: nenhum clientes/<nome>/painel.json. Monte um pelo modelo clientes/_exemplo/painel.json.")
        return 1
    atual = a.cliente if a.cliente in dados else max(dados, key=lambda k: dados[k].get("atualizado", ""))
    if a.cliente and a.cliente not in dados:
        print(f"AVISO: {a.cliente} sem painel.json; abrindo {atual}")

    arq_idioma = os.path.join(AQUI, ".idioma")
    if a.idioma:
        with open(arq_idioma, "w") as f:
            f.write(a.idioma)
    idioma = a.idioma or (open(arq_idioma).read().strip() if os.path.isfile(arq_idioma) else "pt")
    corpo = json.dumps(dados, ensure_ascii=False, sort_keys=True)
    versao = hashlib.sha1((corpo + atual + idioma).encode("utf-8")).hexdigest()[:12]
    js = ("window.JHON_DADOS = " + corpo + ";\nwindow.JHON_ATUAL = " + json.dumps(atual)
          + ";\nwindow.JHON_VERSAO = " + json.dumps(versao) + ";\nwindow.JHON_IDIOMA = " + json.dumps(idioma) + ";\n")
    fav = os.path.join(AQUI, "favorito.url.txt")
    if os.path.isfile(fav):
        js += "window.JHON_FAVORITO = " + json.dumps(open(fav, encoding="utf-8").read().strip()) + ";\n"
    with open(os.path.join(AQUI, "dados.js"), "w", encoding="utf-8") as f:
        f.write(js)

    index = os.path.join(AQUI, "index.html")
    marca = os.path.join(AQUI, ".aberto")
    recente = os.path.isfile(marca) and time.time() - os.path.getmtime(marca) < 6 * 3600
    no_ar = subir_servidor()
    if a.nao_abrir:
        print("PAINEL_PRONTO: " + (URL if no_ar else "file://" + index))
    elif recente and not a.abrir:
        print("PAINEL_ATUALIZADO: a aba aberta recarrega sozinha em poucos segundos (" + (URL if no_ar else "file://" + index) + ")")
    else:
        print("PAINEL_ABERTO: " + abrir(index))
        with open(marca, "w") as f:
            f.write(str(time.time()))
    print(f"cliente: {atual} | clientes no painel: {', '.join(dados)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
