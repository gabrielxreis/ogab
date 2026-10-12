<!-- Movido do SKILL.md em 12/10/2026 (texto completo, sem cortes). Ler só na etapa. -->

## 4. DaVinci: projeto e narração

`scripts/resolve_lib.py`: `criar_projeto(nome, w, h, fps)` (grava fps de timeline **e playback** antes de qualquer timeline). **Logo ao criar a timeline, antes de importar qualquer coisa:** `criar_timeline` confere playback = timeline; se avisar, corrigir na hora pela interface (File > Project Settings > Master Settings > Playback frame rate > Save). **Não ligar Render Cache (Smart ou User): o usuário não quer**; deixar em None. Não deixar para quando o áudio picotar. Depois dos letterings, rodar `checar_fades(t)` (todos com fade out limpo). Se o áudio picotar, `checar_playback(p)` e, se divergir, corrigir em Project Settings > Master Settings pela interface, ver docs/PROCESSO.md), `criar_timeline`, `colocar_narracao(db=+5)`. Formato pela plataforma (9:16 1080x1920; 4:5 1080x1350; 16:9 1920x1080).

**Gravação de apresentador (vlog, talking head):** transcrição = a do DaVinci que o usuário fez no clipe (`transcrever.py saida.json --clipe "<clipe>"`), cortes com `scripts/cortes.py` (plano por frase/retake + `montar`), legenda pela `broll.transcricao_na_timeline`, depois b-roll com `scripts/broll.py`. Bugs já resolvidos e suas causas: `docs/PROCESSO.md` > Bugs encontrados.

**Whisper é só RESERVA (regra do usuário, 12/10/2026):** DaVinci 21.1+ transcreve sozinho; o Whisper só roda em DaVinci antigo ou se o usuário pedir `--motor whisper` (o install nem instala na 21.1+). Nunca chamar o Whisper "para conferir".

**Transcrição (tempo de cada palavra):** sempre por `python3 SKILL_DIR/scripts/transcrever.py narracoes/narracao.wav narracoes/transcricao.json`. Ele **detecta sozinho a versão do DaVinci**: na **21.1 ou mais nova** usa a transcrição do próprio DaVinci (`TranscribeAudio` + `GetTranscription`); **abaixo da 21.1** (a API não devolve o texto, mesmo o DaVinci transcrevendo na interface desde a 18.5) usa o **Whisper local** (mlx-whisper no Apple Silicon, faster-whisper no Intel, grátis; o `install.sh` instala só quando a versão precisa). `transcrever.py --versao` mostra qual caminho vai ser usado. Abaixo da 20.2.2, conferir se narração e música caíram em A1/A2 (bug da API corrigido nessa versão).

