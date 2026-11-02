# Vila em Tempo Real — Cervejaria artesanal

Trabalho 01 – Programação Orientada a Eventos · Linguagem de Programação e Paradigmas (UNIDAVI, Sistemas de Informação) · Prof. Ademar Perfoll Junior

Vila cooperativa em tempo real (tipo sorteado: **\#9 – Cervejaria artesanal**, cevada → cerveja). Cada jogador usa uma aba do navegador; o servidor decide tudo e todas as abas reagem aos fatos.

## Integrantes

- Kauan Faust — @kauanfaust30  
- Anderson Moreira — @PingoStar

Repositório: https\://github.com/kauanfaust30/lpp-trabalho01-kauan-anderson.git

## Como instalar e executar

Pré-requisitos: Python 3.11+ e Git.

```
git clone https://github.com/kauanfaust30/lpp-trabalho01-kauan-anderson.git
cd lpp-trabalho01-kauan-anderson
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server:app --reload
```

Abra `http://localhost:8000` no navegador. 

Testes automáticos: `pytest`.

## Como testar com duas abas

1. Abra duas abas em `http://localhost:8000` (uma terceira ajuda a testar a disputa).  
2. **Aba 1 – Mestre:** entre e clique em **Abrir temporada**. Só o Mestre abre e encerra a temporada. As duas abas passam a mostrar "Temporada aberta" e a cevada (150).  
3. **Aba 2 – Jogador:** entre com outro nome. Ele vê a mesma vila.  
4. Em qualquer aba, escolha o tipo de obra e clique em **Construir**. As duas abas mostram o canteiro (cevada cai 50\) e, 8 segundos depois, a adega concluída.  
5. Peça uma obra com pouca cevada ou com os 2 cervejeiros ocupados: **só a aba que pediu** vê a recusa (`operacao.recusada`).  
6. Quando a obra termina nasce um lote de cerveja. Clique em **Engarrafar** nas duas abas ao mesmo tempo: só uma consegue (+1 cerveja); a outra é recusada.  
7. Deixe um lote 20 segundos sem engarrafar: aparece `lote.perdido`.  
8. Acompanhe tudo no **Painel de eventos** (pedidos, fatos, recusas e contadores). O Mestre pode **Encerrar temporada**; depois disso ninguém mais constrói.

## Perguntas

### 1\. Quais eventos o seu sistema emite e escuta?

São 14 eventos. **Pedidos** (`*_solicitada`) saem do cliente e o servidor escuta; **fatos** saem do servidor para todas as abas e os clientes escutam; a **recusa** sai do servidor só para quem pediu.

| Evento | Quem emite | Quem escuta | O que muda |
| :---- | :---- | :---- | :---- |
| `cervejaria.abertura_solicitada` | cliente (Mestre) | servidor | pedido de abrir a temporada |
| `cervejaria.iniciada` | servidor | todas as abas | fase passa a "aberta", cevada inicial |
| `construcao.solicitada` | cliente | servidor | pedido de obra |
| `construcao.iniciada` | servidor | todas as abas | cevada −50, cervejeiro ocupado, canteiro |
| `operacao.recusada` | servidor | só quem pediu | nada muda; mostra o motivo |
| `recurso.produzido` | servidor (temporizador) | todas as abas | cevada aumenta a cada 5 s |
| `construcao.concluida` | servidor (temporizador) | todas as abas | adega pronta, produção \+5 |
| `lote.pronto` | servidor | todas as abas | nasce um lote com prazo de 20 s |
| `engarrafamento.solicitado` | cliente | servidor | pedido de engarrafar |
| `lote.engarrafado` | servidor | todas as abas | \+1 cerveja, lote some |
| `lote.perdido` | servidor (temporizador) | todas as abas | lote passou do prazo e some |
| `cervejaria.encerramento_solicitado` | cliente (Mestre) | servidor | pedido de encerrar |
| `cervejaria.encerrada` | servidor | todas as abas | fase "encerrada" |
| `estado.sincronizado` | servidor | quem entrou | recebe o retrato do estado |

No servidor, os pedidos são escutados pelos handlers de `server.py` (`abertura_solicitada`, `construcao_solicitada`, `engarrafamento_solicitado`, `encerramento_solicitado`). No cliente, as escutas ficam em `ESCUTAS` e os pedidos em `PEDIDOS`, em `client/index.html`, usando `ouvir(...)` e `pedir(...)`.

### 2\. Como o sistema sabe quando deve atualizar os outros jogadores?

O servidor é a fonte da verdade. Quando um pedido é aceito, o servidor valida, altera o estado e **emite um fato para todas as abas** com o estado atualizado; os clientes só aplicam esse estado na tela e nunca calculam regra. Fatos que dependem do tempo (cevada produzida, fim da obra, lote que passa do ponto) nascem de **tarefas em segundo plano** do servidor (`sio.start_background_task` \+ `sio.sleep`), que depois da espera revalidam a fase antes de alterar qualquer coisa. Recusas vão só para o `sid` de quem pediu, então os outros jogadores não são perturbados.

### 3\. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

- **`server.py`, `construcao_solicitada` e `concluir_obra`**: o pedido do cliente é a *causa*; `construcao.iniciada` é o *fato* emitido para todos; o temporizador `esperar_obra` é outra *causa* que produz `construcao.concluida`. Ninguém chama função de outra aba: tudo acontece por evento.  
- **`regras.py`**: validações puras (`motivo_recusa_*`) separadas dos handlers, o que permite testar cada pedido sem subir servidor.  
- **`client/index.html`, `ouvir(...)` e `pedir(...)`**: a tela reage aos fatos do servidor e só *pede* ações, sem `socket.on`/`emit` diretos.  
- **Painel de eventos**: mostra cada pedido, fato e recusa em tempo real.

>   
> Ajuste os nomes e as linhas de acordo com o `server.py` final antes de entregar.

## Uso de IA

Usamos o **GitHub Spec Kit** com o **Claude Code** (Anthropic) para desenvolver por especificação (constituição, especificação, plano, tarefas, análise e implementação em etapas, com um commit por etapa) e o Claude (assistente) para orientar o passo a passo e desenhar a arte em pixel art.

**O que nós definimos:** a especificação (`docs/especificacao.md`) e as decisões da equipe (lote perdido só desaparece; engarrafar soma 1 cerveja; vários lotes pendentes, cada um com prazo de 20 s), além de revisar e testar cada etapa no navegador.

**O que a IA gerou e nós ajustamos:** plano, tarefas, `server.py`, `regras.py`, testes e a parte Vue do `client/index.html`. A cena Phaser (`criarJogo`) e as bibliotecas por CDN não foram alteradas.

## Extras

- Mestre único: só ele abre e encerra a temporada.  
- Lotes de cerveja com prazo de 20 s e perda automática; vários lotes pendentes ao mesmo tempo.  
- Contadores no Painel de eventos.  
- Testes automáticos com pytest (regras e handlers).  
- Arte original: adega, canteiro, feixe e sacos de cevada (`sprites-vila.png` e `tileset-vila.png`).

**Observações:** os campos `toras` e `trabalhadores` vêm do Kit Inicial e foram mantidos para não alterar a cena Phaser: `toras` é a cevada e `trabalhadores` são os cervejeiros ocupados. O estado fica só em memória. Depois de encerrar a temporada, a barra de uma obra em andamento continua animada na tela (animação do kit), mas o servidor já parou.