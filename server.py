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
