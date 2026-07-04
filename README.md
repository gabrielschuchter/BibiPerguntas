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
- `questions.json`: base editável em JSON puro.
- `questions.js`: mesma base em JavaScript para funcionar abrindo `index.html` direto.
- `generate_questions.py`: gera a base original equilibrada.
- `scripts/validate-questions.js`: valida qualidade, distribuição e sincronização da base local.
- `data/question-sources.md`: notas sobre Tryvia, OpenTDB e filtros de qualidade.

## Banco de perguntas

O jogo tenta carregar perguntas online da Tryvia API, uma API aberta de trivia em português compatível com Open Trivia Database. Se a Tryvia falhar, o app pode tentar OpenTDB como fonte secundária, mas rejeita perguntas em inglês quando não há normalização segura. Se as APIs falharem ou não houver internet, o jogo usa automaticamente o banco local.

O banco local tem **500 perguntas originais em português brasileiro**. Ele serve como fallback offline e complementa o jogo com perguntas técnicas leves de Nutrição, Odontologia, Enfermagem e Tecnologia. O projeto não copia bancos proprietários de programas de TV.

Categorias:

- Geografia
- História
- Ciências
- Cultura geral
- Cultura pop
- Esportes
- Brasil
- Animais e natureza
- Língua portuguesa
- Artes e literatura
- Tecnologia
- Nutrição
- Odontologia
- Enfermagem
- Matemática e raciocínio

Distribuição:

- 34 perguntas em cada categoria principal.
- 24 perguntas em Matemática e raciocínio.
- Matemática fica abaixo de 5% da base.
- Dificuldades: `Fácil`, `Média` e `Avançada`.

## Como editar perguntas

Cada pergunta deve seguir este formato:

```json
{
  "id": "Q0001",
  "source": "local",
  "area": "Geografia",
  "difficulty": "Fácil",
  "question": "Qual país tem o formato parecido com uma bota?",
  "options": ["Itália", "Canadá", "Japão", "Egito"],
  "answer": "Itália",
  "explanation": "A Itália é frequentemente associada ao formato de uma bota no mapa."
}
```

Regras importantes:

- `id` único e sequencial.
- `source` deve ser `local` no banco embarcado.
- `area` deve ser uma das 15 categorias.
- `difficulty` deve ser `Fácil`, `Média` ou `Avançada`.
- `options` deve ter exatamente 4 alternativas.
- `answer` precisa bater exatamente com uma alternativa.
- `question` deve conter apenas a pergunta limpa, sem prefixos, numeração ou marcadores.
- Mantenha `questions.json` e `questions.js` sincronizados.

Para regenerar a base completa:

```bash
python generate_questions.py
```

Para validar a base:

```bash
node scripts/validate-questions.js
```

O validador não exige dependências externas. Ele checa campos obrigatórios, sincronização entre `questions.json` e `questions.js`, duplicatas, alternativas, prefixos proibidos, inglês provável e matemática acima de 5%.

## Fontes online e cache

Fluxo ao iniciar uma partida:

1. Carregar o banco local.
2. Pedir token da Tryvia.
3. Buscar perguntas `type=multiple`.
4. Normalizar, decodificar HTML entities, validar e filtrar perguntas ruins.
5. Se necessário, tentar OpenTDB com os mesmos filtros.
6. Misturar perguntas externas com perguntas locais técnicas leves.
7. Salvar perguntas externas válidas em `localStorage`.
8. Se a API falhar, usar cache; se o cache também falhar, usar banco local.

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
