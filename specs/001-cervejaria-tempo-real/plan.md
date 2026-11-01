# Implementation Plan: Cervejaria Artesanal em Tempo Real

**Branch**: `main` | **Date**: 2026-11-01 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-cervejaria-tempo-real/spec.md`

## Summary

Cervejaria cooperativa em tempo real: o cliente só **pede** (`*_solicitada`), o servidor
**decide** e anuncia o **fato** (`*_iniciada`, `*_concluida`, `operacao.recusada`…), e todas as
abas reagem. Fatos de tempo (produção de cevada, fim de obra, lote que passa do ponto) nascem de
tarefas em segundo plano do servidor.

Abordagem: completar o Kit Inicial sem recriá-lo.

- `server.py` (kit) ganha os handlers e os temporizadores (`sio.start_background_task` +
  `sio.sleep`). **Cada handler mostra, em linhas visíveis, o paradigma**: validar → recusar só
  para o `sid` → alterar o estado → `emit` → comentário do porquê.
- `regras.py` (novo) contém **só regras puras**: constantes, estado inicial, funções que devolvem
  o motivo de recusa (ou `None`) e o retrato público do estado. Nenhuma função ali altera estado
  nem emite eventos.
- `client/index.html` (kit) ganha as escutas `ouvir(...)`, os pedidos `pedir(...)`, a lista de
  lotes em Vue (`v-for`), os contadores do Painel e o rodapé. **A cena Phaser não é alterada**;
  só são chamados os métodos `jogo.*` que já existem.

## Leitura do kit: campos de estado que o `client/index.html` lê

Lidos em `client/index.html` (template Vue, `resumir`, `porMinuto` e cena Phaser). **Esses nomes
internos são mantidos** no estado do servidor e no contrato; mudam só os textos exibidos.

| Campo (nome interno mantido) | Onde o kit lê | Significado na cervejaria | Texto exibido (novo) |
|------------------------------|---------------|---------------------------|----------------------|
| `fase` | template; `mostrarEstado` (`"aberta"`, `"encerrada"`); início `"aguardando"` | fase da temporada | "Temporada: aguardando/aberta/encerrada" |
| `toras` | template; `resumir` | **cevada** em estoque | "🌾 Cevada" |
| `trabalhadores` | template (`<progress>`); `resumir` | **cervejeiros ocupados** | "🧑‍🍳 Cervejeiros ocupados" |
| `limite` | template; `resumir` | limite de cervejeiros (2) | "/2" |
| `producao` | `porMinuto`; `recursoProduzido` | cevada por intervalo | "(+N/min)" |
| `intervalo` | `porMinuto` | segundos entre produções (5) | — |
| `custo` | botão Construir; `obraIniciada` | custo em cevada (50) | "custo 50 de cevada" |
| `tempo_obra` | `mostrarEstado`; `obraIniciada` | duração da obra (8 s) | — |
| `concluidas` | template; `mostrarEstado` | obras concluídas | "🏭 Construções: N concluídas" |
| `em_obra` | template; `mostrarEstado` | obras em andamento | "N em obra" |
| `d.estado` | `atualizar` (`Object.assign`) | retrato completo enviado pelo servidor | — |
| `d.causa` | `registrar` (Painel) | causa do fato | "causa: …" |

Campos **novos** (sem equivalente no kit), lidos só pela parte Vue: `cerveja`, `prazo_lote`,
`obras` (lista) e `lotes` (lista). Glossário completo em [data-model.md](data-model.md).

Limitação aceita: a cena Phaser mostra o emoji 🪵 nos textos flutuantes de `obraIniciada` e
`recursoProduzido`; como a cena não será alterada, esse ícone permanece.

## Technical Context

**Language/Version**: Python 3.13 (venv do projeto) no servidor; JavaScript no navegador.

**Primary Dependencies**: python-socketio 5.x (ASGI) e uvicorn no servidor. No cliente, **as
versões do kit, sem troca**: Vue `3.5.13` (unpkg), Socket.IO client `4.7.5` (cdn.socket.io) e
Phaser `3.90.0` (jsDelivr).

**Storage**: N/A. Estado em memória do processo; perde-se ao reiniciar (decisão da spec).

**Testing**: pytest (a ser adicionado em `requirements.txt`). `tests/test_regras.py` testa as
regras puras; `tests/test_servidor.py` chama os handlers com `asyncio.run` e um `sio.emit`
substituído por um gravador, verificando mudança de estado, evento e destinatário.

**Target Platform**: servidor local (Windows/Linux) via `uvicorn server:app`; navegador desktop.

**Project Type**: aplicação web de tempo real (servidor de eventos + página única estática).

**Performance Goals**: fato visível em outra aba em < 1 s (SC-001); temporizadores com desvio
< 1 s (SC-005).

**Constraints**: estado só no servidor; nenhum `await` entre validar e alterar; cena Phaser
intocada; versões de CDN do kit intocadas; tudo em português para o usuário.

**Scale/Scope**: 2 a ~10 abas simultâneas, uma única cervejaria, 14 eventos.

## Forma de cada handler em `server.py`

Todo handler de pedido segue a mesma sequência, sem `await` antes do passo 3 terminar:

```text
1. validar   -> motivo = regras.motivo_recusa_<acao>(estado, ...)   # função pura
2. recusar   -> se motivo: await sio.emit("operacao.recusada", {...}, to=sid); return
3. alterar   -> linhas explícitas no handler (ex.: estado["toras"] -= CUSTO_CONSTRUCAO)
4. emit      -> await sio.emit("<fato>", {...})   # todos
5. comentário do porquê em cada @sio.on e cada sio.emit
```

Os temporizadores seguem o mesmo padrão: `await sio.sleep(...)` → revalidar (mesma temporada,
fase aberta, item ainda existe) → alterar → `emit`.

## Reabertura da temporada (FR-019 — mudança de requisito de 2026-11-01)

- **Mesmos eventos**: `cervejaria.abertura_solicitada` → `cervejaria.iniciada` (com o campo
  extra `reaberta: true`). Nenhum evento novo.
- **Regra** (`regras.py`): `motivo_recusa_abertura` passa a aceitar a fase `"encerrada"` para o
  Mestre; continua recusando `"aberta"` ("A temporada já está aberta.") e quem não é Mestre.
  `estado_inicial()` ganha o campo interno `temporada = 0` (fora do retrato).
- **Handler** (`server.py`, `abertura_solicitada`): validar → recusar → se a fase era
  `"encerrada"`, reiniciar o estado no mesmo dicionário com `regras.estado_inicial()`,
  preservando `participantes`, `mestre_sid` e `temporada` → `temporada += 1`, `fase = "aberta"`
  → emitir `cervejaria.iniciada` → iniciar `ciclo_producao(temporada)`. Sem `await` entre validar
  e terminar a reinicialização.
- **Temporizadores**: `ciclo_producao(temporada)`, `esperar_obra(obra_id, temporada)` e
  `esperar_prazo_lote(lote_id, temporada)` recebem o número da temporada ao nascer e, ao acordar,
  não fazem nada se `estado["temporada"]` mudou. Sem isso, uma obra antiga de id 1 poderia
  concluir a obra nova de id 1, já que `proximo_id` volta a 1.
- **Cliente** (Vue, sem alterar `criarJogo` nem a cena Phaser): ao ouvir `cervejaria.iniciada`
  com `reaberta: true`, limpa o `#jogo`, cria uma cena nova com `jogo = criarJogo()` (o `jogo`
  passa de `const` para `let`), chama `jogo.iniciar("jogo")` e `jogo.mostrarEstado(d.estado)`.
  Limitação aceita: a instância Phaser antiga não é destruída (não há acesso a ela sem mudar
  `criarJogo`); só o canvas dela sai da página.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano cumpre | Status |
