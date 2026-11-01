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
