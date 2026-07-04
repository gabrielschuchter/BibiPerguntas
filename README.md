# Batalha de Perguntas

Jogo local de perguntas e respostas por equipes, feito em HTML, CSS e JavaScript puro. Não usa backend, framework nem build obrigatório.

## Como rodar localmente

Opção mais simples:

1. Baixe ou clone o projeto.
2. Abra `index.html` no navegador.
3. Cadastre equipes, cores e jogadores.
4. Clique em **Começar jogo**.

Também é possível usar um servidor estático local:

```bash
python -m http.server 8000
```

Depois abra `http://localhost:8000`.

## Deploy no Vercel

O projeto funciona como site estático.

1. Importe o repositório no Vercel.
2. Framework preset: **Other**.
3. Build command: deixe vazio.
4. Output directory: deixe vazio ou use a raiz do projeto.

## Estrutura

- `index.html`: estrutura das telas, regras, setup, jogo e vitória.
- `style.css`: layout responsivo, visual de game show, animações e estados do timer.
- `app.js`: lógica de equipes, rodadas, sorteio, timer, sons, ajudas e pontuação.
- `scripts/validate-questions.js`: valida que o app não usa banco local e mantém a camada online obrigatória.
- `data/question-sources.md`: notas sobre Tryvia, OpenTDB e filtros de qualidade.

## Fontes de perguntas

O jogo usa apenas perguntas vindas de APIs abertas:

- Tryvia API como fonte principal em português.
- Open Trivia DB como fonte secundária, apenas quando as perguntas passam pelos filtros de idioma e qualidade.
- Cache em `localStorage` com perguntas externas já validadas.

Não existe banco local de perguntas embarcado. Se não houver internet e não existir cache externo validado, a partida não inicia e a interface mostra uma mensagem amigável.

As perguntas são normalizadas internamente neste formato:

```json
{
  "id": "tryvia-...",
  "source": "tryvia",
  "area": "Conhecimentos Gerais",
  "difficulty": "Fácil",
  "question": "Pergunta limpa",
  "options": ["A", "B", "C", "D"],
  "answer": "A",
  "explanation": "Origem da pergunta."
}
```

Para validar a arquitetura:

```bash
node scripts/validate-questions.js
```

O validador não exige dependências externas. Ele checa se não há banco local, se `index.html` não carrega `questions.js` e se `app.js` mantém endpoints, normalização, filtros e cache externo validado.

## Fontes online e cache

Fluxo ao iniciar uma partida:

1. Pedir token da Tryvia.
2. Buscar perguntas `type=multiple`.
3. Normalizar, decodificar HTML entities, validar e filtrar perguntas ruins.
4. Se necessário, tentar OpenTDB com os mesmos filtros.
5. Salvar perguntas externas válidas em `localStorage`.
6. Se uma nova busca falhar, usar apenas cache externo validado.
7. Se não houver API nem cache, não iniciar a partida.

Existe um botão **Limpar cache** no topo da interface para forçar uma nova busca online na próxima partida.

## Sorteio das perguntas

O app embaralha a base e remove da fila cada pergunta sorteada. Quando a fila acaba, ela é embaralhada novamente.

Regra principal: a próxima pergunta nunca repete a mesma `area` da pergunta imediatamente anterior. A lógica filtra candidatas com `area !== lastArea`, inclusive depois de reembaralhar a base. A repetição só é permitida se não houver alternativa possível.

O jogo também tenta evitar repetir a mesma dificuldade em sequência quando há candidatas disponíveis.

## Timer e sons

Tempo padrão: 60 segundos.

- 60s a 31s: estado normal, visual calmo.
- 30s a 16s: atenção, com alerta visual e som discreto em intervalos.
- 15s a 6s: perigo, pulso mais forte e som mais frequente.
- 5s a 1s: crítico, número destacado, brilho e som mais intenso.

Os sons são gerados pela Web Audio API, sem arquivos externos. O jogo tem uma trilha sintética sutil durante cada pergunta e efeitos mais fortes para acerto, erro, vitória e reta final do timer. O áudio só é ativado depois de interação do usuário, respeitando as restrições dos navegadores.

## Ajudas

Cada equipe tem uma quantidade configurável de:

- Consultar equipe: permite conversa rápida com o time.
- Pesquisar: abre uma busca no Google com a pergunta.
- +1 minuto: adiciona 60 segundos ao timer atual.

Só é permitida uma ajuda por pergunta. Depois de usar uma ajuda, as outras ficam bloqueadas até a próxima rodada.

## Atalhos

- `1`, `2`, `3`, `4`: respondem as alternativas A, B, C e D.
- Barra de espaço: avança para a próxima rodada depois de responder.
