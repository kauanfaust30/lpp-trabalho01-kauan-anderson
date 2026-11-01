<!--
Sync Impact Report
- Version change: (template, sem versão) → 1.0.0
- Princípios definidos (todos novos):
  - I. Código Simples e Legível
  - II. Servidor como Fonte da Verdade
  - III. Pedidos Separados de Fatos (Recusa Também é Evento)
  - IV. Validar e Alterar sem Await no Meio
  - V. Eventos Comentados com o Porquê
  - VI. Teste Primeiro com pytest (INEGOCIÁVEL)
  - VII. Mensagens em Português, Claras e Acionáveis
- Seções adicionadas: Restrições Técnicas; Fluxo de Desenvolvimento; Governança
- Seções removidas: nenhuma
- Templates: nenhum alterado (leem a constituição em tempo de execução)
- TODOs pendentes: nenhum
-->

# Cervejaria Artesanal Constitution

## Core Principles

### I. Código Simples e Legível

- O código MUST ser Python simples, direto e legível por quem está aprendendo.
- Funções MUST ser curtas e ter uma única responsabilidade; uma função que passe de
  ~20 linhas SHOULD ser dividida.
- Nomes de variáveis, funções e eventos MUST descrever o que representam.
- Abstrações, bibliotecas ou padrões extras MUST ser justificados por uma necessidade
  concreta (YAGNI).

**Por quê**: o projeto é didático; o paradigma orientado a eventos precisa ficar visível na
leitura do código, não escondido atrás de complexidade.

### II. Servidor como Fonte da Verdade

- Todo o estado do jogo (estoque, pedidos, produção, jogadores) MUST viver no servidor.
- O cliente MUST apenas enviar pedidos e exibir o que o servidor anuncia; ele MUST NOT
  decidir regras, calcular resultados nem alterar o estado local por conta própria.
- A interface MUST ser atualizada somente a partir de eventos recebidos do servidor.

**Por quê**: com várias abas conectadas, só uma fonte de verdade evita estados divergentes e
trapaças pelo navegador.

### III. Pedidos Separados de Fatos (Recusa Também é Evento)

- Eventos enviados pelo cliente MUST ser nomeados como pedidos (intenção), por exemplo
  `pedir_*` / `solicitar_*`.
- Eventos emitidos pelo servidor MUST ser nomeados como fatos já ocorridos, no particípio,
  por exemplo `*_criado`, `*_concluido`, `estado_atualizado`.
- Todo pedido MUST resultar em um fato: aceito (fato do domínio) ou recusado (evento de
  recusa explícito, com motivo). Um pedido MUST NOT ser ignorado em silêncio.

**Por quê**: separar intenção de fato deixa claro quem decide; a recusa como evento permite ao
cliente mostrar ao usuário o que aconteceu.

### IV. Validar e Alterar sem Await no Meio

- Em cada handler, a validação do pedido e a alteração do estado MUST acontecer em sequência,
  sem nenhum `await` entre elas.
- `await` (por exemplo `emit`) MUST vir somente depois que o estado já foi alterado.
- A lógica de validação e mutação SHOULD ficar em funções síncronas puras, chamadas pelo
  handler assíncrono.

**Por quê**: um `await` entre checar e alterar abre espaço para outro evento intercalar e
quebrar a regra validada (condição de corrida).

### V. Eventos Comentados com o Porquê

- Toda chamada `emit` e todo handler `on` (servidor e cliente) MUST ter um comentário
  explicando por que aquele evento existe ou é emitido naquele momento — não apenas o que faz.
- Comentários MUST ser em português.

**Por quê**: os eventos são o coração do paradigma estudado; o comentário torna o fluxo
explicável na apresentação e nas perguntas do README.

### VI. Teste Primeiro com pytest (INEGOCIÁVEL)

- Toda regra do servidor MUST ter um teste pytest escrito antes da implementação.
- O ciclo MUST ser: escrever o teste → ver o teste falhar → implementar → ver passar →
  refatorar.
- Testes MUST cobrir o caminho aceito e o caminho recusado de cada pedido.

**Por quê**: o teste prova que a regra existe e que a recusa acontece, sem depender de testar
manualmente com duas abas.

### VII. Mensagens em Português, Claras e Acionáveis

- Toda mensagem exibida ao usuário MUST estar em português.
- Mensagens de recusa ou erro MUST dizer o que aconteceu e o que o usuário pode fazer
  (ex.: "Malte insuficiente: faltam 2 kg. Compre malte antes de iniciar a brassagem.").
- Mensagens MUST NOT expor detalhes técnicos (stack traces, nomes internos).

**Por quê**: o usuário precisa entender a recusa e saber o próximo passo sem ler o código.

## Restrições Técnicas

- Linguagem: Python 3, servidor com `python-socketio` (ASGI) executado por `uvicorn`.
- Cliente: navegador, consumindo os eventos do servidor via Socket.IO, sem lógica de regra.
- Testes: `pytest`; testes de regra MUST rodar sem precisar subir o servidor.
- Dependências novas MUST ser adicionadas a `requirements.txt` e justificadas.

## Fluxo de Desenvolvimento

- Cada funcionalidade segue o fluxo Spec Kit: especificar → planejar → tarefas → implementar.
- Antes de concluir uma tarefa: `pytest` MUST passar e o fluxo MUST ser verificado com duas
  abas (ex.: Mestre e Jogador).
- Revisões MUST checar: estado só no servidor, pedido/fato nomeados corretamente, recusa
  emitida, nenhum `await` entre validar e alterar, comentários de porquê em `emit`/`on`,
  mensagens em português.

## Governance

- Esta constituição prevalece sobre outras práticas do projeto; em conflito, ela vence.
- Emendas MUST ser feitas via `/speckit-constitution`, registradas em commit e acordadas pelos
  integrantes da dupla.
- Versionamento semântico: MAJOR para remoção ou redefinição de princípio; MINOR para princípio
  ou seção nova; PATCH para ajustes de redação.
- Planos (`plan.md`) MUST incluir a verificação de conformidade com estes princípios; qualquer
  violação MUST ser justificada por escrito na seção de complexidade do plano.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
