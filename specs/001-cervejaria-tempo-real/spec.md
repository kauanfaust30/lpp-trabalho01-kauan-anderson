# Feature Specification: Cervejaria Artesanal em Tempo Real

**Feature Branch**: `main` (sem branch dedicada)

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Use o conteúdo de docs/especificacao.md como base. Quero uma
cervejaria artesanal cooperativa em tempo real: o Mestre abre e encerra a temporada, os
Jogadores (cervejeiros) constroem maltaria, tanques e adega gastando cevada e ocupando
cervejeiros; a cevada é produzida sozinha a cada intervalo; cada obra termina sozinha e gera um
lote de cerveja que passa do ponto se não for engarrafado a tempo. Recusas só vão para quem
pediu e, em disputa, só um pedido vence. O objetivo é mostrar um fluxo controlado por eventos."

**Documento base**: [docs/especificacao.md](../../docs/especificacao.md)

## Clarifications

### Session 2026-10-31

- Q: Depois de encerrada, o Mestre pode abrir uma nova temporada sem reiniciar o servidor? → A: Não; "encerrada" é final, recomeçar exige reiniciar o servidor.
- Q: Quantos participantes podem estar como Mestre ao mesmo tempo? → A: Só um por vez; um segundo Mestre é recusado e precisa entrar como Jogador.
- Q: Ao encerrar a temporada, o que acontece com obras em andamento e lotes pendentes? → A: Tudo fica congelado como está; só `cervejaria.encerrada` é emitido.
- Q: Quem pode pedir para engarrafar um lote: só Jogadores ou o Mestre também? → A: Só Jogadores; pedido do Mestre é recusado (mesma regra de construir).

## Visão geral

Vários participantes acessam a mesma cervejaria ao mesmo tempo, de forma cooperativa: todos
compartilham o mesmo estoque de cevada, os mesmos cervejeiros e os mesmos lotes. O cliente
apenas **pede**; o servidor **decide** e anuncia o **fato** confirmado; todos **reagem** ao fato.
Fatos que nascem da passagem do tempo (produção de cevada, fim de obra, lote que passa do ponto)
acontecem sem que ninguém peça.

### Papéis

| Papel | O que pode fazer |
|-------|------------------|
| Mestre | Abrir e encerrar a temporada |
| Jogador (cervejeiro) | Pedir para construir (maltaria, tanque de fermentação, adega) e para engarrafar lotes |

### Regras e números

| Regra | Valor |
|-------|-------|
| Cevada inicial | 150 |
| Custo de cada construção | 50 de cevada |
| Tempo de uma obra | 8 segundos |
| Intervalo entre produções de cevada | 5 segundos |
| Cevada produzida por intervalo (inicial) | 10 |
| Ganho de produção por obra concluída | +5 de cevada por intervalo |
| Limite de cervejeiros ocupados ao mesmo tempo | 2 |
| Prazo para engarrafar um lote pronto | 20 segundos |
| Cerveja engarrafada inicial | 0 |
| Cerveja somada por lote engarrafado | 1 |

### Eventos (pedidos e fatos)

Convenção de nomes: `objeto.acao_solicitada` para o pedido do cliente e
`objeto.acao_no_passado` para o fato confirmado pelo servidor.

| Evento | Tipo | Quem emite | Quem recebe | O que muda |
|--------|------|-----------|-------------|-----------|
| `estado.sincronizado` | fato | Servidor | Só o recém-conectado | O cliente recebe o estado atual |
| `cervejaria.abertura_solicitada` | pedido | Mestre | Servidor | Pedido para abrir a temporada |
| `cervejaria.iniciada` | fato | Servidor | Todos | Temporada aberta; a produção de cevada começa |
| `construcao.solicitada` | pedido | Jogador | Servidor | Pedido para construir |
| `construcao.iniciada` | fato | Servidor | Todos | Debita o custo, ocupa um cervejeiro e inicia a obra |
| `operacao.recusada` | fato | Servidor | Só quem pediu | Pedido negado, com motivo |
| `recurso.produzido` | fato | Servidor (tempo) | Todos | O estoque de cevada sobe |
| `construcao.concluida` | fato | Servidor (tempo) | Todos | Cervejeiro livre e produção maior |
| `lote.pronto` | fato | Servidor (tempo) | Todos | Lote disponível; começa o prazo de engarrafamento |
| `engarrafamento.solicitado` | pedido | Jogador | Servidor | Pedido para engarrafar um lote |
| `lote.engarrafado` | fato | Servidor | Todos | Lote sai da lista de pendentes; cerveja +1 |
| `lote.perdido` | fato | Servidor (tempo) | Todos | Prazo esgotado; lote descartado |
| `cervejaria.encerramento_solicitado` | pedido | Mestre | Servidor | Pedido para encerrar a temporada |
| `cervejaria.encerrada` | fato | Servidor | Todos | Temporada encerrada; novas ações recusadas |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abrir a temporada e ver o estado em tempo real (Priority: P1)

