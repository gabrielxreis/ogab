#!/bin/bash
# Deixa o /ogab disponível no Codex (CLI e app). Uma instalação só: o Codex usa a mesma pasta do Claude Code.
#   bash ~/.claude/skills/ogab/codex/instalar.sh
# Copia o carregador do Codex para ~/.codex/skills/ogab/SKILL.md (cópia de verdade: o Codex ignora link simbólico;
# o atualizar.py renova a cópia a cada update do Gab).
# Não mexe no sandbox do Codex: quando o Gab precisar de rede ou de escrever fora do projeto, o Codex pede aprovação.
set -e
SKILL="$HOME/.claude/skills/ogab"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST="$CODEX_HOME/skills/ogab"

[ -f "$SKILL/codex/SKILL.md" ] || { echo "ERRO: /ogab não está em $SKILL (rode o install.sh do Gab antes)"; exit 1; }

mkdir -p "$DEST"
rm -f "$DEST/SKILL.md"
cp "$SKILL/codex/SKILL.md" "$DEST/SKILL.md"
echo "OK: skill ogab no Codex ($DEST)"

command -v codex >/dev/null 2>&1 || echo "AVISO: comando codex não encontrado; instale o Codex e rode de novo"
