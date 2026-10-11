---
name: video-redes
description: Produz vídeos para redes sociais (Instagram Reels, YouTube Shorts/longo, Meta Ads) do roteiro até a timeline pronta e renderizada no DaVinci Resolve - roteiro para aprovação, voz por IA, música, efeitos sonoros, takes de banco ou gerados, lettering animado, legenda com métrica e conferência automática. Use quando o usuário pedir para criar/fazer um vídeo, reels, anúncio, pauta ou roteiro para uma empresa/cliente, ou digitar /video-redes (subcomandos ajuda, config, update, pauta, cliente).
---

# video-redes

Pipeline de vídeo para redes sociais com IA + DaVinci Resolve. Duas paradas obrigatórias para o usuário decidir: **aprovar o roteiro** e **escolher a voz**. Nada que gaste crédito roda antes delas.

Pasta da skill: `~/.claude/skills/video-redes/` (chamada de `SKILL_DIR` abaixo). Scripts em `SKILL_DIR/scripts/`. Detalhes técnicos em `SKILL_DIR/docs/PROCESSO.md` (ler a seção da etapa só quando chegar nela, para economizar tokens).

## 0. Subcomandos (`/video-redes <sub>`)

- `ajuda` ou `help` (o `/help` puro é do Claude Code e não pode ser trocado): mostrar em tabela o que está **habilitado/desabilitado** em `SKILL_DIR/config.json` (se não existir, copiar de `config.example.json`), os provedores escolhidos por etapa e os comandos. Oferecer mudar qualquer item; ao mudar, editar `config.json` e confirmar.
- `config <chave> <valor>`: muda direto (ex.: `config opcoes.multi_formatos true`, `config provedores.musica ["envato"]`).
- `update`: `git -C SKILL_DIR pull --ff-only` e mostrar o que mudou (`git log -5 --oneline`). Nunca sobrescrever `config.json` nem `clientes/`.
- `cliente <nome>`: criar/atualizar o perfil do cliente (etapa 1).
- `pauta [cliente]`: rodar a pauta automática (etapa 2b) e sugerir roteiros.
- sem subcomando ou pedido livre ("faz um vídeo para X"): rodar o fluxo completo.

## Regras fixas (sempre)

0. **Contas são de quem usa a skill.** Usar SÓ os conectores e logins da pessoa que está rodando o Claude. Nunca pedir, guardar nem usar senha, token ou chave de outra pessoa; nunca colocar credenciais no `config.json` nem no repositório. Se um provedor não estiver conectado, pedir para a própria pessoa conectar a conta dela.

1. **Pastas: empresa > vídeo.** `<pasta_saida>/<Empresa>/` (padrão `~/Desktop`) guarda `marca/` (logos e identidade visual tiradas do site oficial) e um vídeo por subpasta: `<pasta_saida>/<Empresa>/<Assunto> - <Empresa>/`, com `roteiro.txt`, `links.txt` (origem de tudo: notícia, voz, música, cada take, cada efeito), `narracoes/`, `musica/`, `sfx/`, `brolls/`, `videos/`, `legendas/`. **Projeto do DaVinci com o mesmo nome** `<Assunto> - <Empresa>`.
2. **Tudo via MCP/API, só download pelo navegador** (Claude in Chrome logado nas contas do usuário). Ver `navegador/downloads.md`.
3. **Economizar créditos e tokens**: 1 geração por vez, sem variações extras; estimar custo antes (ElevenLabs `estimate_only`); gerar takes **só em modo ilimitado** (Magnific pelo site); buscas com `perPage` pequeno; no navegador, JS enxuto e zoom pequeno em vez de screenshot grande; não reler arquivos grandes.
4. **Provedores**: usar os da lista de `config.json` na ordem, **pulando o que não estiver conectado** (conferir com a ferramenta de status de conectores / ToolSearch). Se nenhum provedor de uma etapa estiver disponível, avisar e oferecer alternativa (ex.: o usuário baixa à mão e coloca na pasta).
5. **Sem green screen** nem elemento isolado/canal alfa nos takes. Conferir a miniatura antes de baixar.
6. **Pessoas reais**: nunca gerar rosto realista de pessoa real em cena inventada; usar símbolo, pessoa de costas, foto real fornecida pelo usuário ou ilustração. Voz clonada só se for do próprio usuário/cliente ou autorizada.
7. **Movimentos nos takes e lettering no gancho: perguntar** antes (a não ser que `config` diga `sempre`/`nunca`).
8. Sem travessão (em dash) nos textos para o usuário e nas legendas.

