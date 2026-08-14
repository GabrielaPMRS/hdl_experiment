const experimentVersion = "lambda";

const codeQuestions = [
  {
    id: "code-1",
    title: "Código 1",
    code: `module mux (
    input logic [1:0] selector,
    input logic enable,
    output logic [7:0] out
);
    logic [7:0] decoded;

    always_comb begin
        case (selector)
            0: decoded = 8'd10;
            01: decoded = 8'd20;
            10: decoded = 8'd30;
            2: decoded = 8'd40;
            default: decoded = 8'd100;
        endcase

        if (enable)
            out = decoded;
        else
            out = 8'd0;
    end
endmodule`,
    question: "Considerando o código, qual é o valor de 'out' quando 'selector' = 10 e 'enable' = 1?",
    options: ["out = 0", "out = 10", "out = 30", "out = 40", "out = 100"],
    correctIndex: 3
  },
  {
    id: "code-2",
    title: "Código 2",
    code: `module top (
    output logic [31:0] out0,
    output logic [31:0] out1
);

    logic [1:0][31:0] A;

    initial begin
        A = '{1'b1, 1'b1};

        out0 = A[0];
        out1 = A[1];
    end

endmodule`,
    question: "Considerando o código, quais seriam os valores de 'out0' e 'out1'?",
    options: [
      "out0 = 00000000000000000000000000000011\nout1 = 00000000000000000000000000000000",
      "out0 = 00000000000000000000000000000000\nout1 = 00000000000000000000000000000011",
      "out0 = 00000000000000000000000000000001\nout1 = 00000000000000000000000000000001",
      "out0 = 00000000000000000000000000000010\nout1 = 00000000000000000000000000000010",
      "out0 = 00000000000000000000000000000000\nout1 = 00000000000000000000000000000001"
    ],
    correctIndex: 2
  },
  {
    id: "code-3",
    title: "Código 3",
    code: `module example;

    function int maxx(int a, int b);
        int max = a;

        if (b > max)
            max = b;

        return max;
    endfunction

    initial begin
        int r1, r2, r3;

        r1 = maxx(3, 7);
        r2 = maxx(1, 2);
        r3 = maxx(0, 0);
    end

endmodule`,
    question: "Considerando o código, quais seriam os valores correspondentes de r1, r2 e r3, respectivamente?",
    options: [
      "r1 = 7\nr2 = 2\nr3 = 0",
      "r1 = 3\nr2 = 1\nr3 = 0",
      "r1 = 7\nr2 = 7\nr3 = 7",
      "r1 = 2\nr2 = 2\nr3 = 2",
      "r1 = 0\nr2 = 0\nr3 = 0"
    ],
    correctIndex: 2
  },
  {
    id: "code-4",
    title: "Código 4",
    code: `module example (
    input  logic enable,
    output int   out
);

    int result;
    byte in = -5;

    always_comb begin
        result = in + 1'b1;

        if (enable)
            out = result;
        else
            out = in;
    end
endmodule`,
    question: "Considerando o código, qual seria o valor de 'out' quando 'enable' = 1?",
    options: ["out = -4", "out = 251", "out = 4", "out = 252", "Erro de compilação"],
    correctIndex: 3
  },
  {
    id: "code-5",
    title: "Código 5",
    code: `module example;

    int lo, med, hi;
    bit result;
    int selected;

    initial begin
        lo = 20;
        med = 224;
        hi = 164;

        result = (lo < med < hi);

        if (result)
            selected = med;
        else
            selected = hi;
    end

endmodule`,
    question: "Considerando o código, qual seria o valor de 'selected'?",
    options: ["selected = 20", "selected = 164", "selected = 224", "selected = 1", "Erro de compilação"],
    correctIndex: 2
  },
  {
    id: "code-6",
    title: "Código 6",
    code: `module example (
    input  logic [3:0] instruction,
    output logic [2:0] opcode
);

    always_comb begin
        casex (instruction)

            4'b0???:
                opcode = 3'b001;

            4'b1000:
                opcode = 3'b010;

            default:
                opcode = 3'b111;

        endcase
    end
endmodule`,
    question: "Considerando o código, qual seria o valor de 'opcode' considerando instruction = 4'bxxxx?",
    options: ["001", "010", "111", "Erro de compilação", "opcode não muda"],
    correctIndex: 0
  }
];

const storageKey = `hdl-systemverilog-survey-results-${experimentVersion}`;
const session = {
  participantId: null,
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
const eyeBreakScreen = document.querySelector("#eye-break-screen");
const questionScreen = document.querySelector("#question-screen");
const completeScreen = document.querySelector("#complete-screen");
const demographicForm = document.querySelector("#demographic-form");
const answerForm = document.querySelector("#answer-form");
const introError = document.querySelector("#intro-error");
const answerError = document.querySelector("#answer-error");
const progressLabel = document.querySelector("#progress-label");
const participantLabel = document.querySelector("#participant-label");
const questionTitle = document.querySelector("#question-title");
const codeBlock = document.querySelector("#code-block");
const questionText = document.querySelector("#question-text");
const optionsList = document.querySelector("#options-list");
const nextButton = document.querySelector("#next-button");
const downloadJson = document.querySelector("#download-json");
const downloadCsv = document.querySelector("#download-csv");
let eyeBreakNextStep = null;
let eyeBreakTimer = null;
let audioContext = null;

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[randomIndex]] = [copy[randomIndex], copy[index]];
  }
  return copy;
}

