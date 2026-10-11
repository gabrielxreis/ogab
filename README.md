# video-redes: skill do Claude para vídeos de redes sociais no DaVinci Resolve

Do **roteiro** à **timeline pronta e renderizada** no DaVinci Resolve, com IA: você aprova o roteiro, escolhe a voz, e a skill cuida de narração, música, efeitos sonoros, takes (de banco ou gerados), lettering animado, legenda com métrica certa, conferência automática e exportação.

Feita para **Claude Code** (app desktop ou terminal).

> **Cada pessoa usa as PRÓPRIAS contas.** A skill não vem com nenhuma conta, chave ou login. Quem instala conecta os seus serviços (ElevenLabs, Artlist, Envato, Magnific...) no próprio Claude e faz login nos sites no próprio navegador. Nada disso fica salvo no repositório nem no `config.json`. Você escolhe quais plataformas usar em cada etapa, e a skill segue com o que estiver disponível na sua conta.

---

## O que ela faz (o fluxo)

| # | Etapa | Você decide? | Ferramenta |
|---|---|---|---|
| 1 | Perfil do cliente (site, tom, pronúncias) + **logos e identidade visual baixadas do site** | Só na 1ª vez | `competitor-profiling` + `marca.py`, monta `clientes/<empresa>/` e `<Empresa>/marca/` |
| 2 | **Roteiro** no formato da plataforma (Instagram, YouTube, Meta Ads) | **Aprova** | Pesquisa a notícia/tema com fonte |
| 3 | **Voz** (narração por IA) | **Escolhe a voz** | ElevenLabs ou Artlist |
| 4 | Projeto no DaVinci (`Assunto - Empresa`), narração na A1 em +5 dB | - | Scripting API do Resolve |
| 5 | Música emotiva/em alta, clímax no CTA, fade out, -10 dB na A2 | Escolhe entre 3-4 | Artlist ou Envato |
| 6 | Efeitos sonoros (whoosh nas trocas, impacto no gancho) | Liga/desliga no config | Artlist ou Envato |
| 7 | Takes: **tudo IA, tudo banco ou misto** (você escolhe); geração só no modo **ilimitado** | Origem e movimentos: a skill pergunta | Envato, Artlist, Storyblocks, Pexels / Magnific |
| 7b | Cor: aplica o **seu PowerGrade** (.drx) em todos os takes (opcional) | Liga/desliga no config | DaVinci (node graph) |
| 8 | Lettering animado no gancho (pacote de títulos do Fusion) | A skill pergunta | DaVinci + seu pacote .drfx |
| 9 | Legenda: **uma linha**, pedaço natural da frase, grafia corrigida | - | Transcrição do Resolve + `legendas.py` |
| 8d | **Edição dinâmica** (HyperFrames): cortes na batida da música (só quando faz sentido; em vídeo informativo a fala manda), punch-in/zoom nos takes, transições com a cor da marca, tipografia cinética e callouts, CTA animado | Vê a tabela antes | HyperFrames + DaVinci |
| 8e | Pessoa falando: **legenda atrás da pessoa** e (se pedir) **pacote de gráficos de entrevista**; **mapas animados**; **cartão da notícia-fonte**; **mixagem** (música abaixa quando a voz entra); **remover fundo** | Pergunta o que for opcional | HyperFrames |
| 8c | **Motions** (HyperFrames) nos momentos certos da fala, no centro da tela, com as cores e a logo da marca, numa trilha MOTIONS | Vê a tabela antes | HyperFrames + DaVinci |
| 8b | **Palavras-chave** animadas (seu pacote de lettering) no momento em que são faladas; a legenda some enquanto elas aparecem | Vê a lista antes | DaVinci |
| 10 | Timeline pronta (o MP4 você exporta; render só se pedir), **capa** (`capa.png`) e **legenda do post** com hashtags (`legenda_post.txt`) em `videos/`, e **conferência automática** | - | `resolve_lib.py`, `qc.py` |

Tudo fica numa pasta na Mesa com o nome do vídeo:

```
~/Desktop/<Empresa>/
  marca/           logos/ identidade.json identidade.md  (baixados do site oficial)
  <Assunto> - <Empresa>/
    roteiro.txt      links.txt  (de onde veio cada coisa)
    narracoes/  musica/  sfx/  brolls/  videos/  legendas/
```

---

## Instalação

### Com um comando (recomendado)

Abra o **Terminal** do Mac e cole:

```bash
curl -fsSL https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/install.sh | bash
```

O instalador ([install.sh](install.sh)) faz tudo sozinho e pode ser rodado de novo para atualizar:
- instala o **Homebrew** (se faltar), **ffmpeg**, **Node.js**, **Python 3**, **git** e **Pillow**;
- baixa a skill em `~/.claude/skills/video-redes` e cria o seu `config.json`;
- instala o **HyperFrames** (motions, gráficos, edição dinâmica) e roda o `hyperframes doctor`;
- instala as fontes livres (Poppins, Playfair Display, Lobster);
- confere se o **DaVinci Resolve Studio** e o scripting estão no Mac.

