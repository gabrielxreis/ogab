"""Legenda automática do YouTube (.vtt com tempo por palavra) -> transcricao.json no formato da /ogab
({"segments": [{"words": [{"text", "start", "end"}]}]}), o mesmo que o fabrica_cortes.py e o cortes.py leem.

Serve para vídeo longo baixado com yt-dlp (`--write-auto-subs --sub-langs pt --sub-format vtt`): dá para escolher
os cortes antes do vídeo terminar de baixar e sem gastar transcrição. Depois de montar, a legenda final do corte
continua saindo pela transcrição do editor (regra da skill).

  python3 vtt_transcricao.py <legenda.vtt> <transcricao.json>
"""
import html, json, re, sys

TEMPO = r"(\d+):(\d\d):(\d\d)\.(\d{3})"


def seg(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def palavras(vtt):
    """Só as linhas com <00:00:00.000> (as palavras novas de cada bloco); as repetidas do bloco anterior ficam fora."""
    ws, bloco_ini, bloco_fim = [], 0.0, 0.0
    for linha in open(vtt, encoding="utf-8"):
        linha = linha.rstrip("\n")
        m = re.match(TEMPO + r" --> " + TEMPO, linha)
        if m:
            g = m.groups()
            bloco_ini, bloco_fim = seg(*g[:4]), seg(*g[4:])
            continue
        if "<c>" not in linha and not re.search("<" + TEMPO + ">", linha):
            continue
        partes = re.split("<" + TEMPO + ">", linha)
        # partes = [texto0, h, m, s, ms, texto1, h, m, s, ms, texto2, ...]
        t0 = bloco_ini
        textos = [(t0, partes[0])]
        for i in range(1, len(partes), 5):
            textos.append((seg(*partes[i:i + 4]), partes[i + 4]))
        for k, (ini, txt) in enumerate(textos):
            txt = html.unescape(re.sub(r"</?c[^>]*>", "", txt)).replace(">>", " ").strip()
            if not txt or txt.startswith("["):   # [música], [aplausos]; ">>" (troca de quem fala) sai do texto
                continue
            fim = textos[k + 1][0] if k + 1 < len(textos) else bloco_fim
            for p in txt.split():
                ws.append({"text": p, "start": round(ini, 3), "end": round(max(fim, ini + .05), 3)})
    return ws


def main(vtt, saida):
    ws = palavras(vtt)
    # um segmento por pausa > 1 s, para leitura
    segs, cur = [], []
    for w in ws:
        if cur and w["start"] - cur[-1]["end"] > 1.0:
            segs.append(cur); cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    out = {"fonte": vtt, "segments": [{"start": s[0]["start"], "end": s[-1]["end"],
                                       "text": " ".join(w["text"] for w in s), "words": s} for s in segs]}
    json.dump(out, open(saida, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{saida}: {len(ws)} palavras, {len(segs)} segmentos, até {ws[-1]['end'] / 60:.1f} min" if ws else "sem palavras")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
