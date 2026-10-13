"""After Effects pelo /ogab: monta motions como camadas NATIVAS e editáveis no AE (não é vídeo pronto).

O usuário escolhe em config.json > "motion": "hyperframes" (automático, padrão) ou "aftereffects" (controle total
no AE). Com "aftereffects", cada motion do plano vira uma comp no projeto .aep do vídeo: textos, caixas, checks,
contadores e barras com keyframes suaves e uma camada CONTROLES (cores da marca). O Gab renderiza um MOV com alfa
para a timeline (aerender, em segundo plano) e o usuário continua podendo abrir o .aep e mexer em tudo.

Como fala com o AE: a extensão invisível "Gab Ponte AE" (aftereffects/cep, instalada pelo instalar) sobe sozinha
quando o AE abre e recebe ExtendScript em 127.0.0.1:8766. A lógica fica em aftereffects/jsx/gab_ae.jsx.

    import ae_lib as AE
    AE.abrir_projeto(".../motions/motions.aep")
    AE.motion(spec)                                  # spec: ver gab_ae.jsx (GAB.motion) e README.md
    AE.quadro("m01-formacoes", 2.0, ".../conferir.png")
    AE.renderizar("m01-formacoes", ".../motions/m01-formacoes.mov")   # MOV ProRes 4444 com alfa
    AE.mogrt("m01-formacoes", ".../m01.mogrt")      # Premiere: texto e cores editáveis no Essential Graphics
"""
import glob, json, os, subprocess, sys, time, urllib.request

PORTA = int(os.environ.get("OGAB_AE_PORTA", "8766"))
AQUI = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(AQUI, "jsx", "gab_ae.jsx")


def _app():
    """Pasta do After Effects mais novo instalado."""
    if sys.platform == "darwin":
        cands = sorted(glob.glob("/Applications/Adobe After Effects 20*"))
    else:
        cands = sorted(glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Adobe", "Adobe After Effects 20*")))
    if not cands:
        raise SystemExit("After Effects não encontrado (instale o After Effects 2024 ou mais novo pelo Creative Cloud).")
    return cands[-1]


def aerender():
    a = _app()
    return os.path.join(a, "aerender") if sys.platform == "darwin" else os.path.join(a, "Support Files", "aerender.exe")


def _ping():
    try:
        return urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/ping", timeout=2).read() == b"ok"
    except Exception:
        return False


def conectar(espera=240):
    """Abre o AE se precisar e espera a ponte responder."""
    if _ping():
        return True
    a = _app()
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", glob.glob(os.path.join(a, "Adobe After Effects 20*.app"))[0]])
    else:
        subprocess.Popen([os.path.join(a, "Support Files", "AfterFX.exe")], close_fds=True)
    t0, destravou = time.time(), False
    while time.time() - t0 < espera:
        if _ping():
            time.sleep(2)
            return True
        if not destravou and time.time() - t0 > 45:
            _confirmar_aviso()   # depois de um fechamento forçado o AE para num aviso de inicialização
            destravou = True
        time.sleep(2)
    raise SystemExit("O After Effects abriu mas a ponte não respondeu. Rode aftereffects/instalar de novo e reinicie o AE.")


def _confirmar_aviso():
    """Traz o AE para frente e aperta Return (botão padrão = continuar). Só para avisos de inicialização."""
    try:
        if sys.platform == "darwin":
            nome = os.path.basename(_app())
            subprocess.run(["osascript", "-e", f'tell application "{nome}" to activate', "-e", "delay 2",
                            "-e", 'tell application "System Events" to keystroke return'], timeout=20)
        else:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "$w = New-Object -ComObject WScript.Shell; if ($w.AppActivate('After Effects')) { Start-Sleep 2; $w.SendKeys('~') }"],
                           timeout=20)
    except Exception:
        pass


def _esc(s):
    return json.dumps(s, ensure_ascii=True)


