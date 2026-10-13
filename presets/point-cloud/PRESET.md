# Preset POINT CLOUD (motion minimalista em pontos)

Milhares de pontos claros sobre fundo preto desenham fotos reais, textos com volume e formas, e **migram de uma cena para
a outra** enquanto a câmera gira em 3D. Tipografia mínima (serifa itálica + linha pequena espaçada) e crédito da imagem
no rodapé. Estudado na página do curso "O Minimalista com IA" (13/10/2026): galáxia de pontos -> "?" em 3D -> busto
clássico em pontos girando. Serve para curiosidade, história, filosofia, ciência, frase de impacto, abertura de marca.

Exemplo: `exemplo/exemplo_previa.mp4` (prévia leve; o render cheio sai com `gerar.py ... --render`) (13,6 s: nuvem -> galáxia -> "?" -> busto de Sócrates -> esfera), plano em `exemplo/plano.json`.

## Como pedir
`/ogab faz um vídeo no preset point cloud sobre <tema>` (ou `preset: point cloud` no estilo.md do cliente).
Narração: a do usuário (voz clonada ou gravada); cada frase da fala troca a figura (a figura entra JUNTO com a palavra).

## Processo (o que o Gab faz)
1. Roteiro curto (20-45 s), 1 ideia por frase. Para cada frase: "o que a pessoa precisa VER para entender isso?"
   -> uma figura: pessoa/obra real (foto), símbolo/palavra (texto 3D) ou conceito (forma: galáxia, esfera, anel, onda, grade, nuvem).
2. **Imagens reais, sempre com crédito:** buscar no Wikimedia Commons só arquivos **Public domain ou CC0**
   (API: `commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=<busca>&gsrnamespace=6&prop=imageinfo&iiprop=extmetadata|url`,
   conferir `LicenseShortName`). Preferir foto com **fundo escuro ou liso** (o brilho separa a figura do fundo); fundo
   claro/estampado vira pontos também. Pessoa famosa: cuidado com direito de imagem (herdeiros), preferir obras/bustos/
   personagens históricos. O crédito vai no campo `credito` da cena.
3. Plano (ver `gerar.py`, docstring): `tipo` imagem | texto | galaxia | esfera | anel | onda | grade | nuvem, `dur`,
   `transicao` (1,1-1,6 s), `giro` (graus na cena; foto: 15-25, forma: 40-70), `inclinacao`, `relevo` (foto), `profundidade`
   (texto), `titulo` (`<i>` para itálico), `kicker`, `credito`. Cores: `fundo`, `cor` (pontos), `destaque` (itálico) -> cor da marca se pedir.
4. `python3 presets/point-cloud/gerar.py plano.json <pasta>/motions/point-cloud --render <pasta>/motions/point-cloud.mp4`
   (7000 pontos, ~2-4 min de render para 15 s). Conferir 1 folha de quadros antes de entregar.
5. Legenda GAB USA e som seguem o Gab; som: ambiente suave + "sopro"/shimmer quando os pontos migram, nada de whoosh pesado.

## Regras de bom gosto
- Uma figura por vez, centralizada (centro_y 860, abaixo fica o título); nunca texto em cima da figura.
- Transição dos pontos 1,1-1,6 s; segurar a figura pelo menos 1,5 s depois de formada.
- Poucos pontos borram a foto (mínimo 5000); muitos pesam o render (máximo ~12000).
