# Preset MIMIC (teatrinho de bonecos de papel)

O vídeo inteiro acontece num **palco de teatro de papel**: cortina azul de veludo nas laterais, bambolina com franja
dourada em cima, chão de tábuas, holofote com poeira no facho e, no gancho, a plateia de costas. Cada frase vira uma
**placa de papel creme pendurada em dois barbantes**: desce do urdimento, balança como pêndulo e assenta, com a linha
pequena em sans e a linha grande em serifa vermelha; a passagem (ex.: "Mateus 26:52") vem numa plaquinha pendurada
embaixo. **Bonecos de papel** (sem rosto, cabeça redonda, túnica chapada, varetas nos pés) sobem do alçapão, mudam de
pose, andam e caem. Na troca de cena, o **cenário pintado desce de cima como telão**; sol, lua e nuvens descem no
barbante. A última cena fecha a cortina e a placa do CTA desce na frente.

Serve para história bíblica, parábola, "o que Jesus diria", fábula, lição de moral, história contada para criança,
devocional, curiosidade histórica com personagens. Não serve para dado frio, produto, tecnologia nem marca de luxo.

**Referência:** linguagem estudada num Reels de teatro bíblico de papel (@teatrobiblico, 27/10/2026): placa no
barbante que cai e balança, placas empilhadas (a segunda morde a primeira), plaquinha da referência, cenário que troca
por telão, cortina azul com franja dourada. Desenho, personagens e código são nossos; nada do vídeo original é usado.

**Diferença do LÚDICO:** o lúdico é 3D com câmera voando entre cenários. O mimic é 2D chapado, frontal, câmera fixa
no palco (só um empurrão leve de 2% por cena), e o texto é sempre uma placa física pendurada.

Exemplo: `exemplo.mp4` / `exemplo.gif` (13,2 s, 1080x1920): Davi e Golias em 4 cenas ("O que você faz / diante de um
gigante?", "ele pegou cinco pedras" 1 Samuel 17:40, "uma pedra só / e o gigante caiu" 1 Samuel 17:49, "Segue o
perfil"). Plano em `exemplo/plano.json`.

## Como pedir
`/ogab faz um reels no preset mimic sobre <história>` (ou `preset: mimic` no estilo.md do cliente).

## Processo (o que o Gab faz)
1. Roteiro curto (15-60 s) com narração. Cada frase vira 1 placa: linha pequena (até 4 palavras) + linha grande (até
   3 palavras, a palavra que importa). Pergunta do gancho pode virar 2 placas empilhadas. Passagem bíblica na `ref`.
   Conferir toda referência bíblica (livro, capítulo e versículo) antes de pôr na placa: fato aprovado.
2. Para cada cena: qual cenário (`noite`, `jardim`, `por_do_sol`, `dia`, `palacio`, `creme`, `campo`, `deserto`),
   quem está no palco (personagens prontos: `povo`, `jesus`, `discipulo`, `soldado`, `rei`, `diabo`, `menino`,
   `pessoa`, `gigante`; cada campo pode ser trocado: roupa, cabelo, barba, manto, chapéu, objeto) e o que eles FAZEM
   na palavra forte (pose, andar, cair). Adereço quando a frase tem um objeto (sol, lua, balão com palavra, trono,
   urna, pomba voando, estrela, saco de dinheiro, chuva de notas, relógio, gráfico de candles, quadro com texto,
   calendário, seta subindo/caindo, mesa de trader com telas). TODA fala com objeto ou ideia concreta ganha adereço
   (pedido do Gabriel 29/10: "falta objetos no cenário que faz alusão à fala").
   - `cai: true`: o adereço cai do céu e quica no chão; `estoura_em: <s>` estoura com pop (fumaça + notas voando),
     `some_em: <s>` desce pelo alçapão. Perder tudo = sacos caindo e depois estourando.
   - `chuva` (`em`, `ate`, `n`, `estoura_em`); `relogio` (`raio`, `check`: selo verde em s); `grafico` (`sobe`,
     `dur_velas`); `quadro` (`texto` "linha|linha", `passo`); `calendario` (`texto` "MÊS|DIA"); `seta` (`dir`
     "baixo"); `mesa` (`telas`: lista de x) com boneco `sentado: true` atrás; `frente: true` desenha na frente dos
     bonecos (padrão da mesa e da chuva).
3. Tempos pela fala: `"transcricao": "tr.json"` no plano e `"em": "<palavra>"` em placas, bonecos e ações.
4. `python3 SKILL_DIR/presets/mimic/gerar.py plano.json <pasta>/motions/mimic [--tema <marca>] --render <pasta>/motions/mimic.mp4 [--gif]`
   (formato do plano na docstring do `gerar.py`). Ele RECUSA cena com mais de 4,5 s sem nada novo (`CENA_PARADA`,
   regra "tela sempre mudando"; o CTA final pode ir a 7 s): quebrar a frase em 2 placas ou pôr uma ação de boneco.
5. Conferir: `npx --yes $(python3 SKILL_DIR/scripts/componentes.py hf) snapshot <pasta> --at ...`,
   `scripts/storyboard.py`, `scripts/grade.py <mp4> --passo 0.5` e `scripts/revisor.py <mp4> --pasta <pasta>`.

## Tema (cor da marca)
`temas/padrao.json`: `acento` (linha grande da placa: a cor da marca entra aqui), `tinta` (linha pequena), `papel` e
`papel_borda` (placa), `cortina`/`cortina_escura` (veludo), `dourado` (franja, corda, coroa), `madeira` (chão) e as
fontes (`fonte_titulo` Cardo Bold, `fonte_texto` Inter Tight; caminho absoluto vai junto para a pasta). Marca nova:
copiar para `temas/<marca>.json` e passar `--tema <marca>`.

## Regras de bom gosto
- Uma placa por vez (no máximo 2 empilhadas); ela fica na faixa de cima do palco, nunca na frente dos bonecos.
- Gancho nunca vazio: primeira placa e boneco principal com `em` -0,25 s (no quadro 0 já estão no meio da descida/subida, com a cortina abrindo).
- No máximo 3 bonecos por cena; o principal no facho do holofote (perto do centro).
- Cada frase com uma ação: quem fala aponta, quem perde cai, quem comemora levanta os braços. Boneco parado a cena
  toda é cena morta.
- Cenário muda quando a história muda de lugar ou de tempo (noite > pôr do sol > dia), não a cada frase.
- Som: barbante/madeira rangendo quando a placa desce, "pop" de papel quando o boneco sobe, tecido da cortina no
  começo e no fim, caixinha de música ou cordas leves de fundo.

## Créditos
- Fontes: Cardo (David J. Perry, SIL OFL 1.1) e Inter Tight (The Inter Project Authors, SIL OFL 1.1), em `kit/fontes/`.
- Cenários, palco, bonecos e adereços: desenhados em código pelo `kit/mimic.js` (sem imagem de terceiros).
- Fatos do exemplo: 1 Samuel 17:40 (Davi escolhe cinco pedras lisas do ribeiro) e 17:49 (a pedra acerta a testa de
  Golias, que cai com o rosto em terra).
