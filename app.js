(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const COLORS = ["#7dd3fc", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#f472b6", "#38bdf8", "#c4b5fd"];
  const CIRC = 2 * Math.PI * 52;
  const CACHE_KEY = "batalhaPerguntasQuestionCache.v1";
  const PRIMARY_TOKEN_KEY = "batalhaPerguntasPrimaryToken.v1";
  const SECONDARY_TOKEN_KEY = "batalhaPerguntasSecondaryToken.v1";
  const FORBIDDEN_QUESTION_PATTERNS = [
    /Rodada técnica/i, /Pergunta clássica/i, /Questão gerada/i, /Curiosidade geral/i,
    /Pergunta\s*#\d+/i, /Rodada\s*#\d+/i, /Técnica leve\s*#\d+/i,
    /O que está sendo descrito/i, /Qual alternativa corresponde a esta pista/i,
    /Qual resposta combina melhor com esta descrição/i, /Qual opção se encaixa na explicação/i
  ];
  const UNSTABLE_PATTERNS = [/\batualmente\b/i, /\bhoje\b/i, /presidente atual/i, /campeão atual/i, /ranking atual/i, /CEO atual/i];
  const PORTUGUESE_HINTS = /\b(qual|quem|onde|quando|como|por que|Brasil|brasileir|é|ção|ções|ã|õ|á|é|í|ó|ú|ç)\b/i;
  const ENGLISH_HINTS = /\b(what|which|who|where|when|how many|according to|following|true|false)\b/i;

  const els = {
    setupView: $("#setupView"), gameView: $("#gameView"), winnerView: $("#winnerView"),
    setupForm: $("#setupForm"), teamsBuilder: $("#teamsBuilder"), buildTeamsBtn: $("#buildTeamsBtn"),
    addTeamBtn: $("#addTeamBtn"), loadExampleBtn: $("#loadExampleBtn"), initialTeamCount: $("#initialTeamCount"),
    targetScore: $("#targetScore"), baseTime: $("#baseTime"), teamHelpCount: $("#teamHelpCount"),
    googleHelpCount: $("#googleHelpCount"), timeHelpCount: $("#timeHelpCount"), questionCountText: $("#questionCountText"),
    scoreboard: $("#scoreboard"), finalScoreboard: $("#finalScoreboard"), questionPanel: $("#questionPanel"),
    turnStrip: $("#turnStrip"), areaBadge: $("#areaBadge"), difficultyBadge: $("#difficultyBadge"), questionId: $("#questionId"),
    gameTitle: $("#gameTitle"), answers: $("#answers"), feedback: $("#feedback"),
    teamHelpBtn: $("#teamHelpBtn"), googleHelpBtn: $("#googleHelpBtn"), timeHelpBtn: $("#timeHelpBtn"),
    timerWrap: $("#timerWrap"), timerLabel: $("#timerLabel"), timerText: $("#timerText"), timerProgress: $("#timerProgress"), skipBtn: $("#skipBtn"), nextBtn: $("#nextBtn"),
    pauseBtn: $("#pauseBtn"), resetBtn: $("#resetBtn"), clearCacheBtn: $("#clearCacheBtn"), rulesBtn: $("#rulesBtn"), closeRulesBtn: $("#closeRulesBtn"),
    rulesDialog: $("#rulesDialog"), winnerTitle: $("#winnerTitle"), winnerText: $("#winnerText"),
    playAgainBtn: $("#playAgainBtn"), newSetupBtn: $("#newSetupBtn"), confettiLayer: $("#confettiLayer"),
    questionLoadStatus: $("#questionLoadStatus"), startGameBtn: $("#startGameBtn")
  };

  let teamDrafts = [];
  let game = null;
  let timerHandle = null;
  let audioCtx = null;
  let audioReady = false;
  let musicHandle = null;
  let musicStep = 0;

  function shuffle(arr) {
    const copy = [...arr];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function clampNumber(value, fallback, min = 0) {
    const num = Number(value);
    return Number.isFinite(num) && num >= min ? num : fallback;
  }

  function showView(view) {
    [els.setupView, els.gameView, els.winnerView].forEach(v => v.classList.remove("active"));
    view.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function initAudio() {
    if (!audioReady) return;
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }

  function tone(freq, duration, type = "sine", gain = 0.045, delay = 0) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const vol = audioCtx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    vol.gain.value = 0;
    osc.connect(vol);
    vol.connect(audioCtx.destination);
    const t = audioCtx.currentTime + delay;
    vol.gain.linearRampToValueAtTime(gain, t + 0.01);
    vol.gain.exponentialRampToValueAtTime(0.001, t + duration);
    osc.start(t);
    osc.stop(t + duration + 0.04);
  }

  function startMusic() {
    if (!audioReady || musicHandle || !game || game.paused || game.answered) return;
    initAudio();
    if (!audioCtx) return;
    if (audioCtx.state === "suspended") audioCtx.resume();
    musicHandle = setInterval(playMusicPulse, 720);
    playMusicPulse();
  }

  function stopMusic() {
    if (musicHandle) clearInterval(musicHandle);
    musicHandle = null;
  }

  function playMusicPulse() {
    if (!audioCtx || !game || game.paused || game.answered) {
      stopMusic();
      return;
    }
    const bass = [130.81, 146.83, 164.81, 196.00];
    const color = [261.63, 329.63, 392.00, 493.88, 440.00, 392.00, 329.63, 293.66];
    tone(bass[Math.floor(musicStep / 4) % bass.length], 0.42, "triangle", 0.009, 0);
    if (musicStep % 2 === 0) tone(color[musicStep % color.length], 0.18, "sine", 0.006, 0.08);
    musicStep = (musicStep + 1) % 16;
  }

  function playSound(kind) {
    try {
      if (!audioReady) return;
      initAudio();
      if (!audioCtx) return;
      if (audioCtx.state === "suspended") audioCtx.resume();
      if (kind === "correct") {
        tone(523.25, 0.16, "triangle", 0.09, 0);
        tone(659.25, 0.18, "triangle", 0.085, 0.10);
        tone(783.99, 0.24, "triangle", 0.085, 0.21);
        tone(1046.50, 0.28, "sine", 0.065, 0.36);
      } else if (kind === "wrong") {
        tone(196, 0.28, "sawtooth", 0.07, 0);
        tone(155.56, 0.30, "sawtooth", 0.065, 0.16);
        tone(98, 0.36, "triangle", 0.055, 0.34);
      } else if (kind === "tick") {
        tone(880, 0.06, "square", 0.018, 0);
      } else if (kind === "tick-warning") {
        tone(620, 0.06, "triangle", 0.025, 0);
      } else if (kind === "tick-danger") {
        tone(760, 0.075, "square", 0.036, 0);
      } else if (kind === "tick-critical") {
        tone(980, 0.08, "square", 0.048, 0);
        tone(1220, 0.065, "triangle", 0.032, 0.055);
      } else if (kind === "win") {
        [523, 659, 784, 1046, 1318, 1568].forEach((f, i) => tone(f, 0.24, "triangle", 0.085, i * 0.11));
      }
    } catch (e) {
      // Audio is decorative; ignore browser restrictions.
    }
  }

  function celebrate(teamColor = "#7dd3fc") {
    const colors = [teamColor, "#7dd3fc", "#a78bfa", "#34d399", "#fbbf24", "#fb7185"];
    for (let i = 0; i < 90; i++) {
      const piece = document.createElement("span");
      piece.className = Math.random() > 0.72 ? "balloon" : "confetti";
      piece.style.left = `${Math.random() * 100}%`;
      piece.style.top = piece.className === "balloon" ? `${75 + Math.random() * 25}%` : `${-5 - Math.random() * 15}%`;
      piece.style.background = colors[i % colors.length];
      piece.style.color = colors[i % colors.length];
      piece.style.setProperty("--dx", `${(Math.random() - 0.5) * 360}px`);
      piece.style.animationDelay = `${Math.random() * 0.35}s`;
      els.confettiLayer.appendChild(piece);
      setTimeout(() => piece.remove(), 2200);
    }
  }

  function makeTeamDraft(index, existing = {}) {
    return {
      name: existing.name || `Equipe ${index + 1}`,
      color: existing.color || COLORS[index % COLORS.length],
      size: existing.size || 3,
      members: existing.members || Array.from({ length: existing.size || 3 }, (_, i) => `Jogador ${i + 1}`)
    };
  }

  function normalizeMembers(team) {
    const size = clampNumber(team.size, 1, 1);
    const members = [...(team.members || [])];
    while (members.length < size) members.push(`Jogador ${members.length + 1}`);
    team.members = members.slice(0, size);
    team.size = size;
  }

  function renderTeamsBuilder() {
    els.teamsBuilder.innerHTML = "";
    teamDrafts.forEach((team, index) => {
      normalizeMembers(team);
      const card = document.createElement("article");
      card.className = "team-card";
      card.innerHTML = `
        <div class="team-card-head">
          <label>Nome da equipe
            <input data-field="name" data-team="${index}" value="${escapeAttr(team.name)}" />
          </label>
          <label>Cor
            <input data-field="color" data-team="${index}" type="color" value="${team.color}" />
          </label>
          <label>Integrantes
            <input data-field="size" data-team="${index}" type="number" min="1" value="${team.size}" />
          </label>
          <button class="remove-team" type="button" data-remove="${index}">Remover</button>
        </div>
        <div class="members" data-members="${index}"></div>
      `;
      const membersWrap = card.querySelector(".members");
      team.members.forEach((member, memberIndex) => {
        const label = document.createElement("label");
        label.innerHTML = `Integrante ${memberIndex + 1}<input data-team="${index}" data-member="${memberIndex}" value="${escapeAttr(member)}" />`;
        membersWrap.appendChild(label);
      });
      els.teamsBuilder.appendChild(card);
    });
  }

  function escapeAttr(str) {
    return String(str).replaceAll("&", "&amp;").replaceAll("\"", "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  }

  function buildTeams(count = 3) {
    const n = clampNumber(count, 3, 2);
    teamDrafts = Array.from({ length: n }, (_, i) => makeTeamDraft(i, teamDrafts[i]));
    renderTeamsBuilder();
  }

  function collectTeamsFromDom() {
    $$('[data-field]').forEach(input => {
      const team = teamDrafts[Number(input.dataset.team)];
      const field = input.dataset.field;
      if (!team) return;
      if (field === "size") {
        team.size = clampNumber(input.value, 1, 1);
        normalizeMembers(team);
      } else {
        team[field] = input.value.trim() || (field === "name" ? `Equipe ${Number(input.dataset.team) + 1}` : COLORS[Number(input.dataset.team) % COLORS.length]);
      }
    });
    $$('[data-member]').forEach(input => {
      const t = Number(input.dataset.team);
      const m = Number(input.dataset.member);
      if (teamDrafts[t]) teamDrafts[t].members[m] = input.value.trim();
    });
    teamDrafts.forEach(normalizeMembers);
  }

  function validateSetup() {
    collectTeamsFromDom();
    if (teamDrafts.length < 2) return "Cadastre pelo menos 2 equipes.";
    for (const [i, team] of teamDrafts.entries()) {
      if (!team.name.trim()) return `A equipe ${i + 1} precisa ter nome.`;
      if (team.members.length !== Number(team.size)) return `${team.name} precisa ter exatamente ${team.size} integrantes.`;
      const blank = team.members.findIndex(m => !m.trim());
      if (blank !== -1) return `${team.name}: preencha o nome do integrante ${blank + 1}.`;
    }
    return null;
  }

  function setQuestionStatus(message, state = "") {
    if (!els.questionLoadStatus) return;
    els.questionLoadStatus.textContent = message;
    els.questionLoadStatus.classList.remove("warning", "success");
    if (state) els.questionLoadStatus.classList.add(state);
  }

  function decodeHtmlEntities(text) {
    const el = document.createElement("textarea");
    el.innerHTML = String(text || "");
    return el.value.replace(/\s+/g, " ").trim();
  }

  function stripQuestionPrefix(text) {
    return decodeHtmlEntities(text)
      .replace(/^(Rodada técnica leve|Pergunta clássica|Questão gerada|Curiosidade geral|Pergunta|Rodada|Técnica leve)\s*#?\d*\s*[:\-]\s*/i, "")
      .trim();
  }

  function normalizeText(text) {
    return decodeHtmlEntities(text).replace(/\s+/g, " ").trim();
  }

  function mapDifficulty(raw) {
    const value = String(raw || "").toLowerCase();
    if (value === "easy" || value === "fácil") return "Fácil";
    if (value === "medium" || value === "média" || value === "médio") return "Média";
    if (value === "hard" || value === "avançada" || value === "avançado") return "Avançada";
    return "Fácil";
  }

  function mapExternalCategory(category, source) {
    const value = normalizeText(category).toLowerCase();
    if (/geography|geografia/.test(value)) return "Geografia";
    if (/history|história|historia/.test(value)) return "História";
    if (/computer|gadget|technology|tecnologia|informática|informatica|computadores|dispositivos/.test(value)) return "Tecnologia";
    if (/mathematics|math|matemática|matematica/.test(value)) return "Matemática e Raciocínio";
    if (/science|nature|ciências|ciencias|natureza/.test(value)) return "Ciências";
    if (/animal|animais/.test(value)) return "Animais e Natureza";
    if (/sport|esporte/.test(value)) return "Esportes";
    if (/book|art|literature|arte|literatura/.test(value)) return "Artes e Literatura";
    if (/film|music|television|video game|cartoon|anime|entertainment|cultura pop/.test(value)) return "Cultura Pop";
    if (/brasil|brazil/.test(value)) return "Brasil";
    return source === "opentdb" ? "Conhecimentos Gerais" : "Conhecimentos Gerais";
  }

  function canonicalArea(area) {
    const value = normalizeText(area).toLowerCase();
    if (value === "cultura geral" || value === "conhecimentos gerais") return "Conhecimentos Gerais";
    if (value === "cultura pop") return "Cultura Pop";
    if (value === "animais e natureza") return "Animais e Natureza";
    if (value === "artes e literatura") return "Artes e Literatura";
    if (value === "matemática e raciocínio" || value === "matemática e raciocinio") return "Matemática e Raciocínio";
    return normalizeText(area);
  }

  function isProbablyPortuguese(question, source) {
    if (source === "tryvia") return true;
    return PORTUGUESE_HINTS.test(question) && !ENGLISH_HINTS.test(question);
  }

  function normalizeExternalQuestion(raw, source, index = 0) {
    if (!raw || raw.type !== "multiple") return null;
    const question = stripQuestionPrefix(raw.question);
    const answer = normalizeText(raw.correct_answer);
    const wrongs = Array.isArray(raw.incorrect_answers) ? raw.incorrect_answers.map(normalizeText) : [];
    const options = [answer, ...wrongs].filter(Boolean);
    return {
      id: `Q${String(Date.now()).slice(-6)}-${String(index + 1).padStart(2, "0")}`,
      source,
      area: canonicalArea(mapExternalCategory(raw.category, source)),
      difficulty: mapDifficulty(raw.difficulty),
      question,
      options,
      answer,
      explanation: ""
    };
  }

  function validateQuestion(question) {
    if (!question || !question.question || !question.answer || !question.area || !question.difficulty) return false;
    if (!Array.isArray(question.options) || question.options.length !== 4) return false;
    if (new Set(question.options.map(o => o.toLowerCase())).size !== 4) return false;
    if (!question.options.includes(question.answer)) return false;
    if (question.question.length < 10 || question.question.length > 180) return false;
    if (question.options.some(option => option.length < 1 || option.length > 90)) return false;
    if (FORBIDDEN_QUESTION_PATTERNS.some(pattern => pattern.test(question.question))) return false;
    if (UNSTABLE_PATTERNS.some(pattern => pattern.test(question.question))) return false;
    if (!isProbablyPortuguese(question.question, question.source)) return false;
    if (/<[^>]+>/.test(question.question) || question.options.some(option => /<[^>]+>/.test(option))) return false;
    return true;
  }

  function dedupeQuestions(questions) {
    const seen = new Set();
    return questions.filter(question => {
      const key = question.question.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\w]+/g, " ").trim();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function limitMathShare(questions) {
    const nonMath = questions.filter(q => q.area !== "Matemática e Raciocínio");
    const mathLimit = Math.floor((nonMath.length / 95) * 5);
    const math = questions.filter(q => q.area === "Matemática e Raciocínio").slice(0, Math.max(1, mathLimit));
    return [...nonMath, ...math];
  }

  function buildBalancedQuestionQueue(questions) {
    const clean = limitMathShare(dedupeQuestions(questions.filter(validateQuestion)));
    const byArea = clean.reduce((acc, question) => {
      (acc[question.area] ||= []).push(question);
      return acc;
    }, {});
    Object.values(byArea).forEach(list => {
      const order = { "Fácil": 0, "Média": 1, "Avançada": 2 };
      list.sort((a, b) => order[a.difficulty] - order[b.difficulty]);
    });
    const result = [];
    let lastArea = null;
    while (Object.values(byArea).some(list => list.length)) {
      const areas = Object.keys(byArea)
        .filter(area => byArea[area].length && area !== lastArea)
        .sort((a, b) => byArea[b].length - byArea[a].length);
      const area = areas[0] || Object.keys(byArea).find(key => byArea[key].length);
      if (!area) break;
      result.push(byArea[area].shift());
      lastArea = area;
    }
    return result;
  }

  function readQuestionCache() {
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (!cached || !Array.isArray(cached.questions)) return [];
      if (Date.now() - cached.savedAt > 6 * 60 * 60 * 1000) return [];
      return cached.questions.map((q, i) => ({ ...q, id: q.id || `cache-${i + 1}` }));
    } catch (e) {
      return [];
    }
  }

  function saveQuestionCache(questions) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), questions: questions.slice(0, 300) }));
    } catch (e) {
      console.warn("Não foi possível salvar cache de perguntas.", e);
    }
  }

  async function requestToken(url, storageKey) {
    const cached = JSON.parse(localStorage.getItem(storageKey) || "null");
    if (cached?.token && Date.now() - cached.savedAt < 5 * 60 * 60 * 1000) return cached.token;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Falha ao pedir token: ${response.status}`);
    const data = await response.json();
    if (!data.token) throw new Error("Token ausente na resposta.");
    localStorage.setItem(storageKey, JSON.stringify({ token: data.token, savedAt: Date.now() }));
    return data.token;
  }

  async function fetchPrimaryQuestions({ amount = 50 } = {}) {
    const token = await requestToken("https://tryvia.ptr.red/api_token.php?command=request", PRIMARY_TOKEN_KEY);
    const url = `https://tryvia.ptr.red/api.php?amount=${amount}&type=multiple&token=${encodeURIComponent(token)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Fonte principal HTTP ${response.status}`);
    const data = await response.json();
    if (Number(data.response_code) !== 0 || !Array.isArray(data.results)) throw new Error(`Fonte principal response_code ${data.response_code}`);
    return data.results.map((raw, index) => normalizeExternalQuestion(raw, "tryvia", index)).filter(validateQuestion);
  }

  async function fetchSecondaryQuestions({ amount = 20 } = {}) {
    const token = await requestToken("https://opentdb.com/api_token.php?command=request", SECONDARY_TOKEN_KEY);
    const url = `https://opentdb.com/api.php?amount=${Math.min(50, amount)}&type=multiple&token=${encodeURIComponent(token)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Fonte secundária HTTP ${response.status}`);
    const data = await response.json();
    if (Number(data.response_code) !== 0 || !Array.isArray(data.results)) throw new Error(`Fonte secundária response_code ${data.response_code}`);
    return data.results.map((raw, index) => normalizeExternalQuestion(raw, "opentdb", index)).filter(validateQuestion);
  }

  async function loadQuestions() {
    const cached = readQuestionCache();
    setQuestionStatus("Carregando perguntas...", "");
    const slowMessage = setTimeout(() => setQuestionStatus("Buscando perguntas em português...", ""), 1800);
    try {
      setQuestionStatus("Buscando perguntas em português...", "");
      let external = [];
      try {
        external = await fetchPrimaryQuestions({ amount: 50 });
      } catch (e) {
        console.warn("Fonte principal indisponível ou sem perguntas adequadas.", e);
      }
      if (external.length < 20) {
        try {
          setQuestionStatus("Preparando mais perguntas...", "");
          external = [...external, ...(await fetchSecondaryQuestions({ amount: 20 }))];
        } catch (e) {
          console.warn("Fonte secundária indisponível ou sem perguntas adequadas.", e);
        }
      }
      if (external.length) {
        saveQuestionCache(external);
        const queue = buildBalancedQuestionQueue(external);
        clearTimeout(slowMessage);
        setQuestionStatus(`Perguntas carregadas: ${external.length} aprovadas para o jogo.`, "success");
        return queue;
      }
      throw new Error("Nenhuma pergunta externa passou nos filtros.");
    } catch (error) {
      clearTimeout(slowMessage);
      console.warn("Não foi possível carregar perguntas online.", error);
      if (cached.length) {
        const queue = buildBalancedQuestionQueue(cached);
        setQuestionStatus("Não foi possível carregar novas perguntas. Usando perguntas já preparadas anteriormente.", "warning");
        return queue;
      }
      setQuestionStatus("Não foi possível carregar perguntas. Verifique a conexão e tente novamente.", "warning");
      return [];
    }
  }

  function createGame(questionBank) {
    const targetScore = clampNumber(els.targetScore.value, 50, 1);
    const baseTime = clampNumber(els.baseTime.value, 60, 15);
    const teamHelp = clampNumber(els.teamHelpCount.value, 3, 0);
    const googleHelp = clampNumber(els.googleHelpCount.value, 3, 0);
    const timeHelp = clampNumber(els.timeHelpCount.value, 3, 0);
    const teams = teamDrafts.map((t, i) => ({
      name: t.name.trim(), color: t.color || COLORS[i % COLORS.length], members: t.members.map(m => m.trim()),
      memberIndex: 0, score: 0, correct: 0, wrong: 0,
      helps: { team: teamHelp, google: googleHelp, time: timeHelp }
    }));
    game = {
      targetScore, baseTime, teams,
      currentTeamIndex: 0, round: 1, paused: false,
      helpUsedThisTurn: false, usedHelpType: null, answered: false,
      remaining: baseTime, totalForTimer: baseTime,
      questions: shuffle(questionBank || []), allQuestions: questionBank || [], currentQuestion: null, currentOptions: [],
      lastArea: null, lastDifficulty: null, lastTickSecond: null
    };
    localStorage.setItem("batalhaPerguntasSetup", JSON.stringify({ teams: teamDrafts, targetScore, baseTime, teamHelp, googleHelp, timeHelp }));
  }

  async function startGame() {
    const error = validateSetup();
    if (error) {
      alert(error);
      return;
    }
    els.startGameBtn.disabled = true;
    els.startGameBtn.textContent = "Carregando...";
    const questionBank = await loadQuestions();
    if (!questionBank.length) {
      els.startGameBtn.disabled = false;
      els.startGameBtn.textContent = "Começar jogo";
      return;
    }
    createGame(questionBank);
    els.startGameBtn.disabled = false;
    els.startGameBtn.textContent = "Começar jogo";
    showView(els.gameView);
    nextQuestion();
  }

  function getCurrentTeam() {
    return game.teams[game.currentTeamIndex];
  }

  function getCurrentPlayer(team = getCurrentTeam()) {
    return team.members[team.memberIndex % team.members.length];
  }

  function drawQuestion() {
    if (!game.questions.length) {
      game.questions = shuffle(game.allQuestions || []);
    }
    let candidates = game.questions
      .map((q, index) => ({ q, index }))
      .filter(({ q }) => q.area !== game.lastArea);

    if (!candidates.length) {
      game.questions = shuffle(game.allQuestions || []);
      candidates = game.questions
        .map((q, index) => ({ q, index }))
        .filter(({ q }) => q.area !== game.lastArea);
    }

    if (!candidates.length) {
      candidates = game.questions.map((q, index) => ({ q, index }));
    }

    const diffCandidates = candidates.filter(({ q }) => q.difficulty !== game.lastDifficulty);
    if (diffCandidates.length) candidates = diffCandidates;

    const picked = candidates[Math.floor(Math.random() * candidates.length)];
    const q = game.questions.splice(picked.index, 1)[0];
    game.currentQuestion = q;
    game.currentOptions = shuffle(q.options || []);
    game.lastArea = q.area;
    game.lastDifficulty = q.difficulty;
    game.lastTickSecond = null;
  }

  function nextQuestion() {
    clearInterval(timerHandle);
    game.answered = false;
    game.helpUsedThisTurn = false;
    game.usedHelpType = null;
    game.remaining = game.baseTime;
    game.totalForTimer = game.baseTime;
    game.paused = false;
    els.pauseBtn.textContent = "Pausar";
    els.feedback.innerHTML = "";
    els.nextBtn.disabled = true;
    els.questionPanel.classList.remove("correct", "wrong", "timer-normal", "timer-warning", "timer-danger", "timer-critical");
    drawQuestion();
    renderQuestion();
    renderScoreboard();
    updateHelpButtons();
    startTimer();
    startMusic();
  }

  function renderQuestion() {
    const q = game.currentQuestion;
    const team = getCurrentTeam();
    const player = getCurrentPlayer(team);
    document.documentElement.style.setProperty("--team-color", team.color);
    els.turnStrip.innerHTML = `<span class="player-pill" style="--team-color:${team.color}">${escapeHtml(player)}</span><span>${escapeHtml(team.name)} responde agora · Rodada ${game.round}</span>`;
    els.areaBadge.textContent = q.area;
    els.difficultyBadge.textContent = q.difficulty;
    els.questionId.textContent = "";
    els.gameTitle.textContent = q.question;
    els.answers.innerHTML = "";
    game.currentOptions.forEach((option, index) => {
      const btn = document.createElement("button");
      btn.className = "answer-btn";
      btn.type = "button";
      btn.dataset.option = option;
      btn.innerHTML = `<span class="answer-key">${String.fromCharCode(65 + index)}</span><span class="answer-text">${escapeHtml(option)}</span>`;
      btn.addEventListener("click", () => answer(option, btn));
      els.answers.appendChild(btn);
    });
    updateTimerVisual();
  }

  function escapeHtml(str) {
    return String(str).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  }

  function renderScoreboard(final = false) {
    const target = final ? els.finalScoreboard : els.scoreboard;
    target.innerHTML = "";
    game.teams.forEach((team, index) => {
      const item = document.createElement("article");
      item.className = `score-item ${!final && index === game.currentTeamIndex ? "active" : ""}`;
      item.style.setProperty("--team-color", team.color);
      const pct = Math.min(100, (team.score / game.targetScore) * 100);
      item.innerHTML = `
        <div class="score-top">
          <span class="team-name">${escapeHtml(team.name)}</span>
          <span class="score-num">${team.score}</span>
        </div>
        <div class="scorebar"><span style="width:${pct}%"></span></div>
        <div class="score-meta">
          <span>Acertos ${team.correct}</span>
          <span>Erros ${team.wrong}</span>
          <span>Meta ${game.targetScore}</span>
        </div>
      `;
      target.appendChild(item);
    });
  }

  function updateHelpButtons() {
    const team = getCurrentTeam();
    const disabled = game.answered || game.helpUsedThisTurn || game.paused;
    setHelp(els.teamHelpBtn, team.helps.team, disabled || team.helps.team <= 0, game.usedHelpType === "team");
    setHelp(els.googleHelpBtn, team.helps.google, disabled || team.helps.google <= 0, game.usedHelpType === "google");
    setHelp(els.timeHelpBtn, team.helps.time, disabled || team.helps.time <= 0, game.usedHelpType === "time");
  }

  function setHelp(btn, count, disabled, active) {
    btn.querySelector("span").textContent = count;
    btn.disabled = disabled;
    btn.classList.toggle("used", disabled);
    btn.classList.toggle("active-help", active);
  }

  function useHelp(type) {
    if (!game || game.answered || game.helpUsedThisTurn || game.paused) return;
    const team = getCurrentTeam();
    if (team.helps[type] <= 0) return;
    team.helps[type]--;
    game.helpUsedThisTurn = true;
    game.usedHelpType = type;
    if (type === "team") {
      els.feedback.innerHTML = `<strong>Consulta liberada.</strong> ${escapeHtml(team.name)} pode ajudar nesta pergunta. As outras ajudas ficam bloqueadas até a próxima rodada.`;
    }
    if (type === "google") {
      els.feedback.innerHTML = `<strong>Pesquisa liberada.</strong> Uma aba do Google foi aberta com a pergunta atual. As outras ajudas ficam bloqueadas nesta pergunta.`;
      const url = `https://www.google.com/search?q=${encodeURIComponent(game.currentQuestion.question)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    }
    if (type === "time") {
      game.remaining += 60;
      game.totalForTimer += 60;
      els.feedback.innerHTML = `<strong>Bônus usado.</strong> +60 segundos adicionados. Nenhuma outra ajuda pode ser usada nesta pergunta.`;
      updateTimerVisual();
    }
    updateHelpButtons();
    renderScoreboard();
  }

  function startTimer() {
    clearInterval(timerHandle);
    timerHandle = setInterval(() => {
      if (!game || game.paused || game.answered) return;
      game.remaining--;
      playTimerTick();
      updateTimerVisual();
      if (game.remaining <= 0) timeoutQuestion();
    }, 1000);
  }

  function updateTimerVisual() {
    const remaining = Math.max(0, game?.remaining ?? 0);
    const total = Math.max(1, game?.totalForTimer ?? 60);
    const pct = remaining / total;
    const state = remaining <= 5 ? "critical" : remaining <= 15 ? "danger" : remaining <= 30 ? "warning" : "normal";
    els.timerText.textContent = remaining;
    els.timerProgress.style.strokeDasharray = `${CIRC}`;
    els.timerProgress.style.strokeDashoffset = `${CIRC * (1 - pct)}`;
    els.timerProgress.style.stroke = state === "critical" ? "var(--critical)" : state === "danger" ? "var(--danger)" : state === "warning" ? "var(--warning)" : "var(--primary)";
    els.questionPanel.classList.remove("timer-normal", "timer-warning", "timer-danger", "timer-critical");
    els.questionPanel.classList.add(`timer-${state}`);
    if (els.timerWrap) els.timerWrap.className = `timer-wrap timer-${state}`;
    if (els.timerLabel) {
      els.timerLabel.textContent = state === "critical" ? "Tempo acabando" : state === "danger" ? "Reta final" : state === "warning" ? "Atenção" : "Tempo";
    }
  }

  function playTimerTick() {
    if (!game || game.paused || game.answered || game.remaining <= 0) return;
    if (game.lastTickSecond === game.remaining) return;
    game.lastTickSecond = game.remaining;
    if (game.remaining <= 5) {
      playSound("tick-critical");
    } else if (game.remaining <= 15) {
      playSound("tick-danger");
    } else if (game.remaining <= 30 && game.remaining % 5 === 0) {
      playSound("tick-warning");
    }
  }

  function timeoutQuestion() {
    if (game.answered) return;
    answer(null, null, true);
  }

  function answer(option, btn, timeout = false) {
    if (!game || game.answered || game.paused) return;
    game.answered = true;
    clearInterval(timerHandle);
    stopMusic();
    const q = game.currentQuestion;
    const team = getCurrentTeam();
    const correct = option === q.answer;

    $$(".answer-btn").forEach(b => {
      if (b.dataset.option === q.answer) b.classList.add("correct");
      else if (b === btn) b.classList.add("wrong");
      else b.classList.add("dim");
      b.disabled = true;
    });

    if (correct) {
      team.score++;
      team.correct++;
      els.questionPanel.classList.add("correct");
      els.feedback.innerHTML = "<strong>Correto!</strong>";
      playSound("correct");
      celebrate(team.color);
      if (team.score >= game.targetScore) {
        setTimeout(() => finishGame(team), 900);
      }
    } else {
      team.wrong++;
      els.questionPanel.classList.add("wrong");
      const intro = timeout ? "<strong>Tempo esgotado.</strong>" : "<strong>Errado.</strong>";
      els.feedback.innerHTML = `${intro} Resposta correta: <strong>${escapeHtml(q.answer)}</strong>.`;
      playSound("wrong");
    }
    els.nextBtn.disabled = false;
    updateHelpButtons();
    renderScoreboard();
  }

  function advanceTurn() {
    if (!game || !game.answered) return;
    const team = getCurrentTeam();
    team.memberIndex = (team.memberIndex + 1) % team.members.length;
    game.currentTeamIndex = (game.currentTeamIndex + 1) % game.teams.length;
    if (game.currentTeamIndex === 0) game.round++;
    nextQuestion();
  }

  function skipQuestion() {
    if (!game || game.answered || game.paused) return;
    answer(null, null, false);
  }

  function togglePause() {
    if (!game || game.answered) return;
    game.paused = !game.paused;
    els.pauseBtn.textContent = game.paused ? "Retomar" : "Pausar";
    els.feedback.innerHTML = game.paused ? "<strong>Jogo pausado.</strong> O timer foi interrompido." : "";
    if (game.paused) stopMusic();
    else startMusic();
    updateHelpButtons();
  }

  function finishGame(winner) {
    clearInterval(timerHandle);
    stopMusic();
    playSound("win");
    celebrate(winner.color);
    els.winnerTitle.textContent = `${winner.name} venceu!`;
    const ranking = [...game.teams].sort((a, b) => b.score - a.score);
    els.winnerText.textContent = `${winner.name} atingiu ${winner.score} acertos e alcançou a pontuação de vitória. Ranking final: ${ranking.map((team, index) => `${index + 1}. ${team.name} (${team.score})`).join(" · ")}.`;
    renderScoreboard(true);
    showView(els.winnerView);
  }

  function resetAll(toSetup = true) {
    clearInterval(timerHandle);
    stopMusic();
    game = null;
    if (toSetup) showView(els.setupView);
  }

  function loadExample() {
    teamDrafts = [
      { name: "Nutrição", color: "#34d399", size: 4, members: ["Gabriel", "Mama", "InIn", "Lulu"] },
      { name: "Tecnologia", color: "#7dd3fc", size: 4, members: ["Pipi", "Papa", "Muri", "Bibi"] },
      { name: "Odonto & Enfermagem", color: "#a78bfa", size: 4, members: ["Riri", "Gabi", "Rica", "Convidado"] }
    ];
    els.initialTeamCount.value = 3;
    renderTeamsBuilder();
  }

  function restoreSetup() {
    const saved = localStorage.getItem("batalhaPerguntasSetup");
    if (!saved) return false;
    try {
      const data = JSON.parse(saved);
      if (Array.isArray(data.teams) && data.teams.length >= 2) {
        teamDrafts = data.teams;
        els.targetScore.value = data.targetScore ?? 50;
        els.baseTime.value = data.baseTime ?? 60;
        els.teamHelpCount.value = data.teamHelp ?? 3;
        els.googleHelpCount.value = data.googleHelp ?? 3;
        els.timeHelpCount.value = data.timeHelp ?? 3;
        els.initialTeamCount.value = teamDrafts.length;
        renderTeamsBuilder();
        return true;
      }
    } catch (e) {}
    return false;
  }

  function bindEvents() {
    ["pointerdown", "keydown"].forEach(eventName => {
      window.addEventListener(eventName, () => {
        audioReady = true;
        initAudio();
      }, { once: true });
    });
    els.buildTeamsBtn.addEventListener("click", () => buildTeams(els.initialTeamCount.value));
    els.addTeamBtn.addEventListener("click", () => {
      collectTeamsFromDom();
      teamDrafts.push(makeTeamDraft(teamDrafts.length));
      els.initialTeamCount.value = teamDrafts.length;
      renderTeamsBuilder();
    });
    els.loadExampleBtn.addEventListener("click", loadExample);
    els.setupForm.addEventListener("submit", (e) => { e.preventDefault(); startGame(); });
    els.teamsBuilder.addEventListener("input", (e) => {
      const input = e.target;
      if (!input.matches("input")) return;
      if (input.dataset.field === "size") {
        collectTeamsFromDom();
        renderTeamsBuilder();
      }
    });
    els.teamsBuilder.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-remove]");
      if (!btn) return;
      if (teamDrafts.length <= 2) {
        alert("O jogo precisa ter pelo menos 2 equipes.");
        return;
      }
      collectTeamsFromDom();
      teamDrafts.splice(Number(btn.dataset.remove), 1);
      els.initialTeamCount.value = teamDrafts.length;
      renderTeamsBuilder();
    });
    els.teamHelpBtn.addEventListener("click", () => useHelp("team"));
    els.googleHelpBtn.addEventListener("click", () => useHelp("google"));
    els.timeHelpBtn.addEventListener("click", () => useHelp("time"));
    els.skipBtn.addEventListener("click", skipQuestion);
    els.nextBtn.addEventListener("click", advanceTurn);
    els.pauseBtn.addEventListener("click", togglePause);
    els.resetBtn.addEventListener("click", () => {
      if (!game || confirm("Reiniciar e voltar para a configuração?")) resetAll(true);
    });
    els.rulesBtn.addEventListener("click", () => els.rulesDialog.showModal());
    els.closeRulesBtn.addEventListener("click", () => els.rulesDialog.close());
    els.playAgainBtn.addEventListener("click", () => { createGame(game?.allQuestions || []); showView(els.gameView); nextQuestion(); });
    els.newSetupBtn.addEventListener("click", () => resetAll(true));
    els.clearCacheBtn.addEventListener("click", () => {
      localStorage.removeItem(CACHE_KEY);
      localStorage.removeItem(PRIMARY_TOKEN_KEY);
      localStorage.removeItem(SECONDARY_TOKEN_KEY);
      setQuestionStatus("Perguntas salvas foram limpas. A próxima partida buscará uma nova seleção.", "success");
    });
    window.addEventListener("keydown", (e) => {
      if (!game || !els.gameView.classList.contains("active")) return;
      if (["1", "2", "3", "4"].includes(e.key) && !game.answered && !game.paused) {
        const idx = Number(e.key) - 1;
        const btn = $$(".answer-btn")[idx];
        if (btn) btn.click();
      }
      if (e.key === " " && game.answered) {
        e.preventDefault();
        advanceTurn();
      }
    });
  }

  function init() {
    els.questionCountText.textContent = "Perguntas selecionadas";
    els.timerProgress.style.strokeDasharray = `${CIRC}`;
    if (!restoreSetup()) buildTeams(3);
    bindEvents();
  }

  init();
})();
