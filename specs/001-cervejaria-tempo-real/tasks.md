---

description: "Lista de tarefas da Cervejaria Artesanal em Tempo Real, organizada pelas etapas 0–8 do Guia de Implementação"
---

# Tasks: Cervejaria Artesanal em Tempo Real

**Input**: Documentos de `specs/001-cervejaria-tempo-real/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/eventos.md](contracts/eventos.md),
[quickstart.md](quickstart.md)

**Tests**: OBRIGATÓRIOS (Constituição, Princípio VI). Em cada etapa os testes vêm **antes** da
implementação e devem **falhar** antes de o código ser escrito.

**Organization**: uma fase por etapa do Guia de Implementação do professor (0 a 8). Cada fase
termina com **um commit**. Cada fase de história leva o rótulo da história da spec que atende.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo — só quando o arquivo é diferente dos das outras tarefas da
  mesma etapa e não depende de tarefa incompleta
- **[Story]**: história da spec atendida (US1–US6)

## Regras que valem para TODAS as tarefas

- **Nomes de evento** desde a etapa 1: exatamente os de `docs/especificacao.md` /
  [contracts/eventos.md](contracts/eventos.md) (`estado.sincronizado`,
  `cervejaria.abertura_solicitada`, `cervejaria.iniciada`, `construcao.solicitada`,
  `construcao.iniciada`, `operacao.recusada`, `recurso.produzido`, `construcao.concluida`,
  `cervejaria.encerramento_solicitado`, `cervejaria.encerrada`, `lote.pronto`,
  `engarrafamento.solicitado`, `lote.engarrafado`, `lote.perdido`). Nunca usar `vila.*`.
- **Números** (iguais em `docs/especificacao.md` e `spec.md`): cevada inicial 150, custo 50,
  obra 8 s, intervalo 5 s, produção inicial 10, ganho +5 por obra, limite 2 cervejeiros, prazo do
  lote 20 s, +1 cerveja por lote engarrafado.
- **Nomes internos do estado** mantidos do kit: `fase`, `toras` (= **cevada**), `trabalhadores`
  (= **cervejeiros ocupados**), `limite`, `producao`, `intervalo`, `custo`, `tempo_obra`,
  `concluidas`, `em_obra`; novos: `cerveja`, `prazo_lote`, `obras`, `lotes`.
- **`server.py`**: manter as linhas do kit (`sio`, `app`, `static_files`) e escrever só abaixo do
  comentário "A partir da Etapa 1…". Todo handler de pedido segue, em linhas visíveis:
  `motivo = regras.motivo_recusa_<acao>(...)` → `if motivo: await recusar(sid, "<pedido>", motivo); return`
  → alterar `estado[...]` → `await sio.emit("<fato>", ...)`. **Nenhum `await` antes de a
  alteração terminar.** Cada `@sio.on` e cada `sio.emit` com comentário `# Por quê: ...`.
- **`regras.py`**: só funções puras (não alteram `estado`, não emitem).
- **`client/index.html`**: **não alterar a cena Phaser** (função `criarJogo`) nem as tags
  `<script>` de CDN (Vue 3.5.13, Socket.IO 4.7.5, Phaser 3.90.0). Cada `ouvir(...)` e `pedir(...)`
  com comentário `// Por quê: ...`. O cliente só copia `d.estado` (`atualizar(d)`) e chama
  métodos `jogo.*` existentes.
- **Commits**: mensagem no formato `feat(etapa N): <resumo>`; rodar `pytest` antes de cada commit.

---

## Phase 1: Etapa 0 — Servidor e tela (Setup)

**Purpose**: dependências, estado inicial, base de testes e rodapé; servidor sobe e mostra a tela
de entrada do kit.

- [X] T001 Adicionar `pytest` em `requirements.txt` (mantendo `python-socketio` e `uvicorn`) e instalar no venv com `.venv\Scripts\python.exe -m pip install -r requirements.txt`
- [X] T002 [P] Escrever em `tests/test_regras.py` o teste `test_estado_inicial` que verifica `regras.estado_inicial()`: `fase == "aguardando"`, `toras == 150`, `producao == 10`, `cerveja == 0`, `concluidas == 0`, `obras == {}`, `lotes == {}`, `participantes == {}`, `mestre_sid is None`, `encerrada_em is None`, `proximo_id == 1`; e as constantes `CEVADA_INICIAL == 150`, `CUSTO_CONSTRUCAO == 50`, `TEMPO_OBRA == 8`, `INTERVALO_PRODUCAO == 5`, `PRODUCAO_INICIAL == 10`, `GANHO_POR_OBRA == 5`, `LIMITE_CERVEJEIROS == 2`, `PRAZO_LOTE == 20`, `CERVEJA_POR_LOTE == 1`, `TIPOS_CONSTRUCAO == ("maltaria", "tanque", "adega")` (deve falhar: módulo não existe)
- [X] T003 Criar `regras.py` com as constantes de T002 e `estado_inicial() -> dict` (função pura que devolve um dicionário novo a cada chamada); fazer T002 passar. A docstring do módulo MUST abrir com o **glossário/aviso**: "Os nomes de campo vêm do Kit Inicial e foram mantidos para a tela do kit continuar funcionando: `toras` é a CEVADA em estoque e `trabalhadores` são os CERVEJEIROS OCUPADOS (= obras em andamento); `limite` é o máximo de cervejeiros ocupados (2). A fase `"aguardando"` do código é a fase "não aberta" da spec (temporada ainda não aberta pelo Mestre)."
- [X] T004 Em `server.py`, abaixo da linha "A partir da Etapa 1…", acrescentar `import time`, `import regras`, `estado = regras.estado_inicial()` e `def agora(): return time.monotonic()` (ponto único de relógio, para os testes poderem substituir)
- [X] T005 Criar `tests/conftest.py` com a fixture `servidor` que: recria `server.estado` com `regras.estado_inicial()`; substitui `server.sio.emit` por uma corrotina que grava `(evento, dados, to)` numa lista `emitidos`; substitui `server.sio.sleep` por corrotina instantânea; substitui `server.sio.start_background_task` por função que só grava `(funcao, args)` em `tarefas`; substitui `server.agora` por um relógio controlável (começa em `1000.0`); devolve um objeto com `server`, `emitidos`, `tarefas`, `relogio` e `rodar(coro)` (= `asyncio.run`)
- [X] T006 [P] Trocar o rodapé de `client/index.html` para `<footer>Desenvolvido por: Kauan Faust e Anderson Moreira</footer>`
- [X] T007 Validar: `pytest` verde; `uvicorn server:app --reload` sobe e `http://127.0.0.1:8000` mostra a tela de entrada com o rodapé
- [X] T008 Commit `feat(etapa 0): servidor, estado inicial, base de testes e rodapé`

