# Bancos de objetos 3D grátis

Quando uma cena precisa de um objeto 3D pronto (`tresd/tresd.py cena`), o Gab procura **primeiro nos bancos abaixo, na ordem**, antes de modelar do zero ou gerar por IA. Blender importa GLB/glTF, FBX, OBJ, STL e USD nativo: preferir **GLB** (já vem com textura embutida).

## Busca e download automáticos

```
python3 tresd/bancos3d.py buscar trophy                        # Poly Haven + Sketchfab, já filtrado por licença
python3 tresd/bancos3d.py baixar polyhaven <id> <pasta>        # glTF + texturas + LICENCA.txt
python3 tresd/bancos3d.py baixar sketchfab <uid> <pasta>       # precisa SKETCHFAB_TOKEN; sem ele, Chrome logado
```

Buscar sempre em inglês. Os bancos sem busca aberta (Kenney, Quaternius, Poly Pizza, Smithsonian, NASA) aparecem como links no fim da busca, para abrir no Chrome.

## Regras de licença (vídeo de cliente é uso comercial)

- **CC0 / domínio público:** usa sem pedir e sem crédito. É o padrão.
- **CC-BY:** pode, mas o crédito vai na descrição do post (`Modelo: <nome> por <autor> (CC-BY)`). Avisar o usuário.
- **Royalty Free (BlenderKit, Fab, TurboSquid, CGTrader):** pode usar no vídeo, não pode revender o arquivo.
- **Nunca usar:** NC (não comercial), "personal use only", "editorial use", ND quando vamos alterar o modelo, nem modelo com marca registrada de terceiros (carro, tênis, logo) em anúncio.
- Todo modelo baixado fica com um `LICENCA.txt` ao lado (banco, link, autor, licença).

## Ordem de busca

| # | Banco | Licença | Bom para | Como baixar |
|---|---|---|---|---|
| 1 | **Poly Haven** (polyhaven.com) | CC0 | Objetos realistas de estúdio (móveis, utensílios, plantas, props), HDRI e texturas PBR | Já integrado: `tresd/polyhaven.py buscar <palavra> models` |
| 2 | **Kenney** (kenney.nl/assets) | CC0 | Low-poly limpo e colorido (estilo lúdico, ícones 3D, cidade, comida, objetos de jogo) | ZIP na página do pacote, sem conta |
| 3 | **Quaternius** (quaternius.com) | CC0 | Low-poly com **personagens animados** (andar, correr, acenar), animais, natureza, armas, naves | ZIP na página, sem conta |
| 4 | **Poly Pizza** (poly.pizza) | CC0 e CC-BY (ver em cada) | Milhares de low-poly avulsos, busca por palavra (inclui o acervo do antigo Google Poly) | Download GLB direto; API com key grátis |
| 5 | **Smithsonian 3D** (3d.si.edu) | CC0 (filtrar "CC0") | Objetos **reais escaneados**: fósseis, peças históricas, instrumentos, aviões, esculturas | Botão Download na página, GLB |
| 6 | **NASA 3D Resources** (science.nasa.gov/3d-resources) | Domínio público | Planetas, foguetes, satélites, rovers, astronautas | Download na página (GLB/STL/OBJ). Não usar o logo da NASA como endosso |
| 7 | **ambientCG** (ambientcg.com) | CC0 | Texturas PBR e HDRI (para vestir objeto modelado no Blender) | API `ambientcg.com/api/v2/full_json`, sem conta |
| 8 | **Sketchfab** (sketchfab.com) | Varia: filtrar "Downloadable" + CC0 ou CC-BY | O maior acervo: quase tudo existe lá, incluindo escaneamentos de lugares e objetos | Conta grátis; API `v3/models/<uid>/download` com token |
| 9 | **BlenderKit** (blenderkit.com) | Royalty Free / CC0 | Modelos e materiais prontos para Blender, qualidade alta, já com material certo | Conta grátis + addon no Blender (os pagos ficam de fora) |
| 10 | **Mixamo** (mixamo.com) | Royalty Free (conta Adobe) | **Animação de personagem**: aplicar caminhada, dança, gesto em qualquer boneco humanoide | Upload do personagem, baixa FBX animado |
| 11 | **Fab** (fab.com), **TurboSquid** e **CGTrader** (filtro Free) | Royalty Free | Produtos e objetos detalhados que não acharam acima | Conta grátis, download manual pelo Chrome |
| 12 | **Printables / Thingiverse / Scan The World** | CC (ver em cada; evitar NC) | Formas e esculturas sem textura (STL), bom para objeto de metal, ouro, mármore com material do Blender | Download STL, material aplicado no Blender |

Para texturas avulsas também servem **ShareTextures** (sharetextures.com, CC0) e **3D Textures** (3dtextures.me, CC0).

## Quando nenhum banco tem

1. Modelar no Blender com as skills `blender-*` (formas simples, objeto estilizado, logo).
2. Gerar por IA (Higgsfield `generate_3d`, Magnific `models3d_generate`, Artlist): **custa crédito**, então só perguntando antes, com o custo.

## Cuidados práticos

- Conferir escala e origem ao importar (`bpy.ops.import_scene.gltf`), aplicar `scale` e centralizar antes de animar a câmera.
- Modelo pesado (> 200 mil faces) em EEVEE: aplicar Decimate antes do render.
- Low-poly (Kenney, Quaternius, Poly Pizza) e realista (Poly Haven, Smithsonian, Sketchfab) **não se misturam na mesma cena**: escolher um estilo por vídeo.
- Guardar o que foi baixado na pasta de assets do cliente para reaproveitar, com o `LICENCA.txt`.
