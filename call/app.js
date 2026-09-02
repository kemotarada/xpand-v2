import {
  GoogleGenAI,
  Modality
} from "@google/genai";


// =========================================================
// KEMO HUMAN CALL UI V4
//
// ONE KEMO
//
// - Ultra fast live audio
// - Shared Telegram/call context
// - 15 minute continuity
// - Desktop tools
// - No forced greeting on continuation
// =========================================================


// =========================================================
// TELEGRAM
// =========================================================

const tg =
  window.Telegram?.WebApp
  ||
  null;


if (tg) {

  try {

    tg.ready();
    tg.expand();

    tg.setHeaderColor("#02060d");
    tg.setBackgroundColor("#02060d");

    if (
      typeof tg.enableClosingConfirmation ===
      "function"
    ) {

      tg.enableClosingConfirmation();
    }

  } catch (error) {

    console.log(
      "Telegram UI warning:",
      error
    );
  }
}


// =========================================================
// DOM
// =========================================================

const orb =
  document.getElementById("orb");

const callStatus =
  document.getElementById("callStatus");

const callTimer =
  document.getElementById("callTimer");

const waveform =
  document.getElementById("waveform");

const liveCaption =
  document.getElementById("liveCaption");

const startCallButton =
  document.getElementById("startCallButton");

const callControls =
  document.getElementById("callControls");

const muteButton =
  document.getElementById("muteButton");

const muteLabel =
  document.getElementById("muteLabel");

const endCallButton =
  document.getElementById("endCallButton");

const errorBox =
  document.getElementById("errorBox");

const errorMessage =
  document.getElementById("errorMessage");


// =========================================================
// ULTRA FAST SETTINGS
// =========================================================

const FAST_VAD_PREFIX_MS =
  20;

const FAST_VAD_SILENCE_MS =
  100;

const PLAYBACK_LEAD_SECONDS =
  0.015;


// =========================================================
// SESSION POLICY
// =========================================================

const LIVE_CONVERSATION_POLICY = `
قواعد المكالمة السريعة:

- هذه نفس محادثة Kemo الموجودة على Telegram.
- لا تتعامل مع المكالمة كشخص أو مساعد مختلف.
- ابدأ الرد بسرعة فور انتهاء كلام كريم.
- لا تعمل مقدمة قبل الجواب.
- السؤال البسيط يحتاج جواباً سريعاً وقصيراً.
- لا تطوّل التفكير إلا إذا السؤال يحتاج فعلاً.
- لا تعيد صياغة سؤال كريم.
- لا تقل "خليني أفكر" إلا إذا ستستخدم أداة فعلاً.
- لا تذكر الساعة أو التاريخ إلا إذا سأل كريم.
- إذا قاطعك كريم توقف فوراً واستمع.
- استخدم الأدوات الحقيقية عندما يطلب كريم تنفيذ شيء.
- أوامر الكمبيوتر لازم تنفذ بأدوات desktop.
`;


// =========================================================
// STATE
// =========================================================

let session = null;

let callId = null;
let callSecret = null;

let callActive = false;
let endingCall = false;
let muted = false;

let micStream = null;

let inputAudioContext = null;
let outputAudioContext = null;

let micSource = null;
let micProcessor = null;
let silentGain = null;

let timerInterval = null;
let callStartedAt = null;

let pendingUserText = "";
let pendingModelText = "";

let transcript = [];

let currentContinuity = null;


// =========================================================
// OUTPUT ROUTING
// =========================================================

let audioOutputButton = null;
let audioOutputIcon = null;
let audioOutputLabel = null;

let audioRouteMode = "speaker";

let selectedOutputDeviceId = "";
let selectedEarpieceDeviceId = "";
let selectedSpeakerDeviceId = "";


// =========================================================
// PLAYBACK
// =========================================================

let playbackTime = 0;

let playbackChain =
  Promise.resolve();

let playbackGeneration = 0;

const activeAudioSources =
  new Set();

let modelSpeakingStartedAt = 0;


// =========================================================
// BARGE-IN
// =========================================================

let localBargeInLatched = false;

let suppressModelAudio = false;

let highConfidenceSpeechFrames = 0;

let micWasSpeaking = false;

let silenceFrames = 0;

let noiseFloor = 0.008;


const USER_SPEECH_RMS =
  0.022;

const BARGE_IN_MIN_RMS =
  0.060;

const BARGE_IN_NOISE_MULTIPLIER =
  5.5;

const BARGE_IN_REQUIRED_FRAMES =
  2;

const BARGE_IN_MODEL_GRACE_MS =
  100;


// =========================================================
// TOOLS
// =========================================================

const processedToolCallIds =
  new Set();

const toolPromises =
  new Map();

const toolAbortControllers =
  new Map();

let activeToolCount = 0;


// =========================================================
// WAKE LOCK
// =========================================================

let wakeLock = null;


// =========================================================
// UI
// =========================================================

function setVisualState(
  state,
  text
) {

  if (orb) {

    orb.classList.remove(
      "idle",
      "listening",
      "thinking",
      "speaking"
    );

    orb.classList.add(
      state
    );
  }


  if (
    text
    &&
    callStatus
  ) {

    callStatus.textContent =
      text;
  }


  if (!waveform) {

    return;
  }


  if (
    state === "listening"
    ||
    state === "thinking"
    ||
    state === "speaking"
  ) {

    waveform.classList.add(
      "active"
    );

  } else {

    waveform.classList.remove(
      "active"
    );
  }
}


// =========================================================
// CAPTION
// =========================================================

