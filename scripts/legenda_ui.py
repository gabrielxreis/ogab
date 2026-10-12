"""Posição das legendas por legenda no DaVinci, sem gastar token (regra: legenda em Y 724, desce p/ 390 só no lettering).

A API do Resolve não expõe estilo de legenda (GetProperty() do item vem vazio). Este script faz o trabalho
pela interface sozinho: clica, digita e CONFERE por OCR (Vision da Apple), numa chamada só.

  python3 legenda_ui.py "<nome da timeline>"            # trilha em 724 e desce as legendas do lettering p/ 390
  python3 legenda_ui.py "<timeline>" --indices 4,5,6     # índices (1 = primeira legenda) escolhidos à mão
  python3 legenda_ui.py "<timeline>" --trilha 390        # vídeo todo em motion: a trilha inteira em 390
  python3 legenda_ui.py "<timeline>" --so-listar         # só mostra quais legendas cruzam a trilha LETTERING
  python3 legenda_ui.py "<timeline>" --preset "GAB USA" [--arquivo x.preset]  # carrega o preset de estilo na trilha e segue
  python3 legenda_ui.py "<timeline>" --conferir          # render + checa a altura do texto de cada legenda

Requisitos: DaVinci aberto e maximizado na página Edit com o Inspector visível; pyobjc-framework-Vision
(pip install pyobjc-framework-Vision); o Python precisa de permissão de Acessibilidade (já tem nesta máquina).
Armadilhas (custaram caro): NUNCA Tab no campo (o foco vai p/ "Add New" e o Return cria legenda "Subtitle");
o 1º duplo clique no campo às vezes arrasta o valor (sai 384), por isso digita 2x e confere por OCR.
"""
import os, re, sys, time, subprocess, unicodedata
import Quartz, Vision
from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as L

BUNDLE = "com.blackmagic-design.DaVinciResolve"
Y_PADRAO, Y_LETTERING = 724, 390
INSPECTOR = (1305, 70, 423, 470)   # x, y, w, h em pontos da tela (Inspector à direita)
TIMELINE = (160, 540, 1568, 450)  # faixa das trilhas (sem os cabeçalhos)


# ---------- tela: captura + OCR ----------
def _captura(r):
    x, y, w, h = r
    return Quartz.CGWindowListCreateImage(Quartz.CGRectMake(x, y, w, h), Quartz.kCGWindowListOptionOnScreenOnly,
                                          Quartz.kCGNullWindowID, Quartz.kCGWindowImageDefault)


def ocr(r):
    """[(texto, cx, cy, x0, y0, x1, y1)] em pontos da tela."""
    img = _captura(r); x, y, w, h = r
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate); req.setUsesLanguageCorrection_(False)
    ok, _ = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(img, None).performRequests_error_([req], None)
    if not ok:   # macOS 27: o nível Accurate falha (e5rtError) e devolve vazio; o Fast funciona
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelFast); req.setUsesLanguageCorrection_(False)
        Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(img, None).performRequests_error_([req], None)
    out = []
    for o in req.results() or []:
        t = o.topCandidates_(1)[0].string(); b = o.boundingBox()
        x0 = x + b.origin.x * w; x1 = x0 + b.size.width * w
        y1 = y + (1 - b.origin.y) * h; y0 = y1 - b.size.height * h
        out.append((t, (x0 + x1) / 2, (y0 + y1) / 2, x0, y0, x1, y1))
    return out


def brilho_max(px, py, raio=4):
    img = _captura((px - raio, py - raio, 2 * raio, 2 * raio))
    w, h = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
    dados = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(img)); bpr = Quartz.CGImageGetBytesPerRow(img)
    m = 0
    for j in range(h):
        for i in range(w):
            o = j * bpr + i * 4; m = max(m, dados[o], dados[o + 1], dados[o + 2])
    return m


