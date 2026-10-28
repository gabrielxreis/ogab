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
    out = conferir.exportar(p, t, [(s, "cor") for s in pegar], os.path.join(pasta, "revisao_cor"))
    rb, gb = [], []
    for png, s, _ in out:
        im = Image.open(png).convert("RGB").resize((270, 480))
        px = [c for c in (im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()) if sum(c) / 3 > 140 and max(c) - min(c) < 70]
        if len(px) < 200: continue
        r_ = st.mean(c[0] for c in px); g_ = st.mean(c[1] for c in px); b_ = st.mean(c[2] for c in px)
        rb.append(r_ - b_); gb.append(g_ - (r_ + b_) / 2)
    if not rb: AVISOS.append("COR: poucos tons claros para medir"); return
    d, v = st.mean(rb), st.mean(gb)
    if d > 28: ERROS.append(f"COR AMARELADA: nos tons claros o vermelho está {d:.0f} acima do azul (máx 28); tirar a LUT/PowerGrade quente ou esfriar no CDL")
    elif d < -18: ERROS.append(f"COR AZULADA: azul {-d:.0f} acima do vermelho nos tons claros")
    if v > 12: ERROS.append(f"COR ESVERDEADA: verde {v:.0f} acima nos tons claros")
    AVISOS.append(f"cor medida em {len(rb)} quadros: vermelho-azul {d:.0f}, verde {v:.0f}")


def audio(t):
    v = itens(t, "video", 1); a = itens(t, "audio", 1)
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
    audio(t); rosto(t); cor(p, t, pasta)
    for x in AVISOS: print("  ·", x)
    for x in dict.fromkeys(ERROS): print("ERRO", x)
    print(f"revisão {nome!r}: {len(ERROS)} erro(s)")
    sys.exit(1 if ERROS else 0)
