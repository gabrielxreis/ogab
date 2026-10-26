"""Teste de ponta a ponta só pela API pública do premiere2019_lib (o que o /ogab chamaria)."""
import json, os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

M = lambda n: os.path.join(AQUI, "midia", n)
R = os.path.join(AQUI, "render")
t0 = time.time()
etapas = [
    ("projeto", lambda: P.abrir_projeto(os.path.join(AQUI, "Teste Gab 2019.prproj"))),
    ("sequência", lambda: P.criar_sequencia("E2E 01")),
    ("bruto V1/A1", lambda: P.colocar("E2E 01", M("bruto.mp4"), 0)),
    ("takes V2", lambda: P.montar_takes("E2E 01", [(M("take_01.mp4"), 3.0), (M("take_02.mp4"), 5.0)], fim=8.0)),
    ("música A2 -10 dB", lambda: P.colocar_musica("E2E 01", M("musica.wav"), inicio_faixa=5.0, dur=20.0, db=-10)),
    ("motion V3", lambda: P.colocar("E2E 01", M("motion.mov"), 0.5, video=2, audio=None)),
    ("legenda V4", lambda: P.legenda("E2E 01", M("legenda.srt"))),
    ("Lumetri no take", lambda: P.efeito("E2E 01", 1, 3.0)),
    ("transição", lambda: P.transicao("E2E 01", 1, 3.0)),
    ("corte V1 10 s", lambda: P.cortar("E2E 01", 0, 10.0)),
    ("marcador", lambda: P.marcador("E2E 01", 0, "GANCHO")),
    ("salvar", P.salvar),
    ("retrato", lambda: P.retrato("E2E 01")),
    ("quadro 6 s", lambda: P.quadro("E2E 01", 6.0, os.path.join(R, "e2e_6s.png"))),
]
for nome, f in etapas:
    t = time.time()
    try:
        r = f()
    except Exception as e:
        r = f"ERRO {e}"
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:500]}")
print(f"montagem total: {time.time() - t0:.2f} s")
t = time.time()
print(P.exportar("E2E 01", os.path.join(R, "e2e.mp4")), f"{time.time() - t:.1f} s de render")
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration",
                      "-of", "compact", os.path.join(R, "e2e.mp4")], capture_output=True, text=True).stdout)
