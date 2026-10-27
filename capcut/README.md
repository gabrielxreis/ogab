# Gab (/ogab) no CapCut (Mac e Windows)

> **CapCut é SEMPRE pelos arquivos, nunca pela tela (regra do usuário 24/10/2026, vale no Mac e no Windows):** ler, editar, salvar, conferir e guardar presets só pelo `capcut/capcut.py` / `capcut_lib` (rascunho JSON, pasta `Presets`, `presets salvar|aplicar|backup`). Não abrir o CapCut, não tirar screenshot, não usar computer-use para "ver como está": o `retrato`, o `ids`, o `conferir` e a `previa` respondem isso. Tela só em ÚLTIMO caso, depois de tentar pelo arquivo e dizer ao usuário o que falhou e por quê (ex.: abrir o projeto = clique na miniatura; exportar pelo app). No Windows não existe computer-use: o clique é pedido ao usuário.

Camada à parte, igual a `premiere/`: o método do `SKILL.md` não muda. Quando o usuário pedir CapCut (ou `"editor": "capcut"` no config), usar `capcut/capcut_lib.py` onde o `SKILL.md` manda usar `resolve_lib.py`.

> **22/10/2026:** linha de comando (`capcut.py`), prévia renderizada sem o app e fábrica de cortes; rascunho gravado pela lib aberto e regravado pelo CapCut 9.4 (versão 181 -> 185) sem perder nada.
>
> **Status: beta, aberto no CapCut em 15/10/2026:** `NBA - TIMELINE` (36 itens vindos do DaVinci) carregou com toda a mídia, áudio com forma de onda, legendas e tempos certos. Ainda não conferidos no app: transição, animações, efeitos, filtros, adesivos, voz e modelos de texto (`GAB TESTE API 2` e `3`).
>
> **Antes:** Rascunhos de teste gerados em 14/10/2026 (`GAB TESTE API` e `GAB TESTE API 2`, este com transição, animações, efeito, máscara, fundo e corte de silêncio); falta conferir dentro do CapCut que tudo abre certo. Até essa conferência, avisar o usuário que é beta.

## Sem editor (`"editor": "nenhum"`, 23/10/2026)

Para quem não tem nenhum editor: o mesmo motor, sem o app. Com `"editor": "nenhum"` no config, a `capcut_lib` grava os rascunhos em `~/Movies/Gab Sem Editor/Rascunhos` (a variável `GAB_RASCUNHOS` força outra pasta) e não confere se o CapCut está aberto. Monta com `capcut.py plano`, entrega com `capcut.py previa "<rascunho>" saida.mp4` (escala 1 = final). Testado 23/10/2026: vídeo com fundo desfocado + MOV com alfa (motion) + texto saiu certo. Fora do render: transição, filtro, efeito, adesivo e animação da loja (usar corte seco, keyframe e motion do HyperFrames). Funciona sem o CapCut instalado (no Windows a pasta é `~/Videos/Gab Sem Editor/Rascunhos`).
Instalou o CapCut depois: `capcut.py levar "<rascunho|*>"` copia para a pasta do CapCut, troca os caminhos e registra na tela inicial; depois `/ogab config editor capcut`. Com a tela inicial do CapCut vazia (nenhum projeto), a entrada é mínima: conferir que aparece.

## Linha de comando (`capcut.py`, 22/10/2026): o jeito padrão de mexer no CapCut

Igual ao DaVinci: tudo por comando, sem clicar. O CapCut só precisa estar com ESTE projeto fechado na hora de gravar.

| Comando | O que faz |
|---|---|
| `python3 capcut/capcut.py rascunhos` | lista os rascunhos |
| `capcut.py retrato "<rascunho>" [--json f]` | trilhas e segmentos (regra 1g) |
| `capcut.py plano plano.json` | monta ou edita um rascunho a partir de um plano JSON: cada op é um método da lib (`video`, `audio`, `texto`, `fundo`, `animar`, `transicao`, `keyframes`...), `"id"` guarda o segmento e `"$id"` usa depois. Formato no topo do `capcut.py` |
| `capcut.py cortes cortes.json <video> --transcricao t.json [--correcoes c.json] [--credito "..."]` | fábrica de cortes no CapCut: um rascunho 9x16 por corte (trechos do `fabrica_cortes.py conferir`, vídeo inteiro com fundo desfocado, gancho no topo, legenda palavra a palavra embaixo) |
| `capcut.py previa "<rascunho>" saida.mp4 [--ate s] [--escala .5]` | **renderiza o rascunho sem o CapCut** (ffmpeg + Pillow): vídeo, foto, fundo desfocado/cor, escala, posição, opacidade, velocidade, textos (fonte, cor, contorno, quebra), áudio com volume e fade. Transição, efeito, filtro, adesivo e animação da loja ficam de fora (avisa). Texto calibrado no motor do CapCut |
| `capcut.py conferir "<rascunho>"` | mídia offline ou fora de `~/Movies`, efeito da loja ainda sem arquivo, buraco na V1 |
| `capcut.py abrir "<rascunho>"` | põe o rascunho em 1o na tela inicial (ela relê a lista sozinha, sem reiniciar) e abre o CapCut |
| `capcut.py fechar` | fecha o CapCut |

