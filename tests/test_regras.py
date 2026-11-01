"""Testes das regras puras da cervejaria (regras.py)."""

import regras


def test_estado_inicial():
    estado = regras.estado_inicial()

    assert estado["fase"] == "aguardando"
    assert estado["toras"] == 150
    assert estado["producao"] == 10
    assert estado["cerveja"] == 0
    assert estado["concluidas"] == 0
    assert estado["obras"] == {}
    assert estado["lotes"] == {}
    assert estado["participantes"] == {}
    assert estado["mestre_sid"] is None
    assert estado["encerrada_em"] is None
    assert estado["proximo_id"] == 1


def test_estado_inicial_devolve_dicionario_novo():
    primeiro = regras.estado_inicial()
    primeiro["obras"][1] = "obra"

    assert regras.estado_inicial()["obras"] == {}


def test_constantes_da_especificacao():
    assert regras.CEVADA_INICIAL == 150
    assert regras.CUSTO_CONSTRUCAO == 50
    assert regras.TEMPO_OBRA == 8
    assert regras.INTERVALO_PRODUCAO == 5
    assert regras.PRODUCAO_INICIAL == 10
    assert regras.GANHO_POR_OBRA == 5
    assert regras.LIMITE_CERVEJEIROS == 2
    assert regras.PRAZO_LOTE == 20
    assert regras.CERVEJA_POR_LOTE == 1
    assert regras.TIPOS_CONSTRUCAO == ("maltaria", "tanque", "adega")
