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
    errors.push(`${file} não deve existir: o jogo não usa banco local.`);
  }
});

if (html.includes("questions.js")) {
  errors.push("index.html ainda carrega questions.js.");
}

if (/QUESTION_BANK|normalizeLocalQuestion|localQuestions|fallback local|perguntas locais|banco local|source:\s*["']local["']/.test(app)) {
  errors.push("app.js ainda contém lógica de banco local.");
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
  "CACHE_KEY",
].forEach((needle) => {
  if (!app.includes(needle)) errors.push(`Rotina obrigatória ausente em app.js: ${needle}`);
});

if (!/source,\s*\n\s*area:/.test(app)) {
  errors.push("normalização não preserva source nas perguntas externas.");
}

if (!/Matemática e Raciocínio/.test(app) || !/\/ 95\) \* 5/.test(app)) {
  errors.push("limite de matemática em até 5% não foi encontrado.");
}

if (errors.length) {
  console.error("Erros:");
  errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

console.log("Validação concluída: jogo sem banco local, usando Tryvia/OpenTDB/cache externo validado.");
