"""Mede a música antes de cortar na batida ou escolher SFX tonal (só numpy + ffmpeg).

  python3 musica.py medir <musica.wav> [--bumbo INI FIM] [--de S --ate S] [--json saida.json]

Devolve:
- BPM MEDIDO (autocorrelação do fluxo espectral). O bpm do Artlist ou do Google erra (no método da trilha
  cinematográfica do @iamjeff.ia, o Google dizia 134 e a medida deu 136); com o BPM errado as cenas escorregam
  da batida depois de alguns compassos.
- Grade de batidas: o tempo de cada batida (fase achada pelos ataques), para cortar cena e motion em cima delas.
- Tom e relativo (perfis de Krumhansl sobre o croma). Detector de tom erra entre o tom e o relativo
  (Lá menor x Dó maior): quando os dois empatam sai "conferir", e aí confirmar no tunebat/songbpm.
- Afinação em cents do Lá 440. Passou de +-20 cents, SFX tonal (riser, drone, impacto com nota) soa desafinado.
- --bumbo INI FIM: o segundo exato do maior salto de grave (< 120 Hz) no intervalo, janelas de 10 ms
  (a entrada da batida, o drop). É ali que corte, impacto e pico de riser caem.
"""
import argparse, json, subprocess, sys
import numpy as np

SR = 22050
NOTAS = ["Dó", "Dó#", "Ré", "Mi♭", "Mi", "Fá", "Fá#", "Sol", "Lá♭", "Lá", "Si♭", "Si"]
MAIOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MENOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def ler(arq, de=0.0, ate=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(de)] + (["-t", str(ate - de)] if ate else []) + \
          ["-i", arq, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)


def espectro(x, n=4096, hop=512):
    w = np.hanning(n); q = 1 + max(0, (len(x) - n)) // hop
    quadros = np.lib.stride_tricks.as_strided(x, (q, n), (x.strides[0] * hop, x.strides[0]))
    return np.abs(np.fft.rfft(quadros * w, axis=1)), np.fft.rfftfreq(n, 1 / SR), hop / SR


def bpm_e_grade(x):
    S, f, dt = espectro(x, 2048, 256)
    fluxo = np.maximum(0, np.diff(np.log1p(S), axis=0)).sum(axis=1)
    fluxo = fluxo - np.convolve(fluxo, np.ones(32) / 32, mode="same"); fluxo = np.maximum(fluxo, 0)
    ac = np.correlate(fluxo, fluxo, mode="full")[len(fluxo) - 1:]
    lags = np.arange(len(ac)) * dt; ok = (lags > 60 / 200) & (lags < 60 / 60)
    peso = np.exp(-0.5 * (np.log2((60 / np.maximum(lags, 1e-9)) / 120)) ** 2)   # prefere ~120 (resolve dobro/metade)
    i = np.argmax(np.where(ok, ac * peso, 0))
    # refino sub-amostra (parábola) para o BPM sair com décimos
    a, b, c = ac[i - 1], ac[i], ac[i + 1]; i_f = i + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    periodo = i_f * dt; bpm = 60 / periodo
    # fase: o deslocamento cuja grade soma mais fluxo
    passos = int(round(periodo / dt)); fases = [fluxo[k::passos].sum() for k in range(passos)]
    t0 = int(np.argmax(fases)) * dt
    grade = np.arange(t0, len(x) / SR, periodo)
    return bpm, periodo, grade


