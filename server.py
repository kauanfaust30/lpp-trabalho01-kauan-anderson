import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# A partir da Etapa 1, adicione o seu código ABAIXO desta linha.

import time

import regras

# O estado vive só aqui no servidor: ele é a fonte da verdade (Princípio II).
estado = regras.estado_inicial()


def agora():
    """Relógio único do servidor; os testes trocam esta função por um relógio controlado."""
    return time.monotonic()


# ----- auxiliares usados por todos os handlers -----

def causa_pedido(sid):
    """Texto da causa de um fato que responde a um pedido (aparece no Painel de eventos)."""
    participante = estado["participantes"].get(sid)
    if participante is None:
        return "conexão"
    return "pedido de " + participante["nome"]


def fato(causa, **extras):
    """Monta os dados de um fato: o retrato do estado, a causa e os campos próprios."""
    return {"estado": regras.retrato(estado, agora()), "causa": causa, **extras}


async def recusar(sid, pedido, motivo):
    # Por quê: a recusa também é um fato, mas só interessa a quem pediu (R4);
    # por isso vai com to=sid e os outros participantes não recebem nada.
    await sio.emit("operacao.recusada", fato(causa_pedido(sid), pedido=pedido, motivo=motivo), to=sid)


# ----- Etapa 1: conectar e sincronizar -----

@sio.event
async def connect(sid, environ, auth):
    # Por quê: cada aba que entra precisa se registrar com nome e papel para o
    # servidor saber quem está pedindo cada coisa.
    dados = auth or {}
    papel = dados.get("papel", "jogador")
    # 1. validar (sem await até registrar: duas abas entrando como Mestre ao mesmo
    #    tempo não conseguem ocupar a vaga juntas)
    motivo = regras.motivo_recusa_conexao(estado, papel)
    # 2. recusar só para quem tentou entrar; ela não é registrada
    if motivo:
        await recusar(sid, "conexao", motivo)
        return
    # 3. alterar o estado: registra o participante
    estado["participantes"][sid] = {"nome": dados.get("nome") or "Anônimo", "papel": papel}
    if papel == "mestre":
        estado["mestre_sid"] = sid
    # Por quê: quem acabou de conectar ainda não sabe nada da cervejaria; o estado
    # vai só para essa aba (to=sid), porque as outras já estão sincronizadas.
    await sio.emit("estado.sincronizado", fato("conexão", papel=papel), to=sid)


@sio.event
async def disconnect(sid, *_):
    # Por quê: quem fecha a aba sai da lista de participantes e, se era o Mestre,
    # libera a vaga. Obras e lotes ficam: a cervejaria é cooperativa e continua.
    estado["participantes"].pop(sid, None)
    if estado["mestre_sid"] == sid:
        estado["mestre_sid"] = None


# ----- Etapa 2: Mestre abre a temporada -----

@sio.on("cervejaria.abertura_solicitada")
async def abertura_solicitada(sid):
    # Por quê: abrir é um PEDIDO do cliente; quem decide se pode é o servidor (R1).
    # 1. validar (sem await até o estado mudar, para nenhum outro pedido se intercalar)
    motivo = regras.motivo_recusa_abertura(estado, estado["participantes"].get(sid))
    # 2. recusar só para quem pediu
    if motivo:
        await recusar(sid, "cervejaria.abertura_solicitada", motivo)
        return
    # 3. alterar o estado
    estado["fase"] = "aberta"
    # 4. emitir o fato
    # Por quê: a temporada aberta muda a tela de TODOS, então vai para todas as abas.
    await sio.emit("cervejaria.iniciada", fato(causa_pedido(sid)))
    # 5. a partir de agora o tempo passa: a cevada é produzida sozinha (R6/FR-006)
    sio.start_background_task(ciclo_producao)


# ----- Etapa 3: pedido e fato de construir -----

