const codeQuestions = [
  {
    id: "code-1",
    title: "Código 1",
    pageName: "1",
    question: "Considerando o código, qual é o valor de 'out' quando 'selector' = 10?",
    options: ["out = 10", "out = 20", "out = 30", "out = 40", "out não muda"],
    correctIndex: 2
  },
  {
    id: "code-2",
    title: "Código 2",
    pageName: "2",
    question: "Considerando o código, quais seriam os valores de saída de A[0] e A[1]?",
    options: [
      "A[0] = 00000000000000000000000000000011\nA[1] = 00000000000000000000000000000000",
      "A[0] = 00000000000000000000000000000000\nA[1] = 00000000000000000000000000000011",
      "A[0] = 00000000000000000000000000000001\nA[1] = 00000000000000000000000000000001",
      "A[0] = 00000000000000000000000000000010\nA[1] = 00000000000000000000000000000010",
      "A[0] = 00000000000000000000000000000000\nA[1] = 00000000000000000000000000000001"
    ],
    correctIndex: 2
  },
  {
    id: "code-3",
    title: "Código 3",
    pageName: "3",
    question: "Considerando o código, quais seriam os valores correspondentes de r1, r2 e r3, respectivamente?",
    options: [
      "r1 = 2\nr2 = 2\nr3 = 2",
      "r1 = 7\nr2 = 7\nr3 = 7",
      "r1 = 0\nr2 = 0\nr3 = 0",
      "r1 = 7\nr2 = 2\nr3 = 0",
      "r1 = 3\nr2 = 1\nr3 = 0"
    ],
    correctIndex: 3
  },
  {
    id: "code-4",
    title: "Código 4",
    pageName: "4",
    question: "Considerando o código, qual seria o valor de saída de out?",
    options: ["out = 252", "out = -6", "out = 251", "out = -4", "out = 4"],
    correctIndex: 3
  },
  {
    id: "code-5",
    title: "Código 5",
    pageName: "5",
    question: "Considerando o código, qual seria o valor de saída de result?",
    options: ["result = 0", "result = 1", "result = 20", "result = 135", "Erro de compilação"],
    correctIndex: 1
  },
  {
    id: "code-6",
    title: "Código 6",
    pageName: "6",
    question: "Considerando o código, qual seria o valor de 'opcode' considerando instruction = 4'bxxxx?",
    options: ["001", "010", "111", "Erro de compilação", "opcode não muda"],
    correctIndex: 2
  }
];

const experimentVersion = "omega";
const storageKey = `hdl-systemverilog-survey-results-${experimentVersion}`;
const session = {
  participantId: crypto.randomUUID ? crypto.randomUUID() : `participant-${Date.now()}`,
  demographics: {},
  order: [],
  responses: [],
  currentIndex: 0,
  currentAttempts: 0,
  pageStartedAt: null,
  startedAt: null,
  completedAt: null
};

const introScreen = document.querySelector("#intro-screen");
const navigationScreen = document.querySelector("#navigation-screen");
const readyScreen = document.querySelector("#ready-screen");
const questionScreen = document.querySelector("#question-screen");
const completeScreen = document.querySelector("#complete-screen");
const demographicForm = document.querySelector("#demographic-form");
const answerForm = document.querySelector("#answer-form");
const introError = document.querySelector("#intro-error");
const answerError = document.querySelector("#answer-error");
const navigationProgress = document.querySelector("#navigation-progress");
const navigationPageName = document.querySelector("#navigation-page-name");
const navigationNext = document.querySelector("#navigation-next");
const readyProgress = document.querySelector("#ready-progress");
const readyPageName = document.querySelector("#ready-page-name");
const readyCheck = document.querySelector("#ready-check");
const readyStart = document.querySelector("#ready-start");
const progressLabel = document.querySelector("#progress-label");
const participantLabel = document.querySelector("#participant-label");
const questionTitle = document.querySelector("#question-title");
const questionText = document.querySelector("#question-text");
const optionsList = document.querySelector("#options-list");
const nextButton = document.querySelector("#next-button");
const downloadJson = document.querySelector("#download-json");
const downloadCsv = document.querySelector("#download-csv");

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[randomIndex]] = [copy[randomIndex], copy[index]];
  }
  return copy;
}

function getCodeNumber(item) {
  const id = typeof item === "string" ? item : item.codigoId;
  return Number(id.replace("code-", ""));
}

function getSortedResponses() {
  return [...session.responses].sort((first, second) => getCodeNumber(first) - getCodeNumber(second));
}

function showScreen(screen) {
  [introScreen, navigationScreen, readyScreen, questionScreen, completeScreen].forEach((item) => item.classList.add("hidden"));
  screen.classList.remove("hidden");
  fitVisibleScreen();
}

function fitVisibleScreen() {
  requestAnimationFrame(() => {
    document.querySelectorAll(".panel:not(.hidden)").forEach((panel) => {
      panel.classList.toggle("is-tight", panel.scrollHeight > panel.clientHeight || panel.scrollWidth > panel.clientWidth);
    });
  });
}

function getCurrentItem() {
  return session.order[session.currentIndex];
}

function updateStepProgress(target) {
  target.textContent = `Pergunta ${session.currentIndex + 1} de ${session.order.length}`;
}