## 1. Cliente (primeira vez por empresa)

Se não existir `SKILL_DIR/clientes/<empresa>/empresa.md`: pedir **site** + **logo** (PNG transparente, claro e escuro) + cores/fontes + redes. Assim que o usuário mandar o site (ou qualquer material da empresa), **varrer tudo antes de começar**: usar a skill **`competitor-profiling`** (`anthropic-skills:competitor-profiling`) apontada para a PRÓPRIA empresa (o que faz, produtos, preços, público, posicionamento, diferenciais, provas sociais, tom, redes, concorrentes), complementar lendo as páginas do site, e só então criar, copiando de `clientes/_exemplo/`. Se a skill não estiver instalada, avisar e oferecer instalar (ver README), ou seguir lendo o site direto:
- `empresa.md`: o que faz, público, dores, diferenciais, tom de voz, CTA, cores, o que **não** dizer (regras do setor).
- `pronuncia.json`: termos da marca/setor com `grafia` correta, `fala` (como escrever para a voz pronunciar certo) e `erros_transcricao` conhecidos.
- **Marca (automático, junto com a varredura):** `python3 SKILL_DIR/scripts/marca.py <site oficial> <pasta_saida>/<Empresa>/marca` baixa do site as logos (img/svg do cabeçalho, favicon, apple-touch-icon, imagem de compartilhamento), as cores mais usadas e as fontes, e grava `identidade.json` + `identidade.md`. Depois **olhar as logos** (abrir as imagens), apagar o que não for logo e marcar no `identidade.md` a principal, a versão clara (para fundo escuro) e a escura. Se o site carrega o estilo por JavaScript e as fontes não aparecem, abrir o site no navegador e ler `getComputedStyle` de `h1`, `p` e botão (ver `navegador/downloads.md`). Só pedir ao usuário o que faltar (ex.: logo em PNG transparente se o site só tiver JPG). Copiar cores/fontes/caminho da logo para o `empresa.md`.
Nos próximos vídeos, ler o perfil em vez de perguntar de novo (só confirmar se mudou algo).

## 2. Roteiro (PARAR para aprovação)

1. Perguntar a **plataforma** (Instagram, YouTube Shorts/longo, Meta Ads) e, se Meta Ads, a duração (15, 30 ou 60 s). Durações em `config.regras.duracao_segundos`; ~150 palavras/min.
2. Pesquisar o assunto (notícia recente com fonte e data) e escrever: gancho nos 3 primeiros segundos, frases curtas, sugestão visual por bloco, CTA do cliente. Respeitar o "não dizer" do cliente.
3. Mostrar e **esperar o "aprovado"**. Salvar como `roteiro.txt`.

### 2b. Pauta automática (se `opcoes.pauta_automatica.ativo` ou `/video-redes pauta`)
`python3 SKILL_DIR/scripts/pauta.py "<temas do cliente>" --fonte <gratis|newsapi|gnews>` e sugerir 2-3 pautas com roteiro curto. Pode ser agendada (tarefa recorrente) se o usuário pedir.

## 3. Voz (PARAR para o usuário escolher)

Listar 3-5 vozes no idioma (ElevenLabs `creative_list_voices`; incluir vozes do próprio usuário) com link de prévia. Depois da escolha: trocar no texto os termos de `pronuncia.json` pela forma `fala` (ex.: "EB-2" -> "ê-bê dois"), `estimate_only` -> informar custo -> gerar **1** take. Baixar para `narracoes/narracao.wav` (48 kHz). Transcrever (Resolve `TranscribeAudio` ou `creative_transcribe_audio`): se a transcrição mostrar erro de pronúncia de um termo, **atualizar `pronuncia.json` do cliente** (novo `erros_transcricao` e ajuste em `fala`) e regerar só o trecho, com aprovação.

## 4. DaVinci: projeto e narração

