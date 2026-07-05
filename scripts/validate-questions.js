const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const appPath = path.join(root, "app.js");
const indexPath = path.join(root, "index.html");
const errors = [];

const app = fs.readFileSync(appPath, "utf8");
const html = fs.readFileSync(indexPath, "utf8");

["questions.json", "questions.js", "generate_questions.py", "validate_questions.py"].forEach((file) => {
  if (fs.existsSync(path.join(root, file))) {
    errors.push(`${file} não deve existir: o fallback local fica embutido em app.js para funcionar abrindo index.html.`);
  }
});

if (html.includes("questions.js")) {
  errors.push("index.html ainda carrega questions.js.");
}

if (/QUESTION_BANK/.test(app)) {
  errors.push("app.js ainda contém a variável antiga QUESTION_BANK.");
}

[
  "https://tryvia.ptr.red/api_token.php?command=request",
  "https://tryvia.ptr.red/api.php",
  "https://opentdb.com/api_token.php?command=request",
  "https://opentdb.com/api.php",
].forEach((needle) => {
  if (!app.includes(needle)) errors.push(`Endpoint ausente em app.js: ${needle}`);
});

[
  "type=multiple",
  "response_code",
  "decodeHtmlEntities",
  "validateQuestion",
  "buildBalancedQuestionQueue",
  "LOCAL_FALLBACK_QUESTIONS",
  "normalizeLocalQuestion",
  "fetchWithTimeout",
  "selectNextQuestion",
  "currentRoundQuestionIds",
  "usedQuestionIds",
  "recentQuestionIdsQueue",
  "teamDifficultyStats",
  "teamAreaStats",
  "DEBUG_QUESTION_SELECTION",
  "CACHE_KEY",
].forEach((needle) => {
  if (!app.includes(needle)) errors.push(`Rotina obrigatória ausente em app.js: ${needle}`);
});

if (!/currentRoundQuestionIds\.has\(key\)/.test(app) || !/currentRoundQuestionIds\.add\(key\)/.test(app)) {
  errors.push("controle de perguntas usadas na rodada não foi encontrado.");
}

if (!/currentRoundQuestionIds\.clear\(\)/.test(app) || !/currentRoundAreas\.clear\(\)/.test(app)) {
  errors.push("limpeza dos controles de rodada não foi encontrada.");
}

if (!/source,\s*\n\s*area:/.test(app)) {
  errors.push("normalização não preserva source nas perguntas externas.");
}

if (!/Matemática e Raciocínio/.test(app) || !/\/ 95\) \* 5/.test(app)) {
  errors.push("limite de matemática em até 5% não foi encontrado.");
}

const fallbackMatch = app.match(/const LOCAL_FALLBACK_QUESTIONS = (\[[\s\S]*?\n  \]);/);
if (!fallbackMatch) {
  errors.push("LOCAL_FALLBACK_QUESTIONS não foi encontrado.");
} else {
  const forbidden = /(Rodada técnica|Pergunta clássica|Questão gerada|Curiosidade geral|Pergunta\s*#|Rodada\s*#|Técnica leve\s*#)/i;
  const unstable = /\b(atualmente|hoje)\b|presidente atual|campeão atual|ranking atual|CEO atual/i;
  const english = /\b(what|which|who|where|when|how many|true|false)\b/i;
  const allowedDifficulties = new Set(["Fácil", "Média", "Avançada"]);
  const allowedAreas = new Set([
    "Conhecimentos Gerais", "Geografia", "História", "Ciências", "Animais e Natureza", "Brasil",
    "Cultura Pop", "Esportes", "Artes e Literatura", "Tecnologia", "Nutrição", "Odontologia",
    "Enfermagem", "Matemática e Raciocínio"
  ]);
  let questions = [];
  try {
    questions = Function(`"use strict"; return ${fallbackMatch[1]};`)();
  } catch (error) {
    errors.push(`fallback local não pôde ser lido: ${error.message}`);
  }
  const ids = new Set();
  const texts = new Set();
  const areaCounts = {};
  const difficultyCounts = {};
  questions.forEach((question, index) => {
    const label = `fallback local #${index + 1}`;
    ["area", "difficulty", "question", "answer", "explanation"].forEach((field) => {
      if (!String(question[field] || "").trim()) errors.push(`${label}: campo vazio ${field}.`);
    });
    const id = question.id || question.question;
    if (ids.has(id)) errors.push(`${label}: id/texto duplicado.`);
    ids.add(id);
    const normalizedText = String(question.question || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\w]+/g, " ").trim();
    if (texts.has(normalizedText)) errors.push(`${label}: pergunta duplicada.`);
    texts.add(normalizedText);
    if (!allowedAreas.has(question.area)) errors.push(`${label}: área inválida ${question.area}.`);
    if (!allowedDifficulties.has(question.difficulty)) errors.push(`${label}: dificuldade inválida ${question.difficulty}.`);
    if (!Array.isArray(question.options) || question.options.length !== 4) errors.push(`${label}: precisa ter 4 alternativas.`);
    else {
      const normalizedOptions = question.options.map((option) => String(option).toLowerCase().trim());
      if (new Set(normalizedOptions).size !== 4) errors.push(`${label}: alternativas duplicadas.`);
      if (!question.options.includes(question.answer)) errors.push(`${label}: resposta ausente nas alternativas.`);
      if (question.options.some((option) => String(option).length > 90)) errors.push(`${label}: alternativa longa demais.`);
    }
    if (String(question.question || "").length > 180) errors.push(`${label}: pergunta longa demais.`);
    if (forbidden.test(question.question)) errors.push(`${label}: prefixo proibido.`);
    if (unstable.test(question.question)) errors.push(`${label}: atualidade instável.`);
    if (english.test(question.question)) errors.push(`${label}: provável pergunta em inglês.`);
    if (/&[a-z]+;|<[^>]+>/.test(question.question)) errors.push(`${label}: HTML/entity não tratado.`);
    areaCounts[question.area] = (areaCounts[question.area] || 0) + 1;
    difficultyCounts[question.difficulty] = (difficultyCounts[question.difficulty] || 0) + 1;
  });
  const mathCount = areaCounts["Matemática e Raciocínio"] || 0;
  if (questions.length && mathCount / questions.length > 0.05) errors.push(`matemática acima de 5% no fallback local: ${mathCount}/${questions.length}.`);
  console.log("Fallback local:", questions.length, "perguntas");
  console.log("Áreas:", areaCounts);
  console.log("Dificuldades:", difficultyCounts);
}

if (errors.length) {
  console.error("Erros:");
  errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

console.log("Validação concluída: fontes online, cache e fallback local validados.");
