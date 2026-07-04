const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const questionsPath = path.join(root, "questions.json");
const jsPath = path.join(root, "questions.js");

const allowedSources = new Set(["local"]);
const allowedDifficulties = new Set(["Fácil", "Média", "Avançada"]);
const allowedAreas = new Set([
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
]);
const forbiddenPatterns = [
  /Rodada técnica/i,
  /Pergunta clássica/i,
  /Questão gerada/i,
  /Curiosidade geral/i,
  /Pergunta\s*#\d+/i,
  /Rodada\s*#\d+/i,
  /Técnica leve\s*#\d+/i,
  /O que está sendo descrito/i,
  /Qual alternativa corresponde a esta pista/i,
  /Qual resposta combina melhor com esta descrição/i,
  /Qual opção se encaixa na explicação/i,
  /#\d+/,
];
const englishHints = /\b(what|which|who|where|when|according to|following|true|false|capital of)\b/i;
const badOptions = new Set(["todas as anteriores", "nenhuma das anteriores", "não sei", "n/a"]);

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^\w]+/g, " ")
    .trim();
}

function countBy(items, field) {
  return items.reduce((acc, item) => {
    acc[item[field]] = (acc[item[field]] || 0) + 1;
    return acc;
  }, {});
}

function loadJsQuestions() {
  const content = fs.readFileSync(jsPath, "utf8");
  const prefix = "window.QUESTION_BANK = ";
  if (!content.startsWith(prefix) || !content.trim().endsWith(";")) {
    throw new Error("questions.js não está no formato esperado.");
  }
  return JSON.parse(content.slice(prefix.length, content.lastIndexOf(";")));
}

const questions = JSON.parse(fs.readFileSync(questionsPath, "utf8"));
const jsQuestions = loadJsQuestions();
const errors = [];

if (JSON.stringify(questions) !== JSON.stringify(jsQuestions)) {
  errors.push("questions.json e questions.js não estão sincronizados.");
}
if (questions.length !== 500) {
  errors.push(`O banco local deve ter 500 perguntas. Atual: ${questions.length}.`);
}

const ids = new Set();
const seenQuestions = new Set();

questions.forEach((question, index) => {
  const label = question.id || `item ${index + 1}`;
  ["id", "source", "area", "difficulty", "question", "options", "answer", "explanation"].forEach((field) => {
    if (question[field] == null || question[field] === "" || (Array.isArray(question[field]) && !question[field].length)) {
      errors.push(`${label}: campo vazio ou ausente: ${field}.`);
    }
  });

  if (ids.has(question.id)) errors.push(`${label}: ID duplicado.`);
  ids.add(question.id);
  if (!allowedSources.has(question.source)) errors.push(`${label}: source inválido: ${question.source}.`);
  if (!allowedAreas.has(question.area)) errors.push(`${label}: área inválida: ${question.area}.`);
  if (!allowedDifficulties.has(question.difficulty)) errors.push(`${label}: dificuldade inválida: ${question.difficulty}.`);

  if (!Array.isArray(question.options) || question.options.length !== 4) {
    errors.push(`${label}: precisa ter exatamente 4 alternativas.`);
  } else {
    const normalizedOptions = question.options.map(normalize);
    if (new Set(normalizedOptions).size !== 4) errors.push(`${label}: alternativas duplicadas ou quase idênticas.`);
    if (!question.options.includes(question.answer)) errors.push(`${label}: resposta correta não está nas alternativas.`);
    if (question.options.some((option) => !String(option).trim())) {
      errors.push(`${label}: alternativa vazia.`);
    }
    if (question.options.some((option) => badOptions.has(normalize(option)))) {
      errors.push(`${label}: alternativa genérica inválida.`);
    }
  }

  const normalizedQuestion = normalize(question.question);
  if (seenQuestions.has(normalizedQuestion)) errors.push(`${label}: pergunta duplicada ou quase duplicada.`);
  seenQuestions.add(normalizedQuestion);

  if (forbiddenPatterns.some((pattern) => pattern.test(question.question))) {
    errors.push(`${label}: pergunta contém prefixo ou formulação proibida.`);
  }
  if (englishHints.test(question.question)) {
    errors.push(`${label}: pergunta parece estar em inglês.`);
  }
  if (question.question.length > 180) {
    errors.push(`${label}: pergunta longa demais.`);
  }
});

const areaCounts = countBy(questions, "area");
const difficultyCounts = countBy(questions, "difficulty");
const mathPct = ((areaCounts["Matemática e raciocínio"] || 0) / questions.length) * 100;
if (mathPct > 5) errors.push(`Matemática acima de 5%: ${mathPct.toFixed(2)}%.`);

const nonMathCounts = Object.entries(areaCounts)
  .filter(([area]) => area !== "Matemática e raciocínio")
  .map(([, count]) => count);
if (Math.max(...nonMathCounts) - Math.min(...nonMathCounts) > 10) {
  errors.push("Categorias locais estão desbalanceadas.");
}

console.log(`Total: ${questions.length}`);
console.log("Áreas:", areaCounts);
console.log("Dificuldades:", difficultyCounts);
console.log(`Matemática: ${mathPct.toFixed(2)}%`);

if (errors.length) {
  console.error("\nErros:");
  errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

console.log("Validação concluída sem erros.");
