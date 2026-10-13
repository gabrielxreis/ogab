# Relatos de erro do Gab

Quem instalou o Gab e respondeu **sim** à pergunta única (no instalador ou na primeira vez que abre) manda, sozinho e
anônimo, cada erro da skill que o Gab corrigiu na máquina dele. O dono (Gabriel) recebe numa planilha, corrige no
repositório e todo mundo recebe no próximo auto-update.

## Como funciona

1. **Na máquina de quem usa** (`scripts/relatar.py`):
   - o Gab corrige algo da skill e roda `relatar.py registrar` (erro, causa, correção e o diff só dos arquivos da skill);
   - o relato é anonimizado ao ser gravado em `~/.claude/ogab_relatos/pendentes/`: caminhos fora da skill viram
     `~/…/*.ext`, saem e-mails, chaves e tokens, parâmetros de link, o nome do usuário e o nome de cada cliente;
   - ao abrir o Gab, `relatar.py enviar` manda os pendentes em segundo plano, **só se `"relatos": true`** no config.
     Sem resposta ou com "não", nada sai da máquina. Mudar: `/ogab config relatos sim|nao`.
2. **No meio** (`relatos/apps_script/`): um app da Web do Google Apps Script na conta do dono grava na planilha
   "Relatos do Gab (/ogab)". O mesmo erro em várias máquinas vira UMA linha (conta vezes e máquinas). Sem token do
   GitHub em lugar nenhum; a URL fica em `relatos/destino.json`.
3. **No dono** (`scripts/relatos.py`, `/ogab relatos`): `listar`, `ver <assinatura>` (com o diff), corrigir no repo,
   commit+push, `resolver <assinatura> <commit> "nota"`.

## Publicar o receptor (uma vez, conta Google do dono)

1. Ligar a API: https://script.google.com/home/usersettings > "Google Apps Script API" ligada.
2. `npx @google/clasp@3.4.1 login` (abre o navegador; entrar e autorizar).
3. Na pasta `relatos/apps_script/`: `npx @google/clasp@3.4.1 create --type webapp --title "Relatos do Gab"`,
   `npx @google/clasp@3.4.1 push -f`, `npx @google/clasp@3.4.1 create-deployment -d "relatos"`.
4. Abrir a URL `https://script.google.com/macros/s/<id>/exec?acao=ping` logada na conta e autorizar o acesso à planilha
   (só na 1ª vez).
5. Colocar a URL `.../exec` em `relatos/destino.json`, rodar `python3 scripts/relatos.py ligar` (guarda a chave de
   admin só no `config.json` do dono e cria a planilha), commit+push do `destino.json`.

Para mudar o código do receptor depois: editar `Code.gs`, `clasp push -f` e `clasp update-deployment <id>` (a URL
continua a mesma).
