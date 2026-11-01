Especificação: Cervejaria Artesanal em Tempo Real
Trabalho 01 · Programação Orientada a Eventos · LPP 2026/2
Tipo de vila: Cervejaria artesanal (sorteio nº 9)
Equipe: Kauan Faust e Anderson Moreira
> Este documento descreve \*\*o quê\*\* e \*\*o porquê\*\*. Nenhuma tecnologia é citada aqui.
> Ele deve ser commitado \*\*antes\*\* de qualquer código.
1. Visão geral
Vários jogadores acessam a mesma cervejaria ao mesmo tempo. Cada ação feita por um jogador
é decidida pelo servidor, e todos veem o resultado na hora, sem recarregar a página.
Objetivo do sistema: mostrar um fluxo de programa controlado por eventos, em que o
cliente pede, o servidor decide e todos reagem ao fato confirmado.
Papéis
Papel	O que pode fazer
Mestre	Abre e encerra a temporada
Jogador (cervejeiro)	Pede para construir e para engarrafar lotes
Recursos
Recurso	Tipo	Descrição
Cevada	primário	Produzida automaticamente a cada intervalo; é gasta nas construções
Cerveja	refinado	Lotes gerados quando uma construção de produção termina; precisam ser engarrafados
Construções
Maltaria, tanques de fermentação e adega. Cada construção custa cevada, ocupa um
cervejeiro durante a obra e, ao terminar, aumenta a produção de cevada.
2. Regras e números
Regra	Valor
Cevada inicial	150
Custo de cada construção	50 de cevada
Tempo de uma obra	8 segundos
Intervalo entre produções de cevada	5 segundos
Cevada produzida por intervalo (inicial)	10
Ganho de produção por obra concluída	+5 de cevada por intervalo
Limite de cervejeiros ocupados ao mesmo tempo	2
Prazo para engarrafar um lote pronto	20 segundos
R1. Só o Mestre abre ou encerra a temporada.
R2. Ações de construir e engarrafar só são aceitas com a temporada aberta.
R3. Construir exige cevada suficiente e cervejeiro livre.
R4. Uma recusa é informada somente a quem fez o pedido.
R5. Quando dois jogadores disputam o último recurso ou o último cervejeiro, o servidor
decide um pedido de cada vez: um é aceito e o outro é recusado.
R6. Ao terminar uma obra, o cervejeiro volta a ficar livre, a produção de cevada
aumenta e um lote de cerveja fica pronto para engarrafar.
R7. Um lote que não for engarrafado dentro do prazo passa do ponto e é perdido.
R8. Ao encerrar a temporada, novos pedidos são recusados e as contagens param.
3. Tabela de eventos
Padrão de nomes: `objeto.acao\_no\_passado` para o que o servidor confirma e
`objeto.acao\_solicitada` para o que o cliente pede.
Evento	Quem emite	Quem recebe	O que muda
`estado.sincronizado`	Servidor	Só o cliente recém-conectado	O cliente recebe o estado atual
`cervejaria.abertura\_solicitada`	Mestre	Servidor	Pedido para abrir a temporada
`cervejaria.iniciada`	Servidor	Todos	Temporada aberta; a produção de cevada começa
`construcao.solicitada`	Jogador	Servidor	Pedido para construir
`construcao.iniciada`	Servidor	Todos	Debita o custo, ocupa um cervejeiro e inicia a obra
`operacao.recusada`	Servidor	Só quem pediu	Faltou cevada ou cervejeiro, ou a temporada não está aberta
`recurso.produzido`	Servidor (temporizador)	Todos	O estoque de cevada sobe
`construcao.concluida`	Servidor (temporizador)	Todos	A obra termina, o cervejeiro fica livre, a produção aumenta e surge um lote
`cervejaria.encerramento\_solicitado`	Mestre	Servidor	Pedido para encerrar a temporada
`cervejaria.encerrada`	Servidor	Todos	Temporada encerrada; novas ações são recusadas
Evento próprio da equipe: lote que passa do ponto
Evento	Quem emite	Quem recebe	O que muda
`lote.pronto`	Servidor (temporizador)	Todos	Um lote de cerveja fica disponível e o prazo de engarrafamento começa
`engarrafamento.solicitado`	Jogador	Servidor	Pedido para engarrafar um lote pronto
`lote.engarrafado`	Servidor	Todos	O lote deixa de estar pendente e a cerveja é somada ao estoque
`lote.perdido`	Servidor (temporizador)	Todos	O prazo acabou sem engarrafar; o lote passa do ponto e é descartado
4. Histórias priorizadas
História 1 (P1): Abrir a temporada e ver o estado em tempo real
O Mestre abre a temporada e todos os conectados passam a ver a cervejaria aberta.
Teste independente: duas pessoas conectadas veem a mudança de fase ao mesmo tempo.
História 2 (P1): Construir
O Jogador pede para construir; se houver cevada e cervejeiro livre, todos veem a obra começar.
Teste independente: estoque e cervejeiros ocupados mudam para todos.
História 3 (P1): Passagem do tempo
A cevada sobe sozinha a cada intervalo e a obra termina sozinha depois de alguns segundos.
História 4 (P2): Engarrafar antes de passar do ponto
Quando uma obra termina, surge um lote de cerveja. O Jogador pede para engarrafar antes do prazo.
História 5 (P2): Encerrar a temporada
O Mestre encerra e novas ações são recusadas.
5. Requisitos
FR-001: O sistema DEVE permitir ao Mestre abrir e encerrar a temporada, e recusar esses pedidos de qualquer Jogador.
FR-002: O sistema DEVE entregar o estado atual apenas ao cliente que acabou de conectar.
FR-003: O sistema DEVE aceitar um pedido de construção somente com a temporada aberta, cevada suficiente e cervejeiro livre.
FR-004: O sistema DEVE informar a recusa somente a quem fez o pedido, com o motivo.
FR-005: O sistema DEVE tratar pedidos simultâneos um de cada vez, de modo que o estoque nunca fique negativo e os cervejeiros ocupados nunca passem do limite.
FR-006: O sistema DEVE aumentar a cevada a cada intervalo e avisar todos, sem ninguém pedir.
FR-007: O sistema DEVE concluir cada obra sozinho após o tempo definido, liberando o cervejeiro e avisando todos.
FR-008: O sistema DEVE gerar um lote de cerveja ao concluir uma obra e avisar todos.
FR-009: O sistema DEVE descartar um lote não engarrafado no prazo e avisar todos.
FR-010: O sistema DEVE recusar qualquer novo pedido de construir ou engarrafar depois do encerramento.
FR-011: O sistema DEVE mostrar, para cada evento emitido ou escutado, o nome, o horário, os dados, a causa e a reação do cliente.
FR-012: O sistema DEVE exibir o nome dos desenvolvedores no rodapé.
FR-013 (dupla): O sistema DEVE mostrar quantas vezes cada evento já ocorreu.
6. Cenários de teste
Cenário 1: Recusa
Dado que a temporada ainda não foi aberta,
quando o Jogador A emite `construcao.solicitada`,
então o servidor emite `operacao.recusada` apenas para o Jogador A, com o motivo
"A temporada não está aberta", e nenhum outro participante recebe nada.
Cenário 2: Passagem do tempo
Dado que a temporada está aberta e o Jogador A emitiu `construcao.solicitada` aceito,
quando passam os segundos de uma obra e os intervalos de produção,
então o servidor emite `recurso.produzido` a cada intervalo (causa: temporizador) para todos
e, ao fim da obra, emite `construcao.concluida` para todos, com o cervejeiro livre e a produção maior.
Cenário 3: Disputa
Dado que há 1 de 2 cervejeiros ocupados e cevada suficiente,
quando os jogadores A e B emitem `construcao.solicitada` ao mesmo tempo,
então o servidor emite `construcao.iniciada` para todos (referente a um deles) e
`operacao.recusada` apenas para o outro, e os cervejeiros ocupados ficam em 2 de 2.
Cenário 4 (evento próprio): Lote que passa do ponto
Dado que uma obra terminou e `lote.pronto` foi emitido,
quando ninguém emite `engarrafamento.solicitado` durante o prazo,
então o servidor emite `lote.perdido` para todos e o lote deixa de poder ser engarrafado.
7. Casos de borda
Pedido de construir exatamente com a cevada igual ao custo: deve ser aceito.
Pedido de engarrafar um lote que já foi perdido ou já foi engarrafado: recusado.
Mestre pedindo para abrir uma temporada já aberta: recusado.
Obra em andamento quando a temporada é encerrada: não gera novos fatos após o encerramento.
Jogador desconectado durante uma obra: a obra continua e termina normalmente.
8. Critérios de sucesso
SC-001: Em duas abas, uma mudança de estado aparece na outra em menos de 1 segundo.
SC-002: O estoque de cevada nunca fica negativo, mesmo com cliques simultâneos.
SC-003: Cada evento da tabela aparece no Painel de eventos com emit/on, causa e reação.
9. Fora de escopo
Login e senha, banco de dados, publicação na internet, pagamento ou multa por lote perdido.
10. Decisões da equipe (dúvidas resolvidas)
O lote perdido apenas desaparece; não reduz nenhum recurso nem gera multa.
Engarrafar um lote soma 1 cerveja ao estoque de cerveja engarrafada.
Vários lotes podem ficar pendentes ao mesmo tempo, cada um com o seu próprio prazo de 20 segundos.