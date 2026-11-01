# Quickstart: validar a Cervejaria com duas abas

## Pré-requisitos

- Python 3.11+ (o projeto usa o venv `.venv` com 3.13).
- Navegador com acesso à internet (Vue, Phaser e Socket.IO vêm por CDN).

## Instalar e rodar

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                      # todos os testes devem passar
uvicorn server:app --reload
```

Abra `http://127.0.0.1:8000` em **duas abas** (A e B).

## Roteiro de validação

Eventos e motivos esperados: [contracts/eventos.md](contracts/eventos.md).

| # | Ação | Resultado esperado | Spec |
|---|------|--------------------|------|
| 1 | A entra como **Mestre**; B entra como **Jogador** | Cada aba recebe só o seu `estado.sincronizado`; fase "aguardando" | US1 |
| 2 | Uma 3ª aba tenta entrar como Mestre | Só ela recebe `operacao.recusada` ("Já existe um Mestre…") e volta à entrada; A e B não mudam | FR-017 |
| 3 | B clica em Construir antes de abrir | Só B recebe a recusa "A temporada não está aberta."; o Painel de A não muda | Cenário 1 |
| 4 | A clica em Abrir temporada | As duas abas mostram "Temporada aberta" em < 1 s | SC-001 |
| 5 | Esperar 5 s sem clicar | `recurso.produzido` nas duas abas (causa: temporizador); cevada 150 → 160 | US3 |
| 6 | B constrói uma maltaria | `construcao.iniciada` nas duas abas; cevada −50; cervejeiros 1/2 | US2 |
| 7 | Esperar 8 s | `construcao.concluida` e `lote.pronto`; cervejeiros 0/2; produção 15 | US3/US4 |
| 8 | B clica em Engarrafar no lote | `lote.engarrafado` nas duas abas; cerveja 1 | US4 |
| 9 | Construir outra obra e **não** engarrafar o lote por 20 s | `lote.perdido` nas duas abas | Cenário 4 |
| 10 | Duas abas de Jogador clicam Construir juntas com 1/2 ocupado | Um `construcao.iniciada`, uma recusa só para o outro; 2/2 | Cenário 3 |
| 11 | A encerra com obra/lote em andamento | `cervejaria.encerrada`; nenhum fato de temporizador depois; obra e lote congelados na tela | US5 |
| 12 | B tenta construir ou engarrafar | Só B recebe "A temporada está encerrada." | FR-011 |
| 13 | Conferir o Painel e o rodapé | Contador por evento; nomes Kauan Faust e Anderson Moreira | FR-013–015 |
| 14 | Com a temporada encerrada e uma obra congelada, A clica em Abrir temporada | `cervejaria.iniciada` nas duas abas; mapa redesenhado sem casas nem canteiros; cevada 150, produção 10, cerveja 0, cervejeiros 0/2; nos 10 s seguintes nenhum `construcao.concluida`/`lote.pronto` da obra antiga, só `recurso.produzido` da nova temporada | FR-019 / Cenário 6 |
| 15 | B tenta abrir a temporada (aberta) | Só B recebe "Apenas o Mestre pode abrir a temporada."; A clicando de novo recebe "A temporada já está aberta." | FR-001 |

## Critério de pronto

- `pytest` verde.
- Roteiro acima completo sem divergência; os 14 eventos aparecem no Painel (SC-004).
