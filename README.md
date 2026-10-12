<div align="center">

[![/ogab](.github/banner.svg)](#readme)

[![Último commit](https://img.shields.io/github/last-commit/gabrielxreis/video-redes-skill?color=brightgreen&label=atualizado&style=for-the-badge)](https://github.com/gabrielxreis/video-redes-skill/commits/main "Histórico")
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-D97757.svg?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.com/claude-code "Claude Code")
[![DaVinci Resolve Studio](https://img.shields.io/badge/DaVinci_Resolve-Studio_21.1+-233A51.svg?style=for-the-badge&logo=davinciresolve&logoColor=white)](#requisitos "Requisitos")
[![macOS](https://img.shields.io/badge/-macOS-lightblue.svg?style=for-the-badge&logo=apple&logoColor=black)](#instalacao "Instalação")
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#requisitos "Requisitos")
[![Licença: MIT](https://img.shields.io/badge/-MIT-red.svg?style=for-the-badge)](LICENSE "Licença")

</div>

**/ogab** (o Gab) é uma skill do Claude Code que edita vídeo para redes sociais **dentro do DaVinci Resolve**: do roteiro aprovado até a timeline pronta e o MP4 masterizado, com narração por IA, música, efeitos sonoros, takes de banco ou gerados, lettering animado, motions (HyperFrames), legenda com métrica e conferência automática. Também edita gravações de apresentador (talking head) já abertas no DaVinci.

> **Cada pessoa usa as PRÓPRIAS contas.** A skill não traz conta, chave nem login. Você conecta os seus serviços (ElevenLabs, Artlist, Envato, Magnific...) no seu Claude e faz login nos sites no seu navegador. Nada disso vai para o repositório nem para o `config.json`.

* [INSTALAÇÃO](#instalacao)
    * [Um comando](#um-comando)
    * [Passo a passo manual](#passo-a-passo-manual)
    * [Atualizar](#atualizar)
    * [Requisitos](#requisitos)
* [USO E COMANDOS](#uso-e-comandos)
    * [Comandos](#comandos)
    * [O fluxo](#o-fluxo)
    * [Editar um vídeo que já está no DaVinci](#editar-um-video-que-ja-esta-no-davinci)
* [CONFIGURAÇÃO](#configuracao)
    * [Opções](#opcoes)
    * [Cor e vídeos de iPhone](#cor-e-videos-de-iphone)
* [CLIENTES](#clientes)
    * [Perfil, pronúncia e estilo de edição](#perfil-pronuncia-e-estilo-de-edicao)
* [PASTA DO VÍDEO](#pasta-do-video)
* [LEGENDA](#legenda)
* [MOTIONS](#motions)
* [ÁUDIO E EXPORT](#audio-e-export)
* [SCRIPTS](#scripts)
* [ARMADILHAS CONHECIDAS](#armadilhas-conhecidas)
* [ESTRUTURA DO REPOSITÓRIO](#estrutura-do-repositorio)
* [LICENÇA](#licenca)


# INSTALAÇÃO

[![Instalar no macOS](https://img.shields.io/badge/-Instalar_no_macOS-lightblue.svg?style=for-the-badge&logo=apple&logoColor=black)](#um-comando)
[![install.sh](https://img.shields.io/badge/-install.sh-grey.svg?style=for-the-badge&logo=gnubash&logoColor=white)](install.sh)
[![HyperFrames](https://img.shields.io/badge/-HyperFrames-6E40C9.svg?style=for-the-badge)](https://github.com/heygen-com/hyperframes)
[![Provedores](https://img.shields.io/badge/-Provedores-orange.svg?style=for-the-badge)](docs/PROVEDORES.md)

## Primeiro uso (leia isto)

Depois de instalar, abra o Claude Code e digite **`/ogab comecar`**. O Gab explica em 1 minuto:
- **Como pedir:** `/ogab edita o vídeo X do cliente Y`, `/ogab faz um reels para Y sobre Z`, ou mande o site/briefing de um cliente novo.
- **Onde ele para e espera você:** roteiro, voz, **legenda** (valide antes dos motions: o tempo de tudo depende dela), música.
- **O que você recebe no fim de cada ação:** só uma barrinha (`▰▰▰▱ 4 de 9`, o que falta, o próximo passo).
- **Como gastar menos tokens:** uma conversa por vídeo; para retomar, `/ogab continua o vídeo X` (ele lê o `PROJETO.md` da pasta do vídeo, que guarda status, decisões, arquivos e pendências); peça várias coisas de uma vez; avise quando mexer na timeline.

Guia completo: [`docs/BEM_VINDO.md`](docs/BEM_VINDO.md). O `SKILL.md` é só o mapa; cada etapa tem seu arquivo em `docs/etapas/`, lido só quando chega nela.

## Um comando

Cole no **Terminal** do Mac:

```bash
curl -fsSL https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/install.sh | bash
```

O [install.sh](install.sh) pode ser rodado de novo para atualizar. Ele:
- instala **Homebrew** (se faltar), **ffmpeg**, **yt-dlp**, **Node.js**, **Python 3**, **git** e **Pillow**;
- baixa a skill em `~/.claude/skills/ogab` e cria o seu `config.json`;
- instala o **HyperFrames** e roda o `hyperframes doctor`;
- instala as fontes livres (Poppins, Playfair Display, Lobster);
- confere o **DaVinci Resolve Studio** e o scripting, **detecta a versão** e, abaixo da 21.1, instala o **Whisper local** para a transcrição.

Depois falta só o que depende de você: ligar o scripting no DaVinci, conectar as suas contas e o Claude in Chrome (passos 5, 8 e 9 abaixo). Reinicie o Claude Code e peça um vídeo.

## Passo a passo manual

1. **HyperFrames** (motions e edição dinâmica):
   ```bash
   npx skills add heygen-com/hyperframes
   ```
2. **Clonar na pasta de skills do Claude:**
   ```bash
   git clone https://github.com/gabrielxreis/video-redes-skill ~/.claude/skills/ogab
   ```
3. **Criar a sua configuração** (fica só na sua máquina):
   ```bash
   cp ~/.claude/skills/ogab/config.example.json ~/.claude/skills/ogab/config.json
   ```
4. **Dependências Python:**
   ```bash
   pip3 install pillow pyobjc-framework-Vision
   ```
   O `pyobjc-framework-Vision` é o OCR da Apple usado pelo `legenda_ui.py`.
5. **No DaVinci:** Preferences > System > General > **External scripting using: Local**.
6. **Fontes:** instale as de `assets/fontes/` (licença OFL). O preset de legenda padrão usa **Poppins Bold**.
7. **Lettering animado (opcional):** a skill foi feita com o pacote **@gabrielxreis_ Text Presets** (Cinematic, Palavra Por Palavra, Blur Up, Destacado, Zoom Out...), que **não** vem no repositório. Use o seu pacote de títulos do Fusion (`.drfx`) em `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/`, reinicie o Resolve e coloque os nomes em `config.json > lettering`.
8. **Conectar as SUAS contas** ([docs/PROVEDORES.md](docs/PROVEDORES.md)): ElevenLabs, Artlist, Envato, Magnific etc. Só o que você usa.
9. **Claude in Chrome:** instale a extensão e faça login nos sites. Downloads são sempre pelo navegador; a IA nunca digita senha.
10. **Acessibilidade:** dê permissão de Acessibilidade ao app que roda o Claude Code (Ajustes do Sistema > Privacidade e Segurança > Acessibilidade). Só é necessário para os ajustes de legenda feitos pela interface.

> **Skill complementar recomendada:** `competitor-profiling` (pacote `anthropic-skills`). Quando você manda o site de uma empresa, a skill usa ela para montar o perfil completo antes de começar.

## Atualizar

A skill faz `git pull` sozinha toda vez que é usada (sem tocar no seu `config.json` nem em `clientes/`). Para forçar:

```
/ogab update
```

## Requisitos

| | Mínimo | Observação |
|---|---|---|
| Sistema | macOS | Testado em Apple Silicon |
| DaVinci Resolve | **Studio 21.1+** | A versão grátis não tem scripting externo. Abaixo da 21.1 a transcrição vai para o Whisper local |
| Python | 3.10+ | Pillow; `pyobjc-framework-Vision` para o `legenda_ui.py` |
| ffmpeg | qualquer recente | Conversão, loudness, master, conferência |
| yt-dlp | qualquer recente (`brew upgrade yt-dlp` se o YouTube mudar) | Baixar trecho de vídeo público do YouTube (reportagem, cena histórica) para b-roll |
| Node.js | 18+ | HyperFrames |


# USO E COMANDOS

## Comandos

No Claude Code, chame com `/ogab` seguido do pedido, ou só peça em linguagem normal:

| Comando | O que faz |
|---|---|
| `/ogab faz um vídeo para a <empresa> sobre <tema>` | Fluxo completo, do roteiro ao export |
| `/ogab <edição no DaVinci>` | Edita a timeline aberta (cortes, legenda, música, motions, b-roll...) |
| `/ogab cliente <nome>` | Cria ou atualiza o perfil do cliente (site, logo, pronúncias, estilo) |
| `/ogab pauta <cliente>` | Busca notícias recentes dos temas do cliente e sugere roteiros |
| `/ogab config <chave> <valor>` | Liga ou desliga opções. Ex.: `config opcoes.multi_formatos true` |
| `/ogab ajuda` | Mostra o que está habilitado e os provedores escolhidos |
| `/ogab update` | Atualiza a skill |

## O fluxo

| # | Etapa | Você decide? | Ferramenta |
|---|---|---|---|
| 1 | Perfil do cliente + logos e identidade visual baixadas do site | Só na 1ª vez | `competitor-profiling`, `marca.py` |
| 2 | **Roteiro** no formato da plataforma (Instagram, YouTube, Meta Ads) | **Aprova** | Pesquisa com fonte e data |
| 3 | **Voz** (narração por IA) | **Escolhe** | ElevenLabs ou Artlist |
| 4 | Projeto no DaVinci (`Assunto - Empresa`), Media Pool organizado, Stacked Timelines | - | Scripting API |
| 5 | Música (pop/remix leve por padrão), -10 dB, fade | Escolhe entre 3-4 | Artlist ou Envato |
| 6 | Efeitos sonoros (whoosh, pop, impacto) | Liga/desliga | Artlist ou Envato |
| 7 | Takes: IA, banco ou misto; geração só no modo ilimitado | Origem | Envato, Artlist, Pexels / Magnific |
| 8 | Lettering animado nas palavras-chave, FadeOut de 31 quadros no bloco | Vê a lista | Seu pacote `.drfx` |
| 9 | **Motions** centralizados e medidos, com as cores da marca, CTA animado | Vê a tabela | HyperFrames + `guias.py` |
| 10 | **Legenda** de uma linha, métrica obrigatória, do início ao fim | - | `legendas.py`, `legenda_ui.py` |
| 11 | Timeline pronta, **conferência**, **master** e export (se pedir), capa e texto do post | - | `resolve_lib.py`, `qc.py` |

## Editar um vídeo que já está no DaVinci

Para gravação de apresentador (talking head), a skill:
- mantém a trilha principal **V1 intocada**: b-roll, lettering, BG e motions entram em camadas acima;
- liga **Voice Isolation** no áudio de iPhone ou câmera;
- enquadra o rosto com o **mínimo de zoom**, sem punch-in alternado; nada sobre o rosto;
- em vídeo emocional, põe **b-roll em toda imagem concreta** e lettering + b-roll nas frases de efeito;
- corta retakes e pausas pela transcrição (`cortes.py`), com a timeline original como backup.


# CONFIGURAÇÃO

Tudo em `config.json` (copiado de `config.example.json`, fora do git).

## Opções

| Opção | Padrão | O que faz |
|---|---|---|
| `opcoes.efeitos_sonoros` | `true` | Whoosh nas trocas, impacto no gancho, pop no CTA |
| `opcoes.movimentos_nos_takes` | `perguntar` | Zoom/movimento leve nos takes (`sempre`, `nunca`, `perguntar`) |
| `opcoes.lettering_no_gancho` | `perguntar` | Título animado no começo |
| `opcoes.multi_formatos` | `false` | Renderiza também 4:5, 16:9 e cortes de 15/30/60 s para Ads |
| `opcoes.origem_takes` | `perguntar` | `ia`, `banco` ou `misto` |
| `opcoes.pacote_entrevista` | `perguntar` | Gráficos de entrevista (nome/cargo, números, citações) |
| `opcoes.renderizar_video` | `false` | Exporta o MP4 sozinho (senão entrega a timeline pronta) |
| `opcoes.capa_e_legenda_post` | `true` | `capa.png` e `legenda_post.txt` em `videos/` |
| `opcoes.conferencia_automatica` | `true` | Roda o `qc.py` antes de entregar |
| `opcoes.pauta_automatica.ativo` | `false` | Sugere pautas sozinha (`gratis`, `newsapi` ou `gnews`) |
| `cor.aplicar_power_grade` | `false` | Aplica o seu PowerGrade em todos os takes |
| `regras.volume_db` | narração +5, música -10 | Volumes na timeline |
| `regras.legenda.max_caracteres` | `25` | Tamanho máximo da linha da legenda |
| `regras.geracao_so_ilimitada` | `true` | Nunca gera take que gaste crédito |

## Cor e vídeos de iPhone

- `cor.drx`: PowerGrade padrão, aplicado em todos os takes.
- `cor.drx_iphone`: PowerGrade **combinado** para iPhone (conversor do iPhone primeiro, depois os nós do seu LUT). A skill detecta iPhone sozinha (metadado Apple ou HEVC HLG/Dolby Vision).
- A API não empilha dois PowerGrades no mesmo clipe, por isso o combinado: grave o still na Gallery e exporte (.dpx + .drx) para `assets/grade/`.


# CLIENTES

## Perfil, pronúncia e estilo de edição

Cada empresa tem uma pasta em `clientes/<empresa>/` (local, fora do git), criada na primeira vez a partir de `clientes/_exemplo/`:

| Arquivo | Para quê |
|---|---|
| `empresa.md` | O que faz, público, dores, tom, CTA, cores, fontes e o que **não** dizer |
| `pronuncia.json` | Grafia certa de cada termo, como escrever para a voz e erros de transcrição já vistos. A skill aprende sozinha |
| `estilo.md` | **O estilo de edição da marca**: formato, camadas, presets de lettering, legenda, motions e CTA, b-roll, música aprovada e rejeitada, export e tom. Lido **antes** de editar qualquer vídeo da empresa |

Cada empresa tem o seu estilo. Regra que você dá para uma marca vai para o `estilo.md` dela; regra geral vai para o `SKILL.md`. O estilo também fica espelhado no perfil da empresa no Desktop (`~/Desktop/<empresa>.md`).


# PASTA DO VÍDEO

```
~/Desktop/<Empresa>/
  marca/                       logos/ identidade.json identidade.md (do site oficial)
  <Assunto> - <Empresa>/
    roteiro.txt  links.txt     (de onde veio cada coisa)
    narracoes/ ou gravacao/    musica/  sfx/  brolls/  motions/  legendas/
    videos/                    <Assunto> - <Empresa>.mp4  capa.png  legenda_post.txt
```

No DaVinci o Media Pool fica em `Timelines / Footages / BRoll / SFX / Musicas / Motions / Legendas`, com subpastas `01`, `02`... quando há mais de um vídeo no projeto.


# LEGENDA

- **Uma linha**, até 25 caracteres, cortada em ponto natural da frase. **Métrica obrigatória** logo depois de gerar: `legendas.py metrica` com 0 problema antes de seguir.
- Preset de trilha **GAB USA** (Poppins Bold, caixa alta).
- Vai do **início ao fim** do vídeo, inclusive no CTA e nos motions. Nunca some.
- Posição padrão **Y 724**; só as legendas que cruzam um lettering, ou um motion na faixa de baixo, descem para **Y 390**. A API do Resolve não mexe em estilo de legenda, então o `legenda_ui.py` faz isso pela interface com OCR, numa chamada só.
- Legendas que faltam se **acrescentam sem apagar** as que já existem: SRT só com as novas, com o tempo contado a partir do fim da última legenda.


# MOTIONS

- Feitos no **HyperFrames**, com as cores, a fonte e a logo da marca, numa trilha `MOTIONS`.
- **Sempre centralizados**, medidos com `guias.py` (cutaway no centro da tela, imersivo abaixo do queixo). Nada sobre o rosto: se cobriria o rosto, vira tela cheia sobre um BG animado, que fica contínuo entre motions próximos.
- Acabamento caprichado e variado, sem repetir o mesmo layout.


# ÁUDIO E EXPORT

- Voz com Voice Isolation, música a -10 dB, SFX discretos.
- `renderizar()` exporta com a legenda gravada, **corta no último quadro de vídeo** (nada de quadro preto no fim) e **masteriza** o áudio: loudnorm em duas passagens para **-14 LUFS** com pico de **-1,5 dBTP**, vídeo copiado sem recomprimir. Para com erro se ficar fora do alvo.
- Render Cache fica desligado.


# SCRIPTS

Todos em `scripts/`, rodando com `python3`.

### legendas.py
    rascunho     transcricao.json frases.txt [--cliente pasta] [--max 25]   Uma legenda por linha, cortada em ponto natural
    sincronizar  transcricao.json frases.txt saida.srt                      Casa cada legenda com o tempo das palavras
    metrica      legenda.srt                                                Uma linha, tamanho, fim fraco, duração, sobreposição

### legenda_ui.py
    "<timeline>"                       Trilha em Y 724 e desce para 390 as legendas que cruzam a trilha LETTERING
    "<timeline>" --indices 4,5,6       Escolhe à mão quais descem (1 = primeira legenda)
    "<timeline>" --so-listar           Só mostra a lista
    "<timeline>" --conferir            Render e mede a altura do texto de cada legenda

### guias.py
    guia      [saida.png]                                   Guia 1080x1920: centros, áreas, faixa da legenda, interface do Instagram
    medir     <arquivo.mov|.png> --alvo cutaway|imersivo    Área visível do motion e distância do centro (passa com até 6 px)
    sobrepor  <arquivo> <fundo.png> <saida.png> [--t 2.0]   Prova visual: fundo + motion + guia

### cortes.py
    plano  <transcricao.json> <saida.json> [--tirar "frase"] [--pausa 0.35]   Tira retakes e encurta pausas pela transcrição

### qc.py
    <pasta_do_video> [--cliente pasta] [--plataforma instagram|meta_ads|youtube_shorts]
    Estrutura, resolução, duração, quadros pretos, loudness, legenda, grafias erradas, green screen, arquivos pesados

### transcrever.py
    <audio.wav> <saida.json> [--motor auto|davinci|whisper] [--idioma pt]   Tempo por palavra (DaVinci 21.1+ ou Whisper local)
    --versao                                                                 Versão do DaVinci e motor escolhido

### marca.py
    <site> <pasta>/marca     Logos, cores, fontes, favicon e imagem de compartilhamento do site oficial
    inverter <logo.png>      Versão oposta da logo (branca <-> preta), mantendo a transparência

### midia.py
    preparar_take  entrada saida.mp4 [1080x1920]   4K/ProRes pesado para 1080 H.264
    audio48k       entrada saida.wav               Converte para 48 kHz
    green / iphone / info  arquivo                 Green screen, detecção de iPhone, metadados

### pauta.py
    "<tema1>; <tema2>" [--fonte gratis|newsapi|gnews] [--dias 7] [--n 8]   Notícias recentes para virar roteiro

### resolve_lib.py
Biblioteca usada pela skill: projeto, timeline, narração, música, SFX, takes, legenda, lettering, enquadramento, organização do Media Pool, `renderizar()` e `masterizar()`.


# ARMADILHAS CONHECIDAS

Já tratadas pela skill:

- **Frame rate de playback** não muda por script depois que o projeto tem timeline: a skill grava ao criar.
- **Takes 4K/ProRes** travam a reprodução: convertidos para 1080 H.264 antes de importar.
- **Títulos animados** só entram pela API na trilha de destino e empurram o resto: a skill trava as outras trilhas e insere numa camada acima. Cortar título no meio derruba o Resolve; a saída é um fade no bloco. Nunca mexer na animação de entrada do template.
- **Estilo de legenda** não existe na API e o Resolve só grava **uma** trilha de legenda no burn-in: a posição por legenda é feita pela interface (`legenda_ui.py`).
- No `legenda_ui.py`, o Resolve (Qt) **ignora teclado enviado pelo Quartz**: as teclas vão pelo System Events. **Tab** no campo de posição joga o foco no botão "Add New" e o próximo Return cria uma legenda "Subtitle": nunca usar.
- `AppendToTimeline` usa a timeline **aberta** e, para SRT, cola **depois da última legenda** da trilha.
- **Trilha de legenda desligada** rejeita o SRT em silêncio.
- **Música passando do fim** gera quadro preto: o render corta no último quadro de vídeo.
- Conectores de Envato/Artlist/Magnific **não baixam** arquivos: download pelo navegador.
- Gerar no Magnific **pelo MCP cobra crédito**; o ilimitado só vale pelo site.


# ESTRUTURA DO REPOSITÓRIO

```
SKILL.md                 instruções que o Claude segue (o "cérebro" da skill)
README.md                este arquivo
install.sh               instalador de um comando
config.example.json      modelo de configuração (copie para config.json)
scripts/                 resolve_lib, legendas, legenda_ui, guias, cortes, qc, transcrever, marca, midia, pauta
navegador/downloads.md   como baixar no Envato, Artlist e Magnific pelo Chrome
docs/PROCESSO.md         referência detalhada, armadilhas e decisões
docs/PROVEDORES.md       o que conectar e quanto custa cada etapa
docs/BACKGROUNDS.md      fundos animados para os motions
clientes/_exemplo/       modelo de empresa.md, pronuncia.json e estilo.md
assets/fontes/           Poppins, Playfair Display, Lobster (OFL)
```


# LICENÇA

Código: [MIT](LICENSE). Fontes em `assets/fontes/`: SIL Open Font License. Pacotes de lettering, músicas, takes e vozes pertencem às plataformas e aos autores e seguem as licenças das suas assinaturas.

## Skills extras instaladas junto (install.sh, passo 5b)

| O quê | Para quê no Gab |
|---|---|
| `design-taste-frontend` (leonxlnx/taste-skill) | motions, cards, CTA e qualquer peça visual em HTML (HyperFrames) sem cara de template |
| `image-to-code` (leonxlnx/taste-skill) | recriar em código uma referência visual (print de site, cartão, layout) para motion |
| `web-design-guidelines` (vercel-labs/agent-skills) | conferir legibilidade, contraste e acessibilidade dos motions/peças |
| `playwright-cli` (microsoft/playwright-cli) | automação de navegador por linha de comando (capturar página do cliente, prints, rolagem para motion de site) |
| `reverse-engineer-anything` + MCP REA (morluto/rea) | entender como um app/site/efeito funciona (ex.: como um app faz uma animação ou template) para recriar no fluxo |
| `awesome-design-md` (voltagent) | `~/.claude/referencias/awesome-design-md/design-md/<marca>/DESIGN.md`: sistemas visuais de 70+ marcas como referência de estilo |
