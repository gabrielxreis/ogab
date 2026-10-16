#!/usr/bin/env python3
"""Liga módulos de efeito num projeto HyperFrames da /ogab (docs/etapas/fx.md).

    python3 fx.py cinema <projeto> [--nivel sutil|suave|forte] [--cor "#ff9a3c"] [--alvo "#push"] [--alfa]
                                   [--bloom .6 --grao .1 --aberracao 2 --vinheta .3 --vazamento .5]
    python3 fx.py cinema <projeto> --tirar
    python3 fx.py fisica <projeto>          # copia matter.js + fisica.js e liga no <head>; o uso vai no código do motion

Copia os .js para a pasta do projeto (o render não depende de rede) e escreve um bloco marcado no index.html;
rodar de novo troca o bloco, `--tirar` remove. O cinema entra DEPOIS do script da timeline (window.__timelines.main).
"""
import argparse, json, re, shutil
from pathlib import Path

FX = Path(__file__).resolve().parent.parent / "assets" / "fx"


def _bloco(html, nome, novo, onde):
    ini, fim = f"<!-- fx:{nome} -->", f"<!-- /fx:{nome} -->"
    html = re.sub(re.escape(ini) + r".*?" + re.escape(fim) + r"\n?", "", html, flags=re.S)
    if novo is None:
        return html
    bloco = f"{ini}\n{novo}\n{fim}\n"
    if onde == "head":
        i = html.find("<script")  # antes do primeiro script do projeto (GSAP pode vir antes, tanto faz)
        i = html.find("</head>") if i < 0 else i
        return html[:i] + bloco + html[i:]
    i = html.rfind("</body>")
    return html[:i] + bloco + html[i:]


def cinema(g):
    pasta = Path(g.projeto).expanduser().resolve()
    idx = pasta / "index.html"
    html = idx.read_text(encoding="utf-8")
    if g.tirar:
        idx.write_text(_bloco(html, "cinema", None, "body"), encoding="utf-8")
        print("cinema removido")
        return
    shutil.copy(FX / "cinema.js", pasta / "cinema.js")
    op = {"nivel": g.nivel}
    for k in ("cor", "alvo", "bloom", "grao", "aberracao", "vinheta", "vazamento", "limiar", "raio"):
        v = getattr(g, k)
        if v is not None:
            op[k] = v
    if g.alfa:
        op["alfa"] = True
    if "alvo" not in op:
        m = re.search(r'id="(push|palco|stage|world|cena)"', html)
        if m:
            op["alvo"] = "#" + m.group(1)
    novo = ('<script src="cinema.js"></script>\n'
            f"<script>Cinema.aplicar(window.__timelines.main, {json.dumps(op, ensure_ascii=False)});</script>")
    idx.write_text(_bloco(html, "cinema", novo, "body"), encoding="utf-8")
    print(f"cinema ligado: {op}")


def fisica(g):
    pasta = Path(g.projeto).expanduser().resolve()
    idx = pasta / "index.html"
    for f in ("matter.min.js", "fisica.js"):
        shutil.copy(FX / f, pasta / f)
    html = idx.read_text(encoding="utf-8")
    idx.write_text(_bloco(html, "fisica", '<script src="matter.min.js"></script>\n<script src="fisica.js"></script>', "head"),
                   encoding="utf-8")
    print("física ligada: use Fisica.cair(tl, {...}) / Fisica.explodir(tl, {...}) no script do motion")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("cinema"); c.add_argument("projeto")
    c.add_argument("--nivel", default="suave", choices=["sutil", "suave", "forte"])
    c.add_argument("--cor"); c.add_argument("--alvo"); c.add_argument("--alfa", action="store_true")
    for k in ("bloom", "grao", "aberracao", "vinheta", "vazamento", "limiar", "raio"):
        c.add_argument("--" + k, type=float)
    c.add_argument("--tirar", action="store_true")
    f = sp.add_parser("fisica"); f.add_argument("projeto")
    g = ap.parse_args()
    {"cinema": cinema, "fisica": fisica}[g.cmd](g)


if __name__ == "__main__":
    main()