|-----------|---------------------|--------|
| I. Código simples e legível | Handlers curtos com a sequência fixa acima; `regras.py` só com funções puras pequenas; sem frameworks extras | ✅ |
| II. Servidor como fonte da verdade | Todo fato leva `estado` completo; o cliente faz `Object.assign(estado, d.estado)`; a lista de lotes e os tempos restantes vêm do servidor | ✅ |
| III. Pedidos separados de fatos | Pedidos `objeto.acao_solicitada`, fatos `objeto.acao_no_passado`; toda recusa vira `operacao.recusada` só para o `sid` de quem pediu | ✅ |
| IV. Validar e alterar sem `await` | Passos 1–3 do handler sem `await`; temporizadores revalidam depois do `sleep` e antes de alterar | ✅ |
| V. Eventos comentados com o porquê | Passo 5 obrigatório em cada `@sio.on`, `sio.emit`, `ouvir(...)` e `pedir(...)` | ✅ |
| VI. Teste primeiro com pytest | Testes de regras e de handlers escritos antes; cada pedido com teste de aceite e de recusa | ✅ |
| VII. Mensagens em português | Motivos de recusa fechados em [contracts/eventos.md](contracts/eventos.md), todos acionáveis | ✅ |

Observação: o Princípio III dá `pedir_*`/`*_criado` como **exemplo**; a convenção da spec
(`*.acao_solicitada`/`*.acao_no_passado`) cumpre a mesma regra. Não é violação.

**Re-check pós-Fase 1**: ✅ sem violações. Manter os nomes internos do kit (`toras`,
`trabalhadores`) não fere o Princípio I porque os textos exibidos e o glossário dizem o que cada
campo representa.

## Project Structure

### Documentation (this feature)

```text
specs/001-cervejaria-tempo-real/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: decisões técnicas
├── data-model.md        # Fase 1: entidades, estados, validações e glossário
├── quickstart.md        # Fase 1: como rodar e validar com duas abas
├── contracts/
│   └── eventos.md       # Fase 1: contrato dos 14 eventos, números e recusas
└── tasks.md             # Fase 2 (/speckit-tasks; não criado aqui)
```

### Source Code (repository root)

```text
server.py                # KIT: mantém sio/app; handlers (validar → recusar → alterar → emit) e temporizadores
regras.py                # NOVO: constantes, estado inicial, motivo_recusa_*(), retrato() — só funções puras
requirements.txt         # KIT: + pytest
client/
├── index.html           # KIT: ETAPAS (ouvir/pedir), lotes em Vue v-for, textos, contadores, rodapé; cena Phaser intocada
└── assets/              # KIT: inalterado
tests/
├── test_regras.py       # regras puras: motivos de recusa, limites, retrato
└── test_servidor.py     # handlers e passos de temporizador: estado, destinatário, disputa, Mestre único
```

**Structure Decision**: projeto único na raiz, preservando o Kit Inicial (`server.py` +
`client/`). A única peça nova de código é `regras.py`, restrita a regras puras para que possam
ser testadas sem servidor, enquanto o fluxo de eventos fica legível em `server.py`.

## Complexity Tracking

Sem violações da constituição; nada a justificar.