function setCaption(
  text,
  active = true
) {

  if (!liveCaption) {

    return;
  }


  liveCaption.textContent =
    String(
      text || ""
    );


  if (active) {

    liveCaption.classList.add(
      "active"
    );

  } else {

    liveCaption.classList.remove(
      "active"
    );
  }
}


// =========================================================
// ERROR
// =========================================================

function hideError() {

  if (errorBox) {

    errorBox.classList.add(
      "hidden"
    );
  }
}


function showError(
  text
) {

  console.error(
    text
  );


  if (errorMessage) {

    errorMessage.textContent =
      String(
        text
        ||
        "صار خلل."
      );
  }


  if (errorBox) {

    errorBox.classList.remove(
      "hidden"
    );
  }


  setVisualState(
    "idle",
    "الاتصال توقف"
  );
}


// =========================================================
// TIMER
// =========================================================

function formatTime(
  totalSeconds
) {

  const minutes =
    Math.floor(
      totalSeconds / 60
    );


  const seconds =
    totalSeconds % 60;


  return (
    String(
      minutes
    ).padStart(
      2,
      "0"
    )
    +
    ":"
    +
    String(
      seconds
    ).padStart(
      2,
      "0"
    )
  );
}


function startTimer() {

  stopTimer();


  callStartedAt =
    Date.now();


  if (callTimer) {

    callTimer.textContent =
      "00:00";
  }


  timerInterval =
    setInterval(
      () => {

        const elapsed =
          Math.floor(
            (
              Date.now()
              -
              callStartedAt
            )
            /
            1000
          );


        if (callTimer) {

          callTimer.textContent =
            formatTime(
              elapsed
            );
        }

      },
      1000
    );
}


function stopTimer() {

  if (timerInterval) {

    clearInterval(
      timerInterval
    );

    timerInterval = null;
  }
}


// =========================================================
// WAKE LOCK
// =========================================================

async function requestWakeLock() {

  try {

    if (
      !("wakeLock" in navigator)
    ) {

      return;
    }


    wakeLock =
      await navigator
        .wakeLock
        .request(
          "screen"
        );


    wakeLock.addEventListener(
      "release",
      () => {

        wakeLock = null;
      }
    );

  } catch (error) {

    console.log(
      "Wake lock warning:",
      error
    );
  }
}


async function releaseWakeLock() {

  try {

    if (wakeLock) {

      await wakeLock.release();

      wakeLock = null;
    }

  } catch {

    wakeLock = null;
  }
}


// =========================================================
// AUDIO OUTPUT
// =========================================================

function normalizeDeviceLabel(
  label
) {

  return String(
    label || ""
  ).toLowerCase();
}


function looksLikeEarpiece(
  device
) {

  const label =
    normalizeDeviceLabel(
      device?.label
    );


  const id =
    String(
      device?.deviceId
      ||
      ""
    ).toLowerCase();


  return (
    id === "communications"
    ||
    label.includes(
      "earpiece"
    )
    ||
    label.includes(
      "receiver"
    )
    ||
    label.includes(
      "communications"
    )
    ||
    label.includes(
      "phone"
    )
    ||
    label.includes(
      "call"
    )
  );
}


function looksLikeSpeaker(
  device
) {

  const label =
    normalizeDeviceLabel(
      device?.label
    );


  const id =
    String(
      device?.deviceId
      ||
      ""
    ).toLowerCase();


  return (
    id === "default"
    ||
    label.includes(
      "speaker"
    )
    ||
    label.includes(
      "loudspeaker"
    )
    ||
    label.includes(
      "built-in speaker"
    )
    ||
    label.includes(
      "built in speaker"
    )
  );
}


function updateAudioOutputButton() {

  if (
    !audioOutputButton
    ||
    !audioOutputLabel
    ||
    !audioOutputIcon
  ) {

    return;
  }


  if (
    audioRouteMode ===
    "earpiece"
  ) {

    audioOutputIcon.textContent =
      "📞";

    audioOutputLabel.textContent =
      "سماعة";

  } else {

    audioOutputIcon.textContent =
      "🔊";

    audioOutputLabel.textContent =
      "سبيكر";
  }
}


function createAudioOutputButton() {

  if (
    audioOutputButton
    ||
    !callControls
  ) {

    return;
  }


  audioOutputButton =
    document.createElement(
      "button"
    );


  audioOutputButton.type =
    "button";


  audioOutputButton.className =
    muteButton?.className
    ||
    "control-button";


  audioOutputButton.id =
    "audioOutputButton";


  audioOutputIcon =
    document.createElement(
      "span"
    );


  audioOutputLabel =
    document.createElement(
      "span"
    );


  audioOutputButton.appendChild(
    audioOutputIcon
  );


  audioOutputButton.appendChild(
    audioOutputLabel
  );


  updateAudioOutputButton();


  audioOutputButton.addEventListener(
    "click",
    () => {

      toggleAudioRoute()
        .catch(
          error => {

            console.log(
              "Audio route:",
              error
            );
          }
        );
    }
  );


  if (
    endCallButton
  ) {

    callControls.insertBefore(
      audioOutputButton,
      endCallButton
    );

  } else {

    callControls.appendChild(
      audioOutputButton
    );
  }
}


async function getAudioOutputDevices() {

  if (
    !navigator
      .mediaDevices
      ?.enumerateDevices
  ) {

    return [];
  }


  const devices =
    await navigator
      .mediaDevices
      .enumerateDevices();


  return devices.filter(
    item =>
      item.kind ===
      "audiooutput"
  );
}


