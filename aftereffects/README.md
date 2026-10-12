# Gab (/ogab) com motions no After Effects

Duas formas de fazer os motions, escolhidas na instalação e trocáveis a qualquer hora:

| `config.json` > `motion` | Como é |
|---|---|
| `"hyperframes"` (padrão) | **Automático:** o Gab escreve o motion em código (HyperFrames) e renderiza. Rápido, sem precisar de After Effects |
| `"aftereffects"` | **Controle total:** o Gab monta cada motion no After Effects como **camadas nativas e editáveis** e entrega o MOV com alfa para a timeline. O usuário abre o `.aep` e mexe em qualquer detalhe: texto, número, check, cor, tempo, keyframe |

`/ogab config motion aftereffects` ou `/ogab config motion hyperframes` troca. O editor (DaVinci ou Premiere) não muda: o MOV com alfa entra na trilha de motions dos dois.

## Instalar (uma vez por máquina, com o AE FECHADO)

- Mac: `bash ~/.claude/skills/ogab/aftereffects/instalar.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\aftereffects\instalar.ps1"`

Instala a extensão **Gab Ponte AE** (invisível: sobe sozinha quando o AE abre, não tem painel) e liga "Permitir que scripts gravem arquivos" nas preferências do AE. Depois é só abrir o AE normalmente.

## O que o Gab entrega por motion

1. Uma comp no projeto do vídeo: `<pasta do vídeo>/motions/<Assunto> - motions.aep`, uma comp por motion (`m01-nome`, `m02-nome`...).
2. Dentro da comp, **uma camada por elemento**, com nome legível (`TITULO`, `LINHA 1`, `CHECK 1`, `NUM 1`, `FORMACAO 1`...):
   - **textos** são camadas de texto do AE (troca o texto e a âncora continua centralizada);
   - **caixas, checks e barras** são formas (o check se desenha com Trim Paths);
   - **contadores** sobem de "Valor inicial" a "Valor final", controles deslizantes na própria camada (Controles de efeito), com separador de milhar;
   - **keyframes** com a curva calma do Gab (entra e sai devagar, influência 70-80%);
   - **CONTROLES** (camada guia no topo): `Cor principal`, `Cor de destaque`, `Cor do texto`, `Cor do fundo`. Trocar ali muda o motion inteiro.
3. O MOV com alfa (ProRes 4444) em `<pasta do vídeo>/motions/mNN-nome.mov`, colocado na trilha de motions do editor como sempre.

## Como montar (para o Gab)

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/aftereffects")); import ae_lib as AE
AE.abrir_projeto("<pasta do vídeo>/motions/<Assunto> - motions.aep")
AE.motion(spec)                                   # cria (ou recria) a comp
AE.quadro("m01-formacoes", 2.0, "<pasta>/motions/conferir_m01.png")   # conferir: centro 540/960, nada no rosto
AE.renderizar("m01-formacoes", "<pasta>/motions/m01-formacoes.mov")   # ~14 s para 6 s de motion
AE.fechar()                                       # no fim: salva e fecha sem perguntas
```

**O plano (spec)** vem do mesmo plano de motions de sempre (`docs/etapas/lettering_motions.md`): centro 540/960, visual do site do cliente, calmo, duração medida na fala.

```python
spec = {"nome": "m01-formacoes", "w": 1080, "h": 1920, "fps": 30, "dur": 5.9,
        "cores": {"principal": "#0B1F3A", "destaque": "#C9A657", "texto": "#F3EFE4", "fundo": "#0B1F3A"},
        "elementos": [   # de baixo para cima
          {"tipo": "fundo"},                                   # sem "fundo" o MOV sai transparente (por cima do take)
          {"tipo": "texto", "nome": "TITULO", "texto": "Se você é formada em", "caixa_alta": True, "fonte": "Inter-Bold",
           "tamanho": 40, "tracking": 220, "cor": "destaque", "y": 520, "inicio": 0, "entrada": "fade_up", "saida_em": 5.4},
          {"tipo": "caixa", "nome": "LINHA 1", "w": 820, "h": 118, "raio": 22, "cor": "#0D2547", "borda": "destaque", "y": 680,
           "inicio": 0.45, "entrada": "slide_esq", "sombra": True},
          {"tipo": "check", "x": 880, "y": 680, "tamanho": 64, "inicio": 0.8},
          {"tipo": "contador", "de": 0, "ate": 141000, "sufixo": " médicos", "tamanho": 96, "cor": "texto", "inicio": 0.2, "dur": 1.8},
          {"tipo": "barra", "w": 700, "h": 16, "y": 1080, "inicio": 0.2, "dur": 1.8, "ate": 100},
          {"tipo": "imagem", "arquivo": "<Empresa>/marca/logo.png", "largura": 420, "y": 760, "entrada": "pop"},
        ]}