**Abrir e exportar dentro do app (testado 22/10/2026):** abrir = clique na 1a miniatura (o Gab faz com o computer-use em segundo plano, `app_click`; o projeto abre numa janela nova). Exportar = menu Arquivo > Exportar (dá para chamar em segundo plano com `app_menu`), mas o diálogo (folha com `ExportOkBtn`, `automationcancel`, resolução padrão 4K, pasta padrão Área de Trabalho) só aceita clique/tecla com o CapCut NA FRENTE: em segundo plano não exporta. Por script (AppleScript/System Events) funciona se o usuário der permissão de Acessibilidade ao Terminal/Claude (ajuste de segurança do macOS, só ele liga). Por isso a entrega padrão é o `previa` (MP4 do Gab) e o CapCut fica para o ajuste fino e a exportação manual. Com o diálogo aberto o "Sair" do CapCut é cancelado: `pkill -TERM -x CapCut` fecha limpo.

**Comandos rápidos (22/10/2026):** `capcut.py faz "<rascunho|CORTE*|A,B>" <ação> [@seletor] [args] [chave=valor] [+ outra ação]` roda qualquer ação da lib em 1 ou vários rascunhos e salva uma vez (16 ações em 0,5 s). Seletores no lugar do id: `@v0:2` (vídeo 0, 3o clipe), `@v0:todos`, `@t1:2-5`, `@em=12.5` (clipe da V1 nesse segundo), `@texto=Lula`. `capcut.py ids` mostra o seletor de cada clipe; `capcut.py ops` lista as ações; `catalogo` e `loja` acham os nomes. Novas na lib: `estilo_texto` (tamanho, cor, contorno, fonte, posição de um texto já na timeline) e `trocar_texto`.

**Legenda animada palavra por palavra (resolvido 22/10/2026, dissecando uma legenda automática real):** o texto precisa de `words` = tempo de cada palavra em ms relativo ao início do texto, com o espaço entre palavras como item de duração zero (`d.palavras(sid, [(ini_s, fim_s, "palavra"), ...])`; sem lista divide por igual). A animação de legenda vai com `id` e `name` vazios (`d.animar(sid, legenda=<nome ou id>)` já faz). Marcar como legenda (`add_type 1`, `check_flag 47`, `recognize_task_id`, `recognize_text`, trilha `flag 1`) NÃO é obrigatório para animar, mas é para **modelo de legenda** da loja: sem isso o modelo carrega com o texto de exemplo dele ("La veloce volpe marrone"). Conferido no app: id `7343518591062381057` (usado no rascunho 0629) anima.
**Itens de teste da loja:** o cache traz itens internos (`publish_source` "lumi_test", 88 animações de legenda) que o app mostra no painel mas não baixa ("Perda da animação"). `atualizar_loja()` agora descarta. Alguns itens novos válidos também falham (ex.: "Amor feliz", `7646094275096300820`), por isso o validador.
**Validador (`capcut.py validar`):** `validar criar <grupo> --n 60` monta um rascunho com N itens da loja (1 s cada); abrir uma vez no app, fechar, `validar ler` varre TODOS os rascunhos que o app já regravou (new_version > 181) e grava `validados.json` (com arquivo baixado = funciona). Pendente: rodar o lote "GAB VALIDA legenda" (60 animações) no app.
**Palavra-chave colorida:** `d.texto(..., destaques={"LULA": "#FFE600"})` ou `d.destacar(sid, {...})` = vários estilos no mesmo texto (conferido no app). Também conferidos no app: keyframes de opacidade e escala, velocidade 1,5x, fade de áudio.

