#!/bin/bash
# MP4 1080x1920 -> GIF 240x426, 15 fps, paleta própria (leve para o README)
set -e
cd "$(dirname "$0")/out"
DEST="$HOME/.claude/skills/ogab/.github/motions"
mkdir -p "$DEST"
for m in contador lista frase grafico cta; do
  ffmpeg -y -loglevel error -i "$m.mp4" -vf "fps=15,scale=240:-2:flags=lanczos,palettegen=max_colors=96:stats_mode=diff" "_pal_$m.png"
  ffmpeg -y -loglevel error -i "$m.mp4" -i "_pal_$m.png" -lavfi "fps=15,scale=240:-2:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" -loop 0 "$DEST/$m.gif"
  echo "$m $(du -k "$DEST/$m.gif" | cut -f1) KB"
done
