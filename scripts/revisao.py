"""Revisão OBRIGATÓRIA da timeline antes de mostrar ou exportar (regra do usuário, 27/10/2026: "mais uma vez o problema dos
buracos entre um vídeo e outro... a parte de revisão precisa existir com a skill para ela não deixar esses furos").
Sai com código 1 se houver qualquer ERRO; só mostra ao usuário com 0 ERRO.

  python3 revisao.py "<timeline>" [--pasta <pasta do vídeo>] [--corrigir]

Confere:
  1. BURACO na V1 e na A1 (qualquer quadro entre dois clipes, ou começo depois do 0) e VÃO de até 0,6 s entre clipes
     seguidos de uma mesma trilha de cima (V2+: b-roll, motion, CTA): nesse vão a imagem de baixo pisca.
     --corrigir fecha os vãos das trilhas de cima: estica o clipe anterior até o seguinte (ou puxa o seguinte, se a
     mídia do anterior não tiver sobra). Buraco na V1/A1 não se corrige sozinho: é erro de montagem, remontar.
  2. ROSTO: mede o rosto da gravação da V1 (detector da OpenCV) com o zoom/pan/tilt aplicados na timeline: queixo acima
     da faixa da legenda (QUEIXO_MAX) e rosto no centro (até 70 px). Sem enquadramento aplicado e fora disso = ERRO,
     com o valor certo de `enquadrar()` para aplicar.
  3. COR: exporta do DaVinci 3 quadros só com a V1 (sem nada por cima) e mede os tons claros e pouco saturados
     (parede, camiseta, papel): azul muito abaixo do vermelho = AMARELADO; o contrário = AZULADO; verde demais = VERDE.
  4. ÁUDIO x IMAGEM: a A1 cobre a V1 inteira (mesmo início e fim de cada clipe da gravação).
"""
import os, sys, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R

ERROS, AVISOS = [], []
VAO_MAX = 0.6


def tl_por_nome(p, nome):
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == nome:
            return t
    raise SystemExit(f"timeline {nome!r} não existe")


def itens(t, k, n):
    return sorted(t.GetItemListInTrack(k, n) or [], key=lambda x: x.GetStart())


def buracos(t, mp, corrigir):
    S, F = t.GetStartFrame(), R.fps_tl(t)
    for k in ("video", "audio"):
        its = itens(t, k, 1)
        if its and its[0].GetStart() > S:
            ERROS.append(f"BURACO no começo da {k[0].upper()}1: {(its[0].GetStart() - S) / F:.2f} s vazios")
        for a, b in zip(its, its[1:]):
            g = b.GetStart() - a.GetEnd()
            if g > 0:
                ERROS.append(f"BURACO na {k[0].upper()}1 em {(a.GetEnd() - S) / F:.2f} s ({g} quadros): remontar a gravação")
    if corrigir: R.pagina_edit()
    tentativas = {}
    for n in range(2, t.GetTrackCount("video") + 1):
        mudou = True
        while mudou:
            mudou = False
            its = itens(t, "video", n)
            for a, b in zip(its, its[1:]):
                g = b.GetStart() - a.GetEnd()
                if not (0 < g <= round(VAO_MAX * F)):
                    continue
                onde = f"V{n} em {(a.GetEnd() - S) / F:.2f} s ({g} quadros entre {a.GetName()} e {b.GetName()})"
                if not corrigir:
                    ERROS.append("VÃO " + onde + ": a imagem de baixo pisca (rodar com --corrigir)"); continue
                mpa = a.GetMediaPoolItem(); tot = int(float(mpa.GetClipProperty("Frames") or 0))
                props = {pr: float(a.GetProperty(pr) or 0) for pr in ("ZoomX", "ZoomY", "Pan", "Tilt")}
                fps_a = float(mpa.GetClipProperty("FPS") or F)
                la = a.GetLeftOffset(); da = a.GetDuration()
                # fontes em outro fps: o offset vem em quadros da timeline; a mídia conta em quadros dela
                # arredonda o fim para CIMA: com round() um take de outro fps (4K 25/29,97 numa timeline 24) voltava
                # com o mesmo tamanho, o vão nunca fechava e o laço rodava para sempre (27/10/2026, 06 HORA EXTRA)
                ini_src = int(round(la * fps_a / F)); fim_src = int(math.ceil((la + da + g) * fps_a / F)) + tentativas.get(onde, 0)
                if tot and fim_src <= tot:
                    rec = a.GetStart(); t.DeleteClips([a], False)
                    x = mp.AppendToTimeline([{"mediaPoolItem": mpa, "mediaType": 1, "trackIndex": n, "recordFrame": rec,
                                              "startFrame": ini_src, "endFrame": fim_src}])
                else:   # sem sobra no anterior: puxa o início do seguinte para trás
                    mpb = b.GetMediaPoolItem(); fps_b = float(mpb.GetClipProperty("FPS") or F)
                    props = {pr: float(b.GetProperty(pr) or 0) for pr in ("ZoomX", "ZoomY", "Pan", "Tilt")}
                    lb = b.GetLeftOffset(); db = b.GetDuration()
                    if lb < g:
                        ERROS.append("VÃO " + onde + ": nenhum dos dois clipes tem sobra, refazer o trecho"); continue
                    rec = a.GetEnd(); t.DeleteClips([b], False)
                    x = mp.AppendToTimeline([{"mediaPoolItem": mpb, "mediaType": 1, "trackIndex": n, "recordFrame": rec,
                                              "startFrame": int(round((lb - g) * fps_b / F)), "endFrame": int(round((lb + db) * fps_b / F))}])
                tentativas[onde] = tentativas.get(onde, 0) + 1
                if tentativas[onde] > 3:
                    ERROS.append("VÃO " + onde + ": não fechou em 3 tentativas, ajustar à mão"); continue
                if x:
                    orig = a if x[0].GetName() == a.GetName() else b
                    for pr in ("ZoomX", "ZoomY", "Pan", "Tilt"):
                        v = props.get(pr)
                        if v is not None: x[0].SetProperty(pr, v)
                    AVISOS.append("corrigido: " + onde); mudou = True; break
                ERROS.append("VÃO " + onde + ": não consegui recolocar o clipe")