def jsx(corpo, rotulo="", espera=300, **args):
    """Roda ExtendScript no AE. `corpo` é o miolo de uma função que recebe `args` e usa GAB.*; o retorno vira JSON."""
    conectar()
    script = ("$.evalFile(new File(" + _esc(LIB) + "));\n"
              "GAB.rodar(function (args) {\n" + corpo + "\n}, " + json.dumps(args, ensure_ascii=True) + ");")
    req = urllib.request.Request(f"http://127.0.0.1:{PORTA}/jsx", data=script.encode("utf-8"), method="POST")
    try:
        bruto = urllib.request.urlopen(req, timeout=espera).read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"After Effects ({rotulo}) não respondeu em {espera} s: provavelmente há uma janela aberta no AE "
                           f"esperando clique (peça ao usuário para olhar o AE). Detalhe: {e}")
    if not bruto:
        raise RuntimeError(f"After Effects ({rotulo}): sem resposta (erro de sintaxe no script ou diálogo aberto no AE)")
    r = json.loads(bruto)
    if not r.get("ok"):
        raise RuntimeError(f"After Effects ({rotulo}): {r.get('erro')}")
    for a in r.get("avisos") or []:
        print(f"[AE] aviso: {a}", file=sys.stderr)
    return r.get("r")


def _abs(c):
    return os.path.abspath(os.path.expanduser(c))


# ---------------------------------------------------------------- projeto e motions

def versao():
    return jsx("return app.version;", "versão")


def abrir_projeto(caminho):
    """Abre o .aep (ou cria vazio e salva nesse caminho). Um .aep por vídeo, em <pasta do vídeo>/motions/."""
    caminho = _abs(caminho); os.makedirs(os.path.dirname(caminho), exist_ok=True)
    return jsx("return GAB.projeto(args.c);", "projeto", c=caminho)


def motion(spec, salvar=True):
    """Cria (ou recria) a comp do motion a partir do plano. Ver README.md: tipos de elemento e efeitos."""
    spec = dict(spec)
    for e in spec.get("elementos", []):
        if e.get("tipo") == "imagem":
            e["arquivo"] = _abs(e["arquivo"])
    r = jsx("var r = GAB.motion(args.spec); if (args.salvar) GAB.salvar(); return r;", "motion", spec=spec, salvar=salvar)
    return r


def listar():
    return jsx("return GAB.listar();", "listar")


def salvar():
    return jsx("return GAB.salvar();", "salvar")


def quadro(comp, t, arquivo, espera=30):
    """PNG de um instante da comp (conferência: centro 540/960, nada no rosto, texto legível)."""
    arquivo = _abs(arquivo); os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    if os.path.exists(arquivo):
        os.remove(arquivo)
    jsx("return GAB.quadro(args.comp, args.t, args.a);", "quadro", comp=comp, t=t, a=arquivo)
    t0 = time.time()
    while time.time() - t0 < espera:
        if os.path.exists(arquivo) and os.path.getsize(arquivo) > 0:
            time.sleep(0.3); return arquivo
        time.sleep(0.3)
    raise RuntimeError("o AE não gravou o quadro (Preferências > Scripts e expressões > permitir que scripts gravem arquivos)")


def renderizar(comp, saida, motor="quadros", limite=1800):
    """MOV com alfa (ProRes 4444) da comp, pronto para a trilha de motions do DaVinci ou do Premiere.
    motor="quadros" (padrão): PNG por quadro pelo AE + ffmpeg (não usa o motor de render; sempre funcionou).
    motor="ae": fila de render do AE agendada (no teste, a tarefa agendada não rodou com o AE em segundo plano).
    motor="aerender": processo separado (no Mac 26.5 travou sem log no teste de 12/10/2026; usar só se o "ae" falhar)."""
    saida = _abs(saida); os.makedirs(os.path.dirname(saida), exist_ok=True)
    if os.path.exists(saida):
        os.remove(saida)
    if motor == "quadros":
        return _render_quadros(comp, saida, limite)
    if motor == "ae":
        r = jsx("GAB.salvar(); return GAB.render(args.comp, args.saida);", "render", comp=comp, saida=saida)
        real = r.get("arquivo") or saida
        t0, ultimo = time.time(), None
        while time.time() - t0 < limite:
            time.sleep(2)
            try:
                st = jsx("return GAB.statusRender();", "status do render", espera=15)
            except RuntimeError:
                continue                     # durante o render a ponte pode demorar a responder
            ultimo = st
            if st.get("estado") == "pronto" and os.path.exists(real):
                return real
            if st.get("estado") in ("erro", "falhou", "usuário parou"):
                break
        raise RuntimeError(f"o render no AE não terminou: {ultimo}")
    info = jsx("var p = app.project.file ? app.project.file.fsName : null; GAB.salvar(); var m = GAB.modeloAlfa(); m.projeto = p; return m;", "render")
    cmd = [aerender(), "-project", info["projeto"], "-comp", comp, "-OMtemplate", info["modelo"], "-output", saida]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not os.path.exists(saida):
        raise RuntimeError("aerender falhou:\n" + (r.stdout or "")[-1500:] + (r.stderr or "")[-500:])
    return saida