Um participante entra na cervejaria, escolhe seu papel e recebe imediatamente o estado atual.
O Mestre abre a temporada e todos os conectados passam a ver a cervejaria aberta.

**Why this priority**: sem estado sincronizado e sem temporada aberta nenhuma outra ação é
possível; é a base do fluxo "pede → decide → todos reagem".

**Independent Test**: duas abas conectadas (Mestre e Jogador); o Mestre abre a temporada e as
duas abas mostram a mudança de fase ao mesmo tempo.

**Acceptance Scenarios**:

1. **Given** um participante que acabou de conectar, **When** a conexão se completa, **Then**
   apenas ele recebe `estado.sincronizado` com fase, cevada, produção, cervejeiros ocupados,
   obras, lotes pendentes e cerveja engarrafada.
2. **Given** a temporada ainda não aberta, **When** o Mestre emite
   `cervejaria.abertura_solicitada`, **Then** todos recebem `cervejaria.iniciada`.
3. **Given** a temporada não aberta, **When** um Jogador emite `cervejaria.abertura_solicitada`,
   **Then** só ele recebe `operacao.recusada` com o motivo "Apenas o Mestre pode abrir a
   temporada." e nada muda para os demais.
4. **Given** a temporada já aberta, **When** o Mestre pede para abrir de novo, **Then** só ele
   recebe `operacao.recusada` ("A temporada já está aberta.").
