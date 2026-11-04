"""Planar track no olho (estilo do Vini, 23/10/2026): trava a câmera no rosto de quem está no take.

  python3 planar_olho.py                      -> take embaixo da agulha, pessoa de rosto maior
  python3 planar_olho.py --pessoa direita     -> escolhe o rosto mais à direita (ou esquerda)
  python3 planar_olho.py --trilha 2           -> take da V2 embaixo da agulha (padrão: o de cima)
  python3 planar_olho.py --sem-conferir       -> não exporta os quadros de conferência
  python3 planar_olho.py --lut <arquivo.cube> -> LUT para achar o rosto em take HLG (padrão: iPhone HLG to Rec709)

Só Mac: os olhos são achados com o Vision da Apple (pyobjc: pip install pyobjc-framework-Vision).
Veio da fila de relatos (invenção de usuário, 03/11/2026).

Passos:
  1. Abre o Fusion do take; usa o PlanarTracker que já estiver lá ou cria um entre MediaIn1 e MediaOut1.
  2. Acha os olhos no 1º quadro com o Vision da Apple (fallback: faixa dos olhos dentro do rosto) e
     desenha a área do track em volta deles (pega óculos e sobrancelha).
  3. Track do 1º ao último quadro em Similarity (Perspective escorrega quando o rosto vira).
  4. Operation = Stabilize, Method = FixedFrames, Frame Mode = Zoom + Auto Zoom, Compute Stabilization.
  5. Exporta 6 quadros do Edit para conferir (scratch na pasta temporária, planar_olho/).

Na API do Fusion: Comp.Execute só roda Lua de UMA linha (multilinha falha calado), não existe Polyline()
no Lua, então o polígono entra por LoadSettings; LoadSettings cria um spline de track novo e deixa o antigo
solto (o script apaga). Enquanto calcula o track/estabilização o Resolve não responde: esperar.
"""
import json, os, platform, re, subprocess, sys, tempfile, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as rl

TMP = os.path.join(tempfile.gettempdir(), "planar_olho")
LUT_IPHONE = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/GAB/iPhone HLG to Rec709.cube"   # padrão; --lut troca


def lua(c, codigo, espera=0.6):
    """Roda Lua de uma linha no comp e devolve o que ele gravar em comp:SetData('m', ...)."""
    c.SetData("m", "--")
    c.Execute("local ok,e=pcall(function() " + codigo.replace("\n", " ") + " end) if not ok then comp:SetData('m','ERR '..tostring(e)) end")
    time.sleep(espera)
    return c.GetData("m")


def esperar_livre(r, c, limite=600):
    t0 = time.time()
    while time.time() - t0 < limite:
        if lua(c, "comp:SetData('m','vivo')", 1.5) == "vivo": return True
    return False


def item_na_agulha(t, trilha=None):
    tc = t.GetCurrentTimecode().replace(";", ":")
    fps = round(float(t.GetSetting("timelineFrameRate")))
    h, m, s, f = map(int, tc.split(":"))
    quadro = ((h * 60 + m) * 60 + s) * fps + f
    trilhas = [trilha] if trilha else range(t.GetTrackCount("video"), 0, -1)
    for tr in trilhas:
        for x in t.GetItemListInTrack("video", tr) or []:
            if x.GetStart() <= quadro < x.GetEnd() and x.GetMediaPoolItem(): return x, tr
    return None, None


