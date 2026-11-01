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


# ----- retrato público do estado (Etapa 1) -----

CHAVES_DO_RETRATO = {
    "fase", "toras", "producao", "intervalo", "custo", "tempo_obra",
    "trabalhadores", "limite", "concluidas", "em_obra", "cerveja",
    "prazo_lote", "obras", "lotes",
}


def estado_com_obra_e_lote():
    estado = regras.estado_inicial()
    estado["obras"][1] = {"id": 1, "tipo": "maltaria", "pedida_por": "Ana", "termina_em": 108.0}
    estado["lotes"][2] = {"id": 2, "obra_id": 1, "vence_em": 120.0}
    return estado


def test_retrato_tem_exatamente_as_chaves_publicas():
    retrato = regras.retrato(regras.estado_inicial(), 100.0)

    assert set(retrato) == CHAVES_DO_RETRATO


def test_retrato_esconde_campos_internos():
    retrato = regras.retrato(regras.estado_inicial(), 100.0)

    for interno in ("participantes", "mestre_sid", "encerrada_em", "proximo_id"):
        assert interno not in retrato


def test_retrato_traz_os_numeros_da_especificacao():
    retrato = regras.retrato(regras.estado_inicial(), 100.0)

    assert retrato["intervalo"] == 5
    assert retrato["custo"] == 50
    assert retrato["tempo_obra"] == 8
    assert retrato["limite"] == 2
    assert retrato["prazo_lote"] == 20


def test_retrato_conta_cervejeiros_ocupados_pelas_obras():
    retrato = regras.retrato(estado_com_obra_e_lote(), 100.0)

    assert retrato["trabalhadores"] == 1
    assert retrato["em_obra"] == 1


def test_retrato_lista_obras_e_lotes_com_tempo_restante():
    retrato = regras.retrato(estado_com_obra_e_lote(), 100.0)

    assert retrato["obras"] == [{"id": 1, "tipo": "maltaria", "pedida_por": "Ana", "restante": 8}]
    assert retrato["lotes"] == [{"id": 2, "obra_id": 1, "restante": 20}]


def test_restante_arredonda_para_cima_e_nunca_fica_negativo():
    estado = estado_com_obra_e_lote()

    assert regras.retrato(estado, 107.2)["obras"][0]["restante"] == 1
    assert regras.retrato(estado, 200.0)["obras"][0]["restante"] == 0


def test_restante_congela_no_encerramento():
    estado = estado_com_obra_e_lote()
    estado["encerrada_em"] = 105.0

    retrato = regras.retrato(estado, 500.0)

    assert retrato["obras"][0]["restante"] == 3
    assert retrato["lotes"][0]["restante"] == 15


# ----- Etapa 2: abrir a temporada -----

MESTRE = {"nome": "Kauan", "papel": "mestre"}
JOGADOR = {"nome": "Ana", "papel": "jogador"}


def estado_na_fase(fase):
    estado = regras.estado_inicial()
    estado["fase"] = fase
    return estado


def test_mestre_pode_abrir_temporada_aguardando():
    assert regras.motivo_recusa_abertura(estado_na_fase("aguardando"), MESTRE) is None


def test_abertura_por_quem_nao_esta_na_cervejaria():
    motivo = regras.motivo_recusa_abertura(estado_na_fase("aguardando"), None)

    assert motivo == "Você não está na cervejaria. Entre novamente."


def test_jogador_nao_pode_abrir():
    motivo = regras.motivo_recusa_abertura(estado_na_fase("aguardando"), JOGADOR)

    assert motivo == "Apenas o Mestre pode abrir a temporada."


def test_nao_abre_temporada_ja_aberta():
    motivo = regras.motivo_recusa_abertura(estado_na_fase("aberta"), MESTRE)

    assert motivo == "A temporada já está aberta."


def test_nao_reabre_temporada_encerrada():
    motivo = regras.motivo_recusa_abertura(estado_na_fase("encerrada"), MESTRE)

    assert motivo == "A temporada já foi encerrada. Reinicie o servidor para começar outra."


# ----- Etapa 3: construir (casos aceitos) -----

def test_jogador_pode_construir_cada_tipo_com_temporada_aberta():
    estado = estado_na_fase("aberta")

    for tipo in ("maltaria", "tanque", "adega"):
        assert regras.motivo_recusa_construcao(estado, JOGADOR, tipo) is None


def test_pode_construir_com_cevada_exatamente_igual_ao_custo():
    estado = estado_na_fase("aberta")
    estado["toras"] = 50

    assert regras.motivo_recusa_construcao(estado, JOGADOR, "maltaria") is None


def test_pode_construir_com_um_cervejeiro_ainda_livre():
    estado = estado_na_fase("aberta")
    estado["obras"][1] = {"id": 1, "tipo": "adega", "pedida_por": "Ana", "termina_em": 108.0}

    assert regras.motivo_recusa_construcao(estado, JOGADOR, "tanque") is None


# ----- Etapa 4: recusas de construir (na ordem das checagens) -----

def test_construcao_por_quem_nao_esta_na_cervejaria():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("aberta"), None, "maltaria")

    assert motivo == "Você não está na cervejaria. Entre novamente."


def test_mestre_nao_pode_construir():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("aberta"), MESTRE, "maltaria")

    assert motivo == "Apenas Jogadores podem construir."


def test_nao_constroi_antes_de_abrir():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("aguardando"), JOGADOR, "maltaria")

    assert motivo == "A temporada não está aberta."


def test_nao_constroi_depois_de_encerrar():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("encerrada"), JOGADOR, "maltaria")

    assert motivo == "A temporada está encerrada."


def test_tipo_de_construcao_desconhecido():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("aberta"), JOGADOR, "casa")

    assert motivo == "Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."


def test_tipo_ausente_tambem_e_desconhecido():
    motivo = regras.motivo_recusa_construcao(estado_na_fase("aberta"), JOGADOR, None)

    assert motivo == "Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."


def test_cevada_insuficiente_diz_quanto_falta():
    estado = estado_na_fase("aberta")
    estado["toras"] = 40

    motivo = regras.motivo_recusa_construcao(estado, JOGADOR, "maltaria")

    assert motivo == "Cevada insuficiente: faltam 10. Aguarde a próxima colheita."


def test_sem_cervejeiro_livre():
    estado = estado_na_fase("aberta")
    for i in (1, 2):
        estado["obras"][i] = {"id": i, "tipo": "adega", "pedida_por": "Ana", "termina_em": 108.0}

    motivo = regras.motivo_recusa_construcao(estado, JOGADOR, "maltaria")

    assert motivo == "Nenhum cervejeiro livre. Aguarde uma obra terminar."


# ----- Etapa 4: Mestre único na conexão (FR-017) -----

def test_jogador_sempre_pode_entrar():
    estado = regras.estado_inicial()
    estado["mestre_sid"] = "m1"

    assert regras.motivo_recusa_conexao(estado, "jogador") is None


def test_primeiro_mestre_pode_entrar():
    assert regras.motivo_recusa_conexao(regras.estado_inicial(), "mestre") is None


def test_segundo_mestre_e_recusado():
    estado = regras.estado_inicial()
    estado["mestre_sid"] = "m1"

    motivo = regras.motivo_recusa_conexao(estado, "mestre")

    assert motivo == "Já existe um Mestre na cervejaria. Entre como Jogador."
