# Gab (/ogab) no CapCut (Mac)

Camada à parte, igual a `premiere/`: o método do `SKILL.md` não muda. Quando o usuário pedir CapCut (ou `"editor": "capcut"` no config), usar `capcut/capcut_lib.py` onde o `SKILL.md` manda usar `resolve_lib.py`.

> **Status: beta, aberto no CapCut em 15/10/2026:** `NBA - TIMELINE` (36 itens vindos do DaVinci) carregou com toda a mídia, áudio com forma de onda, legendas e tempos certos. Ainda não conferidos no app: transição, animações, efeitos, filtros, adesivos, voz e modelos de texto (`GAB TESTE API 2` e `3`).
>
> **Antes:** Rascunhos de teste gerados em 14/10/2026 (`GAB TESTE API` e `GAB TESTE API 2`, este com transição, animações, efeito, máscara, fundo e corte de silêncio); falta conferir dentro do CapCut que tudo abre certo. Até essa conferência, avisar o usuário que é beta.

## Como o Gab fala com o CapCut (engenharia reversa, CapCut 9.4.0, 14/10/2026)

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
| `capcut_lib.py` | os comandos acima |
| `loja.json` | ~19 mil itens da loja do CapCut tirados do cache local (filtros, adesivos, modelos, animações, vozes, fontes) |
| `davinci_para_capcut.py` | recria no CapCut a timeline do DaVinci |
| `catalogo.json` | 936 transições, animações, efeitos e máscaras com os ids internos do CapCut |
| `molde.json` | estruturas reais de segmento/material extraídas do CapCut 9.4 (sem caminhos pessoais) |
| `esqueleto/` | pasta de rascunho vazio do 9.4 (ids trocados a cada `novo()`) |
