"""Grade de quadros com a PALAVRA falada embaixo de cada quadro: o jeito mais rápido de ler um vídeo de referência
(em que palavra o texto entra, o corte acontece, o motion sai). Ideia estudada no hypit (22/10/2026), código nosso.

  python3 grade.py <video> [--transcricao tr.json | --transcrever] [--de 0] [--ate 20] [--passo 0.5 | --quadros 12]
                   [--grade 4x3] [--celula 320] [--saida <pasta>] [--cortes] [--no-tempo t1,t2,...]

  --transcricao  JSON do transcrever.py ({"segments": [{"words": [{"text", "start", "end"}]}]}), em segundos do
                 arquivo; timecode HH:MM:SS:FF (DaVinci) também serve (desconta a primeira hora cheia se precisar).
  --transcrever  sem transcrição: extrai o áudio e roda transcrever.py --motor whisper (local, grátis).
  --passo / --quadros  de quanto em quanto tempo tirar um quadro (padrão: 12 quadros no trecho).
  --no-tempo     tempos exatos (ex.: os instantes das palavras que interessam) em vez do passo.
  --grade CxL    colunas x linhas por folha (passa disso, vira outra folha: grade_02.jpg...).
  --cortes       marca em vermelho o quadro logo depois de um corte de câmera (detecção de cena do ffmpeg).

Saída em <pasta> (padrão: <video>_grade/): grade_01.jpg..., e grade.md com a tabela tempo | palavra | frase | corte
para anotar cada elemento da referência: ENTRADA, COMPORTAMENTO, QUANTO FICA e SAÍDA, sempre presos à palavra.
Variar trecho, passo e tamanho conforme a leitura aprofunda: primeiro o vídeo inteiro (passo largo), depois só o
trecho que interessa com passo curto (0,1-0,2 s) para ver a curva de um motion.
"""
import json, os, re, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTES = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
          "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def _probe(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=r_frame_rate,width,height:format=duration", "-of", "json", video],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out); s = j["streams"][0]
    n, d = (s.get("r_frame_rate") or "30/1").split("/")
    return float(j["format"]["duration"]), float(n) / float(d or 1), int(s["width"]), int(s["height"])


def _seg(v, fps):
    if isinstance(v, (int, float)):
        return float(v)
    p = [int(x) for x in re.split(r"[:;]", str(v))]
    while len(p) < 4:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2] + p[3] / fps


def palavras(tr, fps, dur):
    ws = [{"t": w.get("text", "").strip(), "i": _seg(w["start"], fps), "f": _seg(w["end"], fps)}
          for s in tr.get("segments", []) for w in s.get("words", []) if w.get("text", "").strip()]
    if ws and ws[0]["i"] > dur + 1:   # timecode do DaVinci começando em 01:00:00:00
        h = int(ws[0]["i"] // 3600) * 3600
        for w in ws:
            w["i"] -= h; w["f"] -= h
    return ws


def no_tempo(ws, t):
    """(palavra falada em t ou a mais próxima até 0,3 s, frase de contexto com ~3 palavras de cada lado)."""
    if not ws:
        return "", ""
    k = min(range(len(ws)), key=lambda i: 0 if ws[i]["i"] <= t <= ws[i]["f"] else min(abs(ws[i]["i"] - t), abs(ws[i]["f"] - t)))
    w = ws[k]
    dentro = w["i"] - 0.3 <= t <= w["f"] + 0.3
    ctx = " ".join(("[" + x["t"] + "]") if j == k and dentro else x["t"] for j, x in enumerate(ws[max(0, k - 3):k + 4], max(0, k - 3)))
    return (w["t"] if dentro else ""), ctx


def cortes(video, de, ate, limiar=0.32):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(de), "-to", str(ate), "-i", video, "-vf",
                        f"select='gt(scene,{limiar})',showinfo", "-f", "null", "-"], capture_output=True, text=True)
    return [round(de + float(m), 3) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def _fonte(tam):
    from PIL import ImageFont
    for f in FONTES:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, tam)
            except Exception:
                pass
    return ImageFont.load_default()


def _quebra(draw, txt, fonte, larg):
    linhas, atual = [], ""
    for p in txt.split():
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= larg or not atual:
            atual = teste
        else:
            linhas.append(atual); atual = p
    if atual:
        linhas.append(atual)
    return linhas[:2]