**Checkpoint**: servidor sobe, testes rodam, estado inicial com os números da spec.

---

## Phase 2: Etapa 1 — Conectar e sincronizar o estado (Foundational)

**Purpose**: conexão, registro do participante, `estado.sincronizado` só para quem conectou,
retrato público e auxiliares usados por todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta etapa.

### Testes (escrever primeiro, devem falhar)

- [X] T009 [P] Em `tests/test_regras.py`, testar `regras.retrato(estado, agora)`: devolve exatamente as chaves `fase, toras, producao, intervalo, custo, tempo_obra, trabalhadores, limite, concluidas, em_obra, cerveja, prazo_lote, obras, lotes`; `intervalo == 5`, `custo == 50`, `tempo_obra == 8`, `limite == 2`, `prazo_lote == 20`; `trabalhadores == em_obra == len(estado["obras"])`; `obras` como lista de `{id, tipo, pedida_por, restante}` e `lotes` como lista de `{id, obra_id, restante}`; `restante` "inteiro arredondado para cima, ≥ 0"; com `encerrada_em` definido, `restante` é medido a partir de `encerrada_em` (congelado); `participantes`, `mestre_sid`, `encerrada_em` e `proximo_id` NÃO aparecem
- [X] T010 [P] Em `tests/test_servidor.py`, testar com a fixture `servidor`: `connect(sid, environ, {"nome": "Ana", "papel": "jogador"})` registra `participantes[sid] = {"nome": "Ana", "papel": "jogador"}` e grava um único emit `("estado.sincronizado", {estado, causa: "conexão", papel: "jogador"}, to=sid)`; nome vazio vira `"Anônimo"`; conectar como Mestre (sem Mestre presente) define `mestre_sid`; `disconnect(sid)` remove o participante e, se era o Mestre, zera `mestre_sid`; `disconnect` de quem pediu uma obra NÃO altera `estado["obras"]` nem `estado["lotes"]` (a obra continua — caso de borda "Jogador desconectado durante uma obra"); `disconnect` de sid desconhecido não falha

### Implementação

- [X] T011 Implementar `retrato(estado, agora)` em `regras.py` (função pura; usar `math.ceil` e `max(0, ...)`) até T009 passar
- [X] T012 Em `server.py`, criar os auxiliares `def causa_pedido(sid)` (devolve `"pedido de <nome>"` quando `sid` está em `estado["participantes"]` e `"conexão"` quando não está — usar `.get`, **sem `KeyError`**), `def fato(causa, **extras)` (devolve `{"estado": regras.retrato(estado, agora()), "causa": causa, **extras}`) e `async def recusar(sid, pedido, motivo)` que emite `operacao.recusada` com `fato(causa_pedido(sid), pedido=pedido, motivo=motivo)` e `to=sid` — com comentário `# Por quê: a recusa é um fato só de quem pediu (R4)`
- [X] T013 Em `server.py`, implementar `@sio.event async def connect(sid, environ, auth)` (registra o participante com nome padrão `"Anônimo"`, define `mestre_sid` se papel `mestre`, e só então emite `estado.sincronizado` com `to=sid`) e `@sio.event async def disconnect(sid)`, com comentários de porquê; fazer T010 passar
- [X] T014 Em `client/index.html`, **só na parte Vue** (função `entrar()` dentro de `createApp`): mover `conectado.value = true` e `nextTick(() => jogo.iniciar("jogo"))` do `socket.on("connect")` para a reação de `estado.sincronizado` (assim só entra na tela da cervejaria quem o servidor aceitou) e acrescentar `ouvir("estado.sincronizado", "copia o estado e desenha a cervejaria", (d) => { atualizar(d); conectado.value = true; nextTick(() => { jogo.iniciar("jogo"); jogo.mostrarEstado(d.estado); }); })` com comentário de porquê. **Não alterar a função `criarJogo` nem a cena Phaser** (`VilaScene`); conferir com `git diff client/index.html` que nenhuma linha entre `function criarJogo()` e o fim desse `<script>` mudou
- [X] T015 Validar a etapa 1 **antes do commit**: (a) `pytest` verde; (b) com `uvicorn server:app --reload`, abrir duas abas: na aba A entrar como **Jogador** e na aba B como **Mestre**; nas duas, a tela de entrada some e aparece a tela da cervejaria com o mapa Phaser desenhado; (c) o Painel de eventos de cada aba mostra `⬇ on estado.sincronizado` com causa "conexão" e os dados do estado; (d) a aba A não recebe o `estado.sincronizado` da aba B. Se a tela de entrada não sair, corrigir T014 antes de seguir
- [X] T016 Commit `feat(etapa 1): conectar e sincronizar o estado` (só depois de T015 aprovada)