def tom(x):
    S, f, _ = espectro(x, 8192, 2048)
    ok = (f > 55) & (f < 2000); midi = 69 + 12 * np.log2(f[ok] / 440)
    croma = np.zeros(12); e = (S[:, ok] ** 2).sum(axis=0)
    np.add.at(croma, np.round(midi).astype(int) % 12, e)
    croma /= croma.sum()
    notas = {}
    for k in range(12):
        notas[(NOTAS[k], "maior")] = np.corrcoef(croma, np.roll(MAIOR, k))[0, 1]
        notas[(NOTAS[k], "menor")] = np.corrcoef(croma, np.roll(MENOR, k))[0, 1]
    ordem = sorted(notas.items(), key=lambda kv: -kv[1])
    (n1, m1), c1 = ordem[0]; c2 = ordem[1][1]
    k = NOTAS.index(n1)
    rel = (NOTAS[(k + 3) % 12], "maior") if m1 == "menor" else (NOTAS[(k - 3) % 12], "menor")
    # afinação: desvio em cents dos picos fortes em relação à grade do Lá 440 (mediana ponderada)
    pico = S[:, ok].mean(axis=0); fk = f[ok]; mx = (pico[1:-1] > pico[:-2]) & (pico[1:-1] > pico[2:]) & (pico[1:-1] > pico.max() * 0.05)
    cents = 100 * (12 * np.log2(fk[1:-1][mx] / 440) - np.round(12 * np.log2(fk[1:-1][mx] / 440)))
    pesos = pico[1:-1][mx]; ordc = np.argsort(cents)
    afin = float(cents[ordc][np.searchsorted(np.cumsum(pesos[ordc]), pesos.sum() / 2)]) if len(cents) else 0.0
    return {"tom": f"{n1} {m1}", "relativo": f"{rel[0]} {rel[1]}", "confianca": round(float(c1), 2),
            "conferir": bool(c1 - c2 < 0.03), "afinacao_cents": round(afin, 1)}


def bumbo(arq, ini, fim):
    x = ler(arq, ini, fim); n = SR // 100
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.fft.irfft(X * (f < 120), n=len(x))
    e = np.array([(g[i:i + n] ** 2).mean() for i in range(0, len(g) - n, n)]) + 1e-12
    # a entrada da batida é onde o grave do 1 s seguinte mais supera o do 1 s anterior (todo bumbo depois do
    # primeiro também "salta" do silêncio entre batidas; comparar trechos acha a ENTRADA, não um bumbo qualquer)
    c = np.concatenate([[0], np.cumsum(e)]); w = 100
    razao = np.array([((c[min(i + w, len(e))] - c[i]) / min(w, len(e) - i)) / ((c[i] - c[max(0, i - w)]) / max(1, i - max(0, i - w)) + 1e-12)
                      if i > 0 else 0 for i in range(len(e))])
    i = int(np.argmax(razao))
    viz = slice(max(1, i - 10), min(len(e), i + 10)); salto = np.diff(10 * np.log10(e))[viz.start - 1:viz.stop - 1]
    return round(ini + (viz.start + int(np.argmax(salto))) * n / SR, 3)


def medir(arq, de=0.0, ate=None, faixa_bumbo=None):
    x = ler(arq, de, ate)
    bpm, periodo, grade = bpm_e_grade(x)
    r = {"arquivo": arq, "bpm": round(bpm, 1), "batida_s": round(periodo, 4), "compasso_4_4_s": round(4 * periodo, 3),
         "primeira_batida_s": round(de + grade[0], 3), "batidas": [round(de + t, 3) for t in grade[:64]]}
    r.update(tom(x))
    if faixa_bumbo:
        r["bumbo_s"] = bumbo(arq, *faixa_bumbo)
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["medir"]); ap.add_argument("arquivo")
    ap.add_argument("--bumbo", nargs=2, type=float); ap.add_argument("--de", type=float, default=0.0)
    ap.add_argument("--ate", type=float); ap.add_argument("--json")
    a = ap.parse_args()
    r = medir(a.arquivo, a.de, a.ate, a.bumbo)
    if a.json:
        json.dump(r, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"BPM {r['bpm']} (batida {r['batida_s']} s, compasso {r['compasso_4_4_s']} s), 1ª batida em {r['primeira_batida_s']} s")
    print(f"Tom {r['tom']} (relativo {r['relativo']}), confiança {r['confianca']}" + ("  -> CONFERIR no tunebat: tom e relativo empataram" if r["conferir"] else ""))
    print(f"Afinação {r['afinacao_cents']:+} cents" + ("  -> fora de +-20: SFX tonal vai desafinar" if abs(r["afinacao_cents"]) > 20 else ""))
    if "bumbo_s" in r:
        print(f"Bumbo (entrada da batida) em {r['bumbo_s']} s")
    print("Batidas:", ", ".join(map(str, r["batidas"][:16])), "...")
