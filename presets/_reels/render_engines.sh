#!/bin/zsh
# Uso: render_engines.sh [palito|e-se]. Amostras do palito (exemplo pronto do motor, 30 qps convertido a 24) e do e-se (trecho 0-9 s a 24 qps).
P="$(cd "$(dirname "$0")/.." && pwd)"; export NODE_PATH="$P/_reels/kit/node_modules"
# Chromium do Playwright: usa o mais novo do cache se o da versão fixa não estiver baixado
[ -n "$CHROME" ] || export CHROME="$(ls -d $HOME/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/* 2>/dev/null | tail -1)"
G="fps=12,scale=270:480:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3"
if [ -z "$1" ] || [ "$1" = palito ]; then
echo "== palito"; rm -rf "$P/palito/exemplo"; cp -R "$P/palito/engine/template" "$P/palito/exemplo"; cd "$P/palito/exemplo"
node "$P/palito/engine/tools/render.js" video silent.mp4 | grep -v "^\[page\]" || exit 1
ffmpeg -v error -y -i silent.mp4 -i audio/vo_kokoro.wav -map 0:v -map 1:a -r 24 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -shortest "$P/palito/exemplo.mp4"
ffmpeg -v error -y -t 9 -i "$P/palito/exemplo.mp4" -vf "$G" "$P/palito/exemplo.gif"; echo "ok palito"
fi
if [ -z "$1" ] || [ "$1" = e-se ]; then
echo "== e-se"; cd "$P/e-se/engine"
node render.mjs video "$P/e-se/silent.mp4" 24 0 9 || exit 1
ffmpeg -v error -y -i "$P/e-se/silent.mp4" -vf scale=1080:1920:flags=lanczos -c:v libx264 -crf 18 -pix_fmt yuv420p "$P/e-se/exemplo.mp4" && rm "$P/e-se/silent.mp4"
ffmpeg -v error -y -i "$P/e-se/exemplo.mp4" -vf "$G" "$P/e-se/exemplo.gif"; echo "ok e-se"
fi
