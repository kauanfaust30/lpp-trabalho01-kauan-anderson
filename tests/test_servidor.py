"""Testes dos handlers e temporizadores do server.py (usam a fixture `servidor`)."""

import asyncio


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
    # o primeiro fato é a conclusão; a partir da Etapa 8 vem também lote.pronto (ver T062)
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


# ----- Etapa 6: encerramento -----

def temporada_aberta_com_mestre_e_jogador(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    conectar(servidor, "s1", "Ana", "jogador")
    servidor.server.estado["fase"] = "aberta"
    servidor.emitidos.clear()


def test_mestre_encerra_e_todos_recebem_cervejaria_encerrada(servidor):
    temporada_aberta_com_mestre_e_jogador(servidor)
    servidor.relogio.valor = 1234.0

    servidor.rodar(servidor.server.encerramento_solicitado("m1"))

    assert servidor.server.estado["fase"] == "encerrada"
    assert servidor.server.estado["encerrada_em"] == 1234.0
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "cervejaria.encerrada"
    assert to is None
    assert dados["causa"] == "pedido de Kauan"


def test_jogador_que_tenta_encerrar_recebe_recusa_so_para_ele(servidor):
    temporada_aberta_com_mestre_e_jogador(servidor)

    servidor.rodar(servidor.server.encerramento_solicitado("s1"))

    dados = unica_recusa(servidor, "s1")
    assert dados["pedido"] == "cervejaria.encerramento_solicitado"
    assert dados["motivo"] == "Apenas o Mestre pode encerrar a temporada."
    assert servidor.server.estado["fase"] == "aberta"


def test_depois_de_encerrar_o_tempo_congela(servidor):
    temporada_aberta_com_mestre_e_jogador(servidor)
    com_obra(servidor)
    servidor.rodar(servidor.server.encerramento_solicitado("m1"))
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.produzir_cevada())
    servidor.rodar(servidor.server.concluir_obra(1))

    assert servidor.emitidos == []
    assert servidor.server.estado["toras"] == 150
    assert 1 in servidor.server.estado["obras"]


def test_depois_de_encerrar_construir_e_reabrir_sao_recusados(servidor):
    temporada_aberta_com_mestre_e_jogador(servidor)
    servidor.rodar(servidor.server.encerramento_solicitado("m1"))

    servidor.emitidos.clear()
    servidor.rodar(servidor.server.construcao_solicitada("s1", {"tipo": "maltaria"}))
    assert unica_recusa(servidor, "s1")["motivo"] == "A temporada está encerrada."

    servidor.emitidos.clear()
    servidor.rodar(servidor.server.abertura_solicitada("m1"))
    assert unica_recusa(servidor, "m1")["motivo"] == (
        "A temporada já foi encerrada. Reinicie o servidor para começar outra.")


# ----- Etapa 6: disputa (só um pedido vence) -----

def disputar_construcao(servidor, monkeypatch):
    """Dois Jogadores pedem ao mesmo tempo. O emit falso cede a vez (sleep(0)), para
    que qualquer await no meio do handler deixasse o outro pedido se intercalar."""
    emitidos = servidor.emitidos

    async def emit_que_cede(evento, dados=None, to=None, **_):
        await asyncio.sleep(0)
        emitidos.append((evento, dados, to))

    monkeypatch.setattr(servidor.server.sio, "emit", emit_que_cede)
    construir = servidor.server.construcao_solicitada

    async def os_dois_juntos():
        await asyncio.gather(construir("a", {"tipo": "maltaria"}),
                             construir("b", {"tipo": "tanque"}))

    servidor.rodar(os_dois_juntos())
    iniciadas = [e for e in emitidos if e[0] == "construcao.iniciada"]
    recusas = [e for e in emitidos if e[0] == "operacao.recusada"]
    return iniciadas, recusas


def preparar_disputa(servidor, obras, toras):
    conectar(servidor, "a", "Ana", "jogador")
    conectar(servidor, "b", "Bia", "jogador")
    servidor.server.estado["fase"] = "aberta"
    servidor.server.estado["toras"] = toras
    for i in range(obras):
        com_obra(servidor, obra_id=100 + i)
    servidor.emitidos.clear()


def test_disputa_pelo_ultimo_cervejeiro(servidor, monkeypatch):
    preparar_disputa(servidor, obras=1, toras=100)

    iniciadas, recusas = disputar_construcao(servidor, monkeypatch)

    assert len(iniciadas) == 1
    assert len(recusas) == 1
    sid_do_vencedor = {"Ana": "a", "Bia": "b"}[iniciadas[0][1]["obra"]["pedida_por"]]
    sid_recusado = recusas[0][2]
    assert {sid_do_vencedor, sid_recusado} == {"a", "b"}
    assert recusas[0][1]["motivo"] == "Nenhum cervejeiro livre. Aguarde uma obra terminar."
    assert len(servidor.server.estado["obras"]) == 2


def test_disputa_pela_ultima_cevada(servidor, monkeypatch):
    preparar_disputa(servidor, obras=0, toras=50)

    iniciadas, recusas = disputar_construcao(servidor, monkeypatch)

    assert len(iniciadas) == 1
    assert len(recusas) == 1
    assert recusas[0][1]["motivo"] == "Cevada insuficiente: faltam 50. Aguarde a próxima colheita."
    assert servidor.server.estado["toras"] == 0


# ----- Etapa 8: lotes que passam do ponto -----