**Checkpoint**: base pronta; histórias podem começar.

---

## Phase 3: Etapa 2 — Mestre abre a temporada (User Story 1, P1) 🎯 MVP

**Goal**: o Mestre abre a temporada e todas as abas veem a fase "aberta".

**Independent Test**: Mestre e Jogador conectados; o Mestre clica em "Abrir temporada" e as duas
abas mostram "Temporada aberta" em < 1 s.

### Testes (escrever primeiro, devem falhar)

- [X] T017 [P] [US1] Em `tests/test_regras.py`, testar `motivo_recusa_abertura(estado, participante)`: `None` para Mestre com fase `"aguardando"`; `"Você não está na cervejaria. Entre novamente."` para `participante is None`; `"Apenas o Mestre pode abrir a temporada."` para Jogador; `"A temporada já está aberta."` com fase `"aberta"`; ~~`"A temporada já foi encerrada. Reinicie o servidor para começar outra."` com fase `"encerrada"`~~ — **requisito mudou (FR-019, 2026-11-01)**: com fase `"encerrada"` o Mestre recebe `None` (pode reabrir); o teste é ajustado em T078
- [X] T018 [P] [US1] Em `tests/test_servidor.py`, testar o handler `server.abertura_solicitada(sid)` (evento `cervejaria.abertura_solicitada`): pelo Mestre → `estado["fase"] == "aberta"` e um único emit `cervejaria.iniciada` para todos (`to is None`) com `causa == "pedido de <nome>"`; por Jogador → um único emit `operacao.recusada` com `to=sid`, `pedido == "cervejaria.abertura_solicitada"`, motivo exato, e `fase` continua `"aguardando"`

### Implementação

- [X] T019 [US1] Implementar `motivo_recusa_abertura` em `regras.py` (constante `MOTIVO_NAO_REGISTRADO = "Você não está na cervejaria. Entre novamente."`, reutilizada pelas próximas regras) até T017 passar
- [X] T020 [US1] Em `server.py`, implementar `@sio.on("cervejaria.abertura_solicitada") async def abertura_solicitada(sid)` na sequência validar → recusar → `estado["fase"] = "aberta"` → `await sio.emit("cervejaria.iniciada", fato(causa_pedido(sid)))`, com comentários de porquê; fazer T018 passar
- [X] T021 [US1] Em `client/index.html`, implementar `abrirVila()` com `pedir("cervejaria.abertura_solicitada")` e, em `entrar()`, `ouvir("cervejaria.iniciada", "mostra a temporada aberta", (d) => { atualizar(d); jogo.vilaIniciada(); })`, ambos com comentário de porquê
- [X] T022 [US1] Validar o Independent Test com duas abas; `pytest` verde
- [X] T023 [US1] Commit `feat(etapa 2): Mestre abre a temporada`

**Checkpoint**: MVP — conectar, sincronizar e abrir funcionam em tempo real.

---

## Phase 4: Etapa 3 — Pedido e fato de construir (User Story 2, P1)

**Goal**: o Jogador pede para construir; todos veem a obra começar, a cevada cair 50 e um
cervejeiro ficar ocupado.

**Independent Test**: com a temporada aberta, o Jogador constrói; cevada 150 → 100 e cervejeiros
0/2 → 1/2 em todas as abas.

### Testes (escrever primeiro, devem falhar)

- [X] T024 [P] [US2] Em `tests/test_regras.py`, testar que `motivo_recusa_construcao(estado, participante, tipo)` devolve `None` para Jogador, fase `"aberta"`, tipo `"maltaria"`/`"tanque"`/`"adega"`, `toras >= 50` (inclusive exatamente 50) e `len(obras) < 2`
- [X] T025 [P] [US2] Em `tests/test_servidor.py`, testar o handler `server.construcao_solicitada(sid, dados)` (evento `construcao.solicitada`) com `{"tipo": "maltaria"}` (temporada aberta, Jogador): `toras` 150 → 100; nova obra em `estado["obras"]` com `id` vindo de `proximo_id`, `tipo`, `pedida_por` (nome) e `termina_em == relogio + 8`; `proximo_id` incrementado; um único emit `construcao.iniciada` para todos com `obra == {id, tipo, pedida_por}` e `estado.trabalhadores == 1`

### Implementação

- [X] T026 [US2] Criar `motivo_recusa_construcao` em `regras.py` devolvendo `None` (as checagens de recusa entram na etapa 4) até T024 passar
- [X] T027 [US2] Em `server.py`, implementar `@sio.on("construcao.solicitada") async def construcao_solicitada(sid, dados=None)`, lendo o tipo com `tipo = (dados or {}).get("tipo")` (pedido sem dados ou sem a chave vira a recusa de tipo desconhecido, sem quebrar), na sequência validar → recusar → `estado["toras"] -= regras.CUSTO_CONSTRUCAO`, criar a obra e incrementar `proximo_id` → `await sio.emit("construcao.iniciada", fato(..., obra={...}))`, com comentários de porquê; fazer T025 passar
- [X] T028 [US2] Em `client/index.html`, implementar `construir()` com `pedir("construcao.solicitada", { tipo: "maltaria" })` (a escolha do tipo entra na etapa 8) e `ouvir("construcao.iniciada", "desenha o canteiro e desconta a cevada", (d) => { atualizar(d); jogo.obraIniciada(d.estado); })`, com comentários de porquê
- [X] T029 [US2] Validar o Independent Test com duas abas; `pytest` verde
- [X] T030 [US2] Commit `feat(etapa 3): pedido e fato de construir`

