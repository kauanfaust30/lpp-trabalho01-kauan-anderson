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