**Recursos conferidos dentro do CapCut (22/10/2026, rascunho "GAB TESTE RECURSOS", abriu no 9.5.0):** funcionam (o app baixou o arquivo e ligou): transição (`Black Fade`), filtro (`Azul da ilha`), efeito de tela (`70's`), adesivo (`emoji_u0031`), máscara (`Heart`), entrada de vídeo (`Fade In`), entrada e loop de texto (`Blur`, `Blocks`), efeito de voz (`Alto`), fundo desfocado. `Agitação` falhava por ser item de teste (ver acima), não pelo formato. Modelo de texto da loja ainda não testado.

**Edição de clipe e texto (confirmados no app 9.5, 22/10/2026):** `recortar(@alvo, esquerda, cima, direita, baixo)` (fração 0-1 de cada lado), `espelhar(@alvo, horizontal, vertical)`, `estilo_texto`/`texto` com `fundo='#000000'` (caixa; `fundo_raio=1` = pílula; `fundo_alfa`) e `sombra='#000000'` (`sombra_distancia`, `sombra_angulo`, `sombra_suave`). O `check_flag` do texto é um mapa de bits (7 base, +8 contorno, +16 fundo, +32 sombra) recalculado pelo `_flag_texto`; sem o bit o app ignora o recurso. A `previa` desenha fundo e sombra (bate com o app).

**Exportar sem abrir o CapCut (investigado e descartado, 22/10/2026):** só daria chamando o motor interno do app fora dele, o que contorna os controles de exportação do CapCut e quebra a cada versão. Não seguir. A entrega é a `previa` (render próprio) e a exportação dentro do CapCut é manual.

**Texto: medida do motor (22/10/2026):** o CapCut fixa a ALTURA DE LINHA da fonte (hhea ascent - descent) em `tamanho x 6,35 px` num quadro de 1080 de largura; o corpo da letra sai dessa altura dividida pela métrica da fonte (Anton 1,505, Montserrat 1,219). Por isso o mesmo `tamanho` dá letras de alturas diferentes em fontes diferentes. Legenda legível no 9x16: 10-11; gancho: 16-18.

## Como o Gab fala com o CapCut (engenharia reversa, CapCut 9.4.0, 14/10 e 22/10/2026)