---

## Phase 5: Etapa 4 — Recusa (User Story 2 + User Story 1, P1)

**Goal**: todo pedido inválido gera `operacao.recusada` **só para quem pediu**, com motivo
acionável; Mestre único na conexão (FR-017).

**Independent Test**: com a temporada fechada, o Jogador A clica em Construir; só A vê "A
temporada não está aberta." e o Painel da outra aba não muda (Cenário 1).

### Testes (escrever primeiro, devem falhar)

- [X] T031 [P] [US2] Em `tests/test_regras.py`, testar cada motivo de `motivo_recusa_construcao`, na ordem de checagem: `participante is None` → `"Você não está na cervejaria. Entre novamente."`; Mestre → `"Apenas Jogadores podem construir."`; fase `"aguardando"` → `"A temporada não está aberta."`; fase `"encerrada"` → `"A temporada está encerrada."`; tipo `"casa"` → `"Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."`; `toras == 40` → `"Cevada insuficiente: faltam 10. Aguarde a próxima colheita."`; 2 obras → `"Nenhum cervejeiro livre. Aguarde uma obra terminar."`
- [X] T032 [US1] Em `tests/test_regras.py` (mesmo arquivo de T031, escrever em sequência), testar `motivo_recusa_conexao(estado, papel)`: `None` para `"jogador"`; `None` para `"mestre"` sem `mestre_sid`; `"Já existe um Mestre na cervejaria. Entre como Jogador."` para `"mestre"` com `mestre_sid` definido
- [X] T033 [P] [US2] Em `tests/test_servidor.py`, testar: construção recusada (temporada fechada) grava **um único** emit, `operacao.recusada` com `to=sid` e `pedido == "construcao.solicitada"`, e `toras`/`obras` não mudam; `construcao_solicitada` vindo de um sid não registrado (nunca conectou) é recusado só para ele com `"Você não está na cervejaria. Entre novamente."` e `causa == "conexão"`, sem `KeyError`; com a temporada aberta e Jogador registrado, `construcao_solicitada(sid, None)` e `construcao_solicitada(sid, {})` geram só `operacao.recusada` com `"Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."`, sem exceção e sem mudar `toras`/`obras`
- [X] T034 [US1] Em `tests/test_servidor.py` (mesmo arquivo de T033, escrever em sequência), testar: segundo `connect` como Mestre grava um único emit `operacao.recusada` com `to=sid`, `pedido == "conexao"`, motivo exato; esse sid NÃO entra em `participantes` e `mestre_sid` não muda; em seguida, `abertura_solicitada` vindo desse mesmo sid recusado (não registrado) gera só `operacao.recusada` para ele com `"Você não está na cervejaria. Entre novamente."` e `causa == "conexão"`, sem `KeyError` e sem abrir a temporada; após `disconnect` do Mestre, um novo Mestre é aceito

### Implementação

- [X] T035 [US2] Completar `motivo_recusa_construcao` em `regras.py` com as checagens na ordem de T031 até passar
- [X] T036 [US1] Implementar `motivo_recusa_conexao` em `regras.py` e usá-la no `connect` de `server.py` (validar → se motivo: `await recusar(sid, "conexao", motivo)` e retornar sem registrar → registrar → emitir `estado.sincronizado`); fazer T032 e T034 passar
- [X] T037 [US2] Em `client/index.html`, acrescentar `ouvir("operacao.recusada", "mostra o motivo só para quem pediu", (d) => { ... })`: `avisar(d.motivo, "erro")` e `jogo.recusado(d.motivo)`; se `d.pedido === "conexao"`, gravar o motivo em um novo `ref` `erroEntrada`, desconectar o socket e manter a tela de entrada; mostrar `erroEntrada` na tela de entrada (`<p v-if="erroEntrada" class="erro">`), com comentário de porquê
- [X] T038 [US2] Validar o Independent Test e a recusa do segundo Mestre com três abas; `pytest` verde
- [X] T039 [US2] Commit `feat(etapa 4): recusa só para quem pediu e Mestre único`

---

## Phase 6: Etapa 5 — Passagem do tempo (User Story 3, P1)

**Goal**: a cevada sobe sozinha a cada 5 s e cada obra termina sozinha após 8 s.

**Independent Test**: com a temporada aberta e sem cliques, a cevada sobe 10 a cada 5 s em todas
as abas; uma obra iniciada vira casa após 8 s, liberando o cervejeiro.

### Testes (escrever primeiro, devem falhar; todos em `tests/test_servidor.py`, em sequência)

- [X] T040 [US3] Em `tests/test_servidor.py`, testar `produzir_cevada()`: com fase `"aberta"` e `producao == 10`, `toras` sobe 10 e há um emit `recurso.produzido` para todos com `quantidade == 10` e `causa == "temporizador"`; com fase `"aguardando"` ou `"encerrada"`, nada muda e nada é emitido
- [X] T041 [US3] Em `tests/test_servidor.py`, testar `concluir_obra(obra_id)`: com fase `"aberta"` e obra existente → obra removida, `concluidas += 1`, `producao` 10 → 15, emit `construcao.concluida` para todos com `obra == {id, tipo}` e `causa == "temporizador"`; com fase `"encerrada"` ou obra inexistente → nada muda e nada é emitido
- [X] T042 [US3] Em `tests/test_servidor.py`, testar que a abertura aceita registra `ciclo_producao` em `tarefas` e que a construção aceita registra `esperar_obra` com o id da obra (a partir de T078 os argumentos incluem o número da temporada: `(ciclo_producao, (1,))` e `(esperar_obra, (1, 1))`)

### Implementação