# ---------- entrada ----------
def _mouse(tipo, x, y, n=1):
    e = Quartz.CGEventCreateMouseEvent(None, tipo, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventSetIntegerValueField(e, Quartz.kCGMouseEventClickState, n)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def clicar(x, y, n=1):
    for k in range(1, n + 1):
        _mouse(Quartz.kCGEventLeftMouseDown, x, y, k); time.sleep(0.03); _mouse(Quartz.kCGEventLeftMouseUp, x, y, k); time.sleep(0.05)
    time.sleep(0.35)


def _se(*linhas):
    """Teclado pelo System Events: o Resolve (Qt) ignora evento de teclado do Quartz, só aceita este."""
    args = ["osascript", "-e", 'tell application "System Events"']
    for l in linhas: args += ["-e", l]
    subprocess.run(args + ["-e", "end tell"], check=True); time.sleep(0.25)


def tecla(cod, cmd=False):
    _se(f"key code {cod}" + (" using command down" if cmd else ""))


def digitar(txt):
    _se(f'keystroke "{txt}"')


def rolar(x, y, linhas):
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0))
    for _ in range(abs(linhas)):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 1, -1 if linhas > 0 else 1))
        time.sleep(0.02)
    time.sleep(0.4)


RETURN, CMD_A = 36, 0


def frente():
    for a in NSRunningApplication.runningApplicationsWithBundleIdentifier_(BUNDLE):
        a.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    time.sleep(0.8)
    coberta()


def coberta():
    """Bug 12/10/2026: a janela do Claude (ou outra) por cima do Inspector fazia o OCR ler o chat e o clique cair
    nela. Para com erro claro se a primeira janela visível sobre o Inspector/timeline não for do DaVinci."""
    info = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for reg in (INSPECTOR, TIMELINE):
        cx, cy = reg[0] + reg[2] / 2, reg[1] + reg[3] / 2
        for w in info:   # ordem: de cima para baixo
            if w.get("kCGWindowLayer", 0) != 0: continue
            b = w.get("kCGWindowBounds", {})
            if b and b["X"] <= cx <= b["X"] + b["Width"] and b["Y"] <= cy <= b["Y"] + b["Height"]:
                dono = w.get("kCGWindowOwnerName", "")
                if "DaVinci" not in dono:
                    raise RuntimeError(f"a janela de {dono!r} está por cima do DaVinci (Inspector/timeline): "
                                       "minimize ou mova essa janela e rode de novo")
                break


# ---------- helpers de OCR ----------
def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def achar(obs, texto, exato=True):
    alvo = _norm(texto)
    r = [o for o in obs if (_norm(o[0]) == alvo if exato else alvo in _norm(o[0]))]
    return sorted(r, key=lambda o: o[2])


def _tc(f, fps):
    f = int(f); return f"{f // (3600 * fps):02d}:{f // (60 * fps) % 60:02d}:{f // fps % 60:02d}:{f % fps:02d}"


# ---------- Inspector ----------
def aba(nome):
    """Clica na aba Caption/Track do Inspector (a mais alta com esse nome)."""
    rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 300, -25)
    o = achar(ocr(INSPECTOR), nome)
    if not o: raise RuntimeError(f"aba {nome} não encontrada (selecione uma legenda na timeline)")
    clicar(o[0][1], o[0][2])


def legenda_atual(obs, caps, fps):
    tcs = [o[0].replace(" ", "") for o in obs if re.fullmatch(r"\d\d:\d\d:\d\d:\d\d", o[0].replace(" ", ""))]
    if not tcs: return None
    ini = tcs[0]
    for i, c in enumerate(caps):
        if c["tc"] == ini: return i
    return None


def _campo_y(obs):
    """(x, y, texto) do valor Y na linha Position."""
    pos = [o for o in obs if _norm(o[0]) == "position"]
    if not pos: return None
    py = pos[-1][2]
    nums = sorted([o for o in obs if abs(o[2] - py) < 8 and re.fullmatch(r"-?\d+(\.\d+)?", o[0].strip())], key=lambda o: o[1])
    if len(nums) < 2: return None
    return nums[-1][1], nums[-1][2], nums[-1][0], pos[-1]


def setar_y(valor, rolagem=True):
    for tentativa in range(7):
        time.sleep(0.3); obs = ocr(INSPECTOR)
        c = _campo_y(obs)
        if c is None and rolagem:
            rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 350, 8); continue
        if c is None: raise RuntimeError("campo Position Y não encontrado")
        x, y, txt, lab = c
        if txt.startswith(str(valor)): return True
        for _ in range(2):              # a 1ª vez às vezes sai 384; a 2ª acerta
            clicar(x, y, 2); _se('keystroke "a" using command down', f'keystroke "{valor}"', "key code 36")
        clicar(lab[1], lab[2])          # confirma clicando no rótulo "Position" (NUNCA Tab)
    obs = ocr(INSPECTOR); c = _campo_y(obs)
    return bool(c and c[2].startswith(str(valor)))


