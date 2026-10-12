"""Conferência automática antes de entregar.

  python3 qc.py <pasta_do_video> [--cliente <pasta_cliente>] [--plataforma instagram|meta_ads|youtube_shorts] [--timeline "<nome>"]

Confere:
  1. Pastas e arquivos obrigatórios (roteiro.txt, links.txt, narracoes/, musica/, brolls/, videos/, legendas/).
  2. Vídeo final: resolução, duração dentro da regra da plataforma, quadros pretos (blackdetect), loudness (LUFS).
  3. Legendas: uma linha só, tamanho máximo, grafias proibidas do cliente (erros de transcrição), palavra fraca no fim.
  4. Takes: green screen, arquivos pesados (4K/ProRes) que travam o playback.
  4b. Legenda picotada (legendas.picotado) e, com --timeline, motions fora do tempo da fala.
  5. Gera folha de contato (qc_folha.jpg) com 6 quadros do vídeo final.
Saída: lista de OK / AVISO / ERRO. Corrigir os ERROs antes de entregar.
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from midia import info, green, pesado
from legendas import fraca

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg():
    for n in ("config.json", "config.example.json"):
        p = os.path.join(AQUI, n)
        if os.path.exists(p): return json.load(open(p))
    return {}


def motions_no_tempo(nome_tl, ok, av, tol_ini=0.5, tol_fim=0.8):
    """Motion tem que nascer com a fala que ilustra (regra 1h): início perto do início de uma legenda e fim perto do fim
    de uma legenda (ou do fim do vídeo). Fora disso, o motion foi feito no tempo errado: medir de novo e re-renderizar."""
    import resolve_lib as Rl
    from projeto import MOTION
    p = Rl.conectar().GetProjectManager().GetCurrentProject()
    t = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome_tl), None)
    if not t: av(f"timeline '{nome_tl}' não encontrada: checagem de motions pulada"); return
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); sec = lambda f: (f - S) / F
    subs = [(sec(x.GetStart()), sec(x.GetEnd())) for x in t.GetItemListInTrack("subtitle", 1) or []]
    fim_tl = sec(max(x.GetEnd() for x in t.GetItemListInTrack("video", 1)))
    for k in range(2, t.GetTrackCount("video") + 1):
        for x in t.GetItemListInTrack("video", k) or []:
            if not MOTION.search(x.GetName()): continue
            a, b = sec(x.GetStart()), sec(x.GetEnd())
            bom_ini = "cta" in x.GetName().lower() or any(abs(a - s0) <= tol_ini for s0, _ in subs)   # CTA: só o fim conta (termina com o vídeo)
            bom_fim = abs(b - fim_tl) <= tol_fim or any(abs(b - s1) <= tol_fim for _, s1 in subs)
            (ok if bom_ini and bom_fim else av)(f"motion {x.GetName()} {a:.1f}-{b:.1f}s " + ("bate com a fala" if bom_ini and bom_fim else
                f"fora do tempo da fala ({'início' if not bom_ini else ''}{' e ' if not bom_ini and not bom_fim else ''}{'fim' if not bom_fim else ''}): medir na legenda e re-renderizar"))


def main(pasta, cliente=None, plataforma="instagram", timeline=None):
    C = cfg(); R = C.get("regras", {}); res = []
    ok = lambda m: res.append(("OK", m)); av = lambda m: res.append(("AVISO", m)); er = lambda m: res.append(("ERRO", m))

    # gravado pela pessoa (talking head): não há narração gerada por voz de IA, então não há roteiro.txt
    gravado = os.path.isdir(os.path.join(pasta, "gravacao")) or not glob.glob(os.path.join(pasta, "narracoes", "narracao*.wav"))
    itens = ["links.txt", "narracoes|gravacao", "musica", "brolls", "legendas"] + ([] if gravado else ["roteiro.txt"])
    if C.get("opcoes", {}).get("renderizar_video"): itens.append("videos")
    for item in (["videos/capa.png", "videos/legenda_post.txt"] if C.get("opcoes", {}).get("capa_e_legenda_post") else []):
        (ok if os.path.exists(os.path.join(pasta, item)) else av)(f"entrega: {item} (capa e legenda do post)")
    for item in itens:
        # vídeo gravado pela pessoa (talking head) tem gravacao/ no lugar de narracoes/
        (ok if any(os.path.exists(os.path.join(pasta, x)) for x in item.split("|")) else er)(f"estrutura: {item}")

    vids = sorted(glob.glob(os.path.join(pasta, "videos", "*.mp4")), key=os.path.getmtime)
    if not vids: av("sem MP4 em videos/ (normal se o render ficou para o usuário); checagens do vídeo puladas")
    else:
        v = vids[-1]; i = info(v)
        ok(f"vídeo final {os.path.basename(v)}: {i['w']}x{i['h']}, {i['dur']:.1f}s")
        lim = R.get("duracao_segundos", {}).get(plataforma)
        if lim:
            if plataforma == "meta_ads":
                (ok if any(abs(i['dur'] - d) <= 1.5 for d in lim) else er)(f"duração Meta Ads deve ser uma de {lim}s")
            else:
                (ok if lim[0] - 1 <= i['dur'] <= lim[1] + 1 else er)(f"duração {plataforma}: {lim[0]} a {lim[1]} s")
        bd = subprocess.run(["ffmpeg", "-i", v, "-vf", "blackdetect=d=0.03:pix_th=0.05", "-an", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        pretos = re.findall(r"black_start:([\d.]+)", bd)
        (er if pretos else ok)(f"quadros pretos: {', '.join(pretos[:5]) or 'nenhum'}")
        ld = subprocess.run(["ffmpeg", "-i", v, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)
        if m:
            lufs = float(m[-1]); alvo = R.get("loudness_alvo_lufs", -14)
            (ok if abs(lufs - alvo) <= 3 else av)(f"loudness {lufs} LUFS (alvo {alvo})")
        # folha de contato
        d = i['dur']; tmp = []
        for k in range(6):
            o = os.path.join(pasta, f".qc_{k}.jpg"); tmp.append(o)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(d * (k + .5) / 6), "-i", v, "-frames:v", "1",
                            "-vf", "scale=240:-1", o])
        try:
            from PIL import Image
            im = [Image.open(x) for x in tmp]; fl = Image.new("RGB", (240 * 6, im[0].height))
            for k, x in enumerate(im): fl.paste(x, (240 * k, 0))
            fl.save(os.path.join(pasta, "qc_folha.jpg")); ok("folha de contato: qc_folha.jpg")
        finally:
            for x in tmp:
                if os.path.exists(x): os.remove(x)

    srts = sorted(glob.glob(os.path.join(pasta, "legendas", "*.srt")), key=os.path.getmtime)
    if srts:
        L = R.get("legenda", {}); mx = L.get("max_caracteres", 25)
        bl = open(srts[-1]).read().strip().split("\n\n"); linhas = [b.split("\n")[2:] for b in bl]
        if L.get("uma_linha", True):
            multi = [" / ".join(l) for l in linhas if len(l) > 1]
            (er if multi else ok)(f"legenda em uma linha ({len(multi)} com quebra)")
        longas = [l for b in linhas for l in b if len(l) > mx]
        (er if longas else ok)(f"legendas até {mx} caracteres" + (f": {longas[:3]}" if longas else ""))
        from legendas import metrica
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): probs = metrica(srts[-1], mx)
        (er if probs else ok)("métrica da legenda" + (f": {probs[:3]}" if probs else " (0 problema)"))
        from legendas import picotado
        comp = []
        if cliente and os.path.exists(os.path.join(cliente, "pronuncia.json")):
            comp = [t["grafia"] for t in json.load(open(os.path.join(cliente, "pronuncia.json"))).get("termos", []) if " " in t.get("grafia", "")]
        pic = picotado(srts[-1], comp)
        (er if pic else ok)("legenda sem frase/palavra picotada" + (f": {pic[:3]}" if pic else ""))
        if cliente and os.path.exists(os.path.join(cliente, "pronuncia.json")):
            bruto = " ".join(l for b in linhas for l in b)
            for t in json.load(open(os.path.join(cliente, "pronuncia.json"))).get("termos", []):
                for e in t.get("erros_transcricao", []):
                    so_caixa = e.lower() == t["grafia"].lower()
                    pad = r"(?<!\w)" + re.escape(e) + r"(?!\w)"   # palavra inteira ('Visa Bullet' não casa com 'Visa Bulletin')
                    achou = bool(re.search(pad, bruto)) if so_caixa else bool(re.search(pad, bruto, re.I))
                    if so_caixa and L.get("preset_trilha", {}).get("caixa_alta"): achou = False  # legenda vai em caixa alta
                    (er if achou else ok)(f"grafia: '{e}' -> '{t['grafia']}'")
    else: er("nenhum SRT em legendas/")

    if timeline: motions_no_tempo(timeline, ok, av)

    for f in sorted(glob.glob(os.path.join(pasta, "brolls", "take_*"))):
        nome = os.path.basename(f)
        if glob.glob(os.path.splitext(f)[0] + "_1080*"): continue  # já tem versão convertida em uso
        try:
            if pesado(f): av(f"{nome} pesado (4K/ProRes): converter com midia.py preparar_take")
            if R.get("evitar_green_screen", True) and green(f) > 0.25: er(f"{nome} parece green screen")
        except Exception as e: av(f"{nome}: não analisado ({e})")

    for tipo, msg in res: print(f"[{tipo}] {msg}")
    print(f"\n{sum(1 for t, _ in res if t == 'ERRO')} erro(s), {sum(1 for t, _ in res if t == 'AVISO')} aviso(s)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    main(a[0], opt("--cliente"), opt("--plataforma", "instagram"), opt("--timeline"))