```

| Campo | Valores |
|---|---|
| `tipo` | `fundo`, `texto`, `caixa`, `check`, `barra`, `contador`, `imagem` |
| `cor` | `"principal"`, `"destaque"`, `"texto"`, `"fundo"` (ligadas à camada CONTROLES) ou `"#hex"` fixo |
| `entrada` | `fade`, `fade_up`, `fade_down`, `slide_esq`, `slide_dir`, `pop`, `blur_in`, `digitando` (letra a letra), `palavras` (palavra por palavra) |
| `saida_em` / `saida` | segundo em que sai / `fade`, `fade_up`, `fade_down` |
| texto | `fonte` (nome PostScript: `Inter-Bold`, `Poppins-Bold`, `PlayfairDisplay-Bold`...), `tamanho`, `tracking`, `alinhar` (`esquerda`, `direita`), `caixa_alta` |

Se a fonte não estiver instalada, o Gab recebe um aviso (`[AE] aviso: fonte ... não está instalada`) e deve trocar por uma instalada ou pedir ao usuário.

**Fundo transparente sobre take claro:** sem `fundo`, texto dourado ou claro some em take claro. Nesse caso pôr uma `caixa` atrás do texto (cor `principal`, `opacidade_fill` 85) ou usar o `fundo`.

**Qualquer coisa além disso:** `AE.jsx("...ExtendScript...", arg=valor)` roda direto no AE (as funções `GAB.*` de `jsx/gab_ae.jsx` estão disponíveis). Ex.: trocar a cor de destaque de uma comp:
`AE.jsx("GAB.comp(args.c).layer('CONTROLES').property('ADBE Effect Parade').property('Cor de destaque').property(1).setValue(GAB.rgb('#E04848')); return 1;", c="m01-formacoes")`

## Biblioteca de motions (modelos prontos)

Antes de montar um motion do zero, ver se já existe modelo: `python3 SKILL_DIR/scripts/biblioteca_motions.py listar` (prévias em `biblioteca_motions/<modelo>/previa.png`). Se servir: `B.aplicar("<modelo>", {campos do vídeo}, cores_do_cliente)` devolve o spec pronto para `AE.motion(spec)` (centralizado em 960, duração ajustada ao número de itens).

**Salvar todo motion novo aprovado (regra do usuário, 12/10/2026):** quando um motion feito do zero for aprovado, transformar em modelo (textos viram `{{campos}}`, listas viram `repetir`, sem cores fixas da marca) e salvar: `python3 SKILL_DIR/scripts/biblioteca_motions.py salvar modelo.json --previa quadro.png`. No Mac do dono (`config.json` "dono_biblioteca": true) ele publica no GitHub e todo usuário recebe no próximo update; nos outros usuários fica só local (`biblioteca_motions_local/`).

## MOGRT para o Premiere

`AE.mogrt(comp, pasta)` expõe os textos e as cores da CONTROLES no Essential Graphics e exporta `<comp>.mogrt` (textos e cores editáveis dentro do Premiere). Confirmado em 12/10/2026 (2,9 s; o travamento do 1º teste vinha do `aerender` preso ao mesmo tempo). Os modelos da biblioteca viram MOGRT com `python3 SKILL_DIR/scripts/gerar_mogrts.py [modelo]` (vai para `premiere/assets/mogrt/` e é publicado no Mac do dono). **Falta conferir** a inserção desses MOGRTs dentro do Premiere (`premiere_lib.lettering`).

## Armadilhas (teste de 12/10/2026, AE 26.5 no Mac, sem ninguém na frente da tela)

- **Janela modal trava tudo**, inclusive o ping da ponte. Todo comando roda com `app.beginSuppressDialogs()`, mas as mensagens de erro do próprio AE (fora do script) continuam aparecendo. Se o Gab receber "não respondeu em N s", pedir ao usuário para olhar o AE e fechar o aviso.
- **Render:** a fila de render (`renderQueue.render()` dentro da chamada) e o `aerender` travaram neste Mac (o `aerender` até com o AE fechado). O `app.scheduleTask` aceita a tarefa mas ela não roda com o AE em segundo plano. Por isso o render padrão é por quadros: `saveFrameToPng` em cada quadro (~12/s, com alfa) + ffmpeg em ProRes 4444. `renderizar(..., motor="ae")` e `motor="aerender"` ficam para quando o usuário confirmar na tela que não há aviso pendente no primeiro render.
- **Fechar:** nunca Cmd+Q nem `quit` do AppleScript (a pergunta "salvar alterações?" cancela o fechamento e o AE continua aberto). Usar `AE.fechar()`.
- **Depois de um fechamento forçado** o AE para num aviso de inicialização; o `conectar()` aperta Return no AE depois de 45 s sem ponte.
- **Salvar logo depois de `quadro()`** uma vez gerou erro de salvamento (arquivo temporário `.aep` pela metade). Conferir quadros e só depois salvar, ou salvar pelo `motion()`.
- **Fonte:** o AE aceita qualquer nome calado; a conferência usa `app.fonts` (`isSubstitute`).
- A extensão também sobe dentro do `aerender`; ela detecta e não abre o servidor lá.
