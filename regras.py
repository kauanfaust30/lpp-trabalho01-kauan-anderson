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

import math

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

# Motivo reaproveitado por todas as regras: pedido de uma aba que o servidor não registrou.
MOTIVO_NAO_REGISTRADO = "Você não está na cervejaria. Entre novamente."


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


def motivo_recusa_abertura(estado, participante):
    """Por que o pedido de abrir a temporada deve ser recusado, ou None se pode abrir."""
    if participante is None:
        return MOTIVO_NAO_REGISTRADO
    if participante["papel"] != "mestre":
        return "Apenas o Mestre pode abrir a temporada."
    if estado["fase"] == "aberta":
        return "A temporada já está aberta."
    if estado["fase"] == "encerrada":
        return "A temporada já foi encerrada. Reinicie o servidor para começar outra."
    return None


def motivo_recusa_encerramento(estado, participante):
    """Por que o pedido de encerrar a temporada deve ser recusado, ou None se pode encerrar."""
    if participante is None:
        return MOTIVO_NAO_REGISTRADO
    if participante["papel"] != "mestre":
        return "Apenas o Mestre pode encerrar a temporada."
    if estado["fase"] == "aguardando":
        return "A temporada ainda não foi aberta."
    if estado["fase"] == "encerrada":
        return "A temporada já está encerrada."
    return None


def motivo_recusa_fase(estado):
    """Motivo comum a construir e engarrafar: só vale com a temporada aberta."""
    if estado["fase"] == "aguardando":
        return "A temporada não está aberta."
    if estado["fase"] == "encerrada":
        return "A temporada está encerrada."
    return None


def motivo_recusa_construcao(estado, participante, tipo):
    """Por que o pedido de construir deve ser recusado, ou None se pode construir."""
    if participante is None:
        return MOTIVO_NAO_REGISTRADO
    if participante["papel"] != "jogador":
        return "Apenas Jogadores podem construir."
    motivo_fase = motivo_recusa_fase(estado)
    if motivo_fase:
        return motivo_fase
    if tipo not in TIPOS_CONSTRUCAO:
        return "Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."
    if estado["toras"] < CUSTO_CONSTRUCAO:
        falta = CUSTO_CONSTRUCAO - estado["toras"]
        return f"Cevada insuficiente: faltam {falta}. Aguarde a próxima colheita."
    if len(estado["obras"]) >= LIMITE_CERVEJEIROS:
        return "Nenhum cervejeiro livre. Aguarde uma obra terminar."
    return None


def motivo_recusa_engarrafamento(estado, participante, lote_id):
    """Por que o pedido de engarrafar deve ser recusado, ou None se pode engarrafar."""
    if participante is None:
        return MOTIVO_NAO_REGISTRADO
    if participante["papel"] != "jogador":
        return "Apenas Jogadores podem engarrafar."
    motivo_fase = motivo_recusa_fase(estado)
    if motivo_fase:
        return motivo_fase
    if lote_id not in estado["lotes"]:
        return "Este lote não está mais disponível."
    return None


def motivo_recusa_conexao(estado, papel):
    """Por que a entrada deve ser recusada, ou None: só pode haver um Mestre por vez."""
    if papel == "mestre" and estado["mestre_sid"] is not None:
        return "Já existe um Mestre na cervejaria. Entre como Jogador."
    return None


def segundos_restantes(instante_final, estado, agora):
    """Segundos (arredondados para cima, nunca negativos) até `instante_final`.

    Com a temporada encerrada, o relógio para no instante do encerramento.
    """
    referencia = estado["encerrada_em"] if estado["encerrada_em"] is not None else agora
    return max(0, math.ceil(instante_final - referencia))


def obras_publicas(estado, agora):
    """Obras em andamento, com o tempo que falta para terminar."""
    return [
        {"id": o["id"], "tipo": o["tipo"], "pedida_por": o["pedida_por"],
         "restante": segundos_restantes(o["termina_em"], estado, agora)}
        for o in estado["obras"].values()
    ]


def lotes_publicos(estado, agora):
    """Lotes pendentes, com o tempo que falta para passarem do ponto."""
    return [
        {"id": l["id"], "obra_id": l["obra_id"],
         "restante": segundos_restantes(l["vence_em"], estado, agora)}
        for l in estado["lotes"].values()
    ]


def retrato(estado, agora):
    """Parte pública do estado, enviada em todo fato. Mantém os nomes que o kit lê."""
    obras = obras_publicas(estado, agora)
    return {
        "fase": estado["fase"],
        "toras": estado["toras"],                 # cevada
        "producao": estado["producao"],
        "intervalo": INTERVALO_PRODUCAO,
        "custo": CUSTO_CONSTRUCAO,
        "tempo_obra": TEMPO_OBRA,
        "trabalhadores": len(obras),              # cervejeiros ocupados
        "limite": LIMITE_CERVEJEIROS,
        "concluidas": estado["concluidas"],
        "em_obra": len(obras),
        "cerveja": estado["cerveja"],
        "prazo_lote": PRAZO_LOTE,
        "obras": obras,
        "lotes": lotes_publicos(estado, agora),
    }