function renderNavigation() {
  const item = getCurrentItem();
  updateStepProgress(navigationProgress);
  navigationPageName.textContent = item.pageName;
  showScreen(navigationScreen);
}

function renderReadyCheck() {
  const item = getCurrentItem();
  updateStepProgress(readyProgress);
  readyPageName.textContent = item.pageName;
  readyCheck.checked = false;
  readyStart.disabled = true;
  showScreen(readyScreen);
}

function startTimedQuestion() {
  renderQuestion();
  session.pageStartedAt = performance.now();
}

function renderQuestion() {
  const item = session.order[session.currentIndex];
  answerForm.reset();
  answerError.textContent = "";
  session.currentAttempts = 0;
  updateStepProgress(progressLabel);
  participantLabel.textContent = `ID do participante: ${session.participantId}`;
  questionTitle.textContent = item.title;
  questionText.textContent = item.question;
  nextButton.textContent = session.currentIndex === session.order.length - 1 ? "Finalizar" : "Avançar";
  optionsList.replaceChildren(
    ...item.options.map((option, index) => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "answer";
      input.value = String(index);
      input.required = true;
      label.append(input, document.createTextNode(option));
      return label;
    })
  );
  showScreen(questionScreen);
  fitVisibleScreen();
}

function buildResultPayload() {
  return {
    versaoExperimento: experimentVersion,
    participanteId: session.participantId,
    demografia: session.demographics,
    perguntas: getSortedResponses(),
    iniciadoEm: session.startedAt,
    concluidoEm: session.completedAt
  };
}

function persistSession() {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
  const existingIndex = saved.findIndex((item) => item.participanteId === session.participantId);
  const payload = buildResultPayload();

  if (existingIndex >= 0) {
    saved[existingIndex] = payload;
  } else {
    saved.push(payload);
  }
  localStorage.setItem(storageKey, JSON.stringify(saved));
}

function blockBrowserBack() {
  history.pushState(null, "", location.href);
  window.addEventListener("popstate", () => {
    history.pushState(null, "", location.href);
  });
}

function startSurvey(event) {
  event.preventDefault();
  introError.textContent = "";

  if (!demographicForm.reportValidity()) {
    introError.textContent = "Responda às perguntas demográficas antes de iniciar.";
    return;
  }

  const data = new FormData(demographicForm);
  session.demographics = Object.fromEntries(data.entries());
  session.order = shuffle(codeQuestions);
  session.responses = [];
  session.currentIndex = 0;
  session.currentAttempts = 0;
  session.startedAt = new Date().toISOString();
  session.completedAt = null;
  blockBrowserBack();
  renderNavigation();
}

function submitAnswer(event) {
  event.preventDefault();
  answerError.textContent = "";

  const item = session.order[session.currentIndex];
  const data = new FormData(answerForm);
  const answerValue = data.get("answer");
  session.currentAttempts += 1;

  if (answerValue === null) {
    answerError.textContent = "Selecione uma alternativa antes de continuar.";
    return;
  }

  const selectedIndex = Number(answerValue);
  if (selectedIndex !== item.correctIndex) {
    answerError.textContent = "Esta resposta está incorreta. Revise o código no VSCode e selecione a alternativa correta para continuar.";
    return;
  }

  const elapsedMs = Math.round(performance.now() - session.pageStartedAt);
  session.responses.push({
    codigoId: item.id,
    codigoTitulo: item.title,
    segundos: Number((elapsedMs / 1000).toFixed(2)),
    tentativas: session.currentAttempts
  });
  persistSession();

  if (session.currentIndex < session.order.length - 1) {
    session.currentIndex += 1;
    renderNavigation();
    return;
  }

  session.completedAt = new Date().toISOString();
  persistSession();
  showScreen(completeScreen);
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function csvEscape(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function buildCsv() {
  const rows = [
    [
      "participanteId",
      "versaoExperimento",
      "experienciaAnos",
      "proficiencia",
      "areaExperiencia",
      "codigoId",
      "codigoTitulo",
      "segundos",
      "tentativas"
    ]
  ];

  getSortedResponses().forEach((response) => {
    rows.push([
      session.participantId,
      experimentVersion,
      session.demographics.experienciaAnos,
      session.demographics.proficiencia,
      session.demographics.areaExperiencia,
      response.codigoId,
      response.codigoTitulo,
      response.segundos,
      response.tentativas
    ]);
  });

  return rows.map((row) => row.map(csvEscape).join(",")).join("\n");
}

demographicForm.addEventListener("submit", startSurvey);
navigationNext.addEventListener("click", renderReadyCheck);
readyCheck.addEventListener("change", () => {
  readyStart.disabled = !readyCheck.checked;
});
readyStart.addEventListener("click", startTimedQuestion);
answerForm.addEventListener("submit", submitAnswer);
downloadJson.addEventListener("click", () => {
  downloadFile(`experimento-hdl-${experimentVersion}-${session.participantId}.json`, JSON.stringify(buildResultPayload(), null, 2), "application/json");
});
downloadCsv.addEventListener("click", () => {
  downloadFile(`experimento-hdl-${experimentVersion}-${session.participantId}.csv`, buildCsv(), "text/csv");
});
