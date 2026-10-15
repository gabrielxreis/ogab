# Títulos OGraf do Gab (HTML editável dentro do DaVinci)

OGraf é o padrão da EBU para gráfico em HTML/CSS/JS. O DaVinci 21 renderiza OGraf como **título do Edit**, com os
parâmetros do manifesto editáveis no Inspector. É a mesma linguagem dos motions HyperFrames, mas o resultado fica
EDITÁVEL na timeline (texto, cores, tamanho, posição), sem MOV renderizado. Testado em 15/10/2026 (Resolve Studio 21.1,
timeline vertical 1080x1920).

**Beta. O Gab PERGUNTA antes de usar:** "Quer esse lettering/motion como título editável no DaVinci (OGraf, beta) ou
do jeito padrão (Fusion Title do pacote / MOV do HyperFrames)?". Sem resposta, segue o padrão.

## Templates

| Pasta | O que faz | Parâmetros (nome no manifesto) |
|---|---|---|
| `GabLettering/` | Frase de efeito centralizada; palavras entram uma a uma de baixo para cima, uma palavra em destaque | `texto`, `destaque`, `cor`, `corDestaque`, `fonte`, `tamanho` (1 = 100 px do quadro), `posY` (0 topo, 1 base), `sombra` |

O instalador copia cada pasta daqui para `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/OGraf/`
(Windows: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit\Titles\OGraf\`). Reiniciar o DaVinci
depois de instalar ou mudar um template. No Effects ele aparece com o NOME DA PASTA.

## Pela API (`resolve_lib.py`)

```python
# na V2 (destino da timeline na V2 antes, como nos letterings: Option+2 com o DaVinci na frente)
R.inserir_ograf_na_trilha(t, 2, [({"texto": "MUDA DE VIDA HOJE", "destaque": "HOJE", "corDestaque": "#22c55e"}, 12.4, 2.5)])
# num item "Fusion Composition" que já existe
R.ograf_no_item(item, "GabLettering", {"texto": "...", "posY": 0.62}, dur_f=60)
# conferir: SEMPRE pelo render do Fusion (o visualizador mostra a página em cache com os valores velhos)
R.conferir_ograf(item, 30, "/tmp/conf.png")
```

Como funciona (descoberto por engenharia reversa): `InsertTitleIntoTimeline`/`InsertFusionTitleIntoTimeline` NÃO
inserem OGraf pelo nome. O caminho é `InsertFusionCompositionIntoTimeline` + o nó **`OGrafLoader`** do Fusion:
`TemplatePath` = o `.ograf.json`; os parâmetros viram `DynParamText<i>` / `DynParamNum<i>` / `DynParamCheck<i>` /
`DynParamColor<i>_R/G/B` na ORDEM do `schema.properties` (a lib traduz pelo nome). A duração vem de um `stopAction`
agendado (`ScheduledAction_1`), porque a API não corta clipe.

## Regras para criar um template novo (aprendidas no teste)

1. Partir do `GabLettering` (ou de `Developer/OGraf HTML Templates/Examples`) e rodar o linter oficial:
   `python3 "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/OGraf HTML Templates/Scripts/lint-ograf.py" <pasta>` (0 ERROR).
2. `"supportsNonRealTime": true`, tudo calculado a partir do tempo em `goToTime` (sem timer, sem `Math.random`, sem `.play()`).
   GSAP/HyperFrames só no modo "seek" (posição da timeline pelo tempo).
3. **Tamanho do quadro:** o DaVinci monta a página como se fosse 1920 de largura e ENCOLHE (0,5625 no vertical), e prende
   o elemento em 16:9. Usar a resolução de `load(params).renderCharacteristics.resolution`, forçar `width/height` do
   elemento com `!important`, medir a escala `k = getBoundingClientRect().width / offsetWidth` e dividir por `k` todo
   tamanho em px (ver `_applyState` do GabLettering). Sem isso o gráfico sai pequeno no canto de cima.
4. Máximo 20 parâmetros. Cor = `{"type":"string","gddType":"color-rrggbb","pattern":"^#[0-9a-f]{6}$"}`.
5. O template carrega no 1º render e põe os padrões por cima: a lib faz um render de aquecimento antes de escrever os valores.
6. Texto `DEBUG` no 1º parâmetro do GabLettering mostra resolução, tamanho da página e do elemento (para diagnosticar).