- [X] T043 [US3] Em `server.py`, implementar `async def produzir_cevada()` (revalida fase → `estado["toras"] += estado["producao"]` → emit `recurso.produzido` com `quantidade`) e `async def ciclo_producao()` (`while estado["fase"] == "aberta": await sio.sleep(regras.INTERVALO_PRODUCAO); await produzir_cevada()`), com comentários de porquê; fazer T040 passar
- [X] T044 [US3] Em `server.py`, implementar `async def concluir_obra(obra_id)` (revalida fase `"aberta"` e existência → remove obra, `concluidas += 1`, `producao += regras.GANHO_POR_OBRA` → emit `construcao.concluida`) e `async def esperar_obra(obra_id)` (`await sio.sleep(regras.TEMPO_OBRA)` → `await concluir_obra(obra_id)`), com comentários de porquê; fazer T041 passar
- [X] T045 [US3] Em `server.py`, chamar `sio.start_background_task(ciclo_producao)` depois do emit de `cervejaria.iniciada` e `sio.start_background_task(esperar_obra, obra_id)` depois do emit de `construcao.iniciada`; fazer T042 passar
- [X] T046 [US3] Em `client/index.html`, acrescentar `ouvir("recurso.produzido", "mostra a cevada colhida", (d) => { atualizar(d); jogo.recursoProduzido(d.estado); })` e `ouvir("construcao.concluida", "troca o canteiro pela construção pronta", (d) => { atualizar(d); jogo.obraConcluida(d.estado); })`, com comentários de porquê
- [X] T047 [US3] Validar o Independent Test (Cenário 2) com duas abas; `pytest` verde
- [X] T048 [US3] Commit `feat(etapa 5): passagem do tempo (produção e fim de obra)`

---

## Phase 7: Etapa 6 — Encerramento e disputa (User Story 5, P2 + disputa da User Story 2)

**Goal**: o Mestre encerra; tudo congela e novos pedidos são recusados. Em disputa, só um pedido
vence.

**Independent Test**: com obra em andamento, o Mestre encerra; as abas mostram "Temporada
encerrada" e nenhum fato de temporizador aparece depois. Dois Jogadores clicando juntos com 1/2
ocupado geram um `construcao.iniciada` e uma recusa (Cenário 3).

### Testes (escrever primeiro, devem falhar)

- [X] T049 [P] [US5] Em `tests/test_regras.py`, testar `motivo_recusa_encerramento(estado, participante)`: `None` para Mestre com fase `"aberta"`; `"Você não está na cervejaria. Entre novamente."`; `"Apenas o Mestre pode encerrar a temporada."`; fase `"aguardando"` → `"A temporada ainda não foi aberta."`; fase `"encerrada"` → `"A temporada já está encerrada."`
- [X] T050 [P] [US5] Em `tests/test_servidor.py`, testar o handler `server.encerramento_solicitado(sid)` (evento `cervejaria.encerramento_solicitado`): pelo Mestre → `fase == "encerrada"`, `encerrada_em == relogio` e um único emit `cervejaria.encerrada` para todos; depois disso `produzir_cevada()` e `concluir_obra(id)` não mudam nada nem emitem; `construcao_solicitada` é recusada com `"A temporada está encerrada."`; ~~`abertura_solicitada` é recusada com `"A temporada já foi encerrada. Reinicie o servidor para começar outra."`~~ — **requisito mudou (FR-019, 2026-11-01)**: a abertura depois de encerrar passa a ser aceita; essa parte do teste é retirada em T078; por Jogador → recusa só para ele
- [X] T051 [US2] Em `tests/test_servidor.py` (mesmo arquivo de T050, escrever em sequência), testar disputa com `asyncio.gather` de duas chamadas a `server.construcao_solicitada` (Jogadores A e B): (a) 1 obra em andamento e `toras == 100` → exatamente um `construcao.iniciada`, uma `operacao.recusada` só para o outro sid, `len(obras) == 2`; (b) 0 obras e `toras == 50` → um aceito, um recusado com `"Cevada insuficiente: faltam 50. Aguarde a próxima colheita."`, `toras == 0` (nunca negativa)

### Implementação

- [X] T052 [US5] Implementar `motivo_recusa_encerramento` em `regras.py` até T049 passar
- [X] T053 [US5] Em `server.py`, implementar `@sio.on("cervejaria.encerramento_solicitado") async def encerramento_solicitado(sid)` na sequência validar → recusar → `estado["fase"] = "encerrada"`, `estado["encerrada_em"] = agora()` → emit `cervejaria.encerrada`, com comentários de porquê; fazer T050 passar
- [X] T054 [US2] Conferir em `server.py` que nenhum handler tem `await` entre `motivo_recusa_*` e o fim da alteração do estado; fazer T051 passar sem locks
- [X] T055 [US5] Em `client/index.html`, implementar `encerrarVila()` com `pedir("cervejaria.encerramento_solicitado")` e `ouvir("cervejaria.encerrada", "mostra a temporada encerrada e escurece a cena", (d) => { atualizar(d); jogo.vilaEncerrada(); })`, com comentários de porquê
- [X] T056 [US5] Validar o Independent Test com duas e três abas; `pytest` verde
- [X] T057 [US5] Commit `feat(etapa 6): encerramento e disputa`

### Extra: reabrir a temporada (FR-019 = R10/FR-015/Cenário 6 da especificação; mudança de requisito de 2026-11-01)

Mesmos eventos (`cervejaria.abertura_solicitada` → `cervejaria.iniciada`, com o campo extra
`reaberta`); nenhum evento novo. Feito **depois** do commit da etapa 6 (T057).