async function ensureOutputAudio() {

  const AudioContextClass =
    window.AudioContext
    ||
    window.webkitAudioContext;


  if (
    !AudioContextClass
  ) {

    throw new Error(
      "تشغيل الصوت غير مدعوم"
    );
  }


  if (
    !outputAudioContext
  ) {

    outputAudioContext =
      new AudioContextClass({
        latencyHint:
          "interactive"
      });


    playbackTime =
      outputAudioContext.currentTime
      +
      PLAYBACK_LEAD_SECONDS;
  }


  if (
    outputAudioContext.state ===
    "suspended"
  ) {

    await outputAudioContext.resume();
  }
}


async function setOutputDevice(
  deviceId
) {

  await ensureOutputAudio();


  if (
    typeof outputAudioContext
      ?.setSinkId !==
    "function"
  ) {

    return false;
  }


  await outputAudioContext
    .setSinkId(
      deviceId
    );


  selectedOutputDeviceId =
    deviceId;


  return true;
}


async function routeToEarpiece() {

  const outputs =
    await getAudioOutputDevices();


  let device =
    outputs.find(
      item =>
        item.deviceId ===
        selectedEarpieceDeviceId
    );


  if (!device) {

    device =
      outputs.find(
        looksLikeEarpiece
      );
  }


  if (
    device?.deviceId
  ) {

    await setOutputDevice(
      device.deviceId
    );


    selectedEarpieceDeviceId =
      device.deviceId;


    audioRouteMode =
      "earpiece";


    updateAudioOutputButton();


    return true;
  }


  return false;
}


async function routeToSpeaker() {

  const outputs =
    await getAudioOutputDevices();


  let device =
    outputs.find(
      item =>
        item.deviceId ===
        selectedSpeakerDeviceId
    );


  if (!device) {

    device =
      outputs.find(
        looksLikeSpeaker
      );
  }


  if (
    device?.deviceId
  ) {

    await setOutputDevice(
      device.deviceId
    );


    selectedSpeakerDeviceId =
      device.deviceId;

  } else {

    try {

      await setOutputDevice(
        "default"
      );

    } catch {}
  }


  audioRouteMode =
    "speaker";


  updateAudioOutputButton();


  return true;
}


async function toggleAudioRoute() {

  if (
    audioRouteMode ===
    "speaker"
  ) {

    await routeToEarpiece();

  } else {

    await routeToSpeaker();
  }
}


// =========================================================
// BASE64
// =========================================================

function bytesToBase64(
  bytes
) {

  let binary = "";


  for (
    let i = 0;
    i < bytes.length;
    i += 0x8000
  ) {

    binary +=
      String.fromCharCode(
        ...bytes.subarray(
          i,
          Math.min(
            i + 0x8000,
            bytes.length
          )
        )
      );
  }


  return btoa(
    binary
  );
}


function base64ToBytes(
  base64
) {

  const binary =
    atob(
      base64
    );


  const bytes =
    new Uint8Array(
      binary.length
    );


  for (
    let i = 0;
    i < binary.length;
    i++
  ) {

    bytes[i] =
      binary.charCodeAt(
        i
      );
  }


  return bytes;
}


// =========================================================
// TRANSCRIPT
// =========================================================

function mergeTranscriptText(
  current,
  incoming
) {

  current =
    String(
      current || ""
    ).trim();


  incoming =
    String(
      incoming || ""
    ).trim();


  if (!incoming) {

    return current;
  }


  if (!current) {

    return incoming;
  }


  if (
    incoming.startsWith(
      current
    )
  ) {

    return incoming;
  }


  if (
    current.startsWith(
      incoming
    )
  ) {

    return current;
  }


  if (
    current.endsWith(
      incoming
    )
  ) {

    return current;
  }


  const maxOverlap =
    Math.min(
      current.length,
      incoming.length
    );


  for (
    let size = maxOverlap;
    size > 0;
    size--
  ) {

    if (
      current.slice(
        -size
      )
      ===
      incoming.slice(
        0,
        size
      )
    ) {

      return (
        current
        +
        incoming.slice(
          size
        )
      );
    }
  }


  return (
    current
    +
    " "
    +
    incoming
  );
}


function addTranscriptTurn(
  role,
  text
) {

  text =
    String(
      text || ""
    ).trim();


  if (!text) {

    return;
  }


  const previous =
    transcript[
      transcript.length - 1
    ];


  if (
    previous
    &&
    previous.role ===
      role
    &&
    previous.text ===
      text
  ) {

    return;
  }


  transcript.push({
    role,
    text
  });


  if (
    transcript.length >
    500
  ) {

    transcript =
      transcript.slice(
        -500
      );
  }
}


function commitPendingUser() {

  const text =
    pendingUserText.trim();


  if (!text) {

    return;
  }


  addTranscriptTurn(
    "user",
    text
  );


  pendingUserText = "";
}


function commitPendingModel() {

  const text =
    pendingModelText.trim();


  if (!text) {

    return;
  }


  addTranscriptTurn(
    "assistant",
    text
  );


  pendingModelText = "";
}


function commitAllPending() {

  commitPendingUser();
  commitPendingModel();
}


// =========================================================
// AUDIO INPUT
// =========================================================

