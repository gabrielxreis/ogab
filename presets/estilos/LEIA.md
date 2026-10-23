# ESTILOS: efeitos curtos e trocáveis sobre o vídeo da pessoa (motor CENA)

Cada estilo é uma peça pequena (gancho, legenda, layout, prova, batida, b-roll animado, efeito, ritmo ou cor) que o Gab
coloca num trecho do vídeo. O usuário escolhe no `/ogab menu` (o menu lê esta pasta sozinho: estilo com `exemplo.gif`
aparece no grupo dele). Criados em 23/10/2026 a partir de IDEIAS de estilos de edição populares: **nada é copiado de
pacotes de terceiros** (nem texto, nem desenho, nem código, nem nome); cada estilo é desenhado do zero aqui, com nome,
descrição e animação nossos.

## Pasta de um estilo
`presets/estilos/<grupo>/<id>/` com:
- `estilo.json`: metadados (abaixo).
- `<id>.js`: a animação (motor `cena`, padrão) OU o que o `motor` do estilo pedir (ritmo/cor, ver no fim).
- `exemplo.gif`: prévia em loop gerada por `python3 presets/estilos/exemplo/fazer.py <id>` (apresentador ILUSTRADO, nunca
  pessoa real nem cliente).

Grupos (pasta): `gancho`, `legenda`, `layout`, `prova`, `batida`, `broll`, `efeito`, `ritmo`, `cor`.

### estilo.json
```json
{
 "id": "notificacao", "grupo": "batida", "camada": "frente", "precisa": ["rosto"],
 "nome": {"pt": "Notificação do celular", "en": "Phone notification"},
 "desc": {"pt": "Uma frase curta do que aparece (para o menu).", "en": "Same in English."},
 "quando": "em que fala usar (sinais para o Gab e o escolher_preset)",
 "campos": {"titulo": {"tipo": "texto", "exemplo": "Vídeo pronto"}},
 "exemplo": {"de": 0.4, "ate": 3.4}
}
```
- `id`: único em todos os grupos, minúsculo-com-hífen, em português.
- `camada`: `frente` (por cima de tudo) ou `atras` (entre o vídeo e a pessoa recortada: texto atrás da cabeça, fundo
  trocado, canvas inteiro no lugar da sala). `atras` liga o recorte da pessoa sozinho.
- `precisa`: `rosto` (caixa do rosto), `palavras` (transcrição com tempo), `video` (o vídeo da pessoa, com a lente, em
  `C.P.video`), `silhueta` (a pessoa recortada com alfa, WebM, em `C.P.silhueta`; vale até em estilo só de frente),
  `recorte`, `imagem`, `logo`. Para tocar vídeo na camada: `C.video(src, pai, classe)` (já no tempo do vídeo).
- `campos`: o que o Gab preenche com o conteúdo do vídeo; `exemplo` de cada campo é usado na prévia.
- `camada: "ambas"`: o mesmo item entra atrás E na frente da pessoa; o `.js` decide o que desenhar por `C.P.camada`
  (`"palco"` = atrás, `"frente"` = na frente), ex.: cartões girando que passam por trás e pela frente do corpo.
- `"base": {"desfoque": 18, "escurecer": .35}`: no trecho do estilo a sala (vídeo base) fica desfocada/escurecida.
- `"pessoa": {"escala": .42, "x": 620, "y": 1200, "rot": 4}`: no trecho, a pessoa recortada encolhe, vai para o centro
  (x, y) e gira (moldura, polaroid); o `.js` desenha a moldura atrás (camada `atras`). Também aceitos no item do plano.
- Mídia: qualquer campo com caminho de arquivo de imagem/vídeo (`logo`, `imagem`, `imagens`, `img`, `foto`, `src`,
  `video` ou extensão .png/.jpg/.webp/.gif/.svg/.mp4/.mov/.webm, em qualquer nível do item) é copiado para `img/` do
  projeto e o valor vira `img/<nome>`; links http/data: ficam como estão. Sem arquivo, desenhar um substituto ilustrado.