- [ ] T078 [US5] Testes primeiro (devem falhar). Em `tests/test_regras.py`: trocar `test_nao_reabre_temporada_encerrada` (de T017) por um teste em que `motivo_recusa_abertura` devolve `None` para o Mestre com fase `"encerrada"`; Jogador com fase `"encerrada"` continua recebendo `"Apenas o Mestre pode abrir a temporada."`; fase `"aberta"` continua `"A temporada já está aberta."`; `estado_inicial()["temporada"] == 0` (acrescentar em `test_estado_inicial`); `"temporada"` não aparece em `retrato` (acrescentar em `test_retrato_esconde_campos_internos`). Em `tests/test_servidor.py`: (a) **reabertura reinicia o estado** — com fase `"encerrada"`, `temporada == 1`, uma obra e um lote, `toras`, `producao`, `cerveja` e `concluidas` alterados, `abertura_solicitada("m1")` deixa `toras == 150`, `producao == 10`, `cerveja == 0`, `concluidas == 0`, `obras == {}`, `lotes == {}`, `encerrada_em is None`, `proximo_id == 1`, `fase == "aberta"`, `temporada == 2`, mantém `participantes` e `mestre_sid`, e emite um único `cervejaria.iniciada` para todos com `reaberta is True` e `estado.toras == 150`; a primeira abertura emite `reaberta is False` e deixa `temporada == 1`; (b) **temporizador antigo não emite na temporada nova** — depois da reabertura e de uma obra nova de id 1, `esperar_obra(1, 1)` (temporada antiga) não emite nada e não remove a obra nova; `ciclo_producao(1)` com a temporada 2 aberta não produz nem emite; (c) **abrir já aberta continua recusado** — com fase `"aberta"`, `abertura_solicitada("m1")` gera só `operacao.recusada` para `m1` com `"A temporada já está aberta."` e não muda `temporada`. Ajustar os testes existentes afetados: em T050, retirar a parte que espera recusa de `abertura_solicitada` depois de encerrar (`test_depois_de_encerrar_construir_e_reabrir_sao_recusados` passa a testar só a construção); em T042, esperar `(ciclo_producao, (1,))` e `(esperar_obra, (1, 1))`
- [ ] T079 [US5] Em `regras.py`: `estado_inicial()` ganha `"temporada": 0` (campo interno; registrar no glossário da docstring que ele não vai no retrato); `motivo_recusa_abertura` deixa de recusar a fase `"encerrada"` (mantém as recusas de não registrado, de não Mestre e de fase `"aberta"`); `retrato` continua sem `temporada`. Fazer passar os testes de regra de T078
- [ ] T080 [US5] Em `server.py`: (1) criar `def reiniciar_temporada()` (síncrona) que monta `novo = regras.estado_inicial()`, copia `participantes`, `mestre_sid` e `temporada` do estado atual e faz `estado.clear(); estado.update(novo)`; (2) em `abertura_solicitada`, depois de validar e recusar, sem `await` no meio: `reaberta = estado["fase"] == "encerrada"`; se `reaberta`, `reiniciar_temporada()`; `estado["temporada"] += 1`; `estado["fase"] = "aberta"`; emitir `cervejaria.iniciada` com `fato(causa_pedido(sid), reaberta=reaberta)`; iniciar `sio.start_background_task(ciclo_producao, estado["temporada"])`; (3) `ciclo_producao(temporada)`: o laço roda enquanto a fase for `"aberta"` **e** `estado["temporada"] == temporada`, e depois do `sleep` sai sem produzir se a temporada mudou; (4) `esperar_obra(obra_id, temporada)`: depois do `sleep`, se `estado["temporada"] != temporada`, não faz nada; `construcao_solicitada` passa `estado["temporada"]` ao iniciar `esperar_obra`. Comentários `# Por quê:` em cada mudança. Fazer passar todos os testes de T078
- [ ] T081 [US5] Em `client/index.html` (parte Vue, **sem alterar `criarJogo` nem a cena Phaser**): trocar `const jogo = criarJogo()` por `let jogo = criarJogo()`; na escuta de `cervejaria.iniciada`, se `d.reaberta`, limpar o conteúdo de `#jogo`, fazer `jogo = criarJogo()` e, no `nextTick`, `jogo.iniciar("jogo")` e `jogo.mostrarEstado(d.estado)`, além de `avisar("🍺 Nova temporada aberta!", "ok")`; senão manter `jogo.vilaIniciada()`; comentário de porquê. Conferir com `git diff` que nenhuma linha de `criarJogo` mudou
- [ ] T082 [US5] Validar com duas abas (passos 14 e 15 de `quickstart.md`): encerrar com obra em andamento, reabrir pelo Mestre, ver o mapa redesenhado e o estado zerado nas duas abas, e confirmar que nos 10 s seguintes não chega `construcao.concluida` nem `lote.pronto` da obra antiga; `pytest` verde
- [ ] T083 [US5] Commit `feat(extra): reabrir a temporada`

---

## Phase 8: Etapa 7 — Contadores por evento (User Story 6, P2)

**Goal**: o Painel mostra quantas vezes cada evento ocorreu (FR-014), além de nome, horário,
dados, causa e reação (FR-013); rodapé com os nomes (FR-015, feito na etapa 0).

**Independent Test**: fazer qualquer ação e ver o contador do evento subir 1 no Painel.

- [X] T058 [US6] Em `client/index.html`, no lugar do comentário `<!-- ETAPA 7 (dupla): cole aqui os contadores por evento -->`, mostrar `<p class="legenda">` com `<span class="chip" v-for="(qtd, nome) in contadores" :key="nome">{{ nome }}: {{ qtd }}</span>` (o kit já incrementa `contadores` em `registrar`)
- [ ] T059 [US6] Validar o Independent Test, conferir que cada linha do Painel mostra a causa e conferir o rodapé "Kauan Faust e Anderson Moreira"; `pytest` verde
- [ ] T060 [US6] Commit `feat(etapa 7): contadores por evento no Painel`

