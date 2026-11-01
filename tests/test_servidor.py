"""Testes dos handlers e temporizadores do server.py (usam a fixture `servidor`)."""


def conectar(servidor, sid, nome="Ana", papel="jogador"):
    servidor.rodar(servidor.server.connect(sid, {}, {"nome": nome, "papel": papel}))


# ----- Etapa 1: conectar e sincronizar -----

def test_connect_registra_participante(servidor):
    conectar(servidor, "s1", "Ana", "jogador")

    assert servidor.server.estado["participantes"]["s1"] == {"nome": "Ana", "papel": "jogador"}


def test_connect_sincroniza_estado_so_para_quem_conectou(servidor):
    conectar(servidor, "s1", "Ana", "jogador")

    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "estado.sincronizado"
    assert to == "s1"
    assert dados["causa"] == "conexão"
    assert dados["papel"] == "jogador"
    assert dados["estado"]["toras"] == 150


def test_connect_sem_nome_vira_anonimo(servidor):
    conectar(servidor, "s1", "", "jogador")

    assert servidor.server.estado["participantes"]["s1"]["nome"] == "Anônimo"


def test_connect_como_mestre_ocupa_a_vaga(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")

    assert servidor.server.estado["mestre_sid"] == "m1"


def test_disconnect_remove_participante(servidor):
    conectar(servidor, "s1")

    servidor.rodar(servidor.server.disconnect("s1"))

    assert "s1" not in servidor.server.estado["participantes"]


def test_disconnect_do_mestre_libera_a_vaga(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")

    servidor.rodar(servidor.server.disconnect("m1"))

    assert servidor.server.estado["mestre_sid"] is None


def test_disconnect_nao_mexe_em_obras_nem_lotes(servidor):
    conectar(servidor, "s1", "Ana")
    estado = servidor.server.estado
    estado["obras"][1] = {"id": 1, "tipo": "maltaria", "pedida_por": "Ana", "termina_em": 1008.0}
    estado["lotes"][2] = {"id": 2, "obra_id": 1, "vence_em": 1020.0}

    servidor.rodar(servidor.server.disconnect("s1"))

    assert 1 in estado["obras"]
    assert 2 in estado["lotes"]


def test_disconnect_de_sid_desconhecido_nao_falha(servidor):
    servidor.rodar(servidor.server.disconnect("ninguem"))

    assert servidor.server.estado["participantes"] == {}


# ----- Etapa 2: Mestre abre a temporada -----

def test_mestre_abre_e_todos_recebem_cervejaria_iniciada(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.abertura_solicitada("m1"))

    assert servidor.server.estado["fase"] == "aberta"
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "cervejaria.iniciada"
    assert to is None
    assert dados["causa"] == "pedido de Kauan"
    assert dados["estado"]["fase"] == "aberta"


def test_jogador_que_tenta_abrir_recebe_recusa_so_para_ele(servidor):
    conectar(servidor, "s1", "Ana", "jogador")
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.abertura_solicitada("s1"))

    assert servidor.server.estado["fase"] == "aguardando"
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "operacao.recusada"
    assert to == "s1"
    assert dados["pedido"] == "cervejaria.abertura_solicitada"
    assert dados["motivo"] == "Apenas o Mestre pode abrir a temporada."


# ----- Etapa 3: pedido e fato de construir -----

def temporada_aberta_com_jogador(servidor, sid="s1", nome="Ana"):
    conectar(servidor, sid, nome, "jogador")
    servidor.server.estado["fase"] = "aberta"
    servidor.emitidos.clear()


def test_construcao_aceita_desconta_cevada_e_cria_obra(servidor):
    temporada_aberta_com_jogador(servidor)

    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))

    estado = servidor.server.estado
    assert estado["toras"] == 100
    assert estado["obras"] == {
        1: {"id": 1, "tipo": "maltaria", "pedida_por": "Ana", "termina_em": 1008.0},
    }
    assert estado["proximo_id"] == 2


def test_construcao_aceita_avisa_todos_com_construcao_iniciada(servidor):
    temporada_aberta_com_jogador(servidor)

    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))

    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "construcao.iniciada"
    assert to is None
    assert dados["causa"] == "pedido de Ana"
    assert dados["obra"] == {"id": 1, "tipo": "maltaria", "pedida_por": "Ana"}
    assert dados["estado"]["trabalhadores"] == 1
    assert dados["estado"]["toras"] == 100


# ----- Etapa 4: recusa só para quem pediu -----

def unica_recusa(servidor, sid):
    """Confere que houve exatamente um emit, uma recusa só para `sid`, e a devolve."""
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "operacao.recusada"
    assert to == sid
    return dados


def test_construcao_com_temporada_fechada_e_recusada_so_para_quem_pediu(servidor):
    conectar(servidor, "s1", "Ana", "jogador")
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))

    dados = unica_recusa(servidor, "s1")
    assert dados["pedido"] == "construcao.solicitada"
    assert dados["motivo"] == "A temporada não está aberta."
    assert servidor.server.estado["toras"] == 150
    assert servidor.server.estado["obras"] == {}


