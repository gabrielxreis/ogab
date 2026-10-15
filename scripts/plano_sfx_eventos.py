"""Plano de SFX pelo INSTANTE DO EVENTO (regra do usuário, 13/10/2026: "parece que os sfx tá fora do tempo").
colocar_plano_sfx põe cada arquivo a partir do quadro 0; som com respiro antes do ataque (ou cujo momento forte é o
pico, como porta, splash, riser) cai atrasado. Aqui cada linha diz QUANDO o evento acontece na timeline e como alinhar;
o script mede o arquivo, corta o começo (<nome>_cNN.wav) e escreve o plano_sfx.txt já descontado.

  python3 plano_sfx_eventos.py <pasta_sfx> <eventos.txt>
eventos.txt, uma por linha:  T.TT som -NNdB D.D o|p|b: nota
  o = o ATAQUE cai em T (golpe, clique, whoosh curto)   p = o PICO cai em T (porta, splash, riser, impacto com subida)
  b = cama/ambiente: a parte audível começa em T (corta o silêncio do começo do arquivo)
  D.D = quanto o som continua DEPOIS de T.
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def medir(f):
    out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonorizar.py"), "medir", f],
                         capture_output=True, text=True).stdout
    m = re.search(r"ataque\s+([\d.]+)s\s+pico\s+([\d.]+)s", out)
    return float(m[1]), float(m[2])


def main(pasta, eventos):
    linhas = []
    for l in open(eventos):
        m = re.match(r"\s*([\d.]+)\s+(\S+)\s+(-?\d+)(?:dB)?\s+([\d.]+)\s+([opb])\s*:?\s*(.*)", l)
        if not m:
            continue
        t, n, db, dep, al, nota = float(m[1]), m[2], int(m[3]), float(m[4]), m[5], m[6]
        at, pk = medir(os.path.join(pasta, n + ".wav"))
        ref = pk if al == "p" else at
        pre = min(ref, 3.0) if al == "p" else min(ref, 0.04 if al == "o" else 0.05)
        pre = min(pre, t)                       # no começo do vídeo não dá para entrar antes do 0
        corte = ref - pre; nome = n
        if corte > 0.02:
            nome = f"{n}_c{round(corte * 100)}"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{corte:.3f}", "-i", os.path.join(pasta, n + ".wav"),
                            "-af", f"afade=t=in:d={0.25 if al == 'b' else 0.03}", os.path.join(pasta, nome + ".wav")])
        ini = t - pre
        linhas.append((ini, f"{ini:.3f}s A3 {nome} {db}dB {pre + dep:.2f}s: {nota} [evento {t:.2f}s, {'pico' if al == 'p' else 'ataque'}]"))
    linhas.sort()
    open(os.path.join(pasta, "plano_sfx.txt"), "w").write("\n".join(x for _, x in linhas) + "\n")
    print(f"{len(linhas)} sons -> {os.path.join(pasta, 'plano_sfx.txt')}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