`scripts/resolve_lib.py`: `criar_projeto(nome, w, h, fps)` (grava fps de timeline **e playback** antes de qualquer timeline). **Logo ao criar a timeline, antes de importar qualquer coisa:** `criar_timeline` confere playback = timeline; se avisar, corrigir na hora pela interface (File > Project Settings > Master Settings > Playback frame rate > Save) e ligar **Playback > Render Cache > Smart** pelo menu (via `app_menu`). Não deixar para quando o áudio picotar. Depois dos letterings, rodar `checar_fades(t)` (todos com fade out limpo). Se o áudio picotar, `checar_playback(p)` e, se divergir, corrigir em Project Settings > Master Settings pela interface + Render Cache Smart, ver docs/PROCESSO.md), `criar_timeline`, `colocar_narracao(db=+5)`. Formato pela plataforma (9:16 1080x1920; 4:5 1080x1350; 16:9 1920x1080).

## 5. Música

Clima padrão: **emotiva, que faz sonhar**, instrumental, priorizando as mais baixadas/em alta (Artlist `sortBy: TOP_DOWNLOADS`, Envato `sortBy: popular`). Mostrar 3-4 opções com prévia; o usuário escolhe. Baixar WAV pelo navegador. `preparar_musica` posiciona o trecho para o **clímax cair no CTA** (usar `hookStartSeconds` do Artlist), com **fade out** e 48 kHz; `colocar_musica(db=-10)` na A2.

## 6. Efeitos sonoros (se `opcoes.efeitos_sonoros`)

Buscar no Artlist (`search_sfx`) ou Envato (`search_sound_effects`): whoosh/swoosh suave nas trocas de take principais, um impacto/riser no gancho, um "ding"/pop no CTA. Poucos e baixos (`colocar_sfx`, -6 dB na A3). Registrar em `links.txt`.

## 7. Takes

1. Dividir a narração em blocos de 2-5 s pelos tempos da transcrição.
2. Primeiro **banco** (`provedores.takes_banco`, ex.: Envato `search_stock_video` com `orientation` certa). Baixar 1080P pelo navegador -> `brolls/take_XX`.
3. Se não achar, **gerar** (`provedores.geracao_takes`), **só ilimitado**: Magnific pelo site (Nano Banana 2 1K + Kling 2.5 720p 5 s). Se só sair pago, avisar e propor alternativa.
4. `midia.py preparar_take` para 4K/ProRes; `midia.py green` para garantir que não é chroma.
5. `montar_takes` (sem buracos: encadeia pelo fim real e usa ceil).
6. Se o usuário quis **movimentos**: `movimento()` (zoom leve) ou indicar onde animar.

## 7b. Cor (se `config.cor.aplicar_power_grade`)

Depois de montar os takes (e sempre que trocar um take), `aplicar_grade(r, t, config.cor.drx, config.cor.drx_iphone)` em todos os takes da V1. **Take de iPhone** (`midia.py iphone`): recebe o PowerGrade combinado (conversor do iPhone antes, LUT depois), automático. Conferir 2-3 quadros: se algum take de banco estourar (contraste/saturação exagerados), avisar o usuário. Lettering e legenda não recebem grade.

## 8. Lettering e palavras-chave (gancho: perguntar; palavras-chave: se `opcoes.palavras_chave_lettering`)

Pacote de títulos animados instalado (`config.lettering.pacote`, ex. `@gabrielxreis_ Text Presets.drfx` em `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/`; reiniciar o Resolve após instalar).

**Regras do usuário para os letterings:**
- Ficam numa **camada logo acima dos takes** (V2, V3...), **sem compound/timeline aninhada**.
- **Shading Element = Solid** (o template vem com gradiente; `ajustar_titulo` troca `Type1` para 0) e cor sólida.
- Com quebra de linha (`\n`), **entrelinha mais junta** (`LineSpacing` 0.8).
- Tamanho que cabe na largura do vertical (`tamanho_lettering`).
- **Durante uma palavra-chave a legenda some** (`legendas.py` > `sem_legenda`).
- **Variar as animações** para não ficar tudo igual: a favorita é **Palavra Por Palavra** (e Palavra Por Palavra 2), usar em cerca de metade dos letterings e alternar com outras do pacote (`config.lettering.favoritos` / `rodizio`); não repetir a mesma em seguida. Com 2 linhas, evitar `config.lettering.evitar_2_linhas` (Sublinhado cobre a 2ª linha; Moderno e Corte embaralham). Passar o template por item: `(TEXTO, inicio_s, dur_s, template)`.
- **Fade out em tudo**: `ajustar_titulo` põe um nó `FadeSaida` (ColorGain em R, G, B e alfa) antes do MediaOut, então some texto, sombra, caixa e linha juntos em qualquer animação.