def olhos_no_quadro(png, pessoa=None):
    """Caixa (x0,y0,x1,y1) normalizada, y de cima para baixo, em volta dos olhos do rosto escolhido."""
    try:
        import Vision
        from Foundation import NSURL
    except ImportError:
        sys.exit(f"Sem o Vision da Apple neste Python: {sys.executable} -m pip install --user pyobjc-framework-Vision")
    req = Vision.VNDetectFaceLandmarksRequest.alloc().init()
    h = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(png), None)
    h.performRequests_error_([req], None)
    rostos = list(req.results() or [])
    if not rostos:
        req = Vision.VNDetectFaceRectanglesRequest.alloc().init(); h.performRequests_error_([req], None); rostos = list(req.results() or [])
    if not rostos: return None
    cx = lambda o: o.boundingBox().origin.x + o.boundingBox().size.width / 2
    if pessoa == "direita": o = max(rostos, key=cx)
    elif pessoa == "esquerda": o = min(rostos, key=cx)
    else: o = max(rostos, key=lambda o: o.boundingBox().size.width)
    b = o.boundingBox(); L = o.landmarks() if hasattr(o, "landmarks") else None
    pts = []
    if L:
        for reg in (L.leftEye(), L.rightEye(), L.leftEyebrow(), L.rightEyebrow()):
            if reg is None: continue
            for i in range(reg.pointCount()):
                p = reg.normalizedPoints()[i]
                pts.append((b.origin.x + p.x * b.size.width, 1 - (b.origin.y + p.y * b.size.height)))
    if len(pts) >= 6:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        mx, my = (max(xs) - min(xs)) * 0.25, (max(ys) - min(ys)) * 0.6
        return (min(xs) - mx, min(ys) - my, max(xs) + mx, max(ys) + my)
    topo = 1 - (b.origin.y + b.size.height)                    # faixa dos olhos: 20% a 50% da altura do rosto
    return (b.origin.x - b.size.width * 0.05, topo + b.size.height * 0.2,
            b.origin.x + b.size.width * 1.05, topo + b.size.height * 0.5)


