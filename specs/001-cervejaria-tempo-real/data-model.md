# Data Model: Cervejaria Artesanal em Tempo Real

Tudo vive em memória no servidor, em um único dicionário `estado` criado por
`regras.estado_inicial()`. O cliente recebe apenas o **retrato público** (seção final) e nunca
altera nada. Os nomes de campo lidos pelo kit (`client/index.html`) são mantidos.

## Glossário (nome interno → significado)

| Nome interno | Significado na cervejaria | Origem do nome |
|--------------|---------------------------|----------------|
| `toras` | cevada em estoque | kit |
| `trabalhadores` | cervejeiros ocupados (= obras em andamento) | kit |
| `limite` | limite de cervejeiros ocupados | kit |
| `producao` | cevada produzida por intervalo | kit |
| `intervalo` | segundos entre produções | kit |
| `custo` | cevada gasta por construção | kit |
| `tempo_obra` | segundos de uma obra | kit |
| `concluidas` | obras concluídas | kit |
| `em_obra` | obras em andamento | kit |
| `fase` | fase da temporada: `"aguardando"` (= "não aberta" na spec), `"aberta"`, `"encerrada"` | kit |
| `cerveja` | cerveja engarrafada | novo |
| `prazo_lote` | segundos para engarrafar um lote | novo |
| `obras` / `lotes` | listas de obras em andamento / lotes pendentes | novo |

## Números (conferidos com a spec)

| Constante em `regras.py` | Valor | Campo público |
|--------------------------|-------|---------------|
| `CEVADA_INICIAL` | **150** | `toras` inicial |
| `CUSTO_CONSTRUCAO` | **50** | `custo` |
| `TEMPO_OBRA` | **8 s** | `tempo_obra` |
| `INTERVALO_PRODUCAO` | **5 s** | `intervalo` |
| `PRODUCAO_INICIAL` | **10** | `producao` inicial |
| `GANHO_POR_OBRA` | **+5** por obra concluída | — |
| `LIMITE_CERVEJEIROS` | **2** | `limite` |
| `PRAZO_LOTE` | **20 s** | `prazo_lote` |
| `CERVEJA_POR_LOTE` | **1** | — |
| `TIPOS_CONSTRUCAO` | `maltaria`, `tanque`, `adega` | — |

## Estado da cervejaria (temporada)

| Campo | Tipo | Início | Regra |
|-------|------|--------|-------|
| `fase` | `"aguardando"` \| `"aberta"` \| `"encerrada"` | `"aguardando"` | ver transições |
| `toras` | int ≥ 0 | 150 | nunca negativa (FR-005) |
| `producao` | int | 10 | +5 a cada obra concluída |
| `cerveja` | int ≥ 0 | 0 | +1 por lote engarrafado |
| `concluidas` | int | 0 | +1 a cada obra concluída |
| `obras` | dict id → Obra | vazio | só obras em andamento; `len ≤ 2` |
| `lotes` | dict id → Lote | vazio | só lotes pendentes |
| `participantes` | dict sid → Participante | vazio | só conexões aceitas (não vai no retrato) |
| `mestre_sid` | str \| None | None | no máximo um (FR-017; não vai no retrato) |
| `encerrada_em` | float \| None | None | congela os tempos restantes |
| `proximo_id` | int | 1 | gera ids de obras e lotes |
| `temporada` | int | 0 | +1 a cada abertura aceita (1ª abertura → 1); identifica a temporada dos temporizadores; **interno, não vai no retrato** |

Derivados no retrato: `trabalhadores = em_obra = len(obras)`.

### Transições de fase

```text
aguardando --(Mestre: abertura_solicitada)--> aberta --(Mestre: encerramento_solicitado)--> encerrada
                                                ^                                            |
                                                +------(Mestre: abertura_solicitada)---------+
                                                         (reabertura: reinicia o estado)
```

- Abrir em "aberta" é recusado; encerrar em "aguardando" ou "encerrada" é recusado.
- Ao encerrar: `encerrada_em = agora`; obras e lotes ficam como estão (congelados).
- **Reabertura** (abrir com fase `"encerrada"`, FR-019): o estado é trocado por
  `regras.estado_inicial()` **mantendo `participantes`, `mestre_sid` e `temporada`**; depois,
  como em toda abertura aceita, `temporada += 1` e `fase = "aberta"`. A troca é feita no mesmo
  dicionário (`estado.clear(); estado.update(novo)`), sem `await` entre validar e reiniciar.

### Temporizadores e número da temporada

`ciclo_producao`, `esperar_obra` e `esperar_prazo_lote` recebem, ao nascer, o número da
temporada em que foram criados (argumento de `sio.start_background_task`). Ao acordar do
`sleep`, se `estado["temporada"]` for diferente desse número, **não fazem nada**: isso impede
que um temporizador da temporada anterior conclua uma obra (ou perca um lote) da temporada nova
que tenha o mesmo id, já que `proximo_id` volta a 1 na reabertura.

## Participante

| Campo | Tipo | Regra |
|-------|------|-------|
| `nome` | str | "Anônimo" se vazio |
| `papel` | `"mestre"` \| `"jogador"` | Mestre recusado se `mestre_sid` já existe |

Removido no `disconnect`; se era o Mestre, `mestre_sid = None`. Obras e lotes continuam.

## Obra

| Campo | Tipo | Regra |
|-------|------|-------|
| `id` | int | único |
| `tipo` | `maltaria` \| `tanque` \| `adega` | outro valor → recusa |
| `pedida_por` | str | nome de quem pediu |
| `termina_em` | float | `agora + 8` |

**`motivo_recusa_construcao`** (ordem das checagens): 1. `sid` registrado; 2. papel `jogador`;
3. fase `aberta` (motivo diferente para aguardando/encerrada); 4. tipo válido;
5. `toras >= 50` (aceita com exatamente 50); 6. `len(obras) < 2`.

**Alteração no handler**: `toras -= 50`; adiciona a obra.
**Conclusão** (temporizador, só se fase `aberta` e obra existe): remove a obra;
`concluidas += 1`; `producao += 5`; cria um Lote.

## Lote de cerveja

| Campo | Tipo | Regra |
|-------|------|-------|
| `id` | int | único |
| `obra_id` | int | obra de origem |
| `vence_em` | float | `agora + 20` |

Estados: `pendente` (está em `lotes`) → `engarrafado` ou `perdido` (sai de `lotes`).

**`motivo_recusa_engarrafamento`**: 1. `sid` registrado; 2. papel `jogador`; 3. fase `aberta`;
4. lote existe em `lotes`.
**Alteração no handler**: remove o lote; `cerveja += 1`.
**Perda** (temporizador, só se fase `aberta` e lote existe): remove o lote.

## Produção (temporizador)

Só com fase `aberta`: `toras += producao`.

## Retrato público (`estado` enviado em todo fato) — `regras.retrato(estado, agora)`

```text
fase, toras, producao, intervalo, custo, tempo_obra, trabalhadores, limite,
concluidas, em_obra, cerveja, prazo_lote,
obras: [{id, tipo, pedida_por, restante}], lotes: [{id, obra_id, restante}]
```

`restante` = segundos (inteiro arredondado para cima, ≥ 0) até `termina_em`/`vence_em`, medidos
a partir de `encerrada_em` se a temporada estiver encerrada, senão a partir de `agora`.

Não vão no retrato: `participantes`, `mestre_sid`, `encerrada_em`, `proximo_id` e `temporada`.
