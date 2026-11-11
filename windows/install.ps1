# O Gab (/ogab) nao e mais instalado pelo GitHub. Este arquivo so existe para links antigos continuarem funcionando:
# ele chama o instalador oficial do ogab.io, que baixa o Gab do servidor do Gab com a sua key.
# Pegue a sua key e a mensagem pronta de instalacao no painel: https://ogab.io/login
Write-Host "O Gab agora instala pelo ogab.io (com a sua key). Abrindo o instalador oficial..."
irm https://ogab.io/instalar.ps1 | iex