def seguir(comp, camada, trilha_json, inicio_no_arquivo=0.0, deslocamento=(0, -120), comp_inicio=0.0):
    """Faz a camada (texto, forma, grupo) acompanhar a trajetória de scripts/rastrear.py: keyframes de posição.
    deslocamento em pixels da comp (dy < 0 = acima). inicio_no_arquivo: segundo do arquivo rastreado que cai em
    comp_inicio na comp. As posições são convertidas da resolução do vídeo para a da comp."""
    tr = json.load(open(trilha_json)) if isinstance(trilha_json, str) else trilha_json
    pts = [[round(t - inicio_no_arquivo + comp_inicio, 4), x, y] for t, x, y, e in tr["pontos"] if t >= inicio_no_arquivo]
    return jsx("""
      var c = GAB.comp(args.comp); if (!c) throw new Error("comp não encontrada: " + args.comp);
      var l = c.layer(args.camada); if (!l) throw new Error("camada não encontrada: " + args.camada);
      var sx = c.width / args.w, sy = c.height / args.h, pos = l.property("ADBE Transform Group").property("ADBE Position");
      app.beginUndoGroup("Gab: seguir trilha");
      var ts = [], vs = [];
      for (var i = 0; i < args.pts.length; i++) { ts.push(args.pts[i][0]); vs.push([args.pts[i][1] * sx + args.d[0], args.pts[i][2] * sy + args.d[1]]); }
      pos.setValuesAtTimes(ts, vs);
      app.endUndoGroup();
      return ts.length;""", "seguir", comp=comp, camada=camada, pts=pts, w=tr["w"], h=tr["h"], d=list(deslocamento))


def fechar():
    """Salva e fecha o AE sem perguntas (nunca usar Cmd+Q: a pergunta de salvar trava tudo)."""
    try:
        jsx("return GAB.fechar();", "fechar", espera=30)
    except Exception:
        pass


def _render_quadros(comp, saida, limite):
    """Render que não depende do motor de render do AE (no teste de 12/10/2026 a fila, o aerender e a prévia do
    MOGRT travaram no Mac): o AE grava cada quadro em PNG com alfa (saveFrameToPng, ~12 quadros/s) e o ffmpeg junta
    num MOV ProRes 4444 com alfa, no fps da comp."""
    import shutil, tempfile
    tmp = tempfile.mkdtemp(prefix="ogab_ae_", dir=os.path.dirname(saida))
    try:
        info = jsx("""var c = GAB.comp(args.comp); if (!c) throw new Error("comp não encontrada: " + args.comp);
            var fps = c.frameRate, n = Math.round(c.duration * fps);
            for (var i = 0; i < n; i++) c.saveFrameToPng(i / fps, new File(args.d + "/q_" + ("00000" + i).slice(-5) + ".png"));
            return { n: n, fps: fps };""", "quadros", espera=limite, comp=comp, d=tmp)
        n, t0 = info["n"], time.time()
        while time.time() - t0 < limite:
            feitos = len(glob.glob(os.path.join(tmp, "q_*.png")))
            if feitos >= n:
                time.sleep(1); break
            time.sleep(1)
        else:
            raise RuntimeError(f"o AE gravou só {feitos} de {n} quadros")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(info["fps"]), "-i", os.path.join(tmp, "q_%05d.png"),
                            "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16",
                            "-vendor", "apl0", saida], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(saida):
            raise RuntimeError("ffmpeg falhou: " + r.stderr[-800:])
        return saida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mogrt(comp, pasta, limite=600):
    """Exporta a comp como .mogrt na pasta (o AE grava "<comp>.mogrt"): textos e cores da camada CONTROLES ficam
    editáveis no Essential Graphics do Premiere. Devolve o caminho do arquivo."""
    pasta = _abs(pasta); os.makedirs(pasta, exist_ok=True)
    alvo = os.path.join(pasta, comp + ".mogrt")
    if os.path.exists(alvo):
        os.remove(alvo)
    jsx("return GAB.mogrt(args.comp, args.p);", "mogrt", comp=comp, p=pasta)
    t0 = time.time()
    while time.time() - t0 < limite:
        time.sleep(2)
        if os.path.exists(alvo) and os.path.getsize(alvo) > 0:
            time.sleep(1); return alvo
    raise RuntimeError(f"o AE não gravou o MOGRT em {pasta}")


if __name__ == "__main__":
    print("After Effects", versao())
    print(listar())
