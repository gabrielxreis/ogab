# Motion avançado: morph de formas complexas e 3D de verdade

Testado em 12/10/2026 com a logo da Calverstone (e a Bora Imigrar no morph). Usar quando o pedido pedir "a logo
se formando", "transformar uma forma em outra", "logo em 3D", "texto com volume/metal", abertura de marca etc.

## Morph de forma complexa (HyperFrames + GSAP MorphSVG)

- `scripts/svg_texto.py`: transforma texto em contorno vetorial (path SVG) em qualquer fonte .ttf. `caminho()` = a
  palavra inteira; `letras()` = um path por letra, na posição exata da palavra.
- `scripts/morph_logo.py plano.json <projeto hyperframes> --render saida.mp4|.mov`: forma inicial (losango, círculo
  ou qualquer `d` de SVG) -> letra grande -> palavra da marca, com as outras letras em cascata e o divisor.
  `.mov` sai com alfa para ir por cima do vídeo.
- **Regra que evita o "blob":** nunca morphar UMA forma direto numa palavra inteira (o plugin cria letras do nada e a
  forma vira bolha no meio). Morphar a forma em UMA letra e animar as outras letras como elementos próprios.
- Para logo desenhada (não texto): pegar o `d` dos `<path>` do SVG da marca; formas com várias partes: morphar
  parte a parte (cada `<path>` no seu par) ou a parte principal e revelar o resto.

## 3D de verdade (Blender, sem abrir a janela)

- `tresd/tresd.py logo plano.json saida.mov`: texto/logo extrudado com chanfro, metal (cor da marca), três luzes
  (key quente, rim frio, fill), câmera enquadrando 80% da largura. `anim`: `entrada` (vem girando e assenta),
  `giro` (360°) ou `orbita` (câmera em arco). Losango e linhas da marca opcionais. 90 quadros ~40 s.
- Sai MOV ProRes 4444 com alfa (vai na trilha de motions) + o `.blend` ao lado (abre no Blender para ajustar).
- Precisa do Blender (o instalador instala; o doctor confere). Coordenadas: logo de pé no plano XZ, câmera no -Y.
- No After Effects, o mesmo MOV entra como camada; para 3D dentro do AE dá para importar `.glb` (exportar do
  Blender) com o renderizador Advanced 3D, mas o caminho padrão é o MOV.

## Objetos 3D de verdade (diploma, troféu, avião, prédio...)

- **Conhecimento:** pacote **cc-blender-skill** (MIT, github.com/RobLe3/cc-blender-skill), instalado pelo instalador em
  `~/.claude/skills/` (30 skills: `text-to-blender` orquestra; `blender-modeling`, `blender-materials`, `blender-lighting`,
  `blender-cameras`, `blender-animation`...). Ler a skill do domínio antes de modelar (receitas de material por tipo:
  ouro, cromo, vidro, madeira, tecido; luz por tipo de material).
- **Execução (do jeito do Gab, sem janela):** as skills dele mandam o Python para o Blender ABERTO via MCP; aqui o
  mesmo Python vira um **script de cena** e roda sem janela: `python3 tresd/tresd.py cena <cena.py> saida.mov --dur 4`.
  O script recebe `base` (`tresd/cena_base.py`: material, `ouro()`, `tres_pontos(classe)`, `camera()`, `chave()`) e `P`
  (parâmetros) e não renderiza (o runner renderiza com alfa e salva o `.blend`). Exemplo completo: `tresd/cenas/diploma.py`.
- **Convenções:** objetos do assunto com nome `GEO-...` (entram no enquadramento e na luz); objeto de pé no plano XZ,
  câmera no -Y. `base.camera()` enquadra pela LARGURA (no 9:16 objeto horizontal cortava).
- **Metal que fica bonito:** `tres_pontos("metal")` já põe o softbox de cima e um rebatedor atrás da câmera; sem eles o
  ouro sai escuro/oliva (o metal reflete o ambiente). Ambiente (`base.mundo`) cinza neutro médio, não navy escuro.
- Conferir 3 quadros por cima do fundo da marca antes de entregar. Diploma de 4 s: ~2 min de render.

## 3D com qualidade de produto (regras do usuário, 12/10/2026, Bora Imigrar bi10)

- **3D complementa, não substitui:** o vídeo continua sendo o motion 2D aprovado (cards, contadores, carimbos, chips);
  o 3D entra em 2-3 momentos de impacto com um OBJETO REAL (martelo, green card, troféu, logo). Detalhe gráfico
  (carimbo, etiqueta, texto pequeno) fica no 2D, que sai nítido; no 3D fica feio.
- **Objeto real imita o real:** green card com a arte do cartão (fundo guilloche, faixa, foto, campos) numa textura,
  com dados de EXEMPLO e marca "SPECIMEN" visível (nunca documento que passe por verdadeiro). Modelo pronto quando
  existir (Poly Haven CC0: `python3 tresd/polyhaven.py buscar <palavra>`); senão modelar por revolução (`torno`) com
  textura PBR do Poly Haven (`polyhaven.py textura`).
- **Render:** `gpu_cycles()` + `hdri(<estúdio>.hdr)` (Poly Haven `brown_photostudio_02`) + 1-2 luzes de área médias;
  EEVEE com luz forte deu "aberração de luz". 24 amostras + denoise + persistent data: ~5 s/quadro em 1080x1920 no
  M1 Pro. Prévia antes: 3 quadros em 540x960 por cena (rápido) e só então o render final.
- **Tela cheia, sempre:** 1080x1920 com alfa; `deslocar_camera(cam, y)` põe o objeto onde o layout pede (abaixo do
  texto: y≈1180; CTA: 960). Nunca renderizar um quadrado e colar: a borda corta o objeto ("sai de um lugar quadrado").
- Composição: ffmpeg overlay em 0:0 no tempo da cena (fade 0,25 s de alfa), ou a trilha MOTIONS no editor.