Depois disso falta só o que depende de você (o instalador lembra no final): ligar o scripting no DaVinci (passo 5), conectar as suas contas (passo 8) e o Claude in Chrome (passo 9). Reinicie o Claude Code e peça um vídeo.

### Passo a passo manual

> **Skill complementar recomendada:** `competitor-profiling` (pacote `anthropic-skills`). Quando você manda o site ou material de uma empresa, a skill usa ela para varrer e salvar o máximo de informação (produtos, público, posicionamento, diferenciais, provas, tom, concorrentes) antes de começar. Instale pelo catálogo de skills do Claude (Personalização > Skills, ou peça "instala a skill competitor-profiling"). Sem ela, a skill lê o site direto.

1. **Instalar o HyperFrames junto** (motions e edição dinâmica: cortes na batida, zoom, transições, tipografia cinética):
   ```bash
   npx skills add heygen-com/hyperframes
   ```
2. **Clonar na pasta de skills do Claude:**
   ```bash
   git clone https://github.com/gabrielxreis/video-redes-skill ~/.claude/skills/video-redes
   ```
3. **Criar sua configuração** (fica só na sua máquina, não vai para o GitHub):
   ```bash
   cp ~/.claude/skills/video-redes/config.example.json ~/.claude/skills/video-redes/config.json
   ```
4. **Requisitos da máquina:** macOS, **DaVinci Resolve Studio** (a versão grátis não tem scripting externo), Python 3 com Pillow (`pip3 install pillow`), ffmpeg (`brew install ffmpeg`).
5. **No DaVinci:** Preferences > System > General > **External scripting using: Local**.
6. **Fontes:** instale as de `assets/fontes/` (duplo clique em cada .ttf, ou copie para `~/Library/Fonts/`). São fontes livres (licença OFL). O preset de legenda padrão usa **Poppins Bold**.
7. **Lettering animado (opcional):** a skill foi feita com o pacote **@gabrielxreis_ Text Presets** (29 animações: Cinematic, Palavra Por Palavra, Gold Design, Blur Up...). Ele **não** vem neste repositório. Use o seu próprio pacote de títulos do Fusion (`.drfx`): copie para
   `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/` e **reinicie o Resolve**. Coloque o nome do pacote e dos templates em `config.json > lettering` (o nome do template é o nome do arquivo `.setting` dentro do pacote).
8. **Conectar as SUAS contas** (veja [docs/PROVEDORES.md](docs/PROVEDORES.md)): ElevenLabs, Artlist, Envato, Magnific, etc. Conecte só o que você usa.
9. **Claude in Chrome:** instale a extensão e faça login nos sites (Envato, Artlist, Magnific). Downloads são sempre pelo navegador; a IA nunca digita senha.

## Como usar

No Claude Code, peça em linguagem normal ou use o comando:

| Comando | O que faz |
|---|---|
| `faz um vídeo para a <empresa> sobre <tema>` | Fluxo completo |
| `/video-redes ajuda` | Mostra o que está habilitado, os provedores escolhidos e como mudar (o `/help` puro é do próprio Claude Code) |
| `/video-redes config <chave> <valor>` | Liga/desliga opções. Ex.: `config opcoes.multi_formatos true` |
| `/video-redes cliente <nome>` | Cria/atualiza o perfil do cliente (site, logo, pronúncias) |
| `/video-redes pauta <cliente>` | Busca notícias recentes dos temas do cliente e sugere roteiros |
| `/video-redes update` | Atualiza a skill (`git pull`), sem mexer no seu config nem nos clientes |

## Opções que você liga e desliga (`config.json`)

| Opção | Padrão | O que faz |
|---|---|---|
| `opcoes.efeitos_sonoros` | `true` | Whoosh nas trocas, impacto no gancho, pop no CTA |
| `opcoes.movimentos_nos_takes` | `perguntar` | Zoom/movimento leve nos takes (`sempre`, `nunca`, `perguntar`) |
| `opcoes.lettering_no_gancho` | `perguntar` | Título animado no começo |
| `opcoes.multi_formatos` | `false` | Renderiza também 4:5, 16:9 e versões 15/30/60 s para Ads |
| `opcoes.origem_takes` | `perguntar` | Takes `ia` (tudo gerado, só ilimitado), `banco` (Envato etc.) ou `misto` |
| `opcoes.legenda_atras_da_pessoa` | `true` | Com pessoa falando, legenda cinematográfica atrás dela (HyperFrames) |
| `opcoes.pacote_entrevista` | `perguntar` | Gráficos de entrevista (nome/cargo, números, citações) |
| `cor.aplicar_power_grade` | `false` | Aplica o seu PowerGrade (`cor.drx`, em `assets/grade/`) em todos os takes |
| `opcoes.conferencia_automatica` | `true` | Roda o `qc.py` antes de entregar |
| `opcoes.pauta_automatica.ativo` | `false` | Sugere pautas sozinha (fonte `gratis`, `newsapi` ou `gnews`) |
| `regras.volume_db` | narração +5, música -10 | Volumes na timeline |
| `regras.legenda.max_caracteres` | 25 | Tamanho máximo da linha da legenda (uma linha só) |
| `regras.geracao_so_ilimitada` | `true` | Nunca gera take que gaste crédito |

