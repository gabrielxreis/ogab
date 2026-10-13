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