def grade(video, tempos, ws, saida, cols=4, lins=3, celula=320, marcas_corte=()):
    from PIL import Image, ImageDraw
    dur, fps, w, h = _probe(video)
    alt_img = round(celula * h / w)
    rodape = max(64, celula // 4)
    f_t, f_p, f_c = _fonte(max(14, celula // 17)), _fonte(max(18, celula // 12)), _fonte(max(12, celula // 22))
    tmp = tempfile.mkdtemp(prefix="grade_")
    os.makedirs(saida, exist_ok=True)
    folhas, tabela, por_folha = [], [], cols * lins
    for n0 in range(0, len(tempos), por_folha):
        lote = tempos[n0:n0 + por_folha]
        rows = (len(lote) + cols - 1) // cols
        folha = Image.new("RGB", (cols * celula, rows * (alt_img + rodape)), (16, 16, 16))
        d = ImageDraw.Draw(folha)
        for k, t in enumerate(lote):
            q = os.path.join(tmp, f"q{n0 + k:04d}.png")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                            "-vf", f"scale={celula}:{alt_img}", q], check=True)
            x, y = (k % cols) * celula, (k // cols) * (alt_img + rodape)
            if os.path.exists(q):
                folha.paste(Image.open(q), (x, y))
            corte = any(0 <= t - c < 0.5 for c in marcas_corte)
            if corte:
                d.rectangle([x + 1, y + 1, x + celula - 2, y + alt_img - 2], outline=(235, 50, 50), width=4)
            pal, ctx = no_tempo(ws, t)
            d.rectangle([x, y + alt_img, x + celula, y + alt_img + rodape], fill=(0, 0, 0))
            d.text((x + 8, y + 6), f"{t:.2f}s" + ("  CORTE" if corte else ""), font=f_t, fill=(255, 220, 0),
                   stroke_width=2, stroke_fill=(0, 0, 0))
            d.text((x + 8, y + alt_img + 4), pal or "·", font=f_p, fill=(255, 255, 255))
            for i, l in enumerate(_quebra(d, ctx, f_c, celula - 16)):
                d.text((x + 8, y + alt_img + 8 + f_p.size + i * (f_c.size + 2)), l, font=f_c, fill=(170, 170, 170))
            tabela.append((t, pal, ctx, corte))
        arq = os.path.join(saida, f"grade_{len(folhas) + 1:02d}.jpg")
        folha.save(arq, quality=88); folhas.append(arq)
    md = ["# Grade com palavras", "", f"Vídeo: `{os.path.basename(video)}` ({dur:.1f} s, {fps:.2f} fps, {w}x{h})", "",
          "Para cada elemento da referência, anotar: ENTRADA (em que palavra), COMPORTAMENTO (caminho, escala, curva), "
          "QUANTO FICA e SAÍDA (em que palavra). Elemento que atravessa um corte é um sistema que vive mais que o plano.", "",
          "| Tempo | Palavra | Frase | Corte |", "| --- | --- | --- | --- |"]
    md += [f"| {t:.2f} | {p} | {c} | {'sim' if k else ''} |" for t, p, c, k in tabela]
    if marcas_corte:
        md += ["", "Cortes detectados: " + ", ".join(f"{c:.2f}s" for c in marcas_corte)]
    open(os.path.join(saida, "grade.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    return folhas


def main(a):
    if not a or a[0].startswith("-"):
        raise SystemExit(__doc__)
    video = os.path.abspath(a[0])

    def arg(n, pad=None):
        return a[a.index(n) + 1] if n in a else pad
    dur, fps, _, _ = _probe(video)
    de, ate = float(arg("--de", 0)), min(float(arg("--ate", dur)), dur - 0.05)
    if "--no-tempo" in a:
        tempos = [float(x) for x in arg("--no-tempo").split(",") if x.strip()]
    elif "--passo" in a:
        p = float(arg("--passo")); n = int((ate - de) / p) + 1
        tempos = [round(de + i * p, 3) for i in range(n) if de + i * p <= ate]
    else:
        n = int(arg("--quadros", 12))
        tempos = [round(de + (ate - de) * (i + 0.5) / n, 3) for i in range(n)]
    tr = None
    if arg("--transcricao"):
        tr = json.load(open(arg("--transcricao"), encoding="utf-8"))
    elif "--transcrever" in a:
        tmp = tempfile.mkdtemp(prefix="grade_tr_")
        wav, js = os.path.join(tmp, "audio.wav"), os.path.join(tmp, "transcricao.json")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
        subprocess.run([sys.executable, os.path.join(AQUI, "transcrever.py"), wav, js, "--motor", "whisper"], check=True)
        tr = json.load(open(js, encoding="utf-8"))
    ws = palavras(tr, fps, dur) if tr else []
    cg, lg = (int(x) for x in arg("--grade", "4x3").lower().split("x"))
    saida = os.path.abspath(arg("--saida", os.path.splitext(video)[0] + "_grade"))
    if tr:
        os.makedirs(saida, exist_ok=True)
        json.dump(tr, open(os.path.join(saida, "transcricao.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    marcas = cortes(video, de, ate) if "--cortes" in a else []
    for f in grade(video, tempos, ws, saida, cg, lg, int(arg("--celula", 320)), marcas):
        print(f)
    print(os.path.join(saida, "grade.md"))


if __name__ == "__main__":
    main(sys.argv[1:])