def test_construcao_de_sid_nao_registrado_e_recusada(servidor):
    servidor.server.estado["fase"] = "aberta"

    servidor.rodar(servidor.server.construcao_solicitada("fantasma", {"tipo": "maltaria"}))

    dados = unica_recusa(servidor, "fantasma")
    assert dados["motivo"] == "Você não está na cervejaria. Entre novamente."
    assert dados["causa"] == "conexão"
    assert servidor.server.estado["obras"] == {}


def test_construcao_sem_dados_vira_recusa_de_tipo(servidor):
    for dados_do_pedido in (None, {}):
        temporada_aberta_com_jogador(servidor)

        servidor.rodar(servidor.server.construcao_solicitada("s1", dados_do_pedido))

        dados = unica_recusa(servidor, "s1")
        assert dados["motivo"] == "Tipo de construção desconhecido. Escolha maltaria, tanque ou adega."
        assert servidor.server.estado["toras"] == 150
        assert servidor.server.estado["obras"] == {}


def test_segundo_mestre_e_recusado_e_nao_entra(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    servidor.emitidos.clear()

    conectar(servidor, "m2", "Outro", "mestre")

    dados = unica_recusa(servidor, "m2")
    assert dados["pedido"] == "conexao"
    assert dados["motivo"] == "Já existe um Mestre na cervejaria. Entre como Jogador."
    assert "m2" not in servidor.server.estado["participantes"]
    assert servidor.server.estado["mestre_sid"] == "m1"


def test_mestre_recusado_que_tenta_abrir_e_recusado_de_novo(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    conectar(servidor, "m2", "Outro", "mestre")
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.abertura_solicitada("m2"))

    dados = unica_recusa(servidor, "m2")
    assert dados["motivo"] == "Você não está na cervejaria. Entre novamente."
    assert dados["causa"] == "conexão"
    assert servidor.server.estado["fase"] == "aguardando"


def test_depois_que_o_mestre_sai_outro_mestre_entra(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    servidor.rodar(servidor.server.disconnect("m1"))
    servidor.emitidos.clear()

    conectar(servidor, "m2", "Outro", "mestre")

    assert servidor.server.estado["mestre_sid"] == "m2"
    assert servidor.emitidos[0][0] == "estado.sincronizado"


# ----- Etapa 5: passagem do tempo -----

def com_obra(servidor, obra_id=1, tipo="maltaria"):
    servidor.server.estado["obras"][obra_id] = {
        "id": obra_id, "tipo": tipo, "pedida_por": "Ana", "termina_em": 1008.0,
    }


def test_produzir_cevada_com_temporada_aberta(servidor):
    servidor.server.estado["fase"] = "aberta"

    servidor.rodar(servidor.server.produzir_cevada())

    assert servidor.server.estado["toras"] == 160
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "recurso.produzido"
    assert to is None
    assert dados["quantidade"] == 10
    assert dados["causa"] == "temporizador"
    assert dados["estado"]["toras"] == 160


def test_produzir_cevada_fora_da_temporada_nao_faz_nada(servidor):
    for fase in ("aguardando", "encerrada"):
        servidor.server.estado["fase"] = fase

        servidor.rodar(servidor.server.produzir_cevada())

        assert servidor.server.estado["toras"] == 150
        assert servidor.emitidos == []


def test_concluir_obra_libera_cervejeiro_e_aumenta_producao(servidor):
    servidor.server.estado["fase"] = "aberta"
    com_obra(servidor)

    servidor.rodar(servidor.server.concluir_obra(1))

    estado = servidor.server.estado
    assert estado["obras"] == {}
    assert estado["concluidas"] == 1
    assert estado["producao"] == 15
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "construcao.concluida"
    assert to is None
    assert dados["obra"] == {"id": 1, "tipo": "maltaria"}
    assert dados["causa"] == "temporizador"
    assert dados["estado"]["trabalhadores"] == 0


def test_concluir_obra_com_temporada_encerrada_nao_faz_nada(servidor):
    servidor.server.estado["fase"] = "encerrada"
    com_obra(servidor)

    servidor.rodar(servidor.server.concluir_obra(1))

    assert 1 in servidor.server.estado["obras"]
    assert servidor.server.estado["producao"] == 10
    assert servidor.emitidos == []


def test_concluir_obra_inexistente_nao_faz_nada(servidor):
    servidor.server.estado["fase"] = "aberta"

    servidor.rodar(servidor.server.concluir_obra(99))

    assert servidor.server.estado["concluidas"] == 0
    assert servidor.emitidos == []


def test_abertura_aceita_inicia_o_ciclo_de_producao(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")

    servidor.rodar(servidor.server.abertura_solicitada("m1"))

    assert servidor.tarefas == [(servidor.server.ciclo_producao, ())]


def test_construcao_aceita_inicia_o_temporizador_da_obra(servidor):
    temporada_aberta_com_jogador(servidor)

    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))

    assert servidor.tarefas == [(servidor.server.esperar_obra, (1,))]


def test_recusas_nao_iniciam_temporizadores(servidor):
    conectar(servidor, "s1", "Ana", "jogador")

    servidor.rodar(servidor.server.abertura_solicitada("s1"))
    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))

    assert servidor.tarefas == []
