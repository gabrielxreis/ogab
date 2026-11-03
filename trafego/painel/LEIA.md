# Painel do Gab (tráfego)

O Gab mostra todo insight e resultado aqui: um painel local no navegador (layout de dashboard: barra lateral, seletor de cliente, busca ⌘K, Exportar CSV, abas Visão geral / Campanhas / Criativos / Parecer).

## Como abrir
O painel roda num servidor local só da sua máquina (`painel/servidor.py`, `http://127.0.0.1:47830/painel/index.html`), que o `painel.py` sobe sozinho. É ele que faz o ⬇ baixar o vídeo de verdade (aberto como arquivo, o Chrome só abria o vídeo) e monta o zip dos botões "Baixar todos" (`/zip?cliente=&ids=&nomes=&nome=`). O Chrome segura o segundo download seguido de um mesmo site até a pessoa escolher "Sempre permitir" no ícone da barra de endereço.

```
python3 ~/.claude/skills/ogab/trafego/painel/painel.py --cliente <pasta do cliente>
```
Junta `clientes/*/painel.json` em `painel/dados.js` (fora do git, com uma versão) e abre `painel/index.html` se não abriu nas últimas 6 h (`--abrir` força). A aba aberta relê `dados.js` a cada 4 s e se redesenha quando a versão muda. O seletor do topo troca de cliente. A primeira abertura baixa o mapa (precisa de internet; depois fica no navegador).

## clientes/<cliente>/painel.json (fora do git)
Modelo completo: `clientes/_exemplo/painel.json`. Campos:

| Campo | O que é |
|---|---|
| `cliente` | `id, nome, conta, conta_id, handle, iniciais, plataforma` |
| `atualizado`, `fonte` | data da leitura (AAAA-MM-DD) e de onde vieram os números |
| `periodo` | `rotulo, de, ate` |
| `plataformas` | `[{nome, ativo}]`: Meta Ads, Google Ads, TikTok Ads, YouTube... |
| `manchete` | uma frase com a conclusão (faixa azul do topo) |
| `resumo` | `titulo, subtitulo, comparacao, kpis[]`; cada KPI: `rotulo, valor, anterior, formato (brl, brl0, num, pct, comp), melhor (maior, menor, neutro), nota` |
| `serie` | `titulo, subtitulo, nota, linhas[{campo, rotulo}]` (2 linhas), `extra[{campo, rotulo, formato}]` (só no tooltip), `pontos[{mes: "AAAA-MM", ...}]` |
| `geo` | `titulo, subtitulo, nota, pontos[{rotulo, lat, lon, valor (0-1) ou texto}]` |
| `distribuicao` | `titulo, subtitulo, campo` (coluna das campanhas que agrupa o investimento, padrão `grupo`) |
| `campanhas` | `[{id, campanha, grupo, quando, resultado_tipo, resultados, custo_por_resultado, gasto, cpm, cliques_link, alcance, frequencia, orcamento_dia, parecer (bom, atenção, ruim), porque}]` |
| `parecer` | `bom[], ruim[], fazer[], lacunas[]` (frases do Gab) |
| `oferta` | `produto, preco, fonte, cpa_alvo, vendas_semana, taxa_pct`: valores iniciais da área Verba |
| `testes`, `testes_regra` | `[{nome, angulo, gancho, duracao, status}]` e a regra de pausa e vitória |
| `concorrentes` | `[{anunciante, categoria, id, desde (AAAA-MM-DD), versoes, texto, link}]`: o `link` é `https://www.facebook.com/ads/library/?id=<id>` e o botão ▶ abre o anúncio numa janela de player direto do site do Meta (nada é baixado; o endereço do vídeo do Meta expira e não é guardado) |
| `concorrentes_principais` | os 5 principais (pelo menos): `[{anunciante, page_id, foto (https://graph.facebook.com/<page_id>/picture?type=large), categoria, anuncios_ativos, principal (true no maior), porque, ganchos[], mais_antigo, pagina_biblioteca, campeoes[{id, titulo, desde, dias, motivo, link, miniatura}]}]`. `miniatura` = `../clientes/<cliente>/miniaturas/<id>.jpg` (capa do vídeo gravada por `miniaturas.py` + `capas.js`, fora do git; o `painel.py` preenche sozinho quando o arquivo existe e avisa `FALTAM_MINIATURAS`). `fora_do_ar: true` = anúncio que a Biblioteca não mostra mais (o card diz "Saiu do ar" e não cobra miniatura). Baixar: favorito "⬇ Gab" (`favorito.js`, gerado em `favorito.url.txt` e entregue ao painel em `dados.js`). `video_local` (opcional) é marcado pelo `painel.py` para todo vídeo em `clientes/<cliente>/criativos_concorrentes/concorrente_<id>.mp4` (o ícone ⬇ baixa esse arquivo; sem ele, o ícone avisa e copia o pedido ao Gab). O vídeo chega pela janelinha `painel/receber.html` + `POST /receber` do servidor. Campeão = anúncio ativo há mais tempo ou criativo mais repetido (a Biblioteca não mostra impressões de anúncio comercial). `page_id` e anúncios ativos vêm do MCP do Meta (`ads_library_search` com `page_ids`); o `page_id` de uma página nova sai do HTML do anúncio na Biblioteca (`"page_id"`) |
| `concorrentes_resumo`, `concorrentes_insights`, `concorrentes_fonte` | uma linha por anunciante (`anunciante, categoria, anuncios_lidos, desde, leitura`), as leituras do Gab e de onde veio |
| `totais` | `cpm` e outros totais da conta: a ficha da campanha compara com eles |
| `perfil` | `preenchidos, total, rotulo`: quanto do trafego.md está preenchido |

Clicar numa campanha (tabela ou Criativos) abre a ficha dela: números, comparação com as do mesmo tipo e com a média da conta, parecer e o comando para pedir ao Gab uma análise só dela.

Regras: número só do dado do usuário (regra 3 do SKILL.md); o que não foi lido fica fora ou escrito em `nota`. Sem travessão nas frases.