5. **Given** já existe um Mestre conectado, **When** outro participante tenta entrar como
   Mestre, **Then** só ele recebe `operacao.recusada` ("Já existe um Mestre na cervejaria. Entre
   como Jogador.") e não entra; os demais não recebem nada.
6. **Given** o Mestre se desconectou, **When** outro participante entra como Mestre, **Then** a
   entrada é aceita normalmente.

---

### User Story 2 - Construir (Priority: P1)

O Jogador pede para construir uma maltaria, um tanque de fermentação ou uma adega. Se a
temporada estiver aberta, houver cevada suficiente e um cervejeiro livre, todos veem a obra
começar, o estoque cair e um cervejeiro ficar ocupado.

**Why this priority**: é a principal ação do jogador e a que demonstra validação no servidor,
recusa individual e disputa.

**Independent Test**: com a temporada aberta, um Jogador pede uma construção; o estoque e os
cervejeiros ocupados mudam em todas as abas.

**Acceptance Scenarios**:

1. **Given** temporada aberta, 150 de cevada e 0 de 2 cervejeiros ocupados, **When** o Jogador A
   emite `construcao.solicitada` (maltaria), **Then** todos recebem `construcao.iniciada`, a
   cevada passa a 100 e os ocupados passam a 1 de 2.
2. **Given** a temporada não aberta, **When** o Jogador A emite `construcao.solicitada`,
   **Then** só o Jogador A recebe `operacao.recusada` ("A temporada não está aberta.") e nenhum
   outro participante recebe nada.
3. **Given** temporada aberta e 40 de cevada, **When** o Jogador pede uma construção, **Then**
   só ele recebe `operacao.recusada` informando quanto falta ("Cevada insuficiente: faltam 10.
   Aguarde a próxima colheita.").
4. **Given** 2 de 2 cervejeiros ocupados, **When** o Jogador pede uma construção, **Then** só
   ele recebe `operacao.recusada` ("Nenhum cervejeiro livre. Aguarde uma obra terminar.").
6. **Given** temporada aberta, **When** o Mestre emite `construcao.solicitada`, **Then** só ele
   recebe `operacao.recusada` ("Apenas Jogadores podem construir.") e nada muda.
5. **Given** 1 de 2 cervejeiros ocupados e cevada suficiente para uma obra, **When** os
   Jogadores A e B pedem ao mesmo tempo, **Then** todos recebem um único `construcao.iniciada`
   (de um deles), só o outro recebe `operacao.recusada`, e os ocupados ficam em 2 de 2.

---

### User Story 3 - Passagem do tempo (Priority: P1)

Com a temporada aberta, a cevada sobe sozinha a cada intervalo e cada obra termina sozinha
depois do tempo definido, liberando o cervejeiro e aumentando a produção.

**Why this priority**: demonstra fatos gerados pelo tempo, sem pedido de ninguém — essência do
fluxo controlado por eventos.

**Independent Test**: com a temporada aberta, observar sem clicar em nada: a cevada sobe a cada
5 segundos em todas as abas; uma obra iniciada termina após 8 segundos.

**Acceptance Scenarios**:

1. **Given** temporada aberta com produção de 10, **When** passa um intervalo de 5 segundos,
   **Then** todos recebem `recurso.produzido` e a cevada sobe 10.
2. **Given** uma obra iniciada, **When** passam 8 segundos, **Then** todos recebem
   `construcao.concluida`, o cervejeiro fica livre e a produção por intervalo sobe 5.
3. **Given** a temporada não aberta, **When** o tempo passa, **Then** nenhuma cevada é
   produzida.

---

### User Story 4 - Engarrafar antes de passar do ponto (Priority: P2)

Quando uma obra termina, surge um lote de cerveja. Qualquer Jogador pode pedir para engarrafá-lo
dentro do prazo; se ninguém o fizer, o lote passa do ponto e é perdido.

**Why this priority**: é o evento próprio da equipe; acrescenta um prazo controlado pelo tempo e
uma nova disputa, mas depende das histórias P1.

**Independent Test**: concluir uma obra, ver o lote aparecer em todas as abas, engarrafá-lo e
ver a cerveja subir; repetir sem engarrafar e ver o lote sumir após 20 segundos.

**Acceptance Scenarios**:

1. **Given** uma obra concluída, **When** o servidor confirma a conclusão, **Then** todos
   recebem `lote.pronto` com o identificador do lote e o prazo de 20 segundos.
2. **Given** um lote pronto dentro do prazo, **When** um Jogador emite
   `engarrafamento.solicitado`, **Then** todos recebem `lote.engarrafado` e a cerveja
   engarrafada sobe 1.
3. **Given** um lote pronto, **When** ninguém pede o engarrafamento em 20 segundos, **Then**
   todos recebem `lote.perdido` e o lote deixa de poder ser engarrafado.
4. **Given** um lote já engarrafado ou já perdido, **When** um Jogador pede para engarrafá-lo,
   **Then** só ele recebe `operacao.recusada` ("Este lote não está mais disponível.").
5. **Given** um lote pronto, **When** dois Jogadores pedem para engarrafá-lo ao mesmo tempo,
   **Then** só um `lote.engarrafado` é emitido e o outro Jogador recebe `operacao.recusada`.
6. **Given** um lote pronto, **When** o Mestre emite `engarrafamento.solicitado`, **Then** só ele
   recebe `operacao.recusada` ("Apenas Jogadores podem engarrafar.") e o lote continua pendente.

---

### User Story 5 - Encerrar a temporada (Priority: P2)

O Mestre encerra a temporada; todos veem a cervejaria encerrada, novos pedidos são recusados e
as contagens de tempo param.

**Why this priority**: fecha o ciclo da temporada; útil para a demonstração, mas não bloqueia
as demais histórias.

**Independent Test**: com a temporada aberta e obras/lotes em andamento, o Mestre encerra; as
abas mostram a temporada encerrada e nenhum novo fato de tempo aparece depois.

**Acceptance Scenarios**:

1. **Given** temporada aberta, **When** o Mestre emite `cervejaria.encerramento_solicitado`,
   **Then** todos recebem `cervejaria.encerrada`.
2. **Given** temporada encerrada, **When** um Jogador pede para construir ou engarrafar,
   **Then** só ele recebe `operacao.recusada` ("A temporada está encerrada.").
3. **Given** obras e lotes em andamento, **When** a temporada é encerrada, **Then** nenhum
   `recurso.produzido`, `construcao.concluida`, `lote.pronto` ou `lote.perdido` é emitido depois.
4. **Given** temporada aberta, **When** um Jogador pede para encerrar, **Then** só ele recebe
   `operacao.recusada` ("Apenas o Mestre pode encerrar a temporada.").
5. **Given** temporada encerrada, **When** o Mestre emite `cervejaria.abertura_solicitada`,
   **Then** só ele recebe `operacao.recusada` ("A temporada já foi encerrada. Reinicie o
   servidor para começar outra.") e a fase continua encerrada.

---

### User Story 6 - Painel de eventos (Priority: P2)

Cada participante vê um painel listando os eventos emitidos e recebidos pela sua aba, com
contagem por tipo de evento, para entender o fluxo orientado a eventos.

**Why this priority**: torna o paradigma visível na demonstração; não altera regras do jogo.

**Independent Test**: realizar qualquer ação e verificar que o painel registra o pedido e o
fato correspondente com nome, horário, dados, causa e reação, e que o contador do evento sobe.

**Acceptance Scenarios**:

1. **Given** um participante conectado, **When** sua aba emite ou recebe qualquer evento,
   **Then** o painel mostra nome, horário, dados, causa (pedido de alguém ou temporizador),
   direção (emitido/recebido) e a reação da tela.
2. **Given** eventos já ocorridos, **When** um novo evento do mesmo tipo acontece, **Then** o
   contador daquele tipo aumenta em 1.
3. **Given** qualquer tela da aplicação, **When** o participante olha o rodapé, **Then** vê o
   nome dos desenvolvedores (Kauan Faust e Anderson Moreira).

### Edge Cases

- Pedido de construção com cevada exatamente igual ao custo (50): aceito, e a cevada vai a 0.
- Pedido de engarrafar um lote já perdido ou já engarrafado: recusado só para quem pediu.
- Mestre pedindo para abrir uma temporada já aberta, ou encerrar uma não aberta: recusado.
- Obra em andamento ou lote pendente quando a temporada é encerrada: ficam congelados e
  continuam aparecendo como estavam; não geram conclusão, lote nem perda depois do encerramento.
- Jogador desconectado durante uma obra: a obra continua e termina normalmente para os demais.
- Participante que conecta no meio da temporada: recebe o estado atual, incluindo obras e lotes
  pendentes com o tempo restante.
- Vários lotes pendentes ao mesmo tempo: cada um tem seu próprio prazo de 20 segundos.
- Dois participantes tentando entrar como Mestre ao mesmo tempo, sem Mestre conectado: só um
  entra como Mestre; o outro é recusado.
- Mestre que se desconecta com a temporada aberta: a temporada continua; a vaga de Mestre fica
  livre para outro participante.
- Pedido com tipo de construção desconhecido ou lote inexistente: recusado com motivo claro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que somente o Mestre abra e encerre a temporada,
  recusando esses pedidos vindos de Jogadores. As fases seguem só a ordem não aberta → aberta →
  encerrada; "encerrada" é final e qualquer pedido de abertura nela é recusado.
- **FR-002**: O sistema MUST entregar o estado atual apenas ao participante que acabou de
  conectar.
- **FR-003**: O sistema MUST aceitar um pedido de construção somente com a temporada aberta,
  cevada maior ou igual ao custo e ao menos um cervejeiro livre.
- **FR-004**: O sistema MUST informar toda recusa somente a quem fez o pedido, com um motivo em
  português que diga o que aconteceu e o que fazer.
- **FR-005**: O sistema MUST decidir pedidos simultâneos um de cada vez, de modo que a cevada
  nunca fique negativa, os cervejeiros ocupados nunca passem de 2 e um lote nunca seja
  engarrafado mais de uma vez.
- **FR-006**: O sistema MUST aumentar a cevada a cada 5 segundos, na produção vigente, e avisar
  todos, apenas enquanto a temporada estiver aberta.
- **FR-007**: O sistema MUST concluir cada obra sozinho 8 segundos após o início, liberando o
  cervejeiro, somando +5 à produção por intervalo e avisando todos.
- **FR-008**: O sistema MUST gerar um lote de cerveja ao concluir cada obra e avisar todos,
  iniciando um prazo de 20 segundos para aquele lote.
- **FR-009**: O sistema MUST aceitar o engarrafamento de um lote somente com a temporada aberta
  e o lote ainda pendente, somando 1 à cerveja engarrafada e avisando todos.
- **FR-010**: O sistema MUST descartar um lote não engarrafado no prazo e avisar todos.
- **FR-011**: O sistema MUST recusar qualquer pedido de construir ou engarrafar após o
  encerramento e MUST parar todas as contagens de tempo ao encerrar. Obras em andamento e lotes
  pendentes ficam congelados como estão (sem conclusão, sem perda, sem engarrafamento) e o único
  fato emitido no encerramento é `cervejaria.encerrada`.
- **FR-012**: O cliente MUST apenas enviar pedidos e exibir os fatos recebidos; nenhuma regra é
  decidida no cliente.
- **FR-013**: O sistema MUST mostrar, para cada evento emitido ou recebido pela aba, o nome, o
  horário, os dados, a causa e a reação do cliente.
- **FR-014**: O sistema MUST mostrar quantas vezes cada tipo de evento já ocorreu.
- **FR-015**: O sistema MUST exibir o nome dos desenvolvedores no rodapé.
- **FR-016**: O participante MUST poder escolher, ao entrar, se atua como Mestre ou Jogador e
  informar um nome de exibição.
- **FR-017**: O sistema MUST permitir no máximo um Mestre conectado por vez; uma tentativa de
  entrar como Mestre com outro já conectado MUST ser recusada só para quem tentou, com o motivo.
  A vaga de Mestre é liberada quando o Mestre se desconecta.
- **FR-018**: O sistema MUST aceitar pedidos de construir e de engarrafar somente de Jogadores;
  os mesmos pedidos vindos do Mestre MUST ser recusados só para ele, com o motivo.

### Key Entities

- **Cervejaria (temporada)**: fase (não aberta, aberta, encerrada), cevada em estoque,
  produção por intervalo, cervejeiros ocupados, cerveja engarrafada.
- **Participante**: nome de exibição e papel (Mestre ou Jogador); conectado a uma aba.
- **Obra**: identificador, tipo (maltaria, tanque de fermentação, adega), quem pediu, início e
  término previsto; ocupa um cervejeiro enquanto dura.
- **Lote de cerveja**: identificador, obra de origem, momento em que ficou pronto, prazo final
  e situação (pendente, engarrafado, perdido).
- **Evento**: nome, tipo (pedido ou fato), origem, destinatários, dados, horário e causa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em duas abas abertas, uma mudança de estado feita em uma aparece na outra em menos
  de 1 segundo.
- **SC-002**: Em 100% das tentativas com cliques simultâneos, a cevada nunca fica negativa, os
  cervejeiros ocupados nunca passam de 2 e cada lote é engarrafado no máximo uma vez.
- **SC-003**: Em 100% das recusas, apenas a aba que fez o pedido recebe a mensagem; as demais
  não mudam.
- **SC-004**: Todos os 14 eventos da tabela aparecem no painel de eventos com direção, causa e
  reação durante uma demonstração completa (abrir, construir, produzir, concluir, engarrafar,
  perder lote, encerrar).
- **SC-005**: Os fatos de tempo ocorrem dentro de 1 segundo do momento previsto (produção a cada
  5 s, obra em 8 s, perda de lote em 20 s).
- **SC-006**: Um avaliador consegue executar a demonstração com duas abas seguindo o README, sem
  ajuda, em menos de 5 minutos.

## Assumptions

- Não há login nem senha: o papel é escolhido ao entrar; a única verificação é a de haver no
  máximo um Mestre conectado (FR-017).
- Há uma única cervejaria compartilhada por todos os conectados; o estado vive só em memória e
  se perde ao reiniciar o servidor.
- As três construções têm o mesmo custo, tempo e efeito; o tipo serve para identificação e
  exibição.
- Toda obra concluída gera exatamente um lote, independentemente do tipo.
- Uma temporada encerrada não pode ser reaberta na mesma execução; recomeçar exige reiniciar o
  servidor.
- O lote perdido apenas desaparece; não reduz recursos nem gera multa.
- Fora de escopo: login, banco de dados, publicação na internet, pagamento ou multa.