def test_concluir_obra_cria_lote_e_avisa_depois_da_conclusao(servidor):
    servidor.server.estado["fase"] = "aberta"
    servidor.server.estado["proximo_id"] = 2          # a obra 1 já existe
    com_obra(servidor)

    servidor.rodar(servidor.server.concluir_obra(1))

    assert servidor.server.estado["lotes"] == {2: {"id": 2, "obra_id": 1, "vence_em": 1020.0}}
    assert servidor.server.estado["proximo_id"] == 3
    assert [e[0] for e in servidor.emitidos] == ["construcao.concluida", "lote.pronto"]
    _, dados, to = servidor.emitidos[1]
    assert to is None
    assert dados["lote"] == {"id": 2, "obra_id": 1}
    assert dados["prazo"] == 20
    assert dados["causa"] == "temporizador"
    assert servidor.tarefas == [(servidor.server.esperar_prazo_lote, (2,))]


def com_lote(servidor, lote_id=7):
    servidor.server.estado["lotes"][lote_id] = {"id": lote_id, "obra_id": 1, "vence_em": 1020.0}


def test_engarrafamento_aceito_soma_cerveja_e_avisa_todos(servidor):
    temporada_aberta_com_jogador(servidor)
    com_lote(servidor)

    servidor.rodar(servidor.server.engarrafamento_solicitado("s1", {"lote": 7}))

    assert servidor.server.estado["lotes"] == {}
    assert servidor.server.estado["cerveja"] == 1
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "lote.engarrafado"
    assert to is None
    assert dados["lote"] == {"id": 7}
    assert dados["por"] == "Ana"
    assert dados["estado"]["cerveja"] == 1


def test_mestre_que_tenta_engarrafar_recebe_recusa_so_para_ele(servidor):
    conectar(servidor, "m1", "Kauan", "mestre")
    servidor.server.estado["fase"] = "aberta"
    com_lote(servidor)
    servidor.emitidos.clear()

    servidor.rodar(servidor.server.engarrafamento_solicitado("m1", {"lote": 7}))

    dados = unica_recusa(servidor, "m1")
    assert dados["pedido"] == "engarrafamento.solicitado"
    assert dados["motivo"] == "Apenas Jogadores podem engarrafar."
    assert 7 in servidor.server.estado["lotes"]


def test_engarrafar_lote_que_ja_saiu_e_recusado(servidor):
    temporada_aberta_com_jogador(servidor)          # nenhum lote pendente

    servidor.rodar(servidor.server.engarrafamento_solicitado("s1", {"lote": 7}))

    assert unica_recusa(servidor, "s1")["motivo"] == "Este lote não está mais disponível."
    assert servidor.server.estado["cerveja"] == 0


def test_engarrafar_com_temporada_encerrada_e_recusado(servidor):
    temporada_aberta_com_jogador(servidor)
    com_lote(servidor)
    servidor.server.estado["fase"] = "encerrada"

    servidor.rodar(servidor.server.engarrafamento_solicitado("s1", {"lote": 7}))

    assert unica_recusa(servidor, "s1")["motivo"] == "A temporada está encerrada."
    assert 7 in servidor.server.estado["lotes"]


def test_engarrafar_sem_dados_vira_recusa_de_lote(servidor):
    for dados_do_pedido in (None, {}):
        temporada_aberta_com_jogador(servidor)
        com_lote(servidor)

        servidor.rodar(servidor.server.engarrafamento_solicitado("s1", dados_do_pedido))

        assert unica_recusa(servidor, "s1")["motivo"] == "Este lote não está mais disponível."
        assert servidor.server.estado["cerveja"] == 0
        assert 7 in servidor.server.estado["lotes"]


def test_disputa_pelo_mesmo_lote(servidor, monkeypatch):
    conectar(servidor, "a", "Ana", "jogador")
    conectar(servidor, "b", "Bia", "jogador")
    servidor.server.estado["fase"] = "aberta"
    com_lote(servidor)
    servidor.emitidos.clear()

    async def emit_que_cede(evento, dados=None, to=None, **_):
        await asyncio.sleep(0)                      # deixa o outro pedido tentar se intercalar
        servidor.emitidos.append((evento, dados, to))

    monkeypatch.setattr(servidor.server.sio, "emit", emit_que_cede)
    engarrafar = servidor.server.engarrafamento_solicitado

    async def os_dois_juntos():
        await asyncio.gather(engarrafar("a", {"lote": 7}), engarrafar("b", {"lote": 7}))

    servidor.rodar(os_dois_juntos())

    nomes = [e[0] for e in servidor.emitidos]
    assert nomes.count("lote.engarrafado") == 1
    assert nomes.count("operacao.recusada") == 1
    recusa = next(e for e in servidor.emitidos if e[0] == "operacao.recusada")
    assert recusa[1]["motivo"] == "Este lote não está mais disponível."
    assert servidor.server.estado["cerveja"] == 1


def test_perder_lote_no_prazo_avisa_todos(servidor):
    servidor.server.estado["fase"] = "aberta"
    com_lote(servidor)

    servidor.rodar(servidor.server.perder_lote(7))

    assert servidor.server.estado["lotes"] == {}
    assert len(servidor.emitidos) == 1
    evento, dados, to = servidor.emitidos[0]
    assert evento == "lote.perdido"
    assert to is None
    assert dados["lote"] == {"id": 7}
    assert dados["causa"] == "temporizador"


def test_perder_lote_ja_engarrafado_ou_com_temporada_encerrada_nao_faz_nada(servidor):
    servidor.server.estado["fase"] = "aberta"
    servidor.rodar(servidor.server.perder_lote(7))       # lote já saiu (engarrafado)

    servidor.server.estado["fase"] = "encerrada"
    com_lote(servidor)
    servidor.rodar(servidor.server.perder_lote(7))       # congelado

    assert servidor.emitidos == []
    assert 7 in servidor.server.estado["lotes"]
