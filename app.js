(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const QUESTION_BANK = Array.isArray(window.QUESTION_BANK) ? window.QUESTION_BANK : [];
  const COLORS = ["#7dd3fc", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#f472b6", "#38bdf8", "#c4b5fd"];
  const CIRC = 2 * Math.PI * 52;

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
    timerText: $("#timerText"), timerProgress: $("#timerProgress"), skipBtn: $("#skipBtn"), nextBtn: $("#nextBtn"),
    pauseBtn: $("#pauseBtn"), resetBtn: $("#resetBtn"), rulesBtn: $("#rulesBtn"), closeRulesBtn: $("#closeRulesBtn"),
    rulesDialog: $("#rulesDialog"), winnerTitle: $("#winnerTitle"), winnerText: $("#winnerText"),
    playAgainBtn: $("#playAgainBtn"), newSetupBtn: $("#newSetupBtn"), confettiLayer: $("#confettiLayer")
  };

  let teamDrafts = [];
  let game = null;
  let timerHandle = null;
  let audioCtx = null;

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

  function playSound(kind) {
    try {
      initAudio();
      if (audioCtx.state === "suspended") audioCtx.resume();
      if (kind === "correct") {
        tone(523.25, 0.16, "sine", 0.05, 0);
        tone(659.25, 0.18, "sine", 0.05, 0.12);
        tone(783.99, 0.22, "sine", 0.05, 0.24);
      } else if (kind === "wrong") {
        tone(220, 0.22, "sawtooth", 0.035, 0);
        tone(146.83, 0.26, "sawtooth", 0.03, 0.18);
      } else if (kind === "tick") {
        tone(880, 0.06, "square", 0.018, 0);
      } else if (kind === "win") {
        [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.22, "triangle", 0.05, i * 0.13));
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
    if (!QUESTION_BANK.length) return "Nenhuma pergunta foi carregada.";
    return null;
  }

  function createGame() {
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
      helpUsedThisTurn: false, answered: false,
      remaining: baseTime, totalForTimer: baseTime,
      questions: shuffle(QUESTION_BANK), questionIndex: 0, currentQuestion: null, currentOptions: []
    };
    localStorage.setItem("batalhaPerguntasSetup", JSON.stringify({ teams: teamDrafts, targetScore, baseTime, teamHelp, googleHelp, timeHelp }));
  }

  function startGame() {
    const error = validateSetup();
    if (error) {
      alert(error);
      return;
    }
    createGame();
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
    if (game.questionIndex >= game.questions.length) {
      game.questions = shuffle(QUESTION_BANK);
      game.questionIndex = 0;
    }
    const q = game.questions[game.questionIndex++];
    game.currentQuestion = q;
    game.currentOptions = shuffle(q.options || []);
  }

  function nextQuestion() {
    clearInterval(timerHandle);
    game.answered = false;
    game.helpUsedThisTurn = false;
    game.remaining = game.baseTime;
    game.totalForTimer = game.baseTime;
    game.paused = false;
    els.pauseBtn.textContent = "Pausar";
    els.feedback.innerHTML = "";
    els.nextBtn.disabled = true;
    els.questionPanel.classList.remove("correct", "wrong");
    drawQuestion();
    renderQuestion();
    renderScoreboard();
    updateHelpButtons();
    startTimer();
  }

  function renderQuestion() {
    const q = game.currentQuestion;
    const team = getCurrentTeam();
    const player = getCurrentPlayer(team);
    document.documentElement.style.setProperty("--team-color", team.color);
    els.turnStrip.innerHTML = `<span class="player-pill" style="--team-color:${team.color}">${escapeHtml(player)}</span><span>${escapeHtml(team.name)} responde agora · Rodada ${game.round}</span>`;
    els.areaBadge.textContent = q.area;
    els.difficultyBadge.textContent = q.difficulty;
    els.questionId.textContent = q.id;
    els.gameTitle.textContent = q.question;
    els.answers.innerHTML = "";
    game.currentOptions.forEach(option => {
      const btn = document.createElement("button");
      btn.className = "answer-btn";
      btn.type = "button";
      btn.textContent = option;
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
          <span>✅ ${team.correct}</span>
          <span>❌ ${team.wrong}</span>
          <span>🎯 ${game.targetScore}</span>
        </div>
      `;
      target.appendChild(item);
    });
  }

  function updateHelpButtons() {
    const team = getCurrentTeam();
    const disabled = game.answered || game.helpUsedThisTurn || game.paused;
    setHelp(els.teamHelpBtn, team.helps.team, disabled || team.helps.team <= 0);
    setHelp(els.googleHelpBtn, team.helps.google, disabled || team.helps.google <= 0);
    setHelp(els.timeHelpBtn, team.helps.time, disabled || team.helps.time <= 0);
  }

  function setHelp(btn, count, disabled) {
    btn.querySelector("span").textContent = count;
    btn.disabled = disabled;
    btn.classList.toggle("used", disabled);
  }

  function useHelp(type) {
    if (!game || game.answered || game.helpUsedThisTurn || game.paused) return;
    const team = getCurrentTeam();
    if (team.helps[type] <= 0) return;
    team.helps[type]--;
    game.helpUsedThisTurn = true;
    if (type === "team") {
      els.feedback.innerHTML = `<strong>Consulta liberada:</strong> ${escapeHtml(team.name)} pode ajudar uma vez nesta pergunta. O timer continua rodando.`;
    }
    if (type === "google") {
      els.feedback.innerHTML = `<strong>Pesquisa liberada:</strong> uma aba do Google foi aberta com a pergunta atual.`;
      const url = `https://www.google.com/search?q=${encodeURIComponent(game.currentQuestion.question)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    }
    if (type === "time") {
      game.remaining += 60;
      game.totalForTimer += 60;
      els.feedback.innerHTML = `<strong>Bônus usado:</strong> +60 segundos adicionados. Nenhuma outra ajuda pode ser usada nesta pergunta.`;
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
      if (game.remaining <= 5 && game.remaining > 0) playSound("tick");
      updateTimerVisual();
      if (game.remaining <= 0) timeoutQuestion();
    }, 1000);
  }

  function updateTimerVisual() {
    const remaining = Math.max(0, game?.remaining ?? 0);
    const total = Math.max(1, game?.totalForTimer ?? 60);
    const pct = remaining / total;
    els.timerText.textContent = remaining;
    els.timerProgress.style.strokeDasharray = `${CIRC}`;
    els.timerProgress.style.strokeDashoffset = `${CIRC * (1 - pct)}`;
    els.timerProgress.style.stroke = remaining <= 10 ? "var(--danger)" : remaining <= 20 ? "var(--warning)" : "var(--primary)";
  }

  function timeoutQuestion() {
    if (game.answered) return;
    answer(null, null, true);
  }

  function answer(option, btn, timeout = false) {
    if (!game || game.answered || game.paused) return;
    game.answered = true;
    clearInterval(timerHandle);
    const q = game.currentQuestion;
    const team = getCurrentTeam();
    const correct = option === q.answer;

    $$(".answer-btn").forEach(b => {
      if (b.textContent === q.answer) b.classList.add("correct");
      else if (b === btn) b.classList.add("wrong");
      else b.classList.add("dim");
      b.disabled = true;
    });

    if (correct) {
      team.score++;
      team.correct++;
      els.questionPanel.classList.add("correct");
      els.feedback.innerHTML = `<strong>Correto!</strong> ${escapeHtml(q.explanation || `A resposta era ${q.answer}.`)}`;
      playSound("correct");
      celebrate(team.color);
      if (team.score >= game.targetScore) {
        setTimeout(() => finishGame(team), 900);
      }
    } else {
      team.wrong++;
      els.questionPanel.classList.add("wrong");
      const intro = timeout ? "<strong>Tempo esgotado.</strong>" : "<strong>Errado.</strong>";
      els.feedback.innerHTML = `${intro} Resposta correta: <strong>${escapeHtml(q.answer)}</strong>. ${escapeHtml(q.explanation || "")}`;
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
    updateHelpButtons();
  }

  function finishGame(winner) {
    clearInterval(timerHandle);
    playSound("win");
    celebrate(winner.color);
    els.winnerTitle.textContent = `${winner.name} venceu!`;
    els.winnerText.textContent = `A equipe atingiu ${winner.score} acertos e alcançou a pontuação de vitória.`;
    renderScoreboard(true);
    showView(els.winnerView);
  }

  function resetAll(toSetup = true) {
    clearInterval(timerHandle);
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
    els.playAgainBtn.addEventListener("click", () => { createGame(); showView(els.gameView); nextQuestion(); });
    els.newSetupBtn.addEventListener("click", () => resetAll(true));
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
    els.questionCountText.textContent = `${QUESTION_BANK.length.toLocaleString("pt-BR")} perguntas carregadas`;
    els.timerProgress.style.strokeDasharray = `${CIRC}`;
    if (!restoreSetup()) buildTeams(3);
    bindEvents();
  }

  init();
})();