function downsampleBuffer(
  inputBuffer,
  inputSampleRate,
  outputSampleRate
) {

  if (
    outputSampleRate >=
    inputSampleRate
  ) {

    return new Float32Array(
      inputBuffer
    );
  }


  const ratio =
    inputSampleRate
    /
    outputSampleRate;


  const newLength =
    Math.round(
      inputBuffer.length
      /
      ratio
    );


  const result =
    new Float32Array(
      newLength
    );


  let outputOffset = 0;
  let inputOffset = 0;


  while (
    outputOffset <
    result.length
  ) {

    const nextInputOffset =
      Math.round(
        (
          outputOffset + 1
        )
        *
        ratio
      );


    let total = 0;
    let count = 0;


    for (
      let i = inputOffset;
      i < nextInputOffset;
      i++
    ) {

      if (
        i >=
        inputBuffer.length
      ) {

        break;
      }


      total +=
        inputBuffer[i];


      count++;
    }


    result[
      outputOffset
    ] =
      count
        ?
        total / count
        :
        0;


    outputOffset++;


    inputOffset =
      nextInputOffset;
  }


  return result;
}


function float32ToPCM16(
  float32
) {

  const buffer =
    new ArrayBuffer(
      float32.length * 2
    );


  const view =
    new DataView(
      buffer
    );


  for (
    let i = 0;
    i < float32.length;
    i++
  ) {

    let value =
      Math.max(
        -1,
        Math.min(
          1,
          float32[i]
        )
      );


    value =
      value < 0
        ?
        value * 32768
        :
        value * 32767;


    view.setInt16(
      i * 2,
      value,
      true
    );
  }


  return new Uint8Array(
    buffer
  );
}


function calculateRMS(
  samples
) {

  if (!samples.length) {

    return 0;
  }


  let total = 0;


  for (
    const value
    of samples
  ) {

    total +=
      value * value;
  }


  return Math.sqrt(
    total
    /
    samples.length
  );
}


// =========================================================
// BARGE IN
// =========================================================

function triggerLocalBargeIn(
  reason
) {

  if (
    localBargeInLatched
    ||
    !callActive
    ||
    endingCall
    ||
    activeAudioSources.size ===
      0
  ) {

    return;
  }


  localBargeInLatched =
    true;


  suppressModelAudio =
    true;


  commitPendingModel();


  stopCurrentPlayback();


  setVisualState(
    "listening",
    "kemo يسمعك..."
  );


  console.log(
    "🛑 Barge-in:",
    reason
  );
}


function handleLocalSpeechActivity(
  rms
) {

  if (
    activeAudioSources.size ===
    0
    &&
    !micWasSpeaking
  ) {

    noiseFloor =
      (
        noiseFloor * 0.96
      )
      +
      (
        rms * 0.04
      );


    noiseFloor =
      Math.max(
        0.003,
        Math.min(
          0.035,
          noiseFloor
        )
      );
  }


  const userSpeaking =
    rms >=
    Math.max(
      USER_SPEECH_RMS,
      noiseFloor * 2.8
    );


  if (
    userSpeaking
  ) {

    silenceFrames = 0;
    micWasSpeaking = true;

  } else {

    silenceFrames++;


    if (
      silenceFrames >=
      2
    ) {

      micWasSpeaking = false;


      if (
        activeAudioSources.size ===
        0
      ) {

        localBargeInLatched =
          false;
      }
    }
  }


  if (
    activeAudioSources.size > 0
    &&
    modelSpeakingStartedAt > 0
    &&
    (
      performance.now()
      -
      modelSpeakingStartedAt
    )
    >=
    BARGE_IN_MODEL_GRACE_MS
  ) {

    const threshold =
      Math.max(
        BARGE_IN_MIN_RMS,
        noiseFloor
        *
        BARGE_IN_NOISE_MULTIPLIER
      );


    if (
      rms >= threshold
    ) {

      highConfidenceSpeechFrames++;

    } else {

      highConfidenceSpeechFrames =
        0;
    }


    if (
      highConfidenceSpeechFrames >=
      BARGE_IN_REQUIRED_FRAMES
    ) {

      triggerLocalBargeIn(
        "voice-energy"
      );


      highConfidenceSpeechFrames =
        0;
    }

  } else {

    highConfidenceSpeechFrames =
      0;
  }
}


// =========================================================
// MICROPHONE
// =========================================================

async function startMicrophoneStreaming() {

  if (!micStream) {

    throw new Error(
      "الميكروفون غير جاهز"
    );
  }


  const AudioContextClass =
    window.AudioContext
    ||
    window.webkitAudioContext;


  inputAudioContext =
    new AudioContextClass({
      latencyHint:
        "interactive"
    });


  await inputAudioContext.resume();


  micSource =
    inputAudioContext
      .createMediaStreamSource(
        micStream
      );


  micProcessor =
    inputAudioContext
      .createScriptProcessor(
        1024,
        1,
        1
      );


  silentGain =
    inputAudioContext
      .createGain();


  silentGain.gain.value =
    0;


  micSource.connect(
    micProcessor
  );


  micProcessor.connect(
    silentGain
  );


  silentGain.connect(
    inputAudioContext.destination
  );


  micProcessor.onaudioprocess =
    event => {

      if (
        !callActive
        ||
        endingCall
        ||
        muted
        ||
        !session
      ) {

        return;
      }


      try {

        const input =
          event
            .inputBuffer
            .getChannelData(
              0
            );


        const rms =
          calculateRMS(
            input
          );


        handleLocalSpeechActivity(
          rms
        );


        const downsampled =
          downsampleBuffer(
            input,
            inputAudioContext.sampleRate,
            16000
          );


        const pcmBytes =
          float32ToPCM16(
            downsampled
          );


        session.sendRealtimeInput({
          audio: {
            data:
              bytesToBase64(
                pcmBytes
              ),

            mimeType:
              "audio/pcm;rate=16000"
          }
        });

      } catch (error) {

        console.log(
          "Mic warning:",
          error
        );
      }
    };
}