def rosto(t):
    its = itens(t, "video", 1)
    if not its: ERROS.append("V1 vazia"); return
    arq = its[0].GetMediaPoolItem().GetClipProperty("File Path")
    face = R.medir_rosto(arq, passo_s=3.0) if arq and os.path.exists(arq) else None
    if not face: AVISOS.append("ROSTO: não achei rosto na gravação (sem conferência de enquadramento)"); return
    x = its[0]; z = float(x.GetProperty("ZoomX") or 1); pan = float(x.GetProperty("Pan") or 0); tilt = float(x.GetProperty("Tilt") or 0)
    fx = 540 + (face["cx"] - 540) * z + pan; fy = 960 + (face["cy"] - 960) * z - tilt
    queixo = fy + 0.6 * face["lado"] * z; certo = R.enquadrar(face)
    if queixo > R.QUEIXO_MAX + 10:
        if z >= R.ZOOM_MAX - 0.002 and certo[0] >= R.ZOOM_MAX - 0.002:
            AVISOS.append(f"ROSTO: gravação fechada demais, queixo em y {queixo:.0f} já no zoom máximo {R.ZOOM_MAX} (legenda pode encostar no queixo)")
        else:
            ERROS.append(f"ROSTO baixo: queixo em y {queixo:.0f} (máx {R.QUEIXO_MAX}), aplicar enquadrar() = zoom/pan/tilt {certo}")
    if abs(fx - 540) > 70:
        ERROS.append(f"ROSTO fora do centro: x {fx:.0f} (centro 540), aplicar enquadrar() = {certo}")
    dif = {round(float(i.GetProperty("ZoomX") or 1), 3) for i in its} | set()
    if len(dif) > 1: AVISOS.append(f"ROSTO: zoom diferente entre os cortes da V1 {sorted(dif)} (sem punch-in alternado)")