## Cor e vídeos de iPhone

- `cor.drx`: seu PowerGrade padrão, aplicado em todos os takes.
- `cor.drx_iphone`: PowerGrade **combinado** para vídeo de iPhone (nó conversor do iPhone **primeiro**, depois os nós do seu LUT). A skill detecta iPhone sozinha (metadado Apple ou HEVC HLG/Dolby Vision) e aplica esse no lugar do padrão.
- Por que combinado: pela API do DaVinci não dá para empilhar dois PowerGrades no mesmo clipe, e os estágios de grupo (pre/post-clip) não aceitam .drx. Então crie uma vez: num clipe de iPhone, aplique o conversor, adicione depois os nós do seu LUT, grave o still na Gallery e exporte (gera .dpx + .drx) para `assets/grade/`.

## Conferência automática (`scripts/qc.py`)

Antes de entregar, confere e lista **OK / AVISO / ERRO**:
estrutura da pasta, resolução e duração pela regra da plataforma, **quadros pretos** entre takes, **loudness** (alvo -14 LUFS), legenda em uma linha e no tamanho certo, **grafias erradas** do cliente (ex.: nome da marca transcrito errado), takes com **green screen** e arquivos pesados que travam o playback. Gera uma folha de contato com 6 quadros.

## Pronúncia por cliente (aprende sozinha)

`clientes/<empresa>/pronuncia.json` guarda, para cada termo, a **grafia** da legenda, como **escrever para a voz** pronunciar certo e os **erros de transcrição** já vistos. Quando a transcrição mostra um erro novo (ex.: a transcrição ouviu o nome da marca errado), a skill adiciona no arquivo, corrige a legenda e, se for erro da voz, regera só o trecho (com sua aprovação).

## Estrutura do repositório

```
SKILL.md                 instruções que o Claude segue (o "cérebro" da skill)
config.example.json      modelo de configuração (copie para config.json)
scripts/resolve_lib.py   monta projeto, timeline, narração, música, sfx, takes, legenda, lettering, render
scripts/legendas.py      rascunho de legenda por frase + sincronização com a narração
scripts/midia.py         converte takes pesados, áudio 48 kHz, detecta green screen
scripts/qc.py            conferência automática
scripts/marca.py         logos, cores e fontes do site oficial da empresa
scripts/pauta.py         pauta automática (Google News grátis, NewsAPI, GNews)
navegador/downloads.md   como baixar no Envato, Artlist e Magnific pelo Chrome
docs/PROCESSO.md         referência detalhada, armadilhas e decisões
docs/PROVEDORES.md       o que conectar e quanto custa cada etapa
clientes/_exemplo/       modelo de perfil de cliente e pronúncias
assets/fontes/           Poppins, Playfair Display, Lobster (OFL)
```

## Armadilhas conhecidas (já tratadas pela skill)

- O DaVinci não muda o **frame rate de playback** por script depois que o projeto tem timeline: a skill grava ao criar o projeto (senão o áudio engasga). Se um projeto já existente estiver com playback diferente da timeline, corrige em Project Settings > Master Settings > Playback frame rate e liga Playback > Render Cache > Smart.
- Takes **4K/ProRes** travam a reprodução: convertidos para 1080 H.264 antes de importar.
- A API só insere títulos animados na **V1** (empurrando o que estiver lá): a skill monta os letterings numa camada acima dos takes criando trilha na posição 1, sem compound. Cortar um título animado no meio derruba o Resolve, então a duração visível vem de um fade out. Nunca mudar a velocidade das animações (quebra o template).
- A API não faz **fade** de áudio nem aplica **estilo de legenda**: o fade é feito no arquivo (ffmpeg) e o estilo fica na trilha de legenda (preset).
- Fontes 24/25 fps numa timeline 30 fps deixam **1-2 quadros pretos**: os takes são encadeados pelo fim real.
- Os conectores de Envato/Artlist/Magnific **não baixam** arquivos: download pelo navegador.
- Gerar no Magnific **pelo MCP cobra crédito**; o ilimitado só vale pelo site.

## Licença

Código: MIT. Fontes em `assets/fontes/`: SIL Open Font License (ver os OFL.txt). Pacotes de lettering, músicas, takes e vozes pertencem às plataformas/autores e seguem as licenças das suas assinaturas.
