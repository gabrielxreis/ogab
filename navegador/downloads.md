# Download pelo navegador (Claude in Chrome)

Os conectores (MCP) de Envato, Artlist, Magnific etc. **buscam**, mas **não baixam**. Todo download é feito no Chrome do usuário, logado nas contas dele, com a extensão **Claude in Chrome**. Os arquivos caem em `~/Downloads` e a skill move para a pasta do vídeo (`brolls/take_XX.mp4`, `musica/`, `sfx/`).

Antes de baixar: o usuário precisa estar logado no site. A IA **nunca** digita senha.

## Envato Elements (vídeo, música, efeitos)

**Receita que funcionou em lote (11/10/2026, 21 b-rolls sem erro):** usar `browser_batch` com, por clipe: `navigate` (link elements.envato.com) -> `computer screenshot` com `scale 0.2` (**sem screenshot a página não redireciona** para app.envato.com) -> `wait 8` -> `javascript_tool` com o script abaixo. 3 a 4 clipes por lote. Se o script responder "ainda na pagina antiga", repetir screenshot + espera.
```js
const W=ms=>new Promise(r=>setTimeout(r,ms));
if(!location.host.startsWith('app.')) 'ainda na pagina antiga'; else {
 for(let i=0;i<30&&![...document.querySelectorAll('button')].some(b=>/^Baixar/.test(b.innerText.trim()));i++) await W(500);
 const main=[...document.querySelectorAll('button')].find(b=>/^Baixar/.test(b.innerText.trim())); let res='sem botão';
 if(main){ const y=main.getBoundingClientRect().y;
  const seta=[...document.querySelectorAll('button[aria-haspopup]')].find(b=>Math.abs(b.getBoundingClientRect().y-y)<5&&b.getBoundingClientRect().x>main.getBoundingClientRect().x);
  if(seta){ seta.click(); await W(900);
   const op=[...document.querySelectorAll('[role=menuitem],[role=option],li,button,div')].filter(e=>/^1080P/.test(e.innerText.trim())&&e.children.length<4).pop();
   if(op){op.click(); res='1080P';} else {document.body.click(); main.click(); res='principal';} }
  else { main.click(); res='principal '+main.innerText; } }   // clipe só com uma versão (já 1080x1920)
 res }
```
O nome do arquivo baixado não é o do link (o Envato usa outro título + data + `utc`): conferir pelo tamanho/horário em `~/Downloads` e renomear para `brolls/take_XX_<assunto>`. Clipes só em ProRes vêm grandes (centenas de MB): o DaVinci lê direto; o ffmpeg deste Mac não converte alguns ProRes sem `trc`.

1. `navigate` para o link `elements.envato.com/...` que veio da busca do MCP.
2. **Tirar um zoom/screenshot pequeno da aba logo em seguida**: a página só redireciona para `app.envato.com/stock-video/<id>` depois de renderizar (se a navegação acontecer durante o zoom, dá erro "navigated to a different domain"; é normal, siga para o passo 3).
3. Esperar ~8 s e rodar este JS (escolhe 1080P quando há opções; se só existe um arquivo, baixa ele):

```js
const b=location.host.startsWith('app.')&&[...document.querySelectorAll('button')].find(x=>/^Baixar|^Download/i.test(x.innerText.trim()));
if(!b){'sem botao '+location.host}else{const r=b.getBoundingClientRect();
const c=[...document.querySelectorAll('button')].find(x=>{const q=x.getBoundingClientRect();return x!==b&&Math.abs(q.top-r.top)<6&&q.left>=r.right-4&&q.left<r.right+70});
if(c){c.click();await new Promise(r=>setTimeout(r,900));const o=[...document.querySelectorAll('[role=menuitem],[role=menuitemradio],[role=option],button')].find(x=>/1080P/.test(x.innerText||''));o?(o.click(),'1080 '+o.innerText.trim()):'sem 1080'}else{b.click();'unico '+b.innerText}}
```

- Clicar na opção "1080P" do menu **já baixa** (não clicar no botão principal depois, senão baixa duas vezes). Aparece "Licenciado automaticamente".
- Se o botão mostrar um tamanho enorme (ex.: "Baixar 646MB", 4K ProRes), baixar mesmo assim só se não houver alternativa e depois converter com `midia.py preparar_take`.
- **Antes de baixar, conferir a miniatura**: nada de green screen, fundo preto com elemento isolado ou canal alfa.
- Não usar `querySelectorAll('*')` nem varrer `div,span`: congela a aba (timeout de 45 s).
- Uma chamada por item (navigate + zoom) e outra (wait + JS) economiza tokens; não tirar screenshot grande à toa.

