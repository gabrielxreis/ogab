"""Reconhece a fonte de um texto numa imagem usando o "Localizar fonte semelhante" (Match Font) do Photoshop.

    python3 reconhecer_fonte.py imagem.png X1 Y1 X2 Y2 [saida.png]

- Abre a imagem no Photoshop, seleciona o retângulo (em pixels da imagem) em volta de UMA linha de texto,
  roda Texto > Localizar fonte semelhante e salva um print da janela de resultados (fontes instaladas +
  Adobe Fonts, ícone de nuvem = dá para ativar) em `saida.png` (padrão: ao lado da imagem, *.fontes.png).
- Depois, LER o print (Read) e escolher; conferir o PostScript name em app.fonts ou ativar no Adobe Fonts.
- Precisa: Photoshop aberto, Acessibilidade liberada para o Terminal (System Events). Traz o Photoshop para a
  frente por alguns segundos (o menu só funciona assim). Não usar enquanto o usuário trabalha no Photoshop.
Dica: selecionar só a linha do título (letras grandes, sem foto atrás) dá resultado melhor.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ps_lib as PS  # noqa: E402

PROC = '(first process whose bundle identifier is "com.adobe.Photoshop")'


def osa(script):
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60).stdout.strip()


def pronto(png):
    """Lista carregada = muitas linhas com texto escuro na área branca de resultados."""
    try:
        from PIL import Image
    except ImportError:
        return True
    im = Image.open(png).convert("L"); w, h = im.size
    area = im.crop((int(w * .05), int(h * .25), int(w * .9), int(h * .85)))
    escuros = sum(1 for p in area.tobytes() if p < 90)
    return escuros > area.width * area.height * 0.01


def main():
    if os.name == "nt":  # testado 30/10/2026 (PS 27.11): por script o Photoshop cancela o Match Font (erro 8007) e o menu não aparece na automação do Windows
        sys.exit("Windows: o 'Localizar fonte semelhante' não abre por script. Use o comparar_fonte.py (sistema + Adobe Fonts ativadas) "
                 "ou peça ao usuário para rodar Texto > Localizar fonte semelhante no Photoshop e dizer as sugestões.")
    img = os.path.abspath(sys.argv[1]); x1, y1, x2, y2 = map(int, sys.argv[2:6])
    saida = sys.argv[6] if len(sys.argv) > 6 else os.path.splitext(img)[0] + ".fontes.png"
    PS.js(f"""var d=app.open(new File({img!r})); app.preferences.rulerUnits=Units.PIXELS;
d.selection.select([[{x1},{y1}],[{x2},{y1}],[{x2},{y2}],[{x1},{y2}]]); 'ok'""")
    osa('tell application id "com.adobe.Photoshop" to activate'); time.sleep(1.2)
    osa(f'''tell application "System Events" to tell {PROC}
        set m to menu "Texto" of menu bar 1
        repeat with mi in (menu items of m)
            if name of mi starts with "Localizar fonte" or name of mi starts with "Match Font" then click mi
        end repeat
    end tell''')
    # espera a lista: fotografa a janela a cada 3 s até aparecerem linhas de resultado (até 40 s)
    geo = ""
    for _ in range(14):
        time.sleep(3)
        geo = osa(f'''tell application "System Events" to tell {PROC}
            set w to (first window whose name starts with "Localizar fonte" or name starts with "Match Font")
            set {{px, py}} to position of w
            set {{sx, sy}} to size of w
            return (px as text) & "," & (py as text) & "," & (sx as text) & "," & (sy as text)
        end tell''')
        if not geo:
            continue
        subprocess.run(["screencapture", "-x", "-R", geo, saida])
        if pronto(saida):
            break
    osa(f'''tell application "System Events" to tell {PROC}
        try
            click button "Cancelar" of (first window whose name starts with "Localizar fonte")
        end try
        try
            click button "Cancel" of (first window whose name starts with "Match Font")
        end try
    end tell''')
    PS.js("app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); 'ok'")
    print(saida if geo else "janela de resultados não apareceu")


if __name__ == "__main__":
    main()
