"""Variações de GANCHO para anúncio: o corpo do vídeo fica igual e só os primeiros segundos mudam (uma timeline por
gancho no mesmo projeto). Quando o anúncio cansa, entra gancho novo sem refazer o resto. Ideia estudada no hypit
(22/10/2026, "1 workflow, 100 variants"), feita do jeito da /ogab: tudo editável no DaVinci.

  python3 variantes.py ganchos "texto A" "texto B" ... [--voz gabriel]     # duração estimada de cada gancho (estimar.py)
  python3 variantes.py criar --base "<timeline base>" --corte <s> --ganchos "<timeline ou arquivo>" ... [--nomes A,B,C]
  python3 variantes.py listar --base "<timeline base>"

criar: para cada gancho, timeline nova "<base> - gancho <nome>" com o MESMO formato da base:
  1. o gancho no começo (outra timeline do projeto, editada normalmente pelo Gab, ou um arquivo de vídeo com áudio);
  2. logo depois, a timeline BASE ANINHADA a partir de --corte (segundo da base em que o gancho original termina).
  Como o corpo é a própria base aninhada, mexer na base uma vez muda todas as variações. Se o DaVinci recusar
  aninhar (AppendToTimeline com a timeline), o corpo é renderizado UMA vez (renderizar_trecho) e entra como arquivo.
  Depois: legenda em CADA variação pela etapa de legenda (subtitles from audio da timeline da variação: a legenda da
  base aninhada não aparece no render), conferir a emenda gancho > corpo (corte 1 quadro antes da palavra) e
  exportar cada uma com o nome do gancho. O /ojhon sobe as variações como anúncios do mesmo conjunto (teste A/B).
Regras: gancho de 1,5 a 3 s com ação logo no primeiro quadro (takes-brutos-ritmo); a timeline base não é tocada.
"""
import os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


def _timelines(p):
    return {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}


def _item_da_timeline(mp, nome):
    """MediaPoolItem que representa a timeline (para aninhar)."""
    pilha = [mp.GetRootFolder()]
    while pilha:
        f = pilha.pop()
        for c in f.GetClipList() or []:
            if c.GetName() == nome and (c.GetClipProperty("Type") or "").lower().startswith("timeline"):
                return c
        pilha.extend(f.GetSubFolderList() or [])
    return None


def _dur_f(t):
    return t.GetEndFrame() - t.GetStartFrame()


def criar(base_nome, corte_s, ganchos, nomes=None):
    import resolve_lib as R
    r = R.conectar(abrir=False); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    tls = _timelines(p)
    if base_nome not in tls:
        raise SystemExit(f"timeline base não encontrada: {base_nome}")
    base = tls[base_nome]
    F = R.fps_tl(base)
    w, h = base.GetSetting("timelineResolutionWidth"), base.GetSetting("timelineResolutionHeight")
    fps = base.GetSetting("timelineFrameRate")
    corte_f, fim_f = round(corte_s * F), _dur_f(base)
    if not 0 < corte_f < fim_f:
        raise SystemExit(f"--corte fora da timeline base (0 a {fim_f / F:.2f} s)")
    base_item = _item_da_timeline(mp, base_nome)
    corpo_arq = None
    nomes = nomes or [chr(65 + i) for i in range(len(ganchos))]
    feitas = []
    for g, nome in zip(ganchos, nomes):
        alvo = f"{base_nome} - gancho {nome}"
        if alvo in _timelines(p):
            print(f"já existe: {alvo} (apagar à mão para refazer)"); continue
        if g in _timelines(p):
            g_item, g_dur = _item_da_timeline(mp, g), _dur_f(_timelines(p)[g])
        elif os.path.exists(g):
            g_item = R.importar(mp, os.path.abspath(g), "GANCHOS")
            g_dur = round(float(g_item.GetClipProperty("Frames") or 0) * F / float(g_item.GetClipProperty("FPS") or F))
        else:
            raise SystemExit(f"gancho não é timeline do projeto nem arquivo: {g}")
        if not g_item or g_dur <= 0:
            raise SystemExit(f"não achei a duração do gancho: {g}")
        t = R.criar_timeline(p, mp, alvo, w, h, fps, sem_menu="variação de gancho de vídeo já montado")
        S = t.GetStartFrame()
        ok_g = mp.AppendToTimeline([{"mediaPoolItem": g_item, "recordFrame": S}])
        corpo_ok = False
        if base_item and not corpo_arq:
            x = mp.AppendToTimeline([{"mediaPoolItem": base_item, "startFrame": corte_f, "endFrame": fim_f,
                                      "recordFrame": S + g_dur}])
            corpo_ok = bool(x)
        if not corpo_ok:   # plano B: corpo renderizado uma vez, entra como arquivo nas variações seguintes também
            if not corpo_arq:
                p.SetCurrentTimeline(base)
                pasta = os.path.join(os.path.expanduser("~/Movies"), "ogab_variantes")
                corpo_arq = R.renderizar_trecho(p, pasta, f"{base_nome} - corpo", corte_s, fim_f / F, so_v1=False)
                p.SetCurrentTimeline(t)
                print(f"AVISO: o DaVinci não aninhou a timeline; corpo renderizado em {corpo_arq} "
                      "(mexer na base exige renderizar o corpo de novo)")
            c_item = R.importar(mp, corpo_arq, "GANCHOS")
            corpo_ok = bool(mp.AppendToTimeline([{"mediaPoolItem": c_item, "recordFrame": S + g_dur}]))
        R.salvar(r)
        n_v1 = len(t.GetItemListInTrack("video", 1) or [])
        print(f"{alvo}: gancho {g_dur / F:.2f} s + corpo {(fim_f - corte_f) / F:.2f} s"
              + ("" if ok_g and corpo_ok and n_v1 >= 2 else f"  CONFERIR: {n_v1} clipe(s) na V1"))
        feitas.append(alvo)
    if feitas:
        R.abrir_em_abas(p, feitas, r)
    return feitas


def main(a):
    if not a:
        raise SystemExit(__doc__)

    def arg(n, pad=None):
        return a[a.index(n) + 1] if n in a else pad
    if a[0] == "ganchos":
        import estimar
        voz = arg("--voz")
        for txt in [x for x in a[1:] if not x.startswith("--") and x != voz]:
            e = estimar.estimar(txt, voz=voz)
            alerta = "  <- longo: gancho bom tem 1,5 a 3 s" if e["segundos"] > 3.2 else ""
            print(f"{e['segundos']:>4.1f} s  {txt}{alerta}")
    elif a[0] == "criar" and "--base" in a and "--corte" in a and "--ganchos" in a:
        i = a.index("--ganchos") + 1; ganchos = []
        while i < len(a) and not a[i].startswith("--"):
            ganchos.append(a[i]); i += 1
        nomes = arg("--nomes").split(",") if "--nomes" in a else None
        criar(arg("--base"), float(arg("--corte")), ganchos, nomes)
    elif a[0] == "listar" and "--base" in a:
        import resolve_lib as R
        p = R.conectar(abrir=False).GetProjectManager().GetCurrentProject()
        for n in _timelines(p):
            if n.startswith(arg("--base") + " - gancho "):
                print("-", n)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
