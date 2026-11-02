# Vila em Tempo Real — Cervejaria Artesanal

## Integrantes
- Kauan Faust — @kauanfaust30
- Anderson Moreira — @PingoStar

## Como instalar e executar
1. Certifique-se de ter o Python (versão 3.10 ou superior) instalado em sua máquina.
2. Abra o terminal na pasta do projeto e crie um ambiente virtual:
   python -m venv .venv
3. Ative o ambiente virtual:
   - No Windows (PowerShell): .venv\Scripts\Activate.ps1
4. Instale as dependências do projeto executando:
   pip install -r requirements.txt
5. Inicie o servidor local com o Uvicorn:
   uvicorn server:app --port 8001 --reload
6. Abra o navegador e acesse: http://localhost:8001

## Como testar com duas abas
1. Abra duas abas separadas no navegador e acesse http://localhost:8001 em ambas.
2. Na Aba 1, escolha o papel de Mestre e clique no botão "Abrir temporada".
3. Na Aba 2, entre como Jogador. A vila e os dados sincronizados aparecerão em tempo real.
4. Testar construção: Solicite uma construção em qualquer uma das abas. O canteiro de obras se formará e, após o tempo de conclusão, a adega será finalizada.
5. Testar perda de lote: Deixe um lote sem engarrafar por 20 segundos para verificar o evento de `lote.perdido` no painel de eventos.

## Perguntas
1. Quais eventos o seu sistema emite e escuta?
   - O sistema emite e escuta eventos de controle de temporada (cervejaria.abertura_solicitada, cervejaria.iniciada), eventos de produção de recursos (recurso.produzido), atualização de estado sincronizado (estado.sincronizado) e gerenciamento de construções/lotes.

2. Como o sistema sabe quando deve atualizar os outros jogadores?
   - Através de WebSockets gerenciados pelo servidor (Socket.IO / FastAPI), que faz o papel de centralizar as ações e transmitir imediatamente as atualizações de estado para todos os clientes conectados nas abas do navegador.

3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?
   - A parte do código que utiliza ouvintes e emissores de eventos (emit e on), onde as ações do usuário disparam gatilhos assíncronos no servidor e as abas reagem automaticamente aos pacotes de dados recebidos, atualizando a interface sem recarregar a página.

## Uso de IA
Utilizei inteligência artificial para auxiliar na estruturação do código, no entendimento dos fluxos assíncronos de eventos em tempo real e na elaboração da documentação final e dos testes de sincronização.

## Extras
- Sincronização em tempo real via WebSockets entre múltiplas abas.
- Painel de eventos detalhado para rastreamento de ações do Mestre e Jogadores.