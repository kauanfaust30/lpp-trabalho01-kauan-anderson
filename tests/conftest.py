"""Fixture que prepara o servidor para os testes, sem rede e sem esperar o relógio."""

import asyncio
from types import SimpleNamespace

import pytest

import regras
import server


@pytest.fixture
def servidor(monkeypatch):
    emitidos = []   # cada item: (evento, dados, to)
    tarefas = []    # cada item: (funcao, args)
    relogio = SimpleNamespace(valor=1000.0)

    async def emit_falso(evento, dados=None, to=None, **_):
        emitidos.append((evento, dados, to))

    async def sleep_instantaneo(_segundos=0):
        return None

    def tarefa_falsa(funcao, *args, **_):
        tarefas.append((funcao, args))

    monkeypatch.setattr(server, "estado", regras.estado_inicial())
    monkeypatch.setattr(server.sio, "emit", emit_falso)
    monkeypatch.setattr(server.sio, "sleep", sleep_instantaneo)
    monkeypatch.setattr(server.sio, "start_background_task", tarefa_falsa)
    monkeypatch.setattr(server, "agora", lambda: relogio.valor)

    return SimpleNamespace(
        server=server,
        emitidos=emitidos,
        tarefas=tarefas,
        relogio=relogio,
        rodar=asyncio.run,
    )