@sio.on("construcao.solicitada")
async def construcao_solicitada(sid, dados=None):
    # Por quê: construir é um PEDIDO do Jogador; só o servidor sabe se há cevada e
    # cervejeiro livre, então é ele quem decide (R3).
    tipo = (dados or {}).get("tipo")    # pedido sem dados não quebra: vira recusa
    participante = estado["participantes"].get(sid)
    # 1. validar (sem await até o estado mudar: em disputa, só um pedido vence)
    motivo = regras.motivo_recusa_construcao(estado, participante, tipo)
    # 2. recusar só para quem pediu
    if motivo:
        await recusar(sid, "construcao.solicitada", motivo)
        return
    # 3. alterar o estado: gasta a cevada e ocupa um cervejeiro com a obra
    obra_id = estado["proximo_id"]
    estado["proximo_id"] += 1
    estado["toras"] -= regras.CUSTO_CONSTRUCAO
    estado["obras"][obra_id] = {"id": obra_id, "tipo": tipo, "pedida_por": participante["nome"],
                                "termina_em": agora() + regras.TEMPO_OBRA}
    # 4. emitir o fato
    # Por quê: a cevada e os cervejeiros são de todos (cooperativo), então todas as
    # abas precisam ver a obra começar.
    obra = {"id": obra_id, "tipo": tipo, "pedida_por": participante["nome"]}
    await sio.emit("construcao.iniciada", fato(causa_pedido(sid), obra=obra))
    # 5. a obra termina sozinha depois de TEMPO_OBRA segundos (FR-007)
    sio.start_background_task(esperar_obra, obra_id)


# ----- Etapa 5: passagem do tempo (fatos que ninguém pediu) -----

async def produzir_cevada():
    # Por quê: a cevada só cresce com a temporada aberta; a fase é conferida aqui,
    # depois do sleep, porque o Mestre pode ter encerrado enquanto o tempo passava.
    if estado["fase"] != "aberta":
        return
    estado["toras"] += estado["producao"]
    # Por quê: o estoque é de todos, então todas as abas veem a colheita;
    # a causa "temporizador" mostra no Painel que ninguém pediu este fato.
    await sio.emit("recurso.produzido", fato("temporizador", quantidade=estado["producao"]))


async def ciclo_producao():
    # Por quê: tarefa em segundo plano iniciada na abertura; repete a produção a
    # cada INTERVALO_PRODUCAO segundos e para sozinha quando a temporada fecha.
    while estado["fase"] == "aberta":
        await sio.sleep(regras.INTERVALO_PRODUCAO)
        await produzir_cevada()


async def concluir_obra(obra_id):
    # Por quê: revalida depois do sleep; com a temporada encerrada a obra fica
    # congelada, e uma obra que já não existe não pode ser concluída duas vezes.
    obra = estado["obras"].get(obra_id)
    if estado["fase"] != "aberta" or obra is None:
        return
    del estado["obras"][obra_id]                      # o cervejeiro fica livre
    estado["concluidas"] += 1
    estado["producao"] += regras.GANHO_POR_OBRA
    # Por quê: todas as abas trocam o canteiro pela construção pronta e veem a
    # produção maior; a causa é o temporizador, não um pedido.
    await sio.emit("construcao.concluida",
                   fato("temporizador", obra={"id": obra_id, "tipo": obra["tipo"]}))


async def esperar_obra(obra_id):
    # Por quê: uma tarefa por obra; espera o tempo da obra e então tenta concluí-la.
    await sio.sleep(regras.TEMPO_OBRA)
    await concluir_obra(obra_id)


# ----- Etapa 6: encerramento -----

@sio.on("cervejaria.encerramento_solicitado")
async def encerramento_solicitado(sid):
    # Por quê: encerrar é um PEDIDO do Mestre; o servidor confere papel e fase (R1, R8).
    # 1. validar (sem await até o estado mudar)
    motivo = regras.motivo_recusa_encerramento(estado, estado["participantes"].get(sid))
    # 2. recusar só para quem pediu
    if motivo:
        await recusar(sid, "cervejaria.encerramento_solicitado", motivo)
        return
    # 3. alterar o estado: a fase "encerrada" é final; guardar o instante congela os
    #    tempos restantes de obras e lotes, e os temporizadores param sozinhos ao
    #    conferirem a fase depois do sleep
    estado["fase"] = "encerrada"
    estado["encerrada_em"] = agora()
    # 4. emitir o fato
    # Por quê: todas as abas precisam saber que a temporada acabou e que novos
    # pedidos serão recusados; é o único fato emitido no encerramento.
    await sio.emit("cervejaria.encerrada", fato(causa_pedido(sid)))
