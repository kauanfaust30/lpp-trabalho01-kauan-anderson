# Research: Cervejaria Artesanal em Tempo Real

Todas as escolhas de stack vieram do usuário; esta fase resolve **como** usá-las sem ferir a
constituição. Nenhum item ficou como NEEDS CLARIFICATION.

## R1. Divisão entre `server.py` e `regras.py`

- **Decision**: `regras.py` só com regras puras: constantes, `estado_inicial()`,
  `motivo_recusa_<acao>(estado, ...) -> str | None` e `retrato(estado, agora) -> dict`. Nenhuma
  função ali altera o estado ou emite eventos. Em `server.py`, cada handler escreve, em linhas
  visíveis: validar (chama a regra) → recusar só para o `sid` → alterar o estado → `emit` →
  comentário do porquê.
- **Rationale**: o fluxo orientado a eventos fica legível onde os eventos acontecem (pedido do
  usuário); as regras continuam testáveis sem servidor (Princípio VI); validar e alterar ficam
  juntos, sem `await` no meio (Princípio IV).
- **Alternatives considered**: funções `aplicar_*` em `regras.py` (esconderiam a alteração do
  estado fora do handler); tudo em `server.py` (regras mais difíceis de testar).

## R2. Disputa entre pedidos simultâneos

- **Decision**: confiar no laço único do asyncio: cada handler valida e altera sem `await` no
  meio; o primeiro pedido processado vence e o segundo já vê o estado alterado e é recusado.
  Sem locks.
- **Rationale**: uma corrotina só cede a vez em um `await`; sem `await` entre checagem e mutação
  não há intercalação. Atende FR-005 e os cenários de disputa.
- **Alternatives considered**: `asyncio.Lock` (desnecessário e esconde o ponto didático); fila de
  comandos (exagero).

## R3. Temporizadores

- **Decision**: `sio.start_background_task` para três tipos de tarefa, todas em `server.py`:
  1. **produção**: iniciada na abertura; laço `await sio.sleep(INTERVALO_PRODUCAO)` → se a fase
     não for "aberta", sai → senão `estado["toras"] += estado["producao"]` e emite
     `recurso.produzido`;
  2. **obra**: uma por obra; `await sio.sleep(TEMPO_OBRA)` → se fase ≠ "aberta", sai (congelada)
     → senão conclui (libera cervejeiro, +5 de produção, cria lote), emite
     `construcao.concluida` e depois `lote.pronto`, e inicia o prazo do lote;
  3. **prazo do lote**: um por lote; `await sio.sleep(PRAZO_LOTE)` → se fase "aberta" e lote
     ainda pendente → remove e emite `lote.perdido`.
- **Rationale**: revalidar depois do `sleep` implementa o congelamento no encerramento sem
  cancelar tarefas; como "encerrada" é final, não há retomada.
- **Alternatives considered**: "tick" único varrendo tudo (menos legível); `asyncio.create_task`
  (o usuário pediu a API do `sio`).

## R4. Tempo restante para quem conecta no meio

- **Decision**: obras e lotes guardam o instante de término (`time.monotonic()`); `retrato()`
  calcula `restante` a partir de `encerrada_em` (se encerrada, congela) ou de `agora`, recebido
  como parâmetro para os testes não dependerem do relógio.
- **Rationale**: atende "participante que conecta no meio" e o congelamento.
- **Alternatives considered**: contador decrementado por tarefa (mais estado e mais tarefas).

## R5. Papel e Mestre único

- **Decision**: o cliente envia `auth={nome, papel}` (já assim no kit). No `connect`, sem `await`
  antes da decisão, o servidor verifica se já há Mestre; se houver, aceita a conexão técnica, não
  registra o participante e emite `operacao.recusada` só para aquele `sid`; o cliente reage
  voltando à tela de entrada e desconectando. Pedidos de `sid` não registrado são recusados. A
  vaga é liberada no `disconnect` do Mestre.
- **Rationale**: a recusa continua sendo evento do domínio (Princípio III) e aparece no Painel.
- **Alternatives considered**: `ConnectionRefusedError` (vira `connect_error`, fora do contrato e
  do Painel); rebaixar para Jogador (rejeitado na clarificação).

## R6. Formato dos fatos e nomes de campos

- **Decision**: todo fato leva `estado` (retrato completo) + `causa` + campos próprios. O retrato
  **mantém os nomes que o kit já lê** (`fase`, `toras`, `trabalhadores`, `limite`, `producao`,
  `intervalo`, `custo`, `tempo_obra`, `concluidas`, `em_obra`) e acrescenta `cerveja`,
  `prazo_lote`, `obras`, `lotes`. Os mesmos nomes são usados no estado interno do servidor, para
  não haver tradução.
- **Rationale**: o kit faz `Object.assign(estado, d.estado)` e a cena Phaser lê esses campos;
  manter os nomes evita mexer na cena e em `resumir`. Só os textos exibidos mudam para cevada e
  cervejeiros.
- **Alternatives considered**: renomear para `cevada`/`cervejeiros` (obrigaria alterar a cena
  Phaser, vetado pelo usuário); camada de tradução no servidor (código extra sem ganho).

## R7. Adaptação do cliente do kit

- **Decision**:
  - **Cena Phaser intocada.** Cada escuta chama só métodos `jogo.*` existentes:
    `estado.sincronizado` → `mostrarEstado`; `cervejaria.iniciada` → `vilaIniciada`;
    `construcao.iniciada` → `obraIniciada`; `construcao.concluida` → `obraConcluida`;
    `recurso.produzido` → `recursoProduzido`; `operacao.recusada` → `recusado`;
    `cervejaria.encerrada` → `vilaEncerrada`.
  - **Lotes só com Vue**: `lote.pronto`, `lote.engarrafado` e `lote.perdido` atualizam o estado
    (`atualizar(d)`) e um aviso (`avisar`); a lista vem de `estado.lotes` em um `v-for` com botão
    "Engarrafar" (só Jogador) e o `restante` enviado pelo servidor. Nenhum método Phaser novo e
    nenhum método existente reaproveitado para lote (evita, por ex., tremer a tela como recusa).
  - **Textos**: trocar rótulos exibidos (Toras → Cevada, Trabalhadores → Cervejeiros, título,
    texto de `resumir`), mantendo os campos internos.
  - **Botões**: Construir com escolha de tipo (maltaria, tanque, adega).
  - Contadores por evento na ETAPA 7 (o kit já conta em `contadores`) e rodapé com os nomes.
  - Versões de CDN do kit mantidas: Vue 3.5.13, Socket.IO 4.7.5, Phaser 3.90.0.
- **Rationale**: atende o pedido de manter o kit e não alterar a cena; Vue já reage ao estado.
- **Alternatives considered**: métodos Phaser para lote (vetado); contagem regressiva calculada
  no cliente (o `restante` atualizado a cada fato, pelo menos a cada 5 s, é suficiente e mantém o
  cliente sem cálculo).

## R8. Testes

- **Decision**: `tests/test_regras.py` (funções puras) e `tests/test_servidor.py`, que chama os
  handlers e os passos de temporizador com `asyncio.run`, substituindo `sio.emit` por um gravador
  (monkeypatch) e `sio.sleep` por uma versão instantânea, para verificar estado alterado, evento,
  dados e destinatário (`to=sid` × todos). Única dependência nova: `pytest`.
- **Rationale**: rápido, determinístico, sem plugins extras.
- **Alternatives considered**: pytest-asyncio (plugin a mais); ponta a ponta com cliente real
  (fica no quickstart com duas abas).