function getResponsesInExecutionOrder() {
  return [...session.responses];
}

function showScreen(screen) {
  [introScreen, eyeBreakScreen, questionScreen, completeScreen].forEach((item) => item.classList.add("hidden"));
  screen.classList.remove("hidden");
  fitVisibleScreen();
}

function normalizeParticipantCode(value) {
  const digits = String(value).trim().replace(/^P/i, "");
  return `P${digits}`;
}

function showEyeBreak(nextStep) {
  clearInterval(eyeBreakTimer);
  eyeBreakNextStep = nextStep;
  showScreen(eyeBreakScreen);

  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (AudioContext) {
    audioContext ??= new AudioContext();
    audioContext.resume();
  }

  let secondsRemaining = 7;
  eyeBreakTimer = setInterval(() => {
    secondsRemaining -= 1;
    if (secondsRemaining > 0) return;

    clearInterval(eyeBreakTimer);
    playReadySignal();
    setTimeout(() => {
      const step = eyeBreakNextStep;
      eyeBreakNextStep = null;
      step?.();
    }, 400);
  }, 1000);
}

function playReadySignal() {
  if (!audioContext) return;
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.type = "sine";
  oscillator.frequency.value = 880;
  gain.gain.setValueAtTime(0.18, audioContext.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.25);
  oscillator.connect(gain).connect(audioContext.destination);
  oscillator.start();
  oscillator.stop(audioContext.currentTime + 0.25);
}

function fitVisibleScreen() {
  requestAnimationFrame(() => {
    document.querySelectorAll(".panel:not(.hidden)").forEach((panel) => {
      panel.classList.toggle("is-tight", panel.scrollHeight > panel.clientHeight || panel.scrollWidth > panel.clientWidth);
    });
  });
}

function updateStepProgress() {
  progressLabel.textContent = `Pergunta ${session.currentIndex + 1} de ${session.order.length}`;
}

function renderQuestion() {
  const item = session.order[session.currentIndex];
  answerForm.reset();
  answerError.textContent = "";
  session.currentAttempts = 0;
  updateStepProgress();
  participantLabel.textContent = `ID do participante: ${session.participantId}`;
  questionTitle.textContent = item.title;
  codeBlock.textContent = item.code;
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
  session.pageStartedAt = performance.now();
  fitVisibleScreen();
}

function buildResultPayload() {
  return {
    versaoExperimento: experimentVersion,
    participanteId: session.participantId,
    demografia: session.demographics,
    perguntas: getResponsesInExecutionOrder(),
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
  session.participantId = normalizeParticipantCode(session.demographics.participanteCodigo);
  session.order = shuffle(codeQuestions);
  session.responses = [];
  session.currentIndex = 0;
  session.currentAttempts = 0;
  session.startedAt = new Date().toISOString();
  session.completedAt = null;
  blockBrowserBack();
  showEyeBreak(renderQuestion);
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
    answerError.textContent = "Resposta incorreta! Tente novamente.";
    return;
  }

  const elapsedMs = Math.round(performance.now() - session.pageStartedAt);
  session.responses.push({
    ordemExecucao: session.currentIndex + 1,
    codigoId: item.id,
    codigoTitulo: item.title,
    segundos: Number((elapsedMs / 1000).toFixed(2)),
    tentativas: session.currentAttempts
  });
  persistSession();

  if (session.currentIndex < session.order.length - 1) {
    session.currentIndex += 1;
    showEyeBreak(renderQuestion);
    return;
  }

  session.completedAt = new Date().toISOString();
  persistSession();
  downloadJsonResult();
  showEyeBreak(() => showScreen(completeScreen));
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

function downloadJsonResult() {
  downloadFile(
    `resultado${session.participantId}.json`,
    JSON.stringify(buildResultPayload(), null, 2),
    "application/json"
  );
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
      "ordemExecucao",
      "codigoId",
      "codigoTitulo",
      "segundos",
      "tentativas"
    ]
  ];

  getResponsesInExecutionOrder().forEach((response) => {
    rows.push([
      session.participantId,
      experimentVersion,
      session.demographics.experienciaAnos,
      session.demographics.proficiencia,
      session.demographics.areaExperiencia,
      response.ordemExecucao,
      response.codigoId,
      response.codigoTitulo,
      response.segundos,
      response.tentativas
    ]);
  });

  return rows.map((row) => row.map(csvEscape).join(",")).join("\n");
}

demographicForm.addEventListener("submit", startSurvey);
answerForm.addEventListener("submit", submitAnswer);
downloadJson.addEventListener("click", () => {
  downloadJsonResult();
});
downloadCsv.addEventListener("click", () => {
  downloadFile(`resultado${session.participantId}.csv`, buildCsv(), "text/csv");
});
