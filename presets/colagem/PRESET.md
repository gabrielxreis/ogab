# Preset COLAGEM (colagem dadaísta de revista)

Cada frase vira uma **página de colagem**: fotos antigas de domínio público recortadas à tesoura (borda branca em
facetas retas) e impressas em **meio-tom** de jornal, coladas em **papel kraft ou jornal**, com disco ou faixa de cor
construtivista atrás, retalhos de jornal, fita crepe e o texto em **etiquetas de papel rasgado** (Anton, caixa alta).
Tudo se mexe em **passos de 12 qps** ("on twos", cara de stop-motion): a peça cai na página vinda da câmera (3 passos,
maior e com sombra longa), bate, solta fiapos de papel e fica "fervendo" ±1 px a 6 qps, como se alguém tivesse colado
com a mão. Entre as cenas, uma **folha nova é deitada por cima** em 4 passos, com a borda rasgada.

Serve para curiosidade, "você sabia", história, personagem histórico, invenção, arquivo, cultura pop antiga.
Não serve para dado frio, interface, tecnologia nova nem marca de luxo minimalista.

**Diferença do LUME:** o lume é objeto realista com sombra macia numa mesa, nascendo desfocado em movimento contínuo.
A colagem é foto de arquivo em meio-tom com borda de tesoura, papel chapado, cor construtivista e movimento em
degraus (nada contínuo, nada de desfoque). **Diferença da GRAVURA:** a gravura se desenha traço a traço; a colagem já
chega pronta e é colada.

Exemplo: `exemplo.mp4` / `exemplo.gif` (10,6 s, 1080x1920): "Você sabia? Santos Dumont / Paris, 1906, voou
60 metros / Decolou sozinho, sem catapulta, na frente de juízes". Plano em `exemplo/plano.json`, fotos em `exemplo/fotos/`.

## Como pedir
`/ogab faz um reels no preset colagem sobre <tema>` (ou `preset: colagem` no estilo.md do cliente).

## Processo (o que o Gab faz)
1. Roteiro curto (8-40 s), 1 ideia por cena, 2-4 s por cena. Para cada cena: **que foto antiga mostra isso?**
   (pessoa, máquina, prédio, objeto) + 1 ou 2 etiquetas curtas (até 4 palavras cada; o número vai numa etiqueta grande).
2. Fotos **só de domínio público ou CC0, com crédito**: `python3 SKILL_DIR/scripts/baixar_video.py buscar "<termos>"
   --fonte commons --tipo imagem` (conferir a licença; `met`, `aic`, `nasa` também servem). Foto com o assunto bem
   separado do fundo recorta melhor. Pessoa: preferir retrato antigo (morto há mais de 70 anos).
3. Recorte: `"recorte": "sujeito"` usa a Apple Vision (o mesmo "copiar sujeito" do Fotos, via `scripts/sujeito.py`,
   Mac 14+, local e grátis); sem Vision, ou com recorte ruim, `"recorte": "retangulo"` (foto inteira cortada à
   tesoura, com fita crepe). O meio-tom e a borda branca saem prontos no PNG (`gerar.py`, numpy + OpenCV).
4. Plano (`gerar.py`, docstring): por cena `dur`, `papel`, `forma` (disco ou faixa), `jornal` (retalhos), `fotos`
   (`arquivo`, `credito`, `recorte`, `altura`, `largura`, `x`, `y`, `rot`, `em`) e `rotulos` (`texto`, `estilo`
   tinta | acento | papel | jornal, `tam`, `x`, `y`, `rot`, `em`; `|` quebra em tiras que entram uma depois da outra).
   `x`/`y` são px a partir do centro (540, 960); tudo dentro da caixa segura 900x1200 (o `gerar.py` avisa foto fora).
   `em` em segundos desde o começo da cena, ou uma palavra da fala com `"transcricao": "tr.json"` no plano.
5. `python3 SKILL_DIR/presets/colagem/gerar.py plano.json <pasta>/motions/colagem [--tema <marca>] --render <pasta>/motions/colagem.mp4 [--gif]`
   (HyperFrames da versão fixada em `versoes.json`, via `scripts/hf_preset.py`; ~1 min de render para 10 s).
6. Conferir: `npx --yes hyperframes@<versão> snapshot <pasta> --at ...` (o 1º quadro do snapshot às vezes sai no
   estado de t=0; conferir no MP4), `scripts/grade.py <mp4> --passo 0.5` e `scripts/revisor.py <mp4> --pasta <pasta>`.

## Tema (cor da marca)
`temas/padrao.json`: `tinta` (meio-tom e etiqueta preta), `acento` (disco, faixa, etiqueta de destaque: a cor da
marca entra aqui), `claro` (borda de tesoura e letra clara), `fita`, `papel` (kraft | jornal), `kraft`/`jornal` (tom
dos papéis), `fonte`/`fonte_arquivo` e `fonte_pequena`/`fonte_pequena_arquivo` (caminho absoluto vai junto para a
pasta). Marca nova: copiar para `temas/<marca>.json` e passar `--tema <marca>`. Nada de degradê roxo/azul: papel e
tinta chapada.

## Regras de bom gosto
- Uma foto principal por cena (no máximo 2), centralizada; etiqueta em cima e embaixo, pode morder a foto, nunca o rosto.
- Primeira peça com `em` 0-0,3 s: no quadro 0 ela já está no ar caindo (gancho nunca vazio).
- Etiquetas entram inteiras (ou tira por tira), nunca letra a letra; nada de nota de resgate (letras recortadas soltas).
- Movimento só em degraus de 12 qps, sem quique nem passar do ponto: a peça bate e assenta.
- O crédito da foto fica miúdo embaixo da foto, à direita (e vai também na legenda do post).
- Som: tesoura no recorte, papel batendo em cada peça, fita crepe, folha deitando; música com vinil/jazz ou boom bap baixo.
- Os avisos do revisor de "conteúdo encostado na borda" em instantes de queda (peça ainda no ar, 3 passos) são esperados.

## Créditos
- Técnica (slap em 12 qps, tremida de mão com semente, tira rasgada, fiapos, borda de tesoura por `approxPolyDP`,
  meio-tom por tela de pontos): portada do filme **06-collage** do repositório **mg-styles-15** (Vincentwei1021,
  licença MIT). Código reescrito para o /ogab; nada do repositório roda aqui.
- Fontes: Anton (Vernon Adams, SIL OFL 1.1) e Courier Prime (Alan Dague-Greene, SIL OFL 1.1), em `kit/fontes/`.
- Papéis, retalhos de jornal e grão: gerados pelo `gerar.py` (texto falso em barras, sem direito autoral).
- Fotos do exemplo (Wikimedia Commons, domínio público): `Alberto_Santos-Dumont_by_Nadar.jpg` (Nadar),
  `14-bis_de_Alberto_Santos_Dumont.jpg` (Jules Beau), `Luftschiff_von_Santos_Dumont_umkreist_Eiffelturm.jpg`
  (cartão-postal, autor desconhecido).
- Fato do exemplo: em 23/10/1906, no campo de Bagatelle (Paris), o 14-bis decolou por meios próprios e voou cerca de
  60 m diante de uma comissão do Aéro-Club de France (Prêmio Archdeacon).