def main(a):
    if platform.system() != "Darwin":
        sys.exit("planar_olho.py só roda no Mac (usa o Vision da Apple para achar os olhos): desenhe a área à mão no PlanarTracker.")
    lut = a[a.index("--lut") + 1] if "--lut" in a else LUT_IPHONE
    pessoa = a[a.index("--pessoa") + 1] if "--pessoa" in a else None
    trilha = int(a[a.index("--trilha") + 1]) if "--trilha" in a else None
    r = rl.conectar(); p = r.GetProjectManager().GetCurrentProject(); t = p.GetCurrentTimeline()
    x, tr = item_na_agulha(t, trilha)
    if not x: sys.exit("Nenhum take embaixo da agulha.")
    arq = x.GetMediaPoolItem().GetClipProperty("File Path")
    print(f"Take: {x.GetName()} (V{tr}, {x.GetStart()}-{x.GetEnd()})")

    # 1. Fusion do take aberto na página Fusion
    if not x.GetFusionCompCount(): x.AddFusionComp()
    r.OpenPage("fusion"); time.sleep(2)
    c = r.Fusion().CurrentComp
    ini = int(c.GetAttrs()["COMPN_RenderStart"]); fim = int(c.GetAttrs()["COMPN_RenderEnd"])
    pt = next((tl for tl in c.GetToolList(False).values() if tl.ID == "Dimension.PlanarTracker"), None)
    if not pt:
        print(lua(c, "local mi=comp:FindTool('MediaIn1'); local mo=comp:FindTool('MediaOut1'); local t=comp:AddTool('PlanarTracker',-32768,-32768); t.Background=mi.Output; mo.Input=t.Output; comp:SetData('m',t.Name)"))
        pt = next(tl for tl in c.GetToolList(False).values() if tl.ID == "Dimension.PlanarTracker")
    nome = pt.Name

    # 2. Olhos no 1º quadro do take (mesma orientação do Fusion: ffmpeg já gira)
    os.makedirs(TMP, exist_ok=True); png = f"{TMP}/q0.png"
    vf = "scale=iw/4:ih/4"
    if os.path.exists(lut) and "arib-std-b67" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=color_transfer", "-of", "csv=p=0", arq], capture_output=True, text=True).stdout:
        vf += f":in_color_matrix=bt2020,lut3d='{lut}'"
    fps = round(float(t.GetSetting("timelineFrameRate")))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(x.GetLeftOffset() + ini) / fps:.3f}", "-i", arq, "-frames:v", "1", "-vf", vf, png], check=True)
    cx = olhos_no_quadro(png, pessoa)
    if not cx: sys.exit("Não achei rosto no 1º quadro do take: desenhe a área à mão no PlanarTracker.")
    img = c.FindTool("MediaIn1").Output[ini]; asp = (img.Height / img.Width) if img else 16 / 9
    x0, y0, x1, y1 = cx
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    poly = "Polyline { Closed = true, Points = { " + ", ".join(
        f"{{ Linear = true, X = {px - 0.5:.5f}, Y = {(0.5 - py) * asp:.5f} }}" for px, py in pts) + " } }"
    print(f"Área dos olhos (0-1, de cima): x {x0:.3f}-{x1:.3f}  y {y0:.3f}-{y1:.3f}")

    # polígono por LoadSettings (não há Polyline() no Lua do Resolve)
    txt = lua(c, f"comp:SetData('m', bmd.writestring(comp:FindTool('{nome}'):SaveSettings()))")
    txt = re.sub(r'\["Pattern\.Polygon"\] = Input \{\s*Value = Polyline \{.*?\n\t{5}\}', '["Pattern.Polygon"] = Input {\n\t\t\t\t\tValue = ' + poly, txt, count=1, flags=re.S)
    if poly not in txt: sys.exit("Não consegui montar o polígono nas configurações do PlanarTracker.")
    antigos = {tl.Name for tl in c.GetToolList(False).values() if tl.ID == "BezierSpline"}
    c.SetData("t", txt)
    lua(c, f"comp:FindTool('{nome}'):LoadSettings(bmd.readstring(comp:GetData('t'))); comp:SetData('m','ok')", 1)
    for tl in list(c.GetToolList(False).values()):                # spline de track antigo que ficou solto
        if tl.ID == "BezierSpline" and tl.Name in antigos and not any(o.GetConnectedInputs() for o in tl.GetOutputList().values()):
            tl.Delete()

    # 3. Track em Similarity
    c.CurrentTime = ini
    lua(c, f"local t=comp:FindTool('{nome}'); t.Operation='Track'; t.MotionType='Similarity'; t.ReferenceTime={ini}; t.TrackToEnd=1; comp:SetData('m','ok')", 3)
    esperar_livre(r, c)
    for _ in range(300):
        if lua(c, "comp:SetData('m', tostring(comp.CurrentTime))", 1.5) in (str(fim), f"{fim}.0"): break
    print("Track: ok")

    # 4. Stabilize fixo com zoom automático
    lua(c, f"local t=comp:FindTool('{nome}'); t.Operation='Stabilize'; t['Stabilize.Method']='FixedFrames'; t['Stabilize.FrameMode']='Zoom'; t['Stabilize.Zoom.AutoZoom']=1; comp:SetData('m','ok')", 1)
    lua(c, f"comp:FindTool('{nome}')['Stabilize.ComputeStabilization']=1; comp:SetData('m','ok')", 3)
    esperar_livre(r, c)
    zoom = pt.GetInput("Stabilize.Zoom.Scale")
    print(f"Stabilize: FixedFrames, zoom automático {zoom:.2f}")
    if zoom and zoom > 1.6: print("AVISO: zoom alto, a câmera fecha muito no rosto; se a outra pessoa sumir, oferecer Smoothing.")

    # 5. Conferência
    r.OpenPage("edit"); time.sleep(2)
    if "--sem-conferir" not in a:
        n = x.GetEnd() - x.GetStart(); sts = []
        for k in range(6):
            q = x.GetStart() + min(n - 1, k * n // 5); s, f = divmod(q, fps); m, s = divmod(s, 60); h, m = divmod(m, 60)
            t.SetCurrentTimecode(f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"); time.sleep(3)
            if p.ExportCurrentFrameAsStill(f"{TMP}/s{k}.png"): sts.append(f"{TMP}/s{k}.png")
        if sts:
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", s] for s in sts], []), "-filter_complex",
                            f"hstack={len(sts)},scale=1440:-1", f"{TMP}/conferir.jpg"])
            print(f"Conferir: {TMP}/conferir.jpg")


if __name__ == "__main__":
    main(sys.argv[1:])

