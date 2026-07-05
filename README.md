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
- `scripts/validate-questions.js`: valida fontes, fallback local, filtros e regras críticas de sorteio.
- `data/question-sources.md`: notas sobre fontes abertas e filtros de qualidade.

## Fontes de perguntas

O jogo prioriza perguntas vindas de fontes abertas online:

- Uma fonte principal em português.
- Uma fonte secundária, apenas quando as perguntas passam pelos filtros de idioma e qualidade.
- Cache em `localStorage` com perguntas externas já validadas.
- Fallback local embutido no `app.js`, usado apenas quando não há API nem cache disponível.

Assim, o jogo continua funcionando abrindo `index.html` mesmo sem internet.

As perguntas são normalizadas internamente neste formato:

```json
{
  "id": "Q000001",
  "source": "online",
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

O validador não exige dependências externas. Ele checa se `index.html` não carrega `questions.js`, se `app.js` mantém endpoints, normalização, timeout de rede, cache, fallback local e controles de sorteio justo.

## Fontes online e cache

Fluxo ao iniciar uma partida:

1. Pedir token da fonte principal.
2. Buscar perguntas `type=multiple`.
3. Normalizar, decodificar HTML entities, validar e filtrar perguntas ruins.
4. Se necessário, tentar a fonte secundária com os mesmos filtros.
5. Salvar perguntas externas válidas em `localStorage`.
6. Se uma nova busca falhar, usar apenas cache externo validado.
7. Se não houver API nem cache, usar o fallback local embutido.

Existe um botão **Limpar cache** no topo da interface para forçar uma nova busca online na próxima partida.

## Sorteio das perguntas

A rodada é um ciclo completo em que cada equipe responde uma pergunta. A seleção fica concentrada em `selectNextQuestion`.

Regras principais:

- a mesma pergunta nunca se repete dentro da mesma rodada;
- o jogo prioriza perguntas ainda não usadas na partida;
- perguntas recentes são evitadas por uma memória proporcional ao número de equipes;
- a próxima pergunta não repete a mesma `area` da pergunta anterior, salvo se for impossível;
- temas já usados na rodada são evitados quando há alternativa;
- dificuldade e tema são ponderados por equipe para reduzir vantagem pela ordem de cadastro;
- o sorteio usa Fisher-Yates e escolha ponderada, sem percorrer a base em ordem fixa.

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

Só é permitida uma ajuda por pergunta. Depois de usar uma ajuda, as outras ficam bloqueadas até a próxima pergunta.

## Atalhos

- `1`, `2`, `3`, `4`: respondem as alternativas A, B, C e D.
- Barra de espaço: avança para o próximo turno depois de responder.
