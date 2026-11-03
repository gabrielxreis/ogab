# Mudanças da Mariana

## 0.6.1 (22/10/2026)
- LinkedIn: mensagem para recrutador que acabou de publicar uma vaga (editor, filmmaker, social media), em português e inglês. Manda cedo, reforça a candidatura oficial e liga um resultado seu ao que a vaga pede; nada de "tenho interesse" no post.

## 0.6.0 (22/10/2026)
- Removida a automação antiga do LinkedIn (robô de navegador e login por senha no painel e no setup): a Mariana só escreve, você envia
- Aquecimento: comentário num post do lead antes do convite (`mariana linkedin aquecer`); o convite espera 2 dias
- Momento certo: vaga de vídeo ou social media, evento anunciado e cargo novo de marketing põem o lead no topo, com a mensagem citando o motivo (`mariana linkedin momento`)
- Vídeo de oi de 20 s com o Gab para quem aceitou o convite (`mariana linkedin video`)
- Pós-job pede também recomendação no LinkedIn, com texto sugerido
- Calendário de posts: 3 por semana, bastidor, case e antes e depois (só com permissão do cliente)
- Nota do perfil de 0 a 100, antes e depois (`mariana linkedin nota`)
- Conta protegida: limite semanal de convites (80), convite só depois do aceite libera a mensagem, aviso para retirar convites com mais de 21 dias
- Números por estilo de abertura, e a Mariana prefere o que mais responde

## 0.5.0 (22/10/2026)
- Dossiê: `mariana dossie` junta o que o ChatGPT, o claude.ai e a memória do Claude Code já sabem sobre você
- LinkedIn: perfil otimizado pronto para colar (PT e EN), posts dos trabalhos e fila de disparo em lote com limite diário
- Foto de perfil com IA: ficha de personagem a partir das fotos reais e 10 estilos para escolher (`mariana fotos`)
- Ficha de conversa por lead: gostos com a fonte, quebra-gelo e os 3 trabalhos certos para mostrar
- Amostra "antes e depois": o Gab refaz um vídeo fraco do lead e a Mariana oferece a edição grátis

## 0.4.0 (17/10/2026)
- Tudo em português: painel, terminal, documentação, prompts, base de conhecimento e registros
- Cada mensagem sai no idioma do país da empresa (pelo DDI, domínio e cidade): português, espanhol, inglês, francês, alemão, italiano...
- Propostas também em espanhol e francês; horários da agenda em espanhol e francês; radar de eventos busca em espanhol
- Lotes de email separados por idioma; Números por país
- O primeiro `mariana run` abre o onboarding

## 0.3.0 (16/10/2026)
- Sugestão de preço pelo histórico de jobs fechados (marcada para conferir na proposta)
- Follow-up de proposta: lembrete leve após 3 dias e outro após mais 5, se não houver resposta
- "Fechou" cria a pasta do cliente na pasta do /ogab, com `<Cliente>.md` (memória da marca) e `briefing-*.md`
- Produção: data, endereço, contato e checklist; aviso na véspera + rascunho de confirmação ao cliente; aviso de entrega
- Rodadas de revisão contadas, com aviso e rascunho educado quando passar do combinado
- Instalador de uma linha e atualização automática da skill

## 0.2.0
- Respostas no WhatsApp/LinkedIn/Instagram param os emails e viram rascunho de resposta
- Proposta em PDF, Google Agenda real, portfólio por segmento, radar de eventos, amostras com o /ogab, pós-job, avisos no celular, abas Jobs e Números

## 0.1.0
- Primeira versão: onboarding, assinatura de email, email-check, canais por mercado (Brasil WhatsApp, exterior LinkedIn), sinais de audiovisual
