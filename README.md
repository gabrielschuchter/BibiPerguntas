# Batalha de Perguntas — jogo local entre amigos

Aplicativo estático, feito para rodar localmente no navegador, sem servidor, login ou banco de dados externo.

## Como usar

1. Extraia a pasta do ZIP.
2. Abra o arquivo `index.html` no navegador.
3. Cadastre as equipes, cores e integrantes.
4. Clique em **Começar jogo**.

Também é possível rodar com um servidor local simples:

```bash
python -m http.server 8000
```

Depois, abra `http://localhost:8000` no navegador.

## Arquivos principais

- `index.html`: estrutura da aplicação.
- `style.css`: visual responsivo, animações, efeitos e layout.
- `app.js`: lógica do jogo, timer, ajudas, rodadas, placar e vitória.
- `questions.js`: banco de perguntas carregado diretamente pelo navegador.
- `questions.json`: banco de perguntas em JSON puro, para edição/revisão.
- `generate_questions.py`: script usado para gerar a base inicial de perguntas.

## Funcionalidades incluídas

- Cadastro livre de equipes.
- Cadastro de nome, cor e quantidade de integrantes por equipe.
- Validação da quantidade de integrantes.
- Rodízio automático entre equipes.
- Rodízio automático de integrantes dentro de cada equipe.
- Perguntas de múltipla escolha.
- Sorteio aleatório de perguntas.
- Embaralhamento das alternativas a cada rodada.
- Identificação visual de área e dificuldade.
- Timer visual circular.
- Tempo padrão de 60 segundos por pergunta.
- Ajuda de consulta à equipe.
- Ajuda de pesquisa no Google.
- Ajuda de bônus de +1 minuto.
- Regra de apenas 1 ajuda por pergunta.
- Limite configurável de ajudas por equipe.
- Pontuação automática.
- Vitória por pontuação total, padrão de 50 acertos.
- Tela de regras legível.
- Sons gerados no navegador para acerto, erro, contagem final e vitória.
- Confetes e balões no acerto/vitória.
- Botão de pausa.
- Layout responsivo para celular, tablet e desktop.
- Persistência local da última configuração via `localStorage`.

## Banco de perguntas

A base inicial contém **3.200 perguntas**.

Áreas incluídas:

- Conhecimentos gerais
- Raciocínio
- Geografia
- Ciências
- Astronomia
- Biologia
- História e cultura
- Língua portuguesa
- Nutrição
- Odontologia
- Enfermagem
- Tecnologia

Níveis incluídos:

- Fácil
- Médio
- Avançado

Observação: a base é original e não copia literalmente perguntas proprietárias de programas ou jogos televisivos. O formato foi inspirado em jogos de quiz de múltipla escolha, mas as perguntas foram estruturadas para uso local e edição livre.

## Como editar perguntas

Edite `questions.json` e mantenha este formato:

```json
{
  "id": "Q0001",
  "area": "Tecnologia",
  "difficulty": "Fácil",
  "question": "Na tecnologia, o que significa HTTPS?",
  "options": [
    "HyperText Transfer Protocol Secure",
    "High Transfer Text Public System",
    "Home Tool Transfer Page Service",
    "Host Text Terminal Private Signal"
  ],
  "answer": "HyperText Transfer Protocol Secure",
  "explanation": "HTTPS significa HyperText Transfer Protocol Secure."
}
```

Para o app abrir diretamente por duplo clique, ele lê `questions.js`, não `questions.json`, porque muitos navegadores bloqueiam `fetch()` de arquivos locais por segurança. Portanto, após editar o JSON, você pode regenerar `questions.js` com:

```bash
python - <<'PY'
import json
from pathlib import Path
qs = json.loads(Path('questions.json').read_text(encoding='utf-8'))
Path('questions.js').write_text('window.QUESTION_BANK = ' + json.dumps(qs, ensure_ascii=False) + ';\n', encoding='utf-8')
PY
```

## Personalizações rápidas

No início do jogo, você pode alterar:

- Pontos para vencer.
- Tempo por pergunta.
- Número de consultas à equipe.
- Número de pesquisas no Google.
- Número de bônus de +1 minuto.
- Quantidade de equipes.
- Cores das equipes.
- Nomes dos integrantes.

## Atalhos durante o jogo

- Teclas `1`, `2`, `3`, `4`: respondem as alternativas.
- Barra de espaço: avança para a próxima rodada depois de responder.