async function stopMicrophone() {

  try {

    micProcessor?.disconnect();

  } catch {}


  try {

    micSource?.disconnect();

  } catch {}


  try {

    silentGain?.disconnect();

  } catch {}


  try {

    micStream
      ?.getTracks()
      .forEach(
        track =>
          track.stop()
      );

  } catch {}


  try {

    await inputAudioContext
      ?.close();

  } catch {}


  micProcessor = null;
  micSource = null;
  silentGain = null;
  micStream = null;
  inputAudioContext = null;

  micWasSpeaking = false;
  silenceFrames = 0;
  highConfidenceSpeechFrames = 0;
  localBargeInLatched = false;
}


// =========================================================
// PLAYBACK
// =========================================================

function extractSampleRate(
  mimeType
) {

  const match =
    String(
      mimeType || ""
    ).match(
      /rate=(\d+)/i
    );


  return match
    ?
    Number(
      match[1]
    )
    :
    24000;
}


async function playPCMChunk(
  base64,
  mimeType,
  generation
) {

  if (
    !base64
    ||
    endingCall
    ||
    !callActive
    ||
    suppressModelAudio
    ||
    generation !==
      playbackGeneration
  ) {

    return;
  }


  await ensureOutputAudio();


  const bytes =
    base64ToBytes(
      base64
    );


  const sampleRate =
    extractSampleRate(
      mimeType
    );


  const sampleCount =
    Math.floor(
      bytes.byteLength / 2
    );


  if (
    sampleCount <= 0
  ) {

    return;
  }


  const audioBuffer =
    outputAudioContext
      .createBuffer(
        1,
        sampleCount,
        sampleRate
      );


  const channel =
    audioBuffer
      .getChannelData(
        0
      );


  const view =
    new DataView(
      bytes.buffer,
      bytes.byteOffset,
      bytes.byteLength
    );


  for (
    let i = 0;
    i < sampleCount;
    i++
  ) {

    channel[i] =
      view.getInt16(
        i * 2,
        true
      )
      /
      32768;
  }


  const source =
    outputAudioContext
      .createBufferSource();


  source.buffer =
    audioBuffer;


  source.connect(
    outputAudioContext.destination
  );


  const minimumStart =
    outputAudioContext.currentTime
    +
    PLAYBACK_LEAD_SECONDS;


  const startAt =
    Math.max(
      minimumStart,
      playbackTime
    );


  playbackTime =
    startAt
    +
    audioBuffer.duration;


  if (
    activeAudioSources.size ===
    0
  ) {

    modelSpeakingStartedAt =
      performance.now();
  }


  activeAudioSources.add(
    source
  );


  setVisualState(
    "speaking",
    "kemo يحكي..."
  );


  source.onended =
    () => {

      activeAudioSources.delete(
        source
      );


      if (
        activeAudioSources.size ===
        0
      ) {

        modelSpeakingStartedAt = 0;


        if (
          callActive
          &&
          !endingCall
        ) {

          setVisualState(
            muted
              ?
              "idle"
              :
              "listening",

            muted
              ?
              "الميكروفون مكتوم"
              :
              "kemo يسمعك..."
          );
        }
      }
    };


  source.start(
    startAt
  );
}


function queuePCMChunk(
  base64,
  mimeType
) {

  if (
    suppressModelAudio
  ) {

    return;
  }


  const generation =
    playbackGeneration;


  playbackChain =
    playbackChain
      .then(
        () =>
          playPCMChunk(
            base64,
            mimeType,
            generation
          )
      )
      .catch(
        error => {

          console.error(
            "Playback:",
            error
          );
        }
      );
}


function stopCurrentPlayback() {

  playbackGeneration++;


  for (
    const source
    of activeAudioSources
  ) {

    try {

      source.stop();

    } catch {}
  }


  activeAudioSources.clear();


  modelSpeakingStartedAt = 0;


  if (
    outputAudioContext
  ) {

    playbackTime =
      outputAudioContext.currentTime
      +
      PLAYBACK_LEAD_SECONDS;
  }


  playbackChain =
    Promise.resolve();
}


async function closeOutputAudio() {

  stopCurrentPlayback();


  try {

    await outputAudioContext
      ?.close();

  } catch {}


  outputAudioContext = null;

  playbackTime = 0;

  playbackChain =
    Promise.resolve();
}


// =========================================================
// TOOL LABEL
// =========================================================

function getToolLabel(
  name
) {

  const labels = {

    get_current_time:
      "بشيّك الوقت...",

    create_reminder:
      "بثبت التذكير...",

    list_reminders:
      "براجع تذكيراتك...",

    cancel_reminder:
      "بلغي التذكير...",

    send_telegram_message:
      "ببعثلك عالتلغرام...",

    search_web:
      "بدورلك عالنت...",

    recall_memory:
      "بتذكر آخر حكي...",

    remember_information:
      "بحفظها...",

    save_preference:
      "بتعلمها...",

    desktop_status:
      "بشيّك الكمبيوتر...",

    desktop_open_website:
      "بفتح الموقع عالكمبيوتر...",

    desktop_open_url:
      "بفتح الرابط عالكمبيوتر...",

    desktop_open_app:
      "بفتح البرنامج...",

    desktop_find_file:
      "بدور عالملف...",

    desktop_screenshot:
      "بصور الشاشة..."
  };


  return (
    labels[name]
    ||
    "kemo بنفّذ..."
  );
}


// =========================================================
// SERVER TOOL
// =========================================================