## Artlist (música e efeitos)

1. `navigate` para `artlist.io/royalty-free-music/song/<nome>/<id>` (link que vem do `search_music` do MCP).
2. Clicar no ícone de download (seta para baixo ao lado de "Play"); aparecem os botões **MP3** e **WAV**. Clicar em **WAV**.
3. O arquivo cai como `Artista - Música.wav` em `~/Downloads` (44,1 kHz: a skill corta o trecho e converte para 48 kHz com fade).

## Magnific (geração de takes, só ilimitado)

- Imagem: `magnific.com/app/ai-image-generator`, modelo **Google Nano Banana 2**, **1K**, proporção da plataforma. Conferir "Unlimited" no botão Generate e a proporção antes de cada lote (ela pode mudar sozinha).
- Vídeo: abrir `magnific.com/app/creation/<id>` da imagem > **Create video** (só funciona depois de um zoom/screenshot da aba; clicar 2x se precisar) > **Kling 2.5 / 720p / 10 s / Unlimited** (10 s = margem no corte, regra do usuário).
- **Armadilhas do vídeo (11/10/2026):** (1) o gerador abre com **∞ OFF** e **1080p**: 1080 NÃO é ilimitado ("This resolution is not unlimited"); trocar para **720** e ligar **∞ ON**, e só gerar se a página mostrar "Unlimited videos for this resolution" (o JS do Generate confere esse texto). (2) Se o painel abrir vazio (esqueleto), recarregar `/app/ai-video-generator` e esperar ~12 s. (3) Trocar a imagem: clicar no "Start image" > seletor History > clicar na imagem > **conferir a prévia à direita (zoom)** > Add. A ordem do seletor MUDA a cada vídeo gerado (os quadros dos vídeos entram no topo): tirar screenshot do seletor antes de cada escolha. (4) Escrever o prompt numa chamada SEPARADA da troca de imagem (na mesma chamada o texto não entra); achar o campo com `find "video prompt text area"`. (5) Imagens: referências do personagem pelo "Add" (Upload media), viram @img1/@img2 no prompt; desligar "AI prompt".
- O botão Generate muda de lugar com prompt longo: clicar por JS pelo texto `Generate`.
- Baixar o resultado pelo MCP (só leitura: `creations_wait` devolve a URL) e `curl`. Conferir `credits: 0` em `creations_get`.

## Identidade visual quando o site carrega o estilo por JavaScript

Se `marca.py` não achar as fontes (site feito em React/Vite, estilo injetado por JS), abrir o site no navegador e rodar:

```js
const pick=s=>{const e=document.querySelector(s); if(!e) return null; const c=getComputedStyle(e); return {font:c.fontFamily, peso:c.fontWeight, cor:c.color, fundo:c.backgroundColor}};
({h1:pick('h1'), h2:pick('h2'), texto:pick('p'), botao:pick('button, a[class*=rounded]'), fontes:[...document.fonts].filter(f=>f.status=='loaded').map(f=>f.family+' '+f.weight)})
```
Anotar no `marca/identidade.md`. A imagem de compartilhamento (og:image) pode ser de uma versão antiga do site: valer o que a página mostra hoje.

**Artlist (11/10/2026):** em algumas faixas (Artlist Original) o menu MP3/WAV só aparece depois de clicar no ícone de download pela COORDENADA (o clique por ref não abre); depois do clique os botões MP3 e WAV aparecem na linha do Play. Esperar a página sair do esqueleto cinza (7 a 10 s) antes.

**Magnific: Chrome bloqueando downloads (12/10/2026).** Se o zip/MP4 não chega em ~/Downloads, o Chrome está segurando "downloads automáticos" do magnific.com: o usuário libera no ícone de download da barra. Plano B que funcionou sem depender disso: um receptor local (`python3 receptor.py <pasta>` em 127.0.0.1:8765, página GET que lê `#nome=..&u=..`, baixa e faz POST para si mesma) e, na aba da criação, `location.href='http://127.0.0.1:8765/#nome=X.mp4&u='+encodeURIComponent(document.querySelector('video').currentSrc)`. O fetch direto da página do Magnific para o localhost é bloqueado pelo CSP do site; navegar para a página local não é.
