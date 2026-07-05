# Fontes de perguntas

O jogo usa apenas fontes online abertas e cache local de perguntas externas já validadas:

- fonte principal: em português, compatível com formato aberto de trivia.
- fonte secundária: só entra quando a pergunta passa pelos filtros de idioma e qualidade.
- cache em `localStorage`: guarda perguntas externas válidas para reutilização se uma nova chamada falhar.
- fallback local embutido em `app.js`: usado apenas quando não há fonte online nem cache.

O fallback local é pequeno, revisado e existe para manter a partida jogável abrindo `index.html` sem internet.

## Fonte principal

O app pede token de sessão e busca perguntas `multiple`.

## Fonte secundária

Limites considerados:

- máximo de 50 perguntas por chamada;
- rate limit;
- `response_code` precisa ser validado;
- perguntas podem vir com HTML entities;
- perguntas `boolean` são rejeitadas;
- perguntas em inglês são rejeitadas quando não há normalização segura.

## Qualidade

Todas as perguntas aceitas passam por normalização para:

- `id`
- `source`
- `area`
- `difficulty`
- `question`
- `options`
- `answer`
- `explanation`

Perguntas com prefixos artificiais, alternativas duplicadas, menos de 4 opções, resposta ausente, HTML quebrado, texto muito longo ou atualidade instável são rejeitadas.
