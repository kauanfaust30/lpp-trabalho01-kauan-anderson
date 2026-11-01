"""Regras puras da Cervejaria Artesanal.

GLOSSÁRIO — os nomes de campo vêm do Kit Inicial e foram mantidos para a tela
do kit continuar funcionando:
  - `toras` é a CEVADA em estoque;
  - `trabalhadores` são os CERVEJEIROS OCUPADOS (= obras em andamento);
  - `limite` é o máximo de cervejeiros ocupados (2).
A fase "aguardando" do código é a fase "não aberta" da spec (temporada ainda
não aberta pelo Mestre).

Este módulo só tem funções puras: nenhuma delas altera o estado nem emite
eventos. Quem altera o estado e emite é o server.py, dentro de cada handler.
"""

# Números da especificação (docs/especificacao.md, seção 2)
CEVADA_INICIAL = 150
CUSTO_CONSTRUCAO = 50
TEMPO_OBRA = 8             # segundos
INTERVALO_PRODUCAO = 5     # segundos
PRODUCAO_INICIAL = 10      # cevada por intervalo
GANHO_POR_OBRA = 5         # cevada a mais por intervalo, por obra concluída
LIMITE_CERVEJEIROS = 2
PRAZO_LOTE = 20            # segundos para engarrafar
CERVEJA_POR_LOTE = 1
TIPOS_CONSTRUCAO = ("maltaria", "tanque", "adega")


def estado_inicial():
    """Devolve um estado novo da cervejaria, antes de o Mestre abrir a temporada."""
    return {
        "fase": "aguardando",
        "toras": CEVADA_INICIAL,
        "producao": PRODUCAO_INICIAL,
        "cerveja": 0,
        "concluidas": 0,
        "obras": {},           # id -> obra em andamento
        "lotes": {},           # id -> lote pendente
        "participantes": {},   # sid -> {"nome", "papel"}
        "mestre_sid": None,
        "encerrada_em": None,  # instante do encerramento (congela os tempos)
        "proximo_id": 1,
    }