Como fazer: escolher 4-6 palavras-chave do roteiro (números, datas, siglas, a marca no CTA), mostrar a lista (texto + tempo) ao usuário e aplicar com `ocup = camada_letterings(t, mp, [(TEXTO, inicio_s, dur_s), ...], template)` **antes** de `montar_takes` (ou depois: a função guarda e recoloca os takes), depois `aplicar_grade` de novo. Por trás: a API só insere Fusion Title na V1 e com ripple; a função trava áudio/legenda/outras trilhas, insere na V1 vazia, cria trilha na posição 1 (`AddTrack("video", {"index": 1})`) para a camada subir, e reparte em mais camadas quando dois títulos ficariam sobrepostos. **Nunca cortar um Fusion Title no meio (derruba o Resolve)**: a duração visível vem do fade out (`FadeSaida`). A função confere que as trilhas travaram e que áudio/legenda não andaram (senão para com erro); ao recolocar os takes converte quadros da timeline para quadros da fonte (take 24/25 fps). Se o último lettering passar do fim do vídeo, estender o último take e a música (com fade) até ele, para não sobrar preto.

## 9. Legenda

Regras: **uma linha só (nunca quebrar)**, pedaço natural da frase, até `config.regras.legenda.max_caracteres` (25 no 9:16), nunca terminar em palavra fraca, número junto da unidade, **sem misturar idiomas**, grafia do cliente corrigida.
1. `legendas.py rascunho transcricao.json legendas/frases.txt --cliente clientes/<empresa>` -> revisar o frases.txt (ajustar cortes estranhos à mão).
2. `legendas.py sincronizar transcricao.json legendas/frases.txt legendas/legendas_vN.srt` (nome único por versão).
3. `colocar_legendas` (troca só os itens: o **preset de estilo fica na trilha**; projeto novo: aplicar o preset do usuário na trilha pelo Inspector, ver `config.regras.legenda.preset_trilha`).

## 10. Render, formatos e conferência

1. **Não exportar o vídeo** (`opcoes.renderizar_video` = false, padrão): deixar a timeline pronta no DaVinci para o usuário exportar. Só renderizar se o usuário pedir: `renderizar(p, <pasta>/videos, "<Assunto> - <Empresa>")`.
1b. **Capa e legenda do post** (se `opcoes.capa_e_legenda_post`), em `<pasta>/videos/`: `gerar_capa(r, p, mp, <melhor take>, "GANCHO\nEM 2-3\nLINHAS", template, <pasta>/videos, seg_quadro=3.3, drx=<grade>)` gera `capa.png` (1080x1920, lettering do gancho sobre um quadro bonito do vídeo, com a cor aplicada). Escrever `legenda_post.txt`: gancho na 1ª linha, 2-4 parágrafos curtos com o conteúdo, CTA do cliente, fonte da notícia com data, 8-15 hashtags (mistura de amplas e de nicho, + a do cliente). Sem travessão.
2. Se `opcoes.multi_formatos`: criar timelines extras nos formatos de `formatos_extras` (e cortes 15/30/60 s para Ads) e renderizar cada uma com sufixo (`- 4x5`, `- 30s`).
3. **Conferência automática** (se habilitada; sem render, o qc confere legenda, takes e estrutura, e pula as checagens do MP4): `python3 SKILL_DIR/scripts/qc.py <pasta> --cliente clientes/<empresa> --plataforma <p>`. Corrigir todo **ERRO** e reconferir. Olhar a `qc_folha.jpg`.
4. Salvar o projeto e entregar: link do vídeo, resumo (voz, música, takes banco x gerados, créditos gastos) e o que falta (ex.: logo).