- **Nada abre um rascunho direto (22/10/2026):** o lançador (`Contents/MacOS/CapCut`, 446 KB) lê `--draft_path=`, `--draft_type=`, `--draft_from=` e as variáveis `LAUNCH_TOOL`, `DRAFT_PATH`, `DRAFT_TYPE` (modo "tool_app" do Jianying); testados com `open -a CapCut --args --draft_path=...` e com as variáveis: o 9.4 internacional cai na tela inicial nos dois. O `libVECreator` tem `lvop::PluginStandaloneInstance::restoreDraft` (modo plugin, outro produto) e os deep links só de painel (`capcut://com.ies.videocut/uganchor/anchor_point/<função>`). O QML do app está embutido como texto no `libVECreator.dylib` (`strings` mostra telas e nomes de botão).
- **Nomes de automação:** botões do Qt têm nome de acessibilidade (`MainWindowTitleBarExportBtn`, `ExportOkBtn`, `automationcancel`, `automationrecycleBinBtnSmall`, `HomePageDraft`); as miniaturas de projeto não aparecem na árvore de acessibilidade.
- **Não existe API de script nem porta local.** O app é Qt + motor ByteDance (`libVECreator`, `libvideoeditor`). O agente de IA interno (`libDeepAgentsService`, em Go) fala com a nuvem, não abre porta. O `capcut://` só abre painéis de IA (`.../anchor_point/ai_rough_cut`, `caption_auto_subtitles`...), não rascunhos.
- **O rascunho é JSON puro, sem criptografia** (no Mac; o Jianying chinês criptografa): `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<nome>/draft_info.json`. A lib lê e escreve esse arquivo.
- **Sandbox:** o CapCut só lê sem pedir o que está em `~/Movies` (entitlement `assets.movies.read-write`). A lib copia (hardlink quando dá) toda mídia de fora para `~/Movies/Gab CapCut/<rascunho>/`. Mídia fora dali aparece offline.
- **6 cópias do mesmo JSON** no 9.4: `draft_info.json`, `.bak`, `template-2.tmp` na raiz e em `Timelines/<id>/`. A lib grava em todas e zera o `attachment/patch/patch.json` (senão o CapCut reaplica edições antigas por cima).
- **Fluxo obrigatório:** o PROJETO fechado (o CapCut pode ficar na tela inicial ou em outro projeto) → `salvar(projeto_fechado=True)` → clicar no projeto. Com o projeto aberto, o CapCut sobrescreve tudo; por isso `salvar()` recusa com o app aberto até o Gab confirmar com o usuário que o projeto está fechado.
- **Proteção da edição manual:** `abrir()` guarda a impressão digital (sha256) do JSON; se ele mudar até o `salvar()` (o usuário mexeu no CapCut), a gravação é recusada. Reabrir e refazer. Gravação atômica (arquivo temporário + troca), nunca deixa JSON pela metade.
- **Efeitos da loja sem caminho:** transição, animação, efeito e máscara vão só com `resource_id`/`effect_id` (`catalogo.json`); o CapCut baixa o arquivo sozinho quando o projeto abre (precisa de internet na 1a vez).
- **Ímã da trilha principal:** a V1 do CapCut é magnética e, ao abrir, gruda os clipes e some com os buracos. `novo()` grava `config.maintrack_adsorb = false` para a V1 manter os tempos do DaVinci.
- Tempo em microssegundos no JSON (a lib recebe segundos). Posição `clip.transform` em meia-tela (-1 a 1, y para cima); a lib recebe pixels com y a partir de baixo (mesma convenção da legenda Y 724 do DaVinci).

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/capcut")); import capcut_lib as C
```

## Comandos

| Comando | O que faz |
|---|---|
| `C.rascunhos()` | lista rascunhos (nome, duração, modificado) |
| `C.novo(nome, w=1080, h=1920, fps=30)` | rascunho novo a partir do esqueleto real do 9.4, já aparece na tela inicial |
| `d = C.abrir(nome)` | abre um rascunho existente para editar |
| `d.retrato(salvar_em=)` | retrato da timeline (regra 1g): trilhas, segmentos, ids, início/fim |
| `d.video(arq, t, de=, ate=, trilha=0, velocidade=, volume=, mudo=, escala=, x=, y=, rotacao=, opacidade=)` | vídeo; `trilha=0` é a principal (V1, intocável). B-roll: `trilha=1, mudo=True` |
| `d.imagem(arq, t, dur, trilha=1, ...)` | foto/PNG |
| `d.audio(arq, t, de=, ate=, trilha=, db=, fade_in=, fade_out=)` | narração, música bruta (corte e fade no clipe), SFX |
| `d.texto(txt, t, dur, tamanho=10, cor=, contorno=, negrito=, fonte=.ttf, x=, y=)` | texto simples (lettering básico) |
| `d.legenda_srt(srt, y=724, tamanho=8, ...)` | legenda do `.srt` do `legendas.py`, um bloco por fala |
| `d.transformar(id, escala=, x=, y=, rotacao=, opacidade=)` | posição/escala de um clipe |
| `d.keyframes(id, prop, [(t, v), ...])` | animação: `x`, `y`, `escala`, `rotacao`, `opacidade`, `volume` (dB), `saturacao`, `contraste`, `brilho` ou qualquer `KFType*` |
| `d.zoom(id, 1.0, 1.15)` | zoom lento do começo ao fim |
| `d.dividir(id, t)` | corta no tempo da timeline, devolve o id da 2a parte |
| `d.desligar(id)` | esconde sem apagar (estilo do Gabriel) |
| `d.remover(id, fechar_buraco=)` | apaga (nunca na V1) |
| `d.volume(id, db)` / `d.mover(id, t)` | ajustes rápidos |
| `d.cortar_silencio(ruido_db=-30, minimo=0.4, folga=0.12, trilha=0)` | tira as pausas da fala na V1 e junta (ripple). Rodar antes de legenda e b-roll. Devolve os segundos tirados |
| `d.silencios(id, ruido_db, minimo)` | só lista as pausas de um clipe, sem cortar |
| `d.transicao(id, "Dissolve", dur=0.4)` | transição entre este clipe e o próximo da trilha |
| `d.animar(id, entrada=, saida=, combo=, loop=, dur_entrada=, dur_saida=)` | animação de entrada/saída. Vídeo: entrada/saida/combo. Texto: entrada/saida/loop |
| `d.efeito(nome, t, dur, params=[0-100,...])` | efeito de tela inteira (trilha de efeitos) |
| `d.efeito_no_clipe(id, nome, params=)` | efeito só naquele clipe |
| `d.mascara(id, "Circle", x=, y=, tamanho=, suavizar=, cantos=, inverter=)` | máscara: Split, Filmstrip, Circle, Rectangle, Stars, Heart |
| `d.fundo(id, desfoque=0.5)` / `d.fundo(id, cor="#000000")` | fundo atrás de vídeo horizontal no 9x16 |
| `C.catalogo(grupo, busca)` | nomes disponíveis: transicoes (116), video_entrada (43), video_saida (23), video_combo (108), texto_entrada (76), texto_saida (68), texto_loop (53), efeitos (345), efeitos_pessoa (95), mascaras (9). Nome errado devolve os parecidos. "(pro)" = precisa do CapCut Pro para exportar |
| `d.filtro(id, "Azul da ilha", 80)` / `d.filtro_global(nome, t, dur, 80)` | filtro de cor no clipe / numa trilha de filtro que pega tudo embaixo. Nomes: `C.loja("filtros")` |
| `d.adesivo(nome, t, dur, escala=, x=, y=)` | adesivo (sticker) da loja. `C.loja("adesivos", "emoji")` |
| `d.voz(id, nome, forca=100)` | efeito de voz num clipe de áudio/vídeo. `C.loja("voz")` |
| `d.modelo_texto(nome, texto, t, dur, y=, legenda=False)` | texto num modelo pronto da loja (beta). `C.loja("modelos_texto")` |
| `d.animar(id_texto, legenda="Agitação")` | animação de legenda palavra a palavra. `C.loja("texto_anim", tipo="caption")` |
| `C.loja(grupo, busca, tipo=)` | loja do CapCut: filtros, adesivos, modelos_texto, texto_anim (tipo in/out/loop/caption), video_anim, voz, efeitos_loja, fontes |
| `C.atualizar_loja()` | relê o cache do CapCut e regrava `loja.json` (cada painel aberto no CapCut entra no cache) |
| `python3 capcut/davinci_para_capcut.py [retrato.json]` | recria no CapCut a timeline aberta no DaVinci (ver abaixo) |
| `d.salvar(projeto_fechado=True)` | grava em todas as cópias + backup `draft_info.gab_<data>.json` na 1a gravação |
| `C.fechar_capcut()` / `C.abrir_capcut()` | fecha (AppleScript) / abre na tela inicial |

### Keyframes que o motor aceita (tirados do binário)
Transformação: `KFTypePositionX/Y`, `KFTypeScaleX/Y`, `KFTypeRotation`, `KFTypeAlpha`, `KFTypeGlobalAlpha`. Áudio: `KFTypeVolume`, `KFTypeAudioPanning`. Cor: `KFTypeSaturation`, `KFTypeContrast`, `KFTypeBrightness`, `KFTypeTemperature`, `KFTypeHue`, `KFTypeSharpen`, `KFTypeVignetting`, `KFTypeHightLight`, `KFTypeShadow`, `KFTypeLUT`, `KFTypeFilter`. Máscara: `KFTypeMaskPostionX/Y`, `KFTypeMaskSizeX/Y`, `KFTypeMaskFeather`, `KFTypeMaskRotation`. Chroma: `KFTypeChromaIntensity`, `KFTypeChromaShadow`. Texto: `KFTypeTextColor`, `KFTypeTextAlpha`, `KFTypeBorderWidth`, `KFTypeShadowAlpha`, `KFTypeBackgroundAlpha`. Lista completa: `strings libVECreator.dylib | grep -o 'KFType[A-Za-z]*' | sort -u`.

## Loja do CapCut (`loja.json`)
O CapCut guarda as respostas da API dos painéis em `~/Movies/CapCut/User Data/Cache/ressdk_db/*/rp.db` (SQLite, tabela `http_cache`, rotas `/artist/v1/panel/get_panel_info` e `/artist/v1/effect/get_resources_by_category_id`). O `effect_type` diz o que é: 12 filtro, 2 adesivo, 48 modelo de texto, 18 animação de texto (categorias Entrada/Saída/Loop/Legenda), 13 animação de vídeo, 26 efeito de voz, 7/19 efeito, 10 fonte. `atualizar_loja()` lê isso (só leitura) e grava nome, `resource_id`, `effect_id`, Pro e tipo. Em 15/10/2026: 50 filtros, 2.148 adesivos, 4.316 modelos de texto, 1.839 animações de texto, 4.701 de vídeo, 361 vozes, 100 efeitos, 5.985 fontes. Só aparecem os painéis que o usuário já abriu no CapCut: abrir o painel de Filtros inteiro e rodar `atualizar_loja()` traz o resto. "(pro)" precisa do CapCut Pro para exportar.

## DaVinci → CapCut (`davinci_para_capcut.py`)
Só LÊ o DaVinci. Leva: clipes de todas as trilhas de vídeo (trecho exato pelo fps real do arquivo, zoom, pan/tilt, rotação, opacidade, desligado), Cross Dissolve (vira Dissolve), áudio (o que casa com o clipe fica no clipe, o resto vira trilha de áudio; Cross Fade vira fade) e legendas (texto na Y 724). Zoom: o 1.0 do DaVinci (encaixar no quadro) é igual ao 1.0 do CapCut, então o zoom passa direto. Vídeo de câmera/celular gravado em pé (16:9 com rotação 90 nos metadados) é lido como vertical. Rotação feita no DaVinci em Clip Attributes (Image Orientation) NÃO vem pela API: conferir no CapCut e girar com `d.transformar(id, rotacao=-90, escala=zoom*1.778)` (teste NBA, clipes do Dieguinho). Não leva: compound clip, Fusion/lettering, cor/LUT, efeitos do DaVinci (vão listados em `relatorio_capcut.json`). Mídia fora de `~/Movies` é copiada inteira (12 GB no teste NBA); nunca re-renderizar take.

## O que ainda não tem
Chroma key, fontes da loja no `texto()` (os ids já estão em `loja.json`) e conferência visual: modelos de texto e legendas animadas foram gravados mas ainda não abertos no CapCut. O caminho para incluir: aplicar uma vez à mão num rascunho, ler o JSON e copiar `resource_id`/`effect_id` para o `catalogo.json`. Os ids vêm do VectCutAPI (github.com/sun-guannan/VectCutAPI, Apache 2.0, catálogos `pyJianYingDraft/metadata/capcut_*.py` de 12/10/2026), convertidos lendo o código como texto (sem executar).

## Arquivos
| Arquivo | O que é |
|---|---|
| `capcut.py` | linha de comando (plano JSON, cortes, prévia, conferir, abrir, fechar) |
| `capcut_lib.py` | os comandos acima |
| `loja.json` | ~19 mil itens da loja do CapCut tirados do cache local (filtros, adesivos, modelos, animações, vozes, fontes) |
| `davinci_para_capcut.py` | recria no CapCut a timeline do DaVinci |
| `catalogo.json` | 936 transições, animações, efeitos e máscaras com os ids internos do CapCut |
| `molde.json` | estruturas reais de segmento/material extraídas do CapCut 9.4 (sem caminhos pessoais) |
| `esqueleto/` | pasta de rascunho vazio do 9.4 (ids trocados a cada `novo()`) |

## Presets do usuário (24/10/2026, tudo por arquivo)

| Comando | O que faz |
|---|---|
| `capcut.py presets` | lista os presets do Gab (`~/.claude/ogab_capcut/presets`, fora do git) e as predefinições do próprio CapCut (`User Data/Presets`: Adjust, Combination...) |
| `capcut.py presets salvar <nome> "<rascunho>" @t0:2 [--posicao]` | guarda o visual do segmento. Texto: material inteiro menos o que depende do texto (fonte, cor, contorno, fundo, sombra, alinhamento) + 1o estilo + animações. Vídeo/imagem: filtro, efeitos, animação, máscara, fundo (`canvases`). `--posicao` leva escala/posição/rotação. Velocidade e áudio ficam de fora |
| `capcut.py presets aplicar <nome> "<rascunho\|CORTE*>" @t0:*` | aplica: texto, mídia e tempo do destino ficam; o visual troca (refs do mesmo tipo são substituídas). Mesmo que `faz ... aplicar_preset @alvo <nome>` |
| `capcut.py presets ver/apagar <nome>` | conteúdo / apaga |
| `capcut.py presets backup [zip]` / `restaurar <zip> [--substituir]` | cópia das predefinições do CapCut + presets do Gab; restaurar com o CapCut FECHADO (ele regrava as predefinições ao sair) |

O usuário fez o estilo no app e quer guardar: ele fecha o projeto, o Gab acha o segmento com `ids` e roda `presets salvar` (nada de tela). Testado no Mac 24/10/2026 (título com cor, contorno, fundo e animação Blur salvo e aplicado em outro texto). O formato das predefinições NATIVAS do CapCut (Combination/Adjust) ainda não foi lido com um preset real: por isso o Gab guarda as dele em JSON próprio e só faz cópia de segurança das nativas.

## Windows (24/10/2026, beta)

Mesma lib e mesma linha de comando; a `capcut_lib` detecta o Windows (`C.WIN`) e troca sozinha:

| | Mac | Windows |
|---|---|---|
| Pasta dos rascunhos | `~/Movies/CapCut/User Data/Projects/com.lveditor.draft` | `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft` |
| Arquivo do rascunho | `draft_info.json` | `draft_content.json` (`C.arq_rascunho()` aceita os dois: rascunho do Mac abre no Windows e vice-versa) |
| Mídia | copiada para `~/Movies/Gab CapCut` (sandbox) | fica onde está (sem sandbox); caminhos gravados com `/` como o CapCut do Windows grava |
| Aberto? / fechar | `pgrep` / AppleScript | `tasklist` / `taskkill` sem `/F` (o CapCut recebe o pedido de fechar e salva) |
| Abrir | `open -a CapCut` | `CapCut.exe` em `%LOCALAPPDATA%\CapCut\Apps` |
| Fontes | `~/Library/Fonts` | `%LOCALAPPDATA%\Microsoft\Windows\Fonts` e `C:\Windows\Fonts` (`C.fonte("Anton-Regular.ttf")`) |
| Clicar na miniatura para abrir | o Gab (computer-use) | o usuário (computer-use do Claude é só no Mac): `capcut.py abrir "<rascunho>"` e pedir o clique na 1a miniatura |

- **Local do rascunho trocado nos Ajustes do CapCut:** gravar a variável de usuário `GAB_CAPCUT_RAIZ` com a pasta nova (`setx GAB_CAPCUT_RAIZ "D:/CapCut/Projects/com.lveditor.draft"`) e reabrir o Claude Code. Vale no Mac também.
- **Rascunho criptografado:** a lib recusa com aviso claro se o arquivo não for JSON puro (o Jianying chinês criptografa desde a 6.0; o CapCut internacional não, até onde se sabe em 10/2026). Nesse caso: modo `nenhum` + `previa`.
- **Testado:** simulação no Mac (criar, salvar, reabrir, registrar na tela inicial, `previa`). **Ainda não aberto num CapCut de Windows de verdade:** no primeiro uso, conferir que o rascunho aparece na tela inicial e abre; se não abrir, olhar se o CapCut gravou algum arquivo novo na pasta do projeto e registrar em docs/PROCESSO.md.
- `previa`, `conferir`, `plano`, `cortes`, `faz`, `levar` e `davinci_para_capcut.py` rodam iguais (com `PYTHONUTF8=1`, que o `install.ps1` grava).

**Relato de uso real no Windows (24/10/2026, Windows 10 + CapCut 9.6.0, vindo da comunidade):**
- O rascunho gravado pela lib (versão 181) apareceu como 1a miniatura e o CapCut 9.6 abriu e regravou como 189.0.0 sem perder nada (cortes de MOV 4K com rotação do iPhone, motions MP4/MOV ProRes 4444 com alfa, dezenas de textos e áudios). O app criou sozinho `Timelines/<uuid>/`, `subdraft/`, `template-2.tmp` e `.bak`.
- `font_size` gravado como 10 voltou como 7.0 depois que o app regravou: conferir a escala do tamanho de texto no 9.6 do Windows antes de confiar no número.
- Sombra feita no app 9.6 fica só dentro de `content.styles[].shadows` (`alpha`, `distance`, `angle`, `diffuse`, com `useLetterColor: true`); os campos `has_shadow`/`shadow_*` do material ficam no padrão (has_shadow False) e `check_flag` vira 47 mesmo sem contorno. Com o contorno desligado, o app tira o `strokes` do estilo. Para copiar um estilo feito no app, ler esses campos.
- Keyframe: o `time_offset` conta no tempo do arquivo (a partir de `source_timerange.start`), já tratado em `keyframes()`.
- Relatado (não confirmado pelo autor): o computer-use do Claude existe no Windows; pedir acesso a `CapCut` e ao processo `capcut.exe`; com a janela minimizada o `open_application` não traz para a frente e o usuário precisa clicar na barra de tarefas.
