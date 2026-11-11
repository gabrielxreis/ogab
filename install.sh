#!/usr/bin/env bash
# O Gab (/ogab) não é mais instalado pelo GitHub. Este arquivo só existe para links antigos continuarem funcionando:
# ele chama o instalador oficial do ogab.io, que baixa o Gab do servidor do Gab com a sua key.
# Pegue a sua key e a mensagem pronta de instalação no painel: https://ogab.io/login
set -euo pipefail
echo "O Gab agora instala pelo ogab.io (com a sua key). Abrindo o instalador oficial..."
exec bash -c "$(curl -fsSL https://ogab.io/instalar.sh)"
