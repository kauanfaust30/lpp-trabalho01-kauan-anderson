# Contrato de Eventos

Transporte: Socket.IO. **Pedidos** vão do cliente ao servidor; **fatos** vão do servidor aos
clientes. Todo fato carrega `estado` (retrato público, ver [data-model.md](../data-model.md)) e
`causa`.

- `causa` = `"pedido de <nome>"` para fatos que respondem a um pedido, `"temporizador"` para
  fatos de tempo, `"conexão"` para `estado.sincronizado`.
- Destinatário **todos** = broadcast; **só quem pediu** = `to=sid` do pedido.
- Os campos de `estado` mantêm os nomes do kit: `toras` = cevada, `trabalhadores` = cervejeiros
  ocupados (glossário no data-model).

## Números do contrato (conferidos com a spec)

| Regra | Valor | Campo em `estado` |
|-------|-------|-------------------|
| Cevada inicial | 150 | `toras` |
| Custo de cada construção | 50 de cevada | `custo` |
| Tempo de uma obra | 8 s | `tempo_obra` |
| Intervalo de produção | 5 s | `intervalo` |
| Produção inicial por intervalo | 10 | `producao` |
| Ganho por obra concluída | +5 por intervalo | `producao` |
| Limite de cervejeiros ocupados | 2 | `limite` |
| Prazo para engarrafar | 20 s | `prazo_lote` |
| Cerveja por lote engarrafado | +1 | `cerveja` |

## Conexão

O cliente conecta com `auth = { nome: str, papel: "mestre" | "jogador" }`.

| Situação | Servidor emite | Para |
|----------|----------------|------|
| Aceito | `estado.sincronizado` `{estado, causa: "conexão", papel}` | só o recém-conectado |
| Já existe Mestre e `papel = "mestre"` | `operacao.recusada` `{pedido: "conexao", motivo, causa}` | só o recém-conectado (não registrado) |

## Pedidos (cliente → servidor)

| Evento | Quem pode | Dados |
|--------|-----------|-------|
| `cervejaria.abertura_solicitada` | Mestre | — |
| `cervejaria.encerramento_solicitado` | Mestre | — |
| `construcao.solicitada` | Jogador | `{tipo: "maltaria" \| "tanque" \| "adega"}` |
| `engarrafamento.solicitado` | Jogador | `{lote: int}` |

Todo pedido gera **exatamente um** fato: o fato de aceite (todos) ou `operacao.recusada`
(só quem pediu).

## Fatos (servidor → clientes)

| Evento | Para | Dados além de `estado` e `causa` | Origem |
|--------|------|----------------------------------|--------|
| `estado.sincronizado` | só o recém-conectado | `papel` | conexão |
| `cervejaria.iniciada` | todos | `reaberta` (bool: `true` quando a temporada anterior estava encerrada e o estado foi reiniciado) | pedido |
| `cervejaria.encerrada` | todos | — | pedido |
| `construcao.iniciada` | todos | `obra: {id, tipo, pedida_por}` | pedido |
| `construcao.concluida` | todos | `obra: {id, tipo}` | temporizador (8 s) |
| `recurso.produzido` | todos | `quantidade` | temporizador (5 s) |
| `lote.pronto` | todos | `lote: {id, obra_id}`, `prazo` (20) | temporizador, logo após `construcao.concluida` |
| `lote.engarrafado` | todos | `lote: {id}`, `por` | pedido |
| `lote.perdido` | todos | `lote: {id}` | temporizador (20 s) |
| `operacao.recusada` | só quem pediu | `pedido` (nome do evento), `motivo` | pedido |

Após `cervejaria.encerrada`, nenhum `recurso.produzido`, `construcao.concluida`, `lote.pronto`
ou `lote.perdido` é emitido.

**Reabertura (FR-019)**: com a temporada encerrada, o Mestre reabre com o mesmo pedido
`cervejaria.abertura_solicitada`. O servidor reinicia o estado (mantendo participantes e Mestre)
e emite `cervejaria.iniciada` para todos com `reaberta: true` e o `estado` já zerado (cevada 150,
produção 10, cerveja 0, sem obras nem lotes). Nenhum evento novo é criado. Temporizadores da
temporada anterior não emitem nenhum fato depois da reabertura.

## Motivos de recusa (texto exato)

| Situação | `motivo` |
|----------|----------|
| Segundo Mestre | "Já existe um Mestre na cervejaria. Entre como Jogador." |
| Conexão não registrada | "Você não está na cervejaria. Entre novamente." |
| Jogador abre | "Apenas o Mestre pode abrir a temporada." |
| Jogador encerra | "Apenas o Mestre pode encerrar a temporada." |
| Abrir já aberta | "A temporada já está aberta." |
| Encerrar não aberta | "A temporada ainda não foi aberta." |
| Encerrar já encerrada | "A temporada já está encerrada." |
| Mestre constrói | "Apenas Jogadores podem construir." |
| Mestre engarrafa | "Apenas Jogadores podem engarrafar." |
| Construir/engarrafar antes de abrir | "A temporada não está aberta." |
| Construir/engarrafar após encerrar | "A temporada está encerrada." |
| Tipo inválido | "Tipo de construção desconhecido. Escolha maltaria, tanque ou adega." |
| Falta cevada (custo 50) | "Cevada insuficiente: faltam {50 - toras}. Aguarde a próxima colheita." |
| Sem cervejeiro (2 de 2) | "Nenhum cervejeiro livre. Aguarde uma obra terminar." |
| Lote indisponível | "Este lote não está mais disponível." |

## Reação esperada do cliente

A cena Phaser não é alterada; só métodos `jogo.*` existentes são chamados. Lotes são mostrados
pela parte Vue (`v-for` sobre `estado.lotes`).

| Fato | Reação no cliente |
|------|-------------------|
| `estado.sincronizado` | `atualizar(d)`; `jogo.mostrarEstado(d.estado)` |
| `cervejaria.iniciada` | `atualizar(d)`; se `d.reaberta`: recria a cena (limpa `#jogo`, `jogo = criarJogo()`, `jogo.iniciar("jogo")`, `jogo.mostrarEstado(d.estado)`) e avisa "Nova temporada aberta"; senão `jogo.vilaIniciada()`. A função `criarJogo` e a cena Phaser não são alteradas |
| `construcao.iniciada` | `atualizar(d)`; `jogo.obraIniciada(d.estado)` |
| `construcao.concluida` | `atualizar(d)`; `jogo.obraConcluida(d.estado)` |
| `recurso.produzido` | `atualizar(d)`; `jogo.recursoProduzido(d.estado)` |
| `lote.pronto` | `atualizar(d)`; aviso "🍺 Lote N pronto: engarrafe em 20 s"; lote aparece na lista Vue |
| `lote.engarrafado` | `atualizar(d)`; aviso de sucesso; lote sai da lista |
| `lote.perdido` | `atualizar(d)`; aviso "Lote N passou do ponto"; lote sai da lista |
| `operacao.recusada` | aviso vermelho com o motivo; `jogo.recusado(d.motivo)`; se `pedido = "conexao"`, volta à tela de entrada |
| `cervejaria.encerrada` | `atualizar(d)`; `jogo.vilaEncerrada()` |
