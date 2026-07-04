import json
import re
from collections import Counter
from pathlib import Path


EXPECTED_AREAS = {
    "Geografia",
    "História",
    "Ciências",
    "Cultura geral",
    "Cultura pop",
    "Esportes",
    "Brasil",
    "Animais e natureza",
    "Língua portuguesa",
    "Artes e literatura",
    "Tecnologia",
    "Nutrição",
    "Odontologia",
    "Enfermagem",
    "Matemática e raciocínio",
}
EXPECTED_DIFFICULTIES = {"Fácil", "Média", "Avançada"}
FORBIDDEN_PATTERNS = [
    r"Rodada técnica",
    r"Pergunta clássica",
    r"Curiosidade geral",
    r"Questão gerada",
    r"Desempate rápido",
    r"O que está sendo descrito",
    r"Qual alternativa corresponde a esta pista",
    r"Qual resposta combina melhor com esta descrição",
    r"A pista '.+' aponta",
    r"Qual opção se encaixa na explicação",
    r"qual resposta a descrição indica",
    r"#\d+",
]


def normalize_question(text):
    text = text.lower().strip()
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def load_js_bank():
    content = Path("questions.js").read_text(encoding="utf-8")
    prefix = "window.QUESTION_BANK = "
    if not content.startswith(prefix) or not content.rstrip().endswith(";"):
        raise AssertionError("questions.js não tem o formato esperado.")
    return json.loads(content[len(prefix) : content.rfind(";")])


def main():
    questions = json.loads(Path("questions.json").read_text(encoding="utf-8"))
    js_questions = load_js_bank()
    errors = []

    if questions != js_questions:
        errors.append("questions.json e questions.js não estão sincronizados.")
    if len(questions) != 500:
        errors.append(f"Banco deve ter exatamente 500 perguntas, mas tem {len(questions)}.")

    ids = [q.get("id") for q in questions]
    if len(ids) != len(set(ids)):
        errors.append("Há IDs duplicados.")
    expected_ids = [f"Q{i:04d}" for i in range(1, len(questions) + 1)]
    if ids != expected_ids:
        errors.append("IDs não estão sequenciais a partir de Q0001.")

    area_counts = Counter()
    difficulty_counts = Counter()
    normalized_questions = Counter()
    answer_counts = Counter()

    for idx, q in enumerate(questions, start=1):
        label = q.get("id", f"linha {idx}")
        for field in ("id", "area", "difficulty", "question", "options", "answer", "explanation"):
            if field not in q or q[field] in ("", None, []):
                errors.append(f"{label}: campo vazio ou ausente: {field}.")

        area = q.get("area")
        difficulty = q.get("difficulty")
        question = q.get("question", "")
        options = q.get("options", [])
        answer = q.get("answer")

        if area not in EXPECTED_AREAS:
            errors.append(f"{label}: área inválida: {area}.")
        if difficulty not in EXPECTED_DIFFICULTIES:
            errors.append(f"{label}: dificuldade inválida: {difficulty}.")
        if not isinstance(options, list) or len(options) != 4:
            errors.append(f"{label}: precisa ter exatamente 4 alternativas.")
        if len(set(options)) != len(options):
            errors.append(f"{label}: alternativas repetidas.")
        if answer not in options:
            errors.append(f"{label}: resposta não aparece nas alternativas.")
        if any(re.search(pattern, question, flags=re.IGNORECASE) for pattern in FORBIDDEN_PATTERNS):
            errors.append(f"{label}: pergunta tem prefixo ou marcador proibido.")

        area_counts[area] += 1
        difficulty_counts[difficulty] += 1
        normalized_questions[normalize_question(question)] += 1
        answer_counts[answer] += 1

    duplicates = [q for q, count in normalized_questions.items() if count > 1]
    if duplicates:
        errors.append(f"Há perguntas duplicadas ou quase duplicadas: {duplicates[:5]}.")

    math_count = area_counts["Matemática e raciocínio"]
    math_pct = math_count / len(questions) * 100
    if math_pct > 5:
        errors.append(f"Matemática está acima de 5%: {math_pct:.2f}%.")

    non_math_counts = [count for area, count in area_counts.items() if area != "Matemática e raciocínio"]
    if max(non_math_counts) - min(non_math_counts) > 10:
        errors.append("Categorias não matemáticas estão desbalanceadas.")

    easy = difficulty_counts["Fácil"] / len(questions) * 100
    medium = difficulty_counts["Média"] / len(questions) * 100
    advanced = difficulty_counts["Avançada"] / len(questions) * 100
    if not (42 <= easy <= 48 and 37 <= medium <= 43 and 12 <= advanced <= 18):
        errors.append(f"Distribuição de dificuldade fora da faixa: {dict(difficulty_counts)}.")

    overused_answers = [answer for answer, count in answer_counts.items() if count > 28]
    if overused_answers:
        errors.append(f"Respostas corretas repetidas em excesso: {overused_answers[:8]}.")

    print(f"Total: {len(questions)}")
    print("Áreas:")
    for area, count in sorted(area_counts.items()):
        print(f"  {area}: {count}")
    print("Dificuldades:")
    for difficulty, count in sorted(difficulty_counts.items()):
        print(f"  {difficulty}: {count}")
    print(f"Matemática: {math_count} ({math_pct:.2f}%)")

    if errors:
        print("\nErros:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Validação concluída sem erros.")


if __name__ == "__main__":
    main()
