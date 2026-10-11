"""Pauta automática: busca notícias recentes sobre os temas do cliente e lista candidatas a vídeo.

  python3 pauta.py "<tema1>; <tema2>" [--fonte gratis|newsapi|gnews] [--dias 7] [--n 8] [--idioma pt]

Fontes:
  gratis  -> Google News RSS (sem chave, sem custo)
  newsapi -> https://newsapi.org (variável de ambiente NEWSAPI_KEY; plano gratuito tem limites)
  gnews   -> https://gnews.io     (variável de ambiente GNEWS_KEY)
Saída: JSON com título, fonte, data e link. A skill usa isso para sugerir 2-3 roteiros para aprovação.
"""
import json, os, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


def gratis(q, dias, n, idioma):
    hl = {"pt": "pt-BR&gl=BR&ceid=BR:pt-419", "en": "en-US&gl=US&ceid=US:en"}.get(idioma, "pt-BR&gl=BR&ceid=BR:pt-419")
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q + f' when:{dias}d')}&hl={hl}"
    root = ET.fromstring(urllib.request.urlopen(url, timeout=20).read())
    out = []
    for it in root.iter("item"):
        out.append({"titulo": it.findtext("title"), "link": it.findtext("link"),
                    "data": it.findtext("pubDate"), "fonte": (it.find("source").text if it.find("source") is not None else "")})
    return out[:n]


def newsapi(q, dias, n, idioma):
    k = os.environ.get("NEWSAPI_KEY") or sys.exit("defina NEWSAPI_KEY")
    de = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q={urllib.parse.quote(q)}&from={de}&language={idioma}&sortBy=publishedAt&pageSize={n}&apiKey={k}"
    j = json.load(urllib.request.urlopen(url, timeout=20))
    return [{"titulo": a["title"], "link": a["url"], "data": a["publishedAt"], "fonte": a["source"]["name"]} for a in j.get("articles", [])]


def gnews(q, dias, n, idioma):
    k = os.environ.get("GNEWS_KEY") or sys.exit("defina GNEWS_KEY")
    de = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://gnews.io/api/v4/search?q={urllib.parse.quote(q)}&from={de}&lang={idioma}&max={n}&apikey={k}"
    j = json.load(urllib.request.urlopen(url, timeout=20))
    return [{"titulo": a["title"], "link": a["url"], "data": a["publishedAt"], "fonte": a["source"]["name"]} for a in j.get("articles", [])]


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    fonte = {"gratis": gratis, "newsapi": newsapi, "gnews": gnews}[opt("--fonte", "gratis")]
    res = []
    for tema in [t.strip() for t in a[0].split(";") if t.strip()]:
        for x in fonte(tema, int(opt("--dias", 7)), int(opt("--n", 8)), opt("--idioma", "pt")):
            x["tema"] = tema; res.append(x)
    print(json.dumps(res, ensure_ascii=False, indent=1))
