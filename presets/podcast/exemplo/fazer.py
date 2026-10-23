"""Mídia do exemplo do preset PODCAST: duas pessoas REAIS de banco gratuito (Mixkit, licença livre: CREDITOS.md).

  python3 presets/podcast/exemplo/fazer.py            # baixa os clipes e rastreia os rostos
  python3 presets/podcast/gerar.py presets/podcast/exemplo/plano.json /tmp/podcast \\
          --render presets/podcast/exemplo.mp4 --gif   # refaz exemplo.mp4 e exemplo.gif

Grava em exemplo/midia/ (fora do git: a licença da Mixkit não deixa redistribuir o clipe original):
  falante_a.mp4 / falante_b.mp4                  os dois planos (1280x720, mesmo estúdio, sem som; cabeça inteira
                                                 no quadro o tempo todo: clipe com a cabeça encostando no topo não serve)
  falante_a_trilha.json / falante_b_trilha.json  rosto quadro a quadro (scripts/rastrear.py --rosto)
Trocado em 23/10/2026 (pedido do usuário: o exemplo com pessoas ilustradas estava feio).
"""
import os, subprocess, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__)); MIDIA = os.path.join(AQUI, "midia")
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
CLIPES = {   # Mixkit, licença "Free" (mixkit.co/license): uso em projeto, sem redistribuir o arquivo original
    "falante_a": "https://assets.mixkit.co/videos/52181/52181-720.mp4",   # mulher de blazer claro falando e gesticulando
    "falante_b": "https://assets.mixkit.co/videos/52184/52184-720.mp4",   # mulher de preto falando ao microfone
}


def main():
    os.makedirs(MIDIA, exist_ok=True)
    for nome, url in CLIPES.items():
        mp4 = os.path.join(MIDIA, nome + ".mp4")
        if not os.path.exists(mp4):
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(mp4, "wb") as f:
                f.write(r.read())
        subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "rastrear.py"), mp4, "--rosto",
                        "--saida", os.path.join(MIDIA, nome + "_trilha.json")], check=True)
    print("ok:", MIDIA)


if __name__ == "__main__":
    main()