def recolher_estilo(obs=None):
    obs = obs or ocr(INSPECTOR)
    if achar(obs, "Font Family"):
        cs = achar(obs, "Caption Style", exato=False)
        if cs: clicar(cs[0][1], cs[0][2]); return True
    rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 300, -25)
    return False


def customizar(y_alvo):
    """Na legenda selecionada: Customize Caption + Caption Style > Position Y."""
    rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 300, -25)
    obs = ocr(INSPECTOR)
    lab = achar(obs, "Customize Caption")
    if not lab: raise RuntimeError("'Customize Caption' não apareceu (aba Caption ativa?)")
    _, cx, cy, x0, y0, x1, y1 = lab[0]
    caixa = (x0 - 16, cy)
    if brilho_max(*caixa) < 180:            # desmarcado
        clicar(*caixa); obs = ocr(INSPECTOR)
    if not achar(obs, "Font Family"):
        cs = achar(obs, "Caption Style", exato=False)
        if not cs: raise RuntimeError("'Caption Style' não apareceu")
        clicar(cs[0][1], cs[0][2]); time.sleep(0.5)
    rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 350, 10)
    ok = setar_y(y_alvo)
    rolar(INSPECTOR[0] + 200, INSPECTOR[1] + 300, -25)
    recolher_estilo()                       # recolhe p/ o Next/Prev ficar sempre à vista
    return ok


def navegar(alvo, caps, fps, limite=400):
    for _ in range(limite):
        obs = ocr(INSPECTOR); i = legenda_atual(obs, caps, fps)
        if i is None: raise RuntimeError("não consegui ler a legenda atual no Inspector")
        if i == alvo: return
        b = achar(obs, "Next" if alvo > i else "Prev")
        if not b:
            recolher_estilo(obs); continue
        clicar(b[0][1], b[0][2])         # um clique por vez: o layout muda quando a legenda é customizada
    raise RuntimeError("navegação não chegou na legenda")


HOME = 115


def playhead_x(reg=None):
    """x (pontos de tela) da linha vermelha do playhead na faixa das trilhas, pela cor (sem OCR)."""
    import numpy as np
    x, y, w, h = reg or TIMELINE
    img = _captura((x, y + 60, w, h - 60)); W, H = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
    prov = Quartz.CGImageGetDataProvider(img); buf = Quartz.CGDataProviderCopyData(prov); bpr = Quartz.CGImageGetBytesPerRow(img)
    a = np.frombuffer(buf, np.uint8).reshape(H, bpr)[:, :W * 4].reshape(H, W, 4)   # BGRA
    b, g, r_ = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    verm = (r_ > 180) & (g < 90) & (b < 90)
    col = verm.sum(axis=0)
    if col.max() < H * 0.5: return None
    return x + col.argmax() * w / W