async function callServerTool(
  functionCall,
  signal
) {

  if (
    !callId
    ||
    !callSecret
  ) {

    throw new Error(
      "جلسة المكالمة غير جاهزة"
    );
  }


  const response =
    await fetch(
      "/api/call/tool",
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        signal,

        body:
          JSON.stringify({
            callId,
            callSecret,

            toolName:
              functionCall?.name,

            args:
              functionCall?.args
              ||
              {}
          })
      }
    );


  const data =
    await response.json();


  if (
    !response.ok
  ) {

    throw new Error(
      data?.error
      ||
      "Tool failed"
    );
  }


  return data;
}


function buildToolCallKey(
  functionCall,
  index = 0
) {

  if (
    functionCall?.id
  ) {

    return String(
      functionCall.id
    );
  }


  return (
    String(
      functionCall?.name
      ||
      "tool"
    )
    +
    ":"
    +
    JSON.stringify(
      functionCall?.args
      ||
      {}
    )
    +
    ":"
    +
    index
  );
}


async function executeOneToolCall(
  functionCall,
  index
) {

  const key =
    buildToolCallKey(
      functionCall,
      index
    );


  if (
    processedToolCallIds.has(
      key
    )
  ) {

    return null;
  }


  const name =
    String(
      functionCall?.name
      ||
      ""
    ).trim();


  const controller =
    new AbortController();


  toolAbortControllers.set(
    key,
    controller
  );


  activeToolCount++;


  setVisualState(
    "thinking",
    getToolLabel(
      name
    )
  );


  setCaption(
    getToolLabel(
      name
    )
  );


  try {

    const data =
      await callServerTool(
        functionCall,
        controller.signal
      );


    processedToolCallIds.add(
      key
    );


    return {
      id:
        functionCall?.id,

      name,

      response:
        data?.ok
          ?
          {
            output:
              data.result
          }
          :
          {
            error:
              data?.error
              ||
              "Tool failed"
          }
    };

  } catch (error) {

    processedToolCallIds.add(
      key
    );


    return {
      id:
        functionCall?.id,

      name,

      response: {
        error:
          error?.message
          ||
          "Tool failed"
      }
    };

  } finally {

    toolAbortControllers.delete(
      key
    );


    activeToolCount =
      Math.max(
        0,
        activeToolCount - 1
      );
  }
}


async function handleToolCalls(
  message
) {

  const calls =
    message
      ?.toolCall
      ?.functionCalls;


  if (
    !Array.isArray(
      calls
    )
    ||
    !calls.length
    ||
    !session
  ) {

    return;
  }


  const responses =
    (
      await Promise.all(
        calls.map(
          executeOneToolCall
        )
      )
    )
      .filter(
        Boolean
      );


  if (
    responses.length
  ) {

    session.sendToolResponse({
      functionResponses:
        responses
    });
  }
}


function handleToolCancellation(
  message
) {

  const ids =
    message
      ?.toolCallCancellation
      ?.ids;


  if (
    !Array.isArray(
      ids
    )
  ) {

    return;
  }


  for (
    const id
    of ids
  ) {

    try {

      toolAbortControllers
        .get(
          String(
            id
          )
        )
        ?.abort();

    } catch {}
  }
}


// =========================================================
// TRANSCRIPTION
// =========================================================

function handleUserTranscription(
  text,
  interim = false
) {

  text =
    String(
      text || ""
    ).trim();


  if (!text) {

    return;
  }


  if (
    activeAudioSources.size > 0
  ) {

    triggerLocalBargeIn(
      "transcription"
    );
  }


  if (
    !interim
  ) {

    commitPendingModel();


    pendingUserText =
      mergeTranscriptText(
        pendingUserText,
        text
      );


    setCaption(
      "إنت: "
      +
      pendingUserText
    );

  } else {

    setCaption(
      "إنت: "
      +
      text
    );
  }


  if (
    activeAudioSources.size ===
    0
  ) {

    setVisualState(
      "thinking",
      "kemo يرد..."
    );
  }
}


function handleServerContent(
  content
) {

  if (!content) {

    return;
  }


  if (
    content.interrupted
  ) {

    commitPendingModel();


    suppressModelAudio =
      true;


    stopCurrentPlayback();
  }


  if (
    content
      .interimInputTranscription
      ?.text
  ) {

    handleUserTranscription(
      content
        .interimInputTranscription
        .text,
      true
    );
  }


  if (
    content
      .inputTranscription
      ?.text
  ) {

    handleUserTranscription(
      content
        .inputTranscription
        .text,
      false
    );
  }


  if (
    content
      .outputTranscription
      ?.text
  ) {

    commitPendingUser();


    pendingModelText =
      mergeTranscriptText(
        pendingModelText,
        content
          .outputTranscription
          .text
      );


    setCaption(
      "kemo: "
      +
      pendingModelText
    );
  }


  const parts =
    content
      .modelTurn
      ?.parts
    ||
    [];


  for (
    const part
    of parts
  ) {

    const data =
      part?.inlineData;


    if (
      data?.data
      &&
      String(
        data.mimeType || ""
      ).startsWith(
        "audio/"
      )
      &&
      !suppressModelAudio
    ) {

      commitPendingUser();


      queuePCMChunk(
        data.data,
        data.mimeType
      );
    }
  }


  if (
    content.turnComplete
  ) {

    commitAllPending();


    suppressModelAudio =
      false;


    localBargeInLatched =
      false;


    highConfidenceSpeechFrames =
      0;


    if (
      activeAudioSources.size ===
      0
      &&
      activeToolCount ===
      0
      &&
      callActive
    ) {

      setVisualState(
        muted
          ?
          "idle"
          :
          "listening",

        muted
          ?
          "الميكروفون مكتوم"
          :
          "kemo يسمعك..."
      );
    }
  }
}


