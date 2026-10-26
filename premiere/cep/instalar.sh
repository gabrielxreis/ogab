#!/bin/bash
# Instala a extensão "Gab Ponte PPro" (CEP) para o Premiere Pro 2018 a 25.x no Mac. Sem sudo: pasta do usuário.
# NÃO TESTADO (feito no Windows, 26/10/2026): mesmo CEP; conferir caminhos com / na QE do Mac.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Library/Application Support/Adobe/CEP/extensions/com.gabrielxreis.ogab.ppronte"

# Extensão sem assinatura: PlayerDebugMode nas versões do CEP que o Premiere usa (8 = 2018, 9 = 2019 ... 12 = 2024/25).
for v in 8 9 10 11 12; do defaults write "com.adobe.CSXS.$v" PlayerDebugMode 1; done

rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
cp -R "$AQUI/plugin" "$DEST"
echo "Gab Ponte PPro instalada em $DEST. Feche e abra o Premiere para ela iniciar."