def clicar_cmd(x, y):
    """Cmd+clique (adiciona à seleção) pelo Quartz."""
    for tipo in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        e = Quartz.CGEventCreateMouseEvent(None, tipo, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventSetFlags(e, Quartz.kCGEventFlagMaskCommand); Quartz.CGEventPost(Quartz.kCGHIDEventTap, e); time.sleep(0.04)
    time.sleep(0.25)


def selecionar_varias(caps, idxs, fps):
    """Dica do usuário (12/10/2026): seleciona TODAS as legendas que mudam de uma vez (clique + Cmd+clique) para trocar a
    Position delas numa vez só. Sem OCR na régua: Shift+Z (zoom para caber), playhead pela API em dois tempos e a escala
    px/quadro pela linha vermelha; o y da linha ST1 pelo OCR do cabeçalho."""
    r = L.conectar(abrir=False); t = r.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
    cab = []
    for _ in range(4):
        cab = [o for o in ocr((0, 560, 170, 460)) if _norm(o[0]).replace(" ", "") in ("st1", "sti", "stl")]
        if cab: break
        time.sleep(0.8)
    if not cab: raise RuntimeError("cabeçalho ST1 não encontrado")
    y_st = cab[0][2]
    _se('keystroke "z" using shift down'); time.sleep(0.8)          # zoom para caber a timeline inteira
    a, b = caps[0]["ini"], caps[-1]["fim"]
    t.SetCurrentTimecode(_tc(a, fps)); time.sleep(0.7); xa = playhead_x()
    t.SetCurrentTimecode(_tc(b, fps)); time.sleep(0.7); xb = playhead_x()
    if xa is None or xb is None or xb <= xa: raise RuntimeError("não consegui medir a escala da timeline pelo playhead")
    esc = (xb - xa) / (b - a)
    for n, i in enumerate(idxs):
        x = xa + ((caps[i]["ini"] + caps[i]["fim"]) / 2 - a) * esc
        (clicar if n == 0 else clicar_cmd)(x, y_st)
    return True


def selecionar_alguma(caps):
    """Seleciona a 1ª legenda: acha a linha ST1 pelo cabeçalho e o início da timeline pela régua (01:00:00:00)."""
    cab = []
    for _ in range(4):                  # a timeline recém-aberta demora a desenhar; OCR às vezes lê "STI"/"STl"
        cab = [o for o in ocr((0, 560, 170, 460)) if _norm(o[0]).replace(" ", "") in ("st1", "sti", "stl")]
        if cab: break
        time.sleep(0.8)
    if not cab: raise RuntimeError("cabeçalho ST1 não encontrado")
    y_st = cab[0][2]
    # SEM OCR na régua (falhava): playhead pela API no meio da 1ª legenda e o x dele pela COR (linha vermelha).
    r = L.conectar(abrir=False); t = r.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
    fps = int(round(float(t.GetSetting("timelineFrameRate") or 30)))
    meio = (caps[0]["ini"] + caps[0]["fim"]) // 2
    t.SetCurrentTimecode(_tc(meio, fps)); time.sleep(0.8)
    x0 = playhead_x()
    if x0 is None: raise RuntimeError("playhead (linha vermelha) não encontrado na timeline")
    clicar(x0, y_st)        # o playhead está no meio da 1ª legenda
    return True


# ---------- preset de estilo da trilha (a API não aplica estilo de legenda) ----------
def _menu_ocr():
    return ocr((900, 40, 828, 900))


def carregar_preset(nome_preset="GAB USA", arquivo=None):
    """Inspector > Track > menu ⋯ > <preset> > Load Preset. Se o preset não existir, Import Preset... do arquivo.
    Confere pela fonte mostrada no Inspector (Poppins) no fim."""
    aba("Track")
    cab = [o for o in ocr(INSPECTOR) if "subtitle" in _norm(o[0])]
    if not cab: raise RuntimeError("cabeçalho do Inspector (Subtitle) não encontrado")
    y = cab[0][2]; x = INSPECTOR[0] + INSPECTOR[2] - 18
    clicar(x, y); time.sleep(0.6)
    m = _menu_ocr(); item = achar(m, nome_preset, exato=False)
    if not item:
        imp = achar(m, "Import Preset", exato=False)
        if not imp or not arquivo: raise RuntimeError(f"preset {nome_preset!r} não está no menu e não há arquivo p/ importar")
        clicar(imp[0][1], imp[0][2]); time.sleep(1.2)
        _se("keystroke \"g\" using {command down, shift down}"); time.sleep(0.6)
        digitar(arquivo); tecla(RETURN); time.sleep(0.6); tecla(RETURN); time.sleep(1.5)
        clicar(x, y); time.sleep(0.6); m = _menu_ocr(); item = achar(m, nome_preset, exato=False)
        if not item: raise RuntimeError("importei o preset mas ele não apareceu no menu")
    clicar(item[0][1], item[0][2]); time.sleep(0.6)
    load = achar(_menu_ocr(), "Load Preset", exato=False)
    if not load: raise RuntimeError("opção Load Preset não apareceu")
    clicar(load[0][1], load[0][2]); time.sleep(1.0)
    ok = achar(ocr(INSPECTOR), "Poppins", exato=False)
    print("preset", nome_preset, "carregado" if ok else "carregado? (fonte Poppins não lida no Inspector; conferir)")
    return bool(ok)


# ---------- dados pela API ----------
def dados(nome):
    r = L.conectar(); p = r.GetProjectManager().GetCurrentProject(); r.OpenPage("edit")
    t = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome)
    p.SetCurrentTimeline(t); fps = int(round(float(t.GetSetting("timelineFrameRate") or 30)))
    let = []
    for k in range(1, t.GetTrackCount("video") + 1):
        if "LETTERING" in (t.GetTrackName("video", k) or "").upper():
            let += [(x.GetStart(), x.GetEnd()) for x in t.GetItemListInTrack("video", k)]
    subs = sorted(t.GetItemListInTrack("subtitle", 1) or [], key=lambda x: x.GetStart())
    caps = [dict(txt=s.GetName(), ini=s.GetStart(), fim=s.GetEnd(), tc=_tc(s.GetStart(), fps)) for s in subs]
    descer = [i for i, c in enumerate(caps) if any(c["ini"] < b and c["fim"] > a for a, b in let)]
    return r, p, t, fps, caps, descer