function handleGeminiMessage(
  message
) {

  handleToolCancellation(
    message
  );


  if (
    message?.toolCall
  ) {

    handleToolCalls(
      message
    ).catch(
      console.error
    );
  }


  handleServerContent(
    message?.serverContent
  );
}


// =========================================================
// LIVE CONFIG
// =========================================================

function buildLiveConfig(
  callData
) {

  return {

    responseModalities: [
      Modality.AUDIO
    ],


    systemInstruction: {
      parts: [
        {
          text:
            (
              callData.systemInstruction
              +
              "\n\n"
              +
              LIVE_CONVERSATION_POLICY
            )
        }
      ]
    },


    speechConfig: {
      voiceConfig: {
        prebuiltVoiceConfig: {
          voiceName:
            callData.voice
        }
      }
    },


    inputAudioTranscription:
      {},


    outputAudioTranscription:
      {},


    tools:
      Array.isArray(
        callData.liveTools
      )
        ?
        callData.liveTools
        :
        [],


    thinkingConfig: {
      thinkingLevel:
        "MINIMAL",

      includeThoughts:
        false
    },


    realtimeInputConfig: {

      activityHandling:
        "START_OF_ACTIVITY_INTERRUPTS",


      automaticActivityDetection: {

        disabled:
          false,


        startOfSpeechSensitivity:
          "START_SENSITIVITY_HIGH",


        endOfSpeechSensitivity:
          "END_SENSITIVITY_HIGH",


        prefixPaddingMs:
          FAST_VAD_PREFIX_MS,


        silenceDurationMs:
          FAST_VAD_SILENCE_MS
      }
    },


    sessionResumption:
      {}
  };
}


// =========================================================
// CLEANUP
// =========================================================

function cancelAllActiveTools() {

  for (
    const controller
    of toolAbortControllers.values()
  ) {

    try {

      controller.abort();

    } catch {}
  }


  toolAbortControllers.clear();

  toolPromises.clear();

  activeToolCount = 0;
}


async function cleanupAfterFailure() {

  callActive = false;


  stopTimer();


  cancelAllActiveTools();


  try {

    session?.close();

  } catch {}


  session = null;


  await stopMicrophone();

  await closeOutputAudio();

  await releaseWakeLock();


  callControls
    ?.classList
    .add(
      "hidden"
    );


  startCallButton
    ?.classList
    .remove(
      "hidden"
    );


  if (
    startCallButton
  ) {

    startCallButton.disabled =
      false;
  }
}


// =========================================================
// START CALL
// =========================================================

async function startCall() {

  if (
    callActive
    ||
    endingCall
  ) {

    return;
  }


  hideError();


  if (
    startCallButton
  ) {

    startCallButton.disabled =
      true;
  }


  setCaption(
    "جاري تجهيز المكالمة...",
    false
  );


  setVisualState(
    "thinking",
    "جاري الاتصال..."
  );


  transcript = [];

  pendingUserText = "";

  pendingModelText = "";

  callId = null;

  callSecret = null;

  currentContinuity = null;

  muted = false;

  suppressModelAudio = false;

  playbackGeneration = 0;

  processedToolCallIds.clear();

  cancelAllActiveTools();


  try {

    const initData =
      tg?.initData
      ||
      "";


    if (!initData) {

      throw new Error(
        "افتح المكالمة من زر kemo داخل تيليغرام."
      );
    }


    micStream =
      await navigator
        .mediaDevices
        .getUserMedia({
          audio: {
            channelCount:
              1,

            echoCancellation:
              true,

            noiseSuppression:
              true,

            autoGainControl:
              true
          },

          video:
            false
        });


    await ensureOutputAudio();


    await requestWakeLock();


    const startResponse =
      await fetch(
        "/api/call/start",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({
              initData
            })
        }
      );


    const callData =
      await startResponse.json();


    if (
      !startResponse.ok
      ||
      !callData?.ok
    ) {

      throw new Error(
        callData?.error
        ||
        "فشل بدء المكالمة"
      );
    }


    callId =
      callData.callId;


    callSecret =
      callData.callSecret;


    currentContinuity =
      callData.continuity
      ||
      null;


    const ai =
      new GoogleGenAI({
        apiKey:
          callData.ephemeralToken
      });


    session =
      await ai.live.connect({

        model:
          callData.model,

        config:
          buildLiveConfig(
            callData
          ),

        callbacks: {

          onopen: () => {

            console.log(
              "✅ Gemini Live opened"
            );
          },


          onmessage: (
            message
          ) => {

            handleGeminiMessage(
              message
            );
          },


          onerror: (
            event
          ) => {

            console.error(
              "Gemini Live:",
              event
            );
          },


          onclose: () => {

            if (
              callActive
              &&
              !endingCall
            ) {

              cleanupAfterFailure()
                .catch(
                  () => {}
                );
            }
          }
        }
      });


    callActive =
      true;


    startCallButton
      ?.classList
      .add(
        "hidden"
      );


    callControls
      ?.classList
      .remove(
        "hidden"
      );


    createAudioOutputButton();


    startTimer();


    setVisualState(
      "listening",
      "kemo يسمعك..."
    );


    await startMicrophoneStreaming();


    // =====================================================
    // IMPORTANT:
    //
    // أقل من 15 دقيقة:
    // لا نجبر Kemo يحكي أي شيء.
    // ينتظر كريم ويكمل السياق.
    //
    // أكثر من 15 دقيقة:
    // نسمح بتحية قصيرة.
    // =====================================================

    if (
      currentContinuity
        ?.shouldGreet ===
      true
    ) {

      setCaption(
        "اتصلنا. احكي معه طبيعي."
      );


      session.sendRealtimeInput({
        text:
          `
ابدأ المكالمة الآن.

سلّم على كريم بتحية فلسطينية قصيرة جداً مرة واحدة.

بعدها اسكت وخليه يحكي.

لا تشرح النظام.
`
      });

    } else {

      console.log(
        (
          "↪️ Conversation continuation | gap="
          +
          String(
            currentContinuity
              ?.gapMinutes
          )
          +
          " min"
        )
      );


      setCaption(
        "رجعنا لنفس الحكي. كمل طبيعي."
      );


      // لا نرسل prompt لبدء الكلام.
      // Kemo ينتظر كريم ويكمل من آخر سياق.
    }


  } catch (error) {

    console.error(
      "Start call:",
      error
    );


    showError(
      error?.message
      ||
      "ما قدرنا نبدأ المكالمة."
    );


    await cleanupAfterFailure();
  }
}