def cor(p, t, pasta):
    """3 quadros onde só a V1 aparece; mede os pixels claros e pouco saturados."""
    from PIL import Image
    import conferir
    S, F = t.GetStartFrame(), R.fps_tl(t); fim = (t.GetEndFrame() - S) / F
    cobertos = [((i.GetStart() - S) / F, (i.GetEnd() - S) / F) for n in range(2, t.GetTrackCount("video") + 1) for i in itens(t, "video", n)]
    livres = [s for s in [fim * k / 20 for k in range(1, 20)] if not any(a - .2 <= s <= b + .2 for a, b in cobertos)]
    if not livres: AVISOS.append("COR: nenhum trecho só com a V1 para medir"); return
    pegar = [livres[0], livres[len(livres) // 2], livres[-1]]
    # caminho ABSOLUTO: pasta relativa dava "Render path inaccessible" no DaVinci e travava a revisão (28/10/2026)
    destino = os.path.abspath(os.path.join(pasta, "revisao_cor")); os.makedirs(destino, exist_ok=True)
    out = conferir.exportar(p, t, [(s, "cor") for s in pegar], destino)
    rb, gb, rb_neutro = [], [], []
    for png, s, _ in out:
        im = Image.open(png).convert("RGB").resize((270, 480))
        todos = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
        px = [c for c in todos if sum(c) / 3 > 140 and max(c) - min(c) < 70]
        if len(px) < 200: continue
        r_ = st.mean(c[0] for c in px); g_ = st.mean(c[1] for c in px); b_ = st.mean(c[2] for c in px)
        rb.append(r_ - b_); gb.append(g_ - (r_ + b_) / 2)
        # AZULADO só nos tons quase sem cor: camisa jeans/azul clara entrava como "tom claro" e dava falso
        # COR AZULADA com a cor certa (28/10/2026, 4 vídeos do Ediel de camisa azul)
        # só o terço de cima do quadro (parede/estante atrás): a camisa fica embaixo e enganava (azul ou preta)
        topo = todos[: len(todos) * 2 // 5]
        nt = [c for c in topo if sum(c) / 3 > 140 and max(c) - min(c) < 40]
        if len(nt) >= 120: rb_neutro.append(st.mean(c[0] - c[2] for c in nt))
    if not rb: AVISOS.append("COR: poucos tons claros para medir"); return
    d, v = st.mean(rb), st.mean(gb); dn = st.mean(rb_neutro) if rb_neutro else d
    # camisa preta deixa só pele como "tom claro" e dava falso AMARELADA (28/10/2026): exige os neutros quentes também
    if d > 28 and dn > 14: ERROS.append(f"COR AMARELADA: nos tons claros o vermelho está {d:.0f} acima do azul (máx 28); tirar a LUT/PowerGrade quente ou esfriar no CDL")
    elif dn < -18: ERROS.append(f"COR AZULADA: azul {-dn:.0f} acima do vermelho nos tons neutros")
    if v > 12: ERROS.append(f"COR ESVERDEADA: verde {v:.0f} acima nos tons claros")
    AVISOS.append(f"cor medida em {len(rb)} quadros: vermelho-azul {d:.0f} (neutros {dn:.0f}), verde {v:.0f}")


def bordas(t):
    """Take mais estreito/largo que a timeline (ex.: 4K 2160x4096 numa 1080x1920) precisa de zoom de preencher, senão
    sobra borda preta dos lados (usuário, 28/10/2026: "tem take que precisa dar um scale para completar as bordas")."""
    for n in range(2, t.GetTrackCount("video") + 1):
        for x in itens(t, "video", n):
            mpi = x.GetMediaPoolItem()
            if not mpi: continue
            fp = mpi.GetClipProperty("File Path") or ""
            if not fp.lower().endswith((".mp4", ".mov", ".m4v")) or "/motions/" in fp: continue
            z = R._zoom_preencher(mpi, t); atual = float(x.GetProperty("ZoomX") or 1)
            if z > 1.001 and atual < z - 0.002:
                ERROS.append(f"BORDA no take {os.path.basename(fp)} (V{n}, {mpi.GetClipProperty('Resolution')}): zoom {atual:.3f}, precisa {z:.3f}")


def v1_sem_som(t):
    """Vídeo inteiro em motion / narração por IA: a V1 é o motion (sem áudio) e a fala mora na A1.
    Também quando a V1 são takes de IA (Seedance) com som próprio, mas só a imagem entrou: a A1 é uma narração que não
    vem de nenhum arquivo da V1 (30/10/2026, teaser da Black: o som do take virava 'retake' e 'silêncio' falsos)."""
    its = itens(t, "video", 1)
    if not its or not its[0].GetMediaPoolItem(): return False
    def _arq(x): return (x.GetMediaPoolItem().GetClipProperty("File Path") or "") if x.GetMediaPoolItem() else ""
    a1 = {_arq(x) for x in itens(t, "audio", 1)} - {""}
    if a1 and not (a1 & {_arq(x) for x in its}): return True
    arq = its[0].GetMediaPoolItem().GetClipProperty("File Path") or ""
    if not os.path.exists(arq): return False
    import subprocess
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", arq],
                       capture_output=True, text=True).stdout.strip()
    return not o


def v1_tem_take(t):
    """Algum clipe da V1 é gravação/take com som próprio (o rosto ainda se confere, mesmo com a fala na A1)."""
    import subprocess
    for x in itens(t, "video", 1):
        arq = (x.GetMediaPoolItem().GetClipProperty("File Path") or "") if x.GetMediaPoolItem() else ""
        if arq and os.path.exists(arq) and subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                                           "stream=index", "-of", "csv=p=0", arq], capture_output=True, text=True).stdout.strip():
            return True
    return False


