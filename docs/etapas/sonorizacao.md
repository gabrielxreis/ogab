<!-- Regra do usuário, 12/10/2026: "eu queria alguma skill para ajudar a sonorizar cenas e animações bem melhor" + "faça um caminho que não precisa de chave de IA". Ler ao sonorizar cena, take, animação ou motion. -->

# Sonorização de cenas e animações (sem chave de IA)

Vale para take gerado por IA, animação 2D/3D, cena de banco sem som e motion. Complementa `sfx.md` (tabela de foley por
objeto, sons de motion) e usa `scripts/sfx_conferir.py` para conferir. Nada aqui precisa de chave de IA: o vídeo é lido
pelo OpenCV, o som vem do Artlist (`search_sfx`, assinatura) e das bibliotecas locais, a mixagem é ffmpeg.

## 1. Ler a cena (o que se mexe, quando e onde)
`python3 SKILL_DIR/scripts/sonorizar.py analisar <video> --pasta <video>/som`
- Devolve cortes de cena e eventos: **entrada** (algo começa a se mexer depois de calma), **batida** (movimento forte
  que para de repente: pé no chão, porta, carro aterrissando), **pico** (auge de movimento contínuo), com força 0-1 e
  **pan** (-1 esquerda, +1 direita, pela posição do movimento).
- **Abrir `som/folha.png` e olhar** (quadro de cada evento com tempo e tipo escritos). O script acha QUANDO; o Gab decide
  O QUE é (objeto/ação) olhando a folha. Evento que não é nada (balanço de câmera) se ignora; ação que o script não
  pegou (fala, gesto pequeno) se acrescenta à mão.

## 2. Lista de som em 3 camadas (antes de buscar qualquer arquivo)
| Camada | O que é | Exemplo (carro no deserto) | Nível típico |
|---|---|---|---|
| AMBIENTE | o LUGAR, contínuo, do 1º ao último quadro de cada cena (corta seco no corte de imagem) | vento do deserto; depois motor em marcha lenta parado | -24 a -20 dB |
| FOLEY | o que os personagens/objetos fazem: passos, roupa, abraço, mão na mesa, porta, motor | motor vindo de longe, acelerada no salto | -16 a -10 dB |
| PONTUAIS | as batidas e os momentos fortes, cada um em 3 partes | aterrissagem, derrapagem, cascalho | -12 a -9 dB |
Animação 2D/cartoon: o mesmo, mais exagerado (passo com "tap", abraço com tecido e um "aww" de ambiente), e nada de
silêncio absoluto: sem ambiente, a cena soa falsa (meta de `sfx_conferir.py densidade`: >= 95% acima de -40 dB).

**Som importante = 3 partes no MESMO t** (é o que separa sonorização amadora de profissional):
ataque (o golpe seco, curto, ex. stone_hit) + corpo (o material/peso, ex. thud grave, motor) + cauda (o ar, o lugar,
o que sobra: cascalho, poeira, reverb). Cada parte é um evento do plano com db e dur próprios.

## 3. Achar os sons
- Artlist `search_sfx` em inglês, pelo OBJETO + ação + perspectiva ("porsche engine idle exterior", "car tires skid stop
  on dirt"). Baixar pelo `playableUrl` (curl + `ffmpeg -ar 48000 x.wav`). Bibliotecas locais: `~/Desktop/<Empresa>/_sfx_artlist/`
  e `SKILL_DIR/biblioteca_sfx/`.
- Não confiar no título: `sfx_conferir.py arquivos <pasta>` diz o que o som é (regra de `sfx.md`).
- `sonorizar.py medir <pasta>` mostra ataque, pico e duração de cada som (o plano usa isso para alinhar sozinho).
- Som que não existe no banco e o usuário tem gerador (ElevenLabs/Artlist): pedir com a fórmula **o que é + material +
  lugar + duração** ("carimbo de borracha em papel grosso, sala pequena seca, 0,4 s"), um som por geração, e empilhar.

## 4. Plano e mixagem
`<video>/som/plano.json` (formato no topo de `scripts/sonorizar.py`): `ambiente` (loop, fade nas pontas), `eventos`
(t, arquivo, db, pan, dur, alinhar), `musica` (com ducking), `voz` (áudio do próprio vídeo).
- `alinhar`: `onset` (padrão: o ataque cai em t), `pico` (motor passando, riser, impacto com subida: o pico cai em t),
  `inicio`. `dur` = quanto continua DEPOIS de t; a subida antes de t entra sozinha.
- **Pan pela tela:** usar o pan da análise (personagem à esquerda soa à esquerda). Ambiente e voz no centro.
- `python3 SKILL_DIR/scripts/sonorizar.py mixar <plano.json>` gera `ambiente.wav`, `sfx.wav`, `musica.wav` (stems),
  `mix.wav` (-14 LUFS em duas passadas, pico <= -1,5 dBTP) e `previa.mp4`. Com voz, ambiente e música abaixam sozinhos
  embaixo da fala (sidechain). `--sem-voz` descarta o áudio original do vídeo (take de IA com som ruim).
- **No editor:** os stems entram em trilhas com nome (AMBIENTE, SFX, MÚSICA) ou, para ficar editável som a som no DaVinci,
  `sonorizar.py davinci <plano.json> <video>/sfx` escreve o `plano_sfx.txt` (já descontando o ataque e recortando o som
  que entra no meio) para `resolve_lib.colocar_plano_sfx(..., trilhas=tuple(range(3, 11)))`. Pan no Inspector.

## 5. Conferir antes de mostrar
- `sfx_conferir.py densidade <mix.wav>` (>= 95%), `trechos` (cada cena soa como o que mostra) e `sincronia <mix> t1 t2 ...`
  (som pontual a <= 0,12 s do evento; foley sobre som contínuo, como acelerada sobre motor, pode não aparecer: normal).
- Mandar a `previa.mp4` para o usuário ouvir e, se ele tiver o vídeo original com som, a comparação.

Teste de referência (12/10/2026): carro saltando e derrapando até parar na frente de um homem sentado, 12 s.
Ambiente vento + marcha lenta, motor vindo, acelerada, aterrissagem em 3 partes, derrapagem, cascalho:
-14,4 LUFS, 99% do tempo com som, render em ~1,5 s.