// =========================================================
// MUTE
// =========================================================

function toggleMute() {

  if (!callActive) {

    return;
  }


  muted =
    !muted;


  micStream
    ?.getAudioTracks()
    .forEach(
      track => {

        track.enabled =
          !muted;
      }
    );


  if (
    muteLabel
  ) {

    muteLabel.textContent =
      muted
        ?
        "فتح المايك"
        :
        "كتم";
  }


  setVisualState(
    muted
      ?
      "idle"
      :
      "listening",

    muted
      ?
      "الميكروفون مكتوم"
      :
      "kemo يسمعك..."
  );
}


// =========================================================
// SAVE CALL
// =========================================================

async function saveCallTranscript() {

  if (
    !callId
    ||
    !callSecret
  ) {

    return;
  }


  commitAllPending();


  try {

    await fetch(
      "/api/call/end",
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify({
            callId,
            callSecret,
            transcript
          })
      }
    );

  } catch (error) {

    console.log(
      "Call save:",
      error
    );
  }
}


// =========================================================
// END CALL
// =========================================================

async function endCall() {

  if (
    endingCall
  ) {

    return;
  }


  if (
    !callActive
    &&
    !callId
  ) {

    return;
  }


  endingCall =
    true;


  callActive =
    false;


  setVisualState(
    "idle",
    "جاري إنهاء المكالمة..."
  );


  stopTimer();


  cancelAllActiveTools();


  try {

    session?.close();

  } catch {}


  session = null;


  await stopMicrophone();

  await closeOutputAudio();

  await releaseWakeLock();

  await saveCallTranscript();


  callControls
    ?.classList
    .add(
      "hidden"
    );


  startCallButton
    ?.classList
    .remove(
      "hidden"
    );


  if (
    startCallButton
  ) {

    startCallButton.disabled =
      false;
  }


  setVisualState(
    "idle",
    "انتهت المكالمة"
  );


  setCaption(
    "المكالمة انحفظت.",
    false
  );


  callId = null;

  callSecret = null;

  currentContinuity = null;

  endingCall = false;
}


// =========================================================
// PAGE CLOSE SAVE
// =========================================================

function saveBeforeClose() {

  if (
    !callId
    ||
    !callSecret
  ) {

    return;
  }


  commitAllPending();


  try {

    const blob =
      new Blob(
        [
          JSON.stringify({
            callId,
            callSecret,
            transcript
          })
        ],
        {
          type:
            "application/json"
        }
      );


    navigator.sendBeacon(
      "/api/call/end",
      blob
    );

  } catch {}
}


// =========================================================
// EVENTS
// =========================================================

startCallButton
  ?.addEventListener(
    "click",
    startCall
  );


muteButton
  ?.addEventListener(
    "click",
    toggleMute
  );


endCallButton
  ?.addEventListener(
    "click",
    endCall
  );


if (
  tg?.BackButton
) {

  try {

    tg.BackButton.onClick(
      async () => {

        if (
          callActive
          ||
          callId
        ) {

          await endCall();
        }


        tg.close();
      }
    );

  } catch {}
}


window.addEventListener(
  "pagehide",
  () => {

    if (
      callActive
      ||
      callId
    ) {

      saveBeforeClose();
    }
  }
);


document.addEventListener(
  "visibilitychange",
  async () => {

    if (
      document.visibilityState ===
      "visible"
      &&
      callActive
    ) {

      try {

        await outputAudioContext
          ?.resume();

      } catch {}


      try {

        await inputAudioContext
          ?.resume();

      } catch {}


      if (!wakeLock) {

        requestWakeLock()
          .catch(
            () => {}
          );
      }
    }
  }
);


// =========================================================
// INITIAL
// =========================================================

createAudioOutputButton();


setVisualState(
  "idle",
  "جاهز للمكالمة"
);


setCaption(
  "اضغط ابدأ، واحكي معه طبيعي.",
  false
);


console.log(
  "===================================="
);

console.log(
  " KEMO HUMAN CALL UI V4 - ONE KEMO"
);

console.log(
  "===================================="
);

console.log(
  "✅ Shared Telegram/call context"
);

console.log(
  "✅ 15-minute continuity"
);

console.log(
  "✅ No forced greeting on continuation"
);

console.log(
  "✅ Desktop tools"
);

console.log(
  "✅ Smart website opening"
);

console.log(
  "✅ Screenshot"
);

console.log(
  "✅ File search"
);

console.log(
  "✅ Ultra-fast VAD preserved"
);


// =========================================================
// KEMO HUMAN CALL UI V4
// =========================================================
