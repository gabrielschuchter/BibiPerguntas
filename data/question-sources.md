# Fontes de perguntas

O jogo usa apenas fontes online abertas e cache local de perguntas externas já validadas:

- `tryvia`: fonte principal, em português, compatível com o formato da Open Trivia Database.
- `opentdb`: fonte secundária. Como a maior parte do conteúdo está em inglês, o app só aceita perguntas que passem por filtros de idioma e qualidade.
- cache em `localStorage`: guarda perguntas externas válidas para reutilização se uma nova chamada falhar.

Não há banco local de perguntas embarcado no jogo.

## Tryvia

Endpoints estudados:

- `https://tryvia.ptr.red/api_category.php`
- `https://tryvia.ptr.red/api_token.php?command=request`
- `https://tryvia.ptr.red/api.php?amount={quantidade}&type=multiple&token={token}`

O app pede token de sessão e busca perguntas `multiple`.

## Open Trivia DB

Referência:

- `https://opentdb.com/api_config.php`

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