---

## Phase 9: Etapa 8 — Adaptação à cervejaria e lotes que passam do ponto (User Story 4, P2)

**Goal**: textos da cervejaria, escolha do tipo de construção e o evento próprio: cada obra
concluída gera um lote que precisa ser engarrafado em 20 s ou é perdido.

**Independent Test**: concluir uma obra, ver o lote na lista de todas as abas, engarrafar e ver a
cerveja subir 1; repetir sem engarrafar e ver o lote sumir após 20 s (Cenário 4).

### Testes (escrever primeiro, devem falhar)

- [X] T061 [P] [US4] Em `tests/test_regras.py`, testar `motivo_recusa_engarrafamento(estado, participante, lote_id)`: `None` para Jogador, fase `"aberta"` e lote em `lotes`; `"Você não está na cervejaria. Entre novamente."`; Mestre → `"Apenas Jogadores podem engarrafar."`; `"aguardando"` → `"A temporada não está aberta."`; `"encerrada"` → `"A temporada está encerrada."`; lote ausente → `"Este lote não está mais disponível."`
- [X] T062 [P] [US4] Em `tests/test_servidor.py`, testar que `concluir_obra` agora também cria um lote `{id, obra_id, vence_em == relogio + 20}` em `estado["lotes"]`, emite `construcao.concluida` e **depois** `lote.pronto` para todos com `lote == {id, obra_id}` e `prazo == 20`, e registra `(esperar_prazo_lote, (lote_id, temporada))` em `tarefas` (FR-019)
- [X] T063 [US4] Em `tests/test_servidor.py` (mesmo arquivo de T062, escrever em sequência), testar o handler `server.engarrafamento_solicitado(sid, dados)` (evento `engarrafamento.solicitado`) com `{"lote": id}`: aceito → lote removido, `cerveja` 0 → 1, emit `lote.engarrafado` para todos com `lote == {id}` e `por == nome`; recusas (Mestre, lote já engarrafado/perdido, temporada encerrada) → só `operacao.recusada` para o sid; `engarrafamento_solicitado(sid, None)` e `engarrafamento_solicitado(sid, {})` → só `operacao.recusada` com `"Este lote não está mais disponível."`, sem exceção e sem mudar `cerveja`/`lotes`; disputa com `asyncio.gather` de dois Jogadores → um `lote.engarrafado` e uma recusa `"Este lote não está mais disponível."`
- [X] T064 [US4] Em `tests/test_servidor.py` (mesmo arquivo, em sequência), testar `perder_lote(lote_id)`: fase `"aberta"` e lote pendente → lote removido e emit `lote.perdido` para todos com `causa == "temporizador"`; lote já engarrafado ou fase `"encerrada"` → nada muda e nada é emitido; `esperar_prazo_lote(lote_id, temporada_antiga)` depois de uma reabertura, com um lote novo de mesmo id, não emite nada e não remove o lote novo (FR-019)

### Implementação

