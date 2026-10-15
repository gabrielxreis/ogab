# Gab (/ogab) no CapCut (Mac)

Camada à parte, igual a `premiere/`: o método do `SKILL.md` não muda. Quando o usuário pedir CapCut (ou `"editor": "capcut"` no config), usar `capcut/capcut_lib.py` onde o `SKILL.md` manda usar `resolve_lib.py`.

> **Status: experimental.** Rascunhos de teste gerados em 14/10/2026 (`GAB TESTE API` e `GAB TESTE API 2`, este com transição, animações, efeito, máscara, fundo e corte de silêncio); falta conferir dentro do CapCut que tudo abre certo. Até essa conferência, avisar o usuário que é beta.

## Como o Gab fala com o CapCut (engenharia reversa, CapCut 9.4.0, 14/10/2026)

- **Não existe API de script nem porta local.** O app é Qt + motor ByteDance (`libVECreator`, `libvideoeditor`). O agente de IA interno (`libDeepAgentsService`, em Go) fala com a nuvem, não abre porta. O `capcut://` só abre painéis de IA (`.../anchor_point/ai_rough_cut`, `caption_auto_subtitles`...), não rascunhos.
- **O rascunho é JSON puro, sem criptografia** (no Mac; o Jianying chinês criptografa): `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<nome>/draft_info.json`. A lib lê e escreve esse arquivo.
- **Sandbox:** o CapCut só lê sem pedir o que está em `~/Movies` (entitlement `assets.movies.read-write`). A lib copia (hardlink quando dá) toda mídia de fora para `~/Movies/Gab CapCut/<rascunho>/`. Mídia fora dali aparece offline.
- **6 cópias do mesmo JSON** no 9.4: `draft_info.json`, `.bak`, `template-2.tmp` na raiz e em `Timelines/<id>/`. A lib grava em todas e zera o `attachment/patch/patch.json` (senão o CapCut reaplica edições antigas por cima).
- **Fluxo obrigatório:** o PROJETO fechado (o CapCut pode ficar na tela inicial ou em outro projeto) → `salvar(projeto_fechado=True)` → clicar no projeto. Com o projeto aberto, o CapCut sobrescreve tudo; por isso `salvar()` recusa com o app aberto até o Gab confirmar com o usuário que o projeto está fechado.
- **Proteção da edição manual:** `abrir()` guarda a impressão digital (sha256) do JSON; se ele mudar até o `salvar()` (o usuário mexeu no CapCut), a gravação é recusada. Reabrir e refazer. Gravação atômica (arquivo temporário + troca), nunca deixa JSON pela metade.
- **Efeitos da loja sem caminho:** transição, animação, efeito e máscara vão só com `resource_id`/`effect_id` (`catalogo.json`); o CapCut baixa o arquivo sozinho quando o projeto abre (precisa de internet na 1a vez).
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
| `d.salvar(projeto_fechado=True)` | grava em todas as cópias + backup `draft_info.gab_<data>.json` na 1a gravação |
| `C.fechar_capcut()` / `C.abrir_capcut()` | fecha (AppleScript) / abre na tela inicial |

### Keyframes que o motor aceita (tirados do binário)
Transformação: `KFTypePositionX/Y`, `KFTypeScaleX/Y`, `KFTypeRotation`, `KFTypeAlpha`, `KFTypeGlobalAlpha`. Áudio: `KFTypeVolume`, `KFTypeAudioPanning`. Cor: `KFTypeSaturation`, `KFTypeContrast`, `KFTypeBrightness`, `KFTypeTemperature`, `KFTypeHue`, `KFTypeSharpen`, `KFTypeVignetting`, `KFTypeHightLight`, `KFTypeShadow`, `KFTypeLUT`, `KFTypeFilter`. Máscara: `KFTypeMaskPostionX/Y`, `KFTypeMaskSizeX/Y`, `KFTypeMaskFeather`, `KFTypeMaskRotation`. Chroma: `KFTypeChromaIntensity`, `KFTypeChromaShadow`. Texto: `KFTypeTextColor`, `KFTypeTextAlpha`, `KFTypeBorderWidth`, `KFTypeShadowAlpha`, `KFTypeBackgroundAlpha`. Lista completa: `strings libVECreator.dylib | grep -o 'KFType[A-Za-z]*' | sort -u`.

## O que ainda não tem
Filtros (LUT de cor da loja), modelos de legenda animada, adesivos, efeitos de voz e chroma. O caminho para incluir: aplicar uma vez à mão num rascunho, ler o JSON e copiar `resource_id`/`effect_id` para o `catalogo.json`. Os ids vêm do VectCutAPI (github.com/sun-guannan/VectCutAPI, Apache 2.0, catálogos `pyJianYingDraft/metadata/capcut_*.py` de 12/10/2026), convertidos lendo o código como texto (sem executar).

## Arquivos
| Arquivo | O que é |
|---|---|
| `capcut_lib.py` | os comandos acima |
| `catalogo.json` | 936 transições, animações, efeitos e máscaras com os ids internos do CapCut |
| `molde.json` | estruturas reais de segmento/material extraídas do CapCut 9.4 (sem caminhos pessoais) |
| `esqueleto/` | pasta de rascunho vazio do 9.4 (ids trocados a cada `novo()`) |
