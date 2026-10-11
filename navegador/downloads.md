# Download pelo navegador (Claude in Chrome)

Os conectores (MCP) de Envato, Artlist, Magnific etc. **buscam**, mas **não baixam**. Todo download é feito no Chrome do usuário, logado nas contas dele, com a extensão **Claude in Chrome**. Os arquivos caem em `~/Downloads` e a skill move para a pasta do vídeo (`brolls/take_XX.mp4`, `musica/`, `sfx/`).

Antes de baixar: o usuário precisa estar logado no site. A IA **nunca** digita senha.

## Envato Elements (vídeo, música, efeitos)

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
- Vídeo: abrir `magnific.com/app/creation/<id>` da imagem > **Create video** (só funciona depois de um zoom/screenshot da aba; clicar 2x se precisar) > **Kling 2.5 / 720p / 5 s / Unlimited**.
- O botão Generate muda de lugar com prompt longo: clicar por JS pelo texto `Generate`.
- Baixar o resultado pelo MCP (só leitura: `creations_wait` devolve a URL) e `curl`. Conferir `credits: 0` em `creations_get`.