- [X] T065 [US4] Implementar `motivo_recusa_engarrafamento` em `regras.py` até T061 passar
- [X] T066 [US4] Em `server.py`, estender `concluir_obra` para criar o lote (id de `proximo_id`, `vence_em = agora() + regras.PRAZO_LOTE`) junto com as demais alterações, emitir `lote.pronto` depois de `construcao.concluida` e iniciar `sio.start_background_task(esperar_prazo_lote, lote_id, estado["temporada"])`; implementar `async def perder_lote(lote_id)` e `async def esperar_prazo_lote(lote_id, temporada)` (`await sio.sleep(regras.PRAZO_LOTE)` → se `estado["temporada"] != temporada`, não faz nada → senão `await perder_lote(lote_id)`), com comentários de porquê; fazer T062 e T064 passar
- [X] T067 [US4] Em `server.py`, implementar `@sio.on("engarrafamento.solicitado") async def engarrafamento_solicitado(sid, dados=None)`, lendo o lote com `lote_id = (dados or {}).get("lote")` (pedido sem dados ou sem a chave vira a recusa "Este lote não está mais disponível.", sem quebrar), na sequência validar → recusar → remover o lote e `estado["cerveja"] += regras.CERVEJA_POR_LOTE` → emit `lote.engarrafado`, com comentários de porquê; fazer T063 passar
- [X] T068 [US4] Em `client/index.html` (parte Vue, sem tocar na cena Phaser): acrescentar `ouvir("lote.pronto", ...)` (`atualizar(d)`; `avisar("🍺 Lote " + d.lote.id + " pronto: engarrafe em " + d.prazo + " s", "ok")`), `ouvir("lote.engarrafado", ...)` (`atualizar(d)`; aviso de sucesso com `d.por`) e `ouvir("lote.perdido", ...)` (`atualizar(d)`; `avisar("Lote " + d.lote.id + " passou do ponto e foi perdido.", "erro")`), cada um com comentário de porquê
- [X] T069 [US4] Em `client/index.html`, acrescentar a seção de lotes com `v-for="l in estado.lotes"` mostrando "🍺 Lote {{ l.id }} — {{ l.restante }} s" e, se `papel === 'jogador'`, botão "Engarrafar" que chama `engarrafar(l.id)` → `pedir("engarrafamento.solicitado", { lote: id })` com comentário de porquê; acrescentar também, na mesma parte Vue, a lista das obras em andamento com `v-for="o in estado.obras"` mostrando "🏭 {{ o.tipo }} de {{ o.pedida_por }} — {{ o.restante }} s" (o campo `restante` das obras já vem de `regras.retrato`, testado em T009) — **sem alterar a cena Phaser**; incluir `lotes: [], obras: [], cerveja: 0, prazo_lote: 0` no `reactive` inicial de `estado` e exportar `engarrafar` no `return`
- [X] T070 [US4] Em `client/index.html`, adicionar um `<select v-model="tipoObra">` com `maltaria`, `tanque` (Tanque de fermentação) e `adega` ao lado do botão Construir e passar `{ tipo: tipoObra.value }` em `construir()`
- [X] T071 [US4] Em `client/index.html`, trocar só os textos exibidos (mantendo os campos internos): `<title>` e títulos para "🍺 Cervejaria Artesanal"; "🪵 Toras" → "🌾 Cevada" (`estado.toras`); "👷 Trabalhadores" → "🧑‍🍳 Cervejeiros ocupados" (`estado.trabalhadores`/`estado.limite`); "🏠 Construções" → "🏭 Construções"; botão "custo {{ estado.custo }} de cevada"; nova linha "🍺 Cerveja engarrafada: {{ estado.cerveja }}"; em `resumir`, o texto `"toras ... trabalhadores ..."` → `"cevada " + e.toras + ", cervejeiros " + e.trabalhadores + "/" + e.limite`
- [ ] T072 [US4] Validar o Independent Test (Cenário 4 e disputa de engarrafamento) com duas abas; `pytest` verde
- [ ] T073 [US4] Commit `feat(etapa 8): adaptação à cervejaria e lotes que passam do ponto`

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T074 [P] Revisar `server.py` e `client/index.html`: todo `@sio.on`/`@sio.event`, `sio.emit`, `ouvir(...)` e `pedir(...)` tem comentário de porquê em português (Princípio V); funções com até ~20 linhas (Princípio I)
- [ ] T075 [P] Preencher `README.md` (modelo do professor): título "Cervejaria em Tempo Real — Cervejaria artesanal", integrantes, instalação (`pip install -r requirements.txt`, `uvicorn server:app --reload`, `http://127.0.0.1:8000`), teste com duas abas (resumo de `specs/001-cervejaria-tempo-real/quickstart.md`), respostas às 3 perguntas apontando trechos de `server.py`, seção "Uso de IA", extras (Mestre único, lotes, contadores) e um **aviso sobre os nomes do estado**: "Os campos `toras` e `trabalhadores` vêm do Kit Inicial e foram mantidos para a tela do kit continuar funcionando sem alterar a cena Phaser: `toras` é a cevada em estoque e `trabalhadores` são os cervejeiros ocupados. Na tela aparecem como Cevada e Cervejeiros."
- [ ] T076 Executar o roteiro de 13 passos de `specs/001-cervejaria-tempo-real/quickstart.md` e confirmar os 14 eventos no Painel (SC-004); corrigir divergências
- [ ] T077 Commit `docs: README e revisão final`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Etapa 0 (Setup)** → **Etapa 1 (Foundational)** → etapas 2 a 8 **em ordem**, porque todas
  editam os mesmos três arquivos (`server.py`, `regras.py`, `client/index.html`) e cada etapa
  tem seu commit.
- **Polish** depois da etapa 8.

### User Story Dependencies

- **US1** (etapa 2 e T032, T034, T036 da etapa 4): depende só da etapa 1.
- **US2** (etapas 3, 4 e disputa T051/T054 da etapa 6): precisa da temporada aberta (US1).
- **US3** (etapa 5): precisa de abertura (US1) e de obras (US2).
- **US5** (etapa 6): precisa de abertura (US1); o congelamento é validado sobre US3.
- **US6** (etapa 7): precisa de eventos já existentes.
- **US4** (etapa 8): precisa da conclusão de obra (US3).

### Within Each Etapa

- Testes primeiro e falhando → `regras.py` → `server.py` → `client/index.html` → validação →
  commit.

### Parallel Opportunities

- [P] só entre arquivos diferentes da mesma etapa: um teste em `tests/test_regras.py` e um em
  `tests/test_servidor.py` (T009/T010, T017/T018, T024/T025, T031/T033, T049/T050, T061/T062).
  Testes do mesmo arquivo na mesma etapa são escritos em sequência.
- Na etapa 0, T002 e T006; no Polish, T074 e T075.
- Entre etapas não há paralelismo: mesmos arquivos e um commit por etapa.

---

## Parallel Example: Etapa 8 (User Story 4)

```text
Task: "T061 Testar motivo_recusa_engarrafamento em tests/test_regras.py"
Task: "T062 Testar criação do lote em concluir_obra em tests/test_servidor.py"
```

(T063 e T064 estão no mesmo arquivo de T062; escreva-os em sequência.)

---

## Implementation Strategy

### MVP First (Etapas 0–2)

1. Etapa 0 → Etapa 1 → Etapa 2 (US1).
2. **PARAR e VALIDAR**: duas abas veem a temporada abrir ao mesmo tempo.

### Incremental Delivery

Cada etapa seguinte acrescenta um pedaço do fluxo de eventos, termina com `pytest` verde, uma
validação com abas e um commit: construir (3) → recusa (4) → tempo (5) → encerramento/disputa (6)
→ contadores (7) → cervejaria e lotes (8).

---

## Notes

- [P] = arquivos diferentes na mesma etapa, sem dependência pendente.
- Confirme que cada teste falha antes de implementar.
- Um commit por etapa (T008, T016, T023, T030, T039, T048, T057, T060, T073) + commit final T077.
- Não alterar a cena Phaser nem as versões de CDN do kit.