def fala(t):
    """LEI 1 e 2. SILÊNCIO pela energia do áudio da gravação, no que ficou na timeline (pausa sem voz > 0,35 s, ou
    começo sem fala > 0,45 s). REPETIÇÃO/RETAKE/GAGUEJO pela transcrição literal de trechos grandes (palavra que
    atravessa um corte não some; 28/10/2026: transcrever pedacinho por pedacinho dava silêncio falso)."""
    try:
        import limpar_fala as LF
    except Exception as e:
        ERROS.append(f"FALA: limpar_fala indisponível ({e}), checagem de fala não rodou"); return
    S, F = t.GetStartFrame(), R.fps_tl(t); its = itens(t, "audio", 1) if v1_sem_som(t) else itens(t, "video", 1)
    if not its: return
    arq = its[0].GetMediaPoolItem().GetClipProperty("File Path")
    if not arq or not os.path.exists(arq): return
    pedacos = [(x.GetLeftOffset() / F, x.GetLeftOffset() / F + x.GetDuration() / F, (x.GetStart() - S) / F) for x in its]
    env = LF._envelope(arq)
    if env:
        db, passo = env
        topo = sorted(db)[int(len(db) * 0.6):]; ref = topo[len(topo) // 2] if topo else -20
        voz = []
        for lo, hi, rec in pedacos:
            voz += [db[k] > ref - 16 for k in range(int(lo / passo), min(len(db), int(hi / passo)))]
        k0 = next((k for k, v in enumerate(voz) if v), 0)
        if k0 * passo > 0.45: ERROS.append(f"SILÊNCIO no começo: a voz começa em {k0 * passo:.2f} s")
        k = k0
        while k < len(voz):
            if not voz[k]:
                j = k
                while j < len(voz) and not voz[j]: j += 1
                if (j - k) * passo > 0.35 and j < len(voz):
                    ERROS.append(f"SILÊNCIO de {(j - k) * passo:.2f} s em {k * passo:.2f} s")
                k = j
            else:
                k += 1
    # REPETIÇÃO pela transcrição do ÁUDIO COMO FICOU na timeline (pedaços da V1 emendados, só para análise; nada
    # disso vai para a timeline). Transcrever a gravação e distribuir as palavras nos cortes perdia palavra curta na
    # emenda e dava gaguejo falso ("como for. Se for" virava "for for", 28/10/2026).
    import tempfile, subprocess, hashlib, json as _json
    chave = hashlib.md5(repr([(round(lo, 3), round(hi, 3)) for lo, hi, _ in pedacos]).encode()).hexdigest()[:12]
    cache = arq + f".revisao_{chave}.json"
    if os.path.exists(cache):
        seq = _json.load(open(cache, encoding="utf-8"))
    else:
        try:
            import mlx_whisper
            with tempfile.TemporaryDirectory() as tmp:
                partes = []
                for k, (lo, hi, rec) in enumerate(pedacos):
                    o = os.path.join(tmp, f"{k:04d}.wav")
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{lo:.3f}", "-to", f"{hi:.3f}", "-i", arq,
                                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", o], check=True)
                    partes.append(o)
                lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{x}'\n" for x in partes))
                junto = os.path.join(tmp, "junto.wav")
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", junto], check=True)
                r = mlx_whisper.transcribe(junto, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="pt",
                                           word_timestamps=True, condition_on_previous_text=False)
            seq = [{"text": w["word"].strip(), "start": w["start"], "end": w["end"]} for sg in r["segments"] for w in sg.get("words", [])]
            _json.dump(seq, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception as e:
            ERROS.append(f"FALA: transcrição do áudio da timeline falhou ({e})"); return
    fins = [rec + hi - lo for lo, hi, rec in pedacos]
    for a, b, motivo, txt in LF.detectar(seq):
        # "técnico..." colado num corte: a pausa que fez o whisper pôr reticências já foi cortada (15 CARGA DE VENTO)
        if motivo == "HESITAÇÃO" and any(a <= f <= b + 0.4 for f in fins): continue
        if motivo != "HESITAÇÃO" or b - a > 0.15:
            ERROS.append(f"FALA {motivo} em {a:.2f} s: '{txt}' (tirar, fica só a última tentativa)")


def fim_do_video(t):
    """Nada depois do fim da fala (V1): legenda, música ou SFX sobrando viram quadros pretos no fim do export; e só
    uma CTA por timeline (28/10/2026: clipe de outro vídeo caiu nesta timeline quando a ativa foi trocada no meio)."""
    S, F = t.GetStartFrame(), R.fps_tl(t)
    v1 = itens(t, "video", 1)
    if not v1: return
    fv1 = (v1[-1].GetEnd() - S) / F; ftl = (t.GetEndFrame() - S) / F
    if ftl - fv1 > 0.1: ERROS.append(f"SOBRA DEPOIS DO FIM: a timeline vai até {ftl:.2f} s e a fala acaba em {fv1:.2f} s")
    ctas = [x for n in range(2, t.GetTrackCount("video") + 1) for x in itens(t, "video", n) if "CTA" in x.GetName().upper()]
    if len(ctas) > 1: ERROS.append(f"{len(ctas)} CTAs na timeline (clipe de outro vídeo?)")


def motions_ligados(t):
    """LEI 4 e 5: motions/takes com menos de 1,5 s de rosto entre eles ficam ligados; motion que termina até 1,2 s
    antes de um corte da V1 tem que passar do corte (senão o pulo da imagem aparece na pessoa)."""
    S, F = t.GetStartFrame(), R.fps_tl(t)
    cortes = [(x.GetEnd() - S) / F for x in itens(t, "video", 1)[:-1]]
    cima = sorted([((x.GetStart() - S) / F, (x.GetEnd() - S) / F, x.GetName()) for x in itens(t, "video", 2)])
    for (a1, b1, n1), (a2, b2, n2) in zip(cima, cima[1:]):
        if 0.6 < a2 - b1 < 1.5:
            ERROS.append(f"MOTION DESLIGADO: {a2 - b1:.2f} s de rosto entre {n1} e {n2} em {b1:.2f} s (ligar os dois)")
    for a, b, n in cima:
        for c in cortes:
            if 0.05 < c - b <= 1.2 and not any(a2 <= c <= b2 for a2, b2, _ in cima):
                ERROS.append(f"CORTE EXPOSTO: {n} termina em {b:.2f} s e o corte da V1 vem em {c:.2f} s (esticar até depois do corte)")


def audio(t):
    v = itens(t, "video", 1); a = itens(t, "audio", 1)
    if v1_sem_som(t):   # motion na V1, narração em trechos na A1: confere só se a fala está dentro da imagem
        if a and v and (a[0].GetStart() < v[0].GetStart() or a[-1].GetEnd() > v[-1].GetEnd()):
            ERROS.append("ÁUDIO x IMAGEM: a narração da A1 passa do começo ou do fim do motion da V1")
        AVISOS.append(f"V1 é motion sem som: fala conferida na A1 ({len(a)} trechos)")
        return
    if len(v) != len(a) or any(x.GetStart() != y.GetStart() or x.GetEnd() != y.GetEnd() for x, y in zip(v, a)):
        ERROS.append(f"ÁUDIO x IMAGEM: V1 tem {len(v)} clipes e A1 {len(a)} (ou fora de posição); a fala pode estar fora do lugar ou faltando")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: raise SystemExit(__doc__)
    nome = a[0]; corrigir = "--corrigir" in a
    pasta = a[a.index("--pasta") + 1] if "--pasta" in a else os.path.join(os.path.expanduser("~"), "Desktop", "revisao_" + nome)
    r = R.conectar(abrir=False); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    t = tl_por_nome(p, nome); p.SetCurrentTimeline(t)
    buracos(t, mp, corrigir)
    if corrigir: R.salvar(r)
    audio(t); fim_do_video(t); bordas(t); fala(t); motions_ligados(t)
    if v1_sem_som(t) and not v1_tem_take(t): AVISOS.append("vídeo inteiro em motion: rosto/legenda não se aplica (rosto é foto do pôster)")
    else: rosto(t)
    cor(p, t, pasta)
    for x in AVISOS: print("  ·", x)
    for x in dict.fromkeys(ERROS): print("ERRO", x)
    print(f"revisão {nome!r}: {len(ERROS)} erro(s)")
    sys.exit(1 if ERROS else 0)