def integridade(t, caps):
    agora = [s.GetName() for s in sorted(t.GetItemListInTrack("subtitle", 1) or [], key=lambda x: x.GetStart())]
    return agora == [c["txt"] for c in caps]


def conferir(nome):
    """Render com legenda gravada e mede a faixa do texto branco em cada legenda (724 ~ y1196, 390 ~ y1530)."""
    import tempfile
    r, p, t, fps, caps, descer = dados(nome)
    pasta = tempfile.mkdtemp(); arq, st = L.renderizar(p, pasta, "conf", legenda_gravada=True)
    r.OpenPage("edit"); erros = []
    for i, c in enumerate(caps):
        seg = ((c["ini"] + c["fim"]) / 2 - t.GetStartFrame()) / fps
        cru = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{seg:.3f}", "-i", arq, "-frames:v", "1", "-vf", "crop=1080:420:0:1150,format=gray",
                              "-f", "rawvideo", "-"], capture_output=True).stdout
        if len(cru) < 1080 * 420: continue
        cima = sum(1 for v in cru[:1080 * 90] if v >= 250); baixo = sum(1 for v in cru[1080 * 340:] if v >= 250)
        esperado = "baixo" if i in descer else "cima"
        visto = "baixo" if baixo > cima else "cima"
        if max(cima, baixo) > 150 and visto != esperado: erros.append((i + 1, c["txt"], esperado, visto))
    print(f"{nome}: {len(caps)} legendas, {len(descer)} descem; divergências: {erros or 'nenhuma'}")
    return erros


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    nome = a[0]
    if "--conferir" in a: conferir(nome); return
    r, p, t, fps, caps, descer = dados(nome)
    if "--indices" in a: descer = [int(x) - 1 for x in a[a.index("--indices") + 1].split(",")]
    global Y_PADRAO
    if "--trilha" in a:      # vídeo todo em motion: a TRILHA inteira vai para esse Y (ex.: 390), sem ajuste por legenda
        Y_PADRAO = int(a[a.index("--trilha") + 1]); descer = []
    print(f"{nome}: {len(caps)} legendas; descem p/ {Y_LETTERING}: {[i + 1 for i in descer]}")
    if "--so-listar" in a: return
    frente()
    selecionar_alguma(caps)
    if "--preset" in a:
        arq = a[a.index("--arquivo") + 1] if "--arquivo" in a else os.path.expanduser("~/Desktop/GAB USA Subtitle.preset")
        carregar_preset(a[a.index("--preset") + 1], arq)
    aba("Track")
    if not setar_y(Y_PADRAO, rolagem=True): raise RuntimeError("trilha não ficou em 724")
    aba("Caption")
    feitos = []
    if descer and "--uma-a-uma" not in a:     # padrão: todas de uma vez (seleção múltipla)
        try:
            selecionar_varias(caps, descer, fps); aba("Caption")
            if not customizar(Y_LETTERING): raise RuntimeError("Position Y não ficou")
            if not integridade(t, caps): raise RuntimeError("legendas mudaram: pare e reanexe o SRT")
            r.GetProjectManager().SaveProject()
            print(f"pronto (de uma vez): {len(descer)} legendas em {Y_LETTERING}, trilha em {Y_PADRAO}"); return
        except Exception as e:
            print("seleção múltipla falhou, indo uma a uma:", e); selecionar_alguma(caps); aba("Caption")
    for i in descer:
        navegar(i, caps, fps)
        if not customizar(Y_LETTERING): raise RuntimeError(f"legenda {i + 1} não ficou em {Y_LETTERING}")
        if not integridade(t, caps): raise RuntimeError(f"legendas mudaram depois da {i + 1}: pare e reanexe o SRT")
        feitos.append(i + 1); print("ok", i + 1, caps[i]["txt"], flush=True)
    r.GetProjectManager().SaveProject()
    print(f"pronto: {len(feitos)} legendas em {Y_LETTERING}, trilha em {Y_PADRAO}, texto íntegro")


if __name__ == "__main__":
    main()
