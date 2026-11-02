#!/bin/zsh
# Renderiza exemplo.mp4 + exemplo.gif dos presets HyperFrames do kit (24 fps). Sem argumento = os 4.
[ $# -eq 0 ] && set -- curva degraus rota explodida
P="$(cd "$(dirname "$0")/.." && pwd)"; PROG="$P/../scripts/progresso.py"
for n in "$@"; do
  python3 "$PROG" --nome "$n" -- python3 "$P/$n/gerar.py" "$P/$n/exemplo/exemplo.json" || exit 1
  mv "$P/$n/exemplo/exemplo.mp4" "$P/$n/exemplo.mp4"
  ffmpeg -v error -y -i "$P/$n/exemplo.mp4" -vf "fps=12,scale=270:480:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" "$P/$n/exemplo.gif"; echo "ok $n"
done