## API do `<id>.js` (motor cena)
```js
ESTILO["meu-estilo"] = (it, C) => {          // it = item do plano (de, ate + campos); C = motor
  C.css("meu-estilo", `...`);                 // CSS uma vez
  const r = C.rostoEm(it.de);                 // [x0, y0, x1, y1] do rosto (ou null): NUNCA desenhar em cima
  const S = C.seguro;                         // {topo: 220, baixo: 450, lado: 35}: área segura de Reels/TikTok
  const e = C.el("div", "classe", pai, html); // cria elemento (C.esc(texto) para escapar)
  C.tl.fromTo(e, {...}, {...}, it.de);        // GSAP: tudo na timeline C.tl, entre it.de e it.ate
};
```
- `C.P`: `w`, `h`, `dur`, `dest` (cor da marca do cliente, também em `var(--dest)`), `rostos`, `palavras` (se precisa).
- Fontes já no projeto: `PalcoSans` (Poppins 700/800/900), `PalcoSerif` (Playfair Display itálico 400/600) e
  `PalcoHand` (Patrick Hand, manuscrita). Fonte nova:
  pedir à sessão principal (o motor copia as fontes).
- Cor de destaque SEMPRE `var(--dest)` (vem do cliente); nada de cor fixa de marca de terceiros.
- Entrada no quadro de `it.de`, saída limpa até `it.ate`; nada de piscar nem fade do preto.

## Regras (valem para todo estilo)
1. **Rosto livre:** nada em cima de olhos a queixo. Fugir com `C.rostoEm`: acima da cabeça, ao lado, abaixo do queixo, ou
   `camada: "atras"`.
2. **Área segura:** texto e cartões dentro de `C.seguro`.
3. **Prova real:** tela recriada (chat, app, post) é ilustração e não finge ser print real; print real vem do cliente.
4. **Logos e marcas de terceiros** só entram como campo (`logo`) preenchido pelo Gab com o arquivo oficial do vídeo; o
   exemplo usa marcas fictícias.
5. **Sem cópia:** não abrir nem copiar o pacote de outra pessoa; descrever e animar com palavras e desenho próprios.
6. Visual: limpo, sem clichês de `docs/etapas/motion_proibidos.md`.

## Testar
1. `python3 presets/estilos/exemplo/fazer.py <id>` (render do apresentador ilustrado com cache em ~/.cache/ogab_estilos).
2. Olhar 2 a 3 quadros do GIF (`ffmpeg -i exemplo.gif -vf "select=eq(n\,30)" -frames:v 1 q.png`): rosto livre, nada
   cortado, texto legível, cor da marca.
3. Plano real: `"estilos": [{"id": "...", "de": 1.0, "ate": 3.5, ...campos}]` no plano do `presets/cena/gerar.py`.

## Motores fora do HyperFrames
- `ritmo` (zoom, punch-in, transição): `"motor": "lente"` usa a LENTE do motor cena (zoom no ffmpeg) ou
  `"motor": "davinci"` com `R.animar_clipe` (keyframes no editor). Prévia: o mesmo `fazer.py`.
- `cor` (acabamento): `"motor": "lut"` com um `.cube` gerado em Python dentro da pasta do estilo; no DaVinci entra com
  `Graph.SetLUT` (a LUT precisa ir para a pasta MASTER de LUTs: `davinci_api.md`). Prévia: aplicar a LUT na gravação
  ilustrada com ffmpeg `lut3d` e cortar o GIF.

## Arquivos que só a sessão principal muda
`presets/cena/gerar.py`, `presets/estilos/estilos.js`, `presets/estilos/exemplo/fazer.py`, `scripts/menu.py`,
`SKILL.md`. Precisa de algo neles: pedir à sessão principal.
