// =========================================================
// XPAND AGENT LIVE CALL UI V2.5
//
// OPENAI REALTIME / WEBRTC
// GEMINI IAPETUS UNIFIED VOICE
//
// FIX V2.5:
//
// - Preflight Gemini TTS BEFORE WebRTC audio starts
// - When unified voice is ready, OpenAI remote audio stays
//   muted for the entire response/call
// - Never unmute OpenAI after successful Gemini playback
// - Never unmute OpenAI on user speech_started
// - Gemini Iapetus is the only audible assistant voice
// - OpenAI audio is used only as fail-safe if Gemini fails
// - Preserve WebRTC / microphone / DataChannel / SDP flow
//
// Standard OpenAI API key NEVER reaches this file.
// Gemini API key NEVER reaches this file.
// =========================================================


// =========================================================
// VERSION
// =========================================================

const VERSION =
  "2.5";


// =========================================================
// TELEGRAM
// =========================================================

const tg =
  window.Telegram?.WebApp
  ||
  null;


if (
  tg
) {

  try {

    tg.ready();

    tg.expand();


    tg.setHeaderColor(
      "#02060d"
    );


    tg.setBackgroundColor(
      "#02060d"
    );


    if (
      typeof tg.enableClosingConfirmation
      ===
      "function"
    ) {

      tg.enableClosingConfirmation();
    }


  } catch (
    error
  ) {

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
  document.getElementById(
    "orb"
  );


const callStatus =
  document.getElementById(
    "callStatus"
  );


const callTimer =
  document.getElementById(
    "callTimer"
  );


const waveform =
  document.getElementById(
    "waveform"
  );


const liveCaption =
  document.getElementById(
    "liveCaption"
  );


const startCallButton =
  document.getElementById(
    "startCallButton"
  );


const callControls =
  document.getElementById(
    "callControls"
  );


const muteButton =
  document.getElementById(
    "muteButton"
  );


const muteLabel =
  document.getElementById(
    "muteLabel"
  );


const endCallButton =
  document.getElementById(
    "endCallButton"
  );


const errorBox =
  document.getElementById(
    "errorBox"
  );


const errorMessage =
  document.getElementById(
    "errorMessage"
  );


const agentNameElement =
  document.getElementById(
    "agentName"
  );


// =========================================================
// FEATURE FLAG
// =========================================================

let unifiedVoiceConfig =
  {
    enabled: false
  };


async function loadUnifiedVoiceConfig() {

  try {

    const response =
      await fetch(
        "/api/voice-config",
        {
          cache:
            "no-store"
        }
      );


    const data =
      await response.json();


    unifiedVoiceConfig =
      {
        enabled:
          Boolean(
            data?.featureFlag
          ),

        raw:
          data
          ||
          {}
      };


  } catch {

    unifiedVoiceConfig =
      {
        enabled:
          false
      };
  }


  return unifiedVoiceConfig;
}


function isUnifiedVoiceEnabled() {

  return Boolean(
    unifiedVoiceConfig?.enabled
  );
}


// =========================================================
// AGENT IDENTITY
// =========================================================

let runtimeAgentName =
  "الوكيل";


let runtimeAgentId =
  "generic-agent";


let runtimeModel =
  "";


function agentLabel() {

  return (
    runtimeAgentName
    ||
    "الوكيل"
  );
}


function updateAgentIdentity(
  name,
  id,
  model = ""
) {

  const cleanName =
    String(
      name
      ||
      ""
    ).trim();


  const cleanId =
    String(
      id
      ||
      ""
    ).trim();


  const cleanModel =
    String(
      model
      ||
      ""
    ).trim();


  if (
    cleanName
  ) {

    runtimeAgentName =
      cleanName;
  }


  if (
    cleanId
  ) {

    runtimeAgentId =
      cleanId;
  }


  if (
    cleanModel
  ) {

    runtimeModel =
      cleanModel;
  }


  if (
    agentNameElement
  ) {

    agentNameElement.textContent =
      runtimeAgentName;
  }


  document.title =
    (
      runtimeAgentName
      +
      " Call"
    );
}


// =========================================================
// CALL STATE
// =========================================================

let peerConnection =
  null;


let dataChannel =
  null;


let microphoneStream =
  null;


let remoteAudio =
  null;


let callId =
  null;


let callSecret =
  null;


let callActive =
  false;


let endingCall =
  false;


let muted =
  false;


let currentContinuity =
  null;


let pendingGreeting =
  false;


let timerInterval =
  null;


let callStartedAt =
  null;


let wakeLock =
  null;


// =========================================================
// TTS STATE
// =========================================================

let ttsAudio =
  null;


let ttsAbortController =
  null;


let ttsCurrentResponseKey =
  null;


let ttsCompletedResponseKeys =
  new Set();


let ttsCompletedTextFingerprints =
  new Set();


let ttsInFlight =
  false;


let ttsObjectUrl =
  null;


let ttsPendingQueue =
  [];


let ttsQueueDraining =
  false;


let unifiedVoiceReady =
  false;


let unifiedVoicePreflightDone =
  false;


let remoteAudioMutedForUnifiedVoice =
  false;


// =========================================================
// TRANSCRIPT STATE
// =========================================================

let transcript =
  [];


let pendingUserText =
  "";


let pendingAssistantText =
  "";


const userTranscriptByItem =
  new Map();


const assistantTranscriptByItem =
  new Map();


// =========================================================
// EVIDENCE
// =========================================================

const reportedEvidence =
  new Set();


let evidenceEnabled =
  true;


// =========================================================
// OUTPUT ROUTING
// =========================================================

let audioOutputButton =
  null;


let audioOutputIcon =
  null;


let audioOutputLabel =
  null;


let audioRouteMode =
  "speaker";


let selectedEarpieceDeviceId =
  "";


let selectedSpeakerDeviceId =
  "";


// =========================================================
// NORMAL TEXT HELPER
//
// IMPORTANT:
// This helper is ONLY for normal text.
// NEVER use this helper on SDP.
// =========================================================

function cleanText(
  value,
  maxLength = 12000
) {

  return String(
    value
    ??
    ""
  )
    .replace(
      /\u0000/g,
      ""
    )
    .trim()
    .slice(
      0,
      maxLength
    );
}


// =========================================================
// SDP HELPER
// =========================================================

function normalizeRemoteSdp(
  value
) {

  let sdp =
    String(
      value
      ??
      ""
    );


  sdp =
    sdp.replace(
      /\u0000/g,
      ""
    );


  if (
    sdp.charCodeAt(
      0
    )
    ===
    0xFEFF
  ) {

    sdp =
      sdp.slice(
        1
      );
  }


  if (
    !sdp
  ) {

    throw new Error(
      "OpenAI SDP answer missing."
    );
  }


  if (
    sdp.length
    >
    300000
  ) {

    throw new Error(
      "OpenAI SDP answer is too large."
    );
  }


  sdp =
    sdp
      .replace(
        /\r\n/g,
        "\n"
      )
      .replace(
        /\r/g,
        "\n"
      );


  let lines =
    sdp.split(
      "\n"
    );


  while (
    lines.length
    &&
    lines[0]
    ===
    ""
  ) {

    lines.shift();
  }


  while (
    lines.length
    &&
    lines[
      lines.length
      -
      1
    ]
    ===
    ""
  ) {

    lines.pop();
  }


  if (
    !lines.length
  ) {

    throw new Error(
      "OpenAI returned empty SDP."
    );
  }


  if (
    lines[0]
    !==
    "v=0"
  ) {

    throw new Error(
      "OpenAI returned invalid SDP start."
    );
  }


  for (
    let index = 0;
    index < lines.length;
    index++
  ) {

    const line =
      lines[
        index
      ];


    if (
      !line
    ) {

      continue;
    }


    if (
      line.length
      <
      2

      ||

      line[1]
      !==
      "="
    ) {

      console.error(
        (
          "Invalid SDP structure"
          +
          " | line="
          +
          (
            index
            +
            1
          )
          +
          " | prefix="
          +
          JSON.stringify(
            line.slice(
              0,
              12
            )
          )
        )
      );


      throw new Error(
        (
          "OpenAI SDP contains an invalid line at "
          +
          (
            index
            +
            1
          )
          +
          "."
        )
      );
    }
  }


  sdp =
    lines.join(
      "\r\n"
    );


  sdp +=
    "\r\n";


  if (
    !sdp.includes(
      "m=audio"
    )
  ) {

    throw new Error(
      "OpenAI SDP answer has no audio section."
    );
  }


  console.log(
    (
      "📥 OPENAI SDP ANSWER CLIENT V2.5"
      +
      " | chars="
      +
      sdp.length
      +
      " | lines="
      +
      lines.length
      +
      " | endsCRLF="
      +
      String(
        sdp.endsWith(
          "\r\n"
        )
      )
      +
      " | audio="
      +
      String(
        sdp.includes(
          "m=audio"
        )
      )
      +
      " | data="
      +
      String(
        sdp.includes(
          "m=application"
        )
      )
      +
      " | icePwd="
      +
      String(
        sdp.includes(
          "a=ice-pwd:"
        )
      )
    )
  );


  return sdp;
}


// =========================================================
// SLEEP
// =========================================================

function sleep(
  milliseconds
) {

  return new Promise(
    resolve =>
      setTimeout(
        resolve,
        milliseconds
      )
  );
}


// =========================================================
// VISUAL STATE
// =========================================================

function setVisualState(
  state,
  text
) {

  if (
    orb
  ) {

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


  if (
    !waveform
  ) {

    return;
  }


  if (
    state
    ===
    "listening"

    ||

    state
    ===
    "thinking"

    ||

    state
    ===
    "speaking"
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

  if (
    !liveCaption
  ) {

    return;
  }


  liveCaption.textContent =
    String(
      text
      ||
      ""
    );


  if (
    active
  ) {

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

  errorBox
    ?.classList
    .add(
      "hidden"
    );
}


function showError(
  text
) {

  const message =
    cleanText(
      text
      ||
      "صار خلل في الاتصال.",
      1500
    );


  console.error(
    message
  );


  if (
    errorMessage
  ) {

    errorMessage.textContent =
      message;
  }


  errorBox
    ?.classList
    .remove(
      "hidden"
    );


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
      totalSeconds
      /
      60
    );


  const seconds =
    totalSeconds
    %
    60;


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


  if (
    callTimer
  ) {

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


        if (
          callTimer
        ) {

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

  if (
    timerInterval
  ) {

    clearInterval(
      timerInterval
    );


    timerInterval =
      null;
  }
}


// =========================================================
// WAKE LOCK
// =========================================================

async function requestWakeLock() {

  try {

    if (
      !(
        "wakeLock"
        in
        navigator
      )
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

        wakeLock =
          null;
      }
    );


  } catch (
    error
  ) {

    console.log(
      "Wake lock warning:",
      error
    );
  }
}


async function releaseWakeLock() {

  try {

    if (
      wakeLock
    ) {

      await wakeLock.release();
    }


  } catch {}


  wakeLock =
    null;
}


// =========================================================
// TRANSCRIPT HELPERS
// =========================================================

function mergeTranscriptText(
  current,
  incoming
) {

  current =
    cleanText(
      current,
      12000
    );


  incoming =
    cleanText(
      incoming,
      12000
    );


  if (
    !incoming
  ) {

    return current;
  }


  if (
    !current
  ) {

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
    cleanText(
      text,
      8000
    );


  if (
    !text
  ) {

    return;
  }


  const normalizedRole =
    role
    ===
    "assistant"
      ?
      "assistant"
      :
      "user";


  const previous =
    transcript[
      transcript.length
      -
      1
    ];


  if (
    previous
    &&
    previous.role
    ===
    normalizedRole
    &&
    previous.text
    ===
    text
  ) {

    return;
  }


  transcript.push({

    role:
      normalizedRole,

    text
  });


  if (
    transcript.length
    >
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
    cleanText(
      pendingUserText,
      8000
    );


  if (
    text
  ) {

    addTranscriptTurn(
      "user",
      text
    );
  }


  pendingUserText =
    "";
}


function commitPendingAssistant() {

  const text =
    cleanText(
      pendingAssistantText,
      8000
    );


  if (
    text
  ) {

    addTranscriptTurn(
      "assistant",
      text
    );
  }


  pendingAssistantText =
    "";
}


function commitAllPending() {

  commitPendingUser();

  commitPendingAssistant();
}


// =========================================================
// UNIFIED VOICE HELPERS
// =========================================================

function unifiedVoiceTextFingerprint(
  value
) {

  return cleanText(
    value,
    4000
  )
    .replace(
      /\s+/g,
      " "
    )
    .toLowerCase();
}


function shouldMuteOpenAiRemoteAudio() {

  return Boolean(
    isUnifiedVoiceEnabled()
    &&
    unifiedVoiceReady
  );
}


// =========================================================
// REMOTE AUDIO
// =========================================================

function ensureRemoteAudioElement() {

  if (
    remoteAudio
  ) {

    remoteAudio.muted =
      shouldMuteOpenAiRemoteAudio();


    remoteAudioMutedForUnifiedVoice =
      Boolean(
        remoteAudio.muted
      );


    return remoteAudio;
  }


  remoteAudio =
    document.createElement(
      "audio"
    );


  remoteAudio.autoplay =
    true;


  remoteAudio.playsInline =
    true;


  remoteAudio.setAttribute(
    "aria-hidden",
    "true"
  );


  remoteAudio.style.position =
    "fixed";


  remoteAudio.style.width =
    "1px";


  remoteAudio.style.height =
    "1px";


  remoteAudio.style.opacity =
    "0";


  remoteAudio.style.pointerEvents =
    "none";


  // CRITICAL V2.5:
  // If Iapetus preflight succeeded, OpenAI audio is muted
  // BEFORE its remote track can become audible.
  remoteAudio.muted =
    shouldMuteOpenAiRemoteAudio();


  remoteAudioMutedForUnifiedVoice =
    Boolean(
      remoteAudio.muted
    );


  document.body.appendChild(
    remoteAudio
  );


  remoteAudio.addEventListener(
    "playing",
    () => {

      if (
        !callActive
      ) {

        return;
      }


      setVisualState(
        "speaking",
        (
          agentLabel()
          +
          " يحكي..."
        )
      );


      reportEvidenceOnce(
        "assistant_audio_playing",
        {

          provider:
            remoteAudio.muted
              ?
              "openai-muted"
              :
              "openai",

          model:
            runtimeModel
        }
      );
    }
  );


  return remoteAudio;
}


async function setRemoteAudioMutedForUnifiedVoice(
  mutedState
) {

  const audio =
    ensureRemoteAudioElement();


  const nextState =
    Boolean(
      mutedState
    );


  try {

    audio.muted =
      nextState;


  } catch {}


  remoteAudioMutedForUnifiedVoice =
    nextState;
}


// =========================================================
// GEMINI AUDIO CLEANUP
// =========================================================

function stopGeminiTtsPlayback() {

  try {

    if (
      ttsAudio
    ) {

      ttsAudio.pause();

      ttsAudio.currentTime =
        0;

      ttsAudio.src =
        "";

      ttsAudio.removeAttribute(
        "src"
      );

      ttsAudio.load?.();
    }


  } catch {}


  ttsAudio =
    null;


  try {

    if (
      ttsObjectUrl
    ) {

      URL.revokeObjectURL(
        ttsObjectUrl
      );
    }


  } catch {}


  ttsObjectUrl =
    null;


  try {

    if (
      ttsAbortController
    ) {

      ttsAbortController.abort();
    }


  } catch {}


  ttsAbortController =
    null;


  ttsInFlight =
    false;


  ttsCurrentResponseKey =
    null;
}


// =========================================================
// TTS REQUEST
// =========================================================

async function requestUnifiedVoiceTts(
  text,
  signal = undefined
) {

  const safeText =
    cleanText(
      text,
      4000
    );


  if (
    !safeText
  ) {

    return {
      ok:
        false,

      error:
        "empty_text"
    };
  }


  try {

    const response =
      await fetch(
        "/api/tts",
        {

          method:
            "POST",

          headers: {

            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({

              text:
                safeText
            }),

          signal
        }
      );


    const contentType =
      cleanText(
        response.headers.get(
          "content-type"
        ),
        200
      ).toLowerCase();


    const blob =
      await response
        .blob()
        .catch(
          () =>
            null
        );


    const blobSize =
      Number(
        blob?.size
        ||
        0
      );


    if (
      response.ok

      &&

      contentType.includes(
        "audio/wav"
      )

      &&

      blob

      &&

      blobSize
      >
      44
    ) {

      return {

        ok:
          true,

        blob,

        contentType,

        blobSize,

        status:
          response.status
      };
    }


    return {

      ok:
        false,

      status:
        response.status,

      contentType,

      blobSize
    };


  } catch (
    error
  ) {

    if (
      error?.name
      ===
      "AbortError"
    ) {

      return {

        ok:
          false,

        aborted:
          true
      };
    }


    return {

      ok:
        false,

      error:
        cleanText(
          error?.message,
          1000
        )
    };
  }
}


// =========================================================
// PRE-FLIGHT
// =========================================================

async function prepareUnifiedVoiceForCall() {

  unifiedVoicePreflightDone =
    false;


  unifiedVoiceReady =
    false;


  if (
    !isUnifiedVoiceEnabled()
  ) {

    unifiedVoicePreflightDone =
      true;


    if (
      remoteAudio
    ) {

      await setRemoteAudioMutedForUnifiedVoice(
        false
      );
    }


    return true;
  }


  console.log(
    "XPAND UNIFIED VOICE | preflight_start"
  );


  const result =
    await requestUnifiedVoiceTts(
      "جاهز"
    );


  unifiedVoicePreflightDone =
    true;


  if (
    result?.ok
  ) {

    unifiedVoiceReady =
      true;


    if (
      remoteAudio
    ) {

      await setRemoteAudioMutedForUnifiedVoice(
        true
      );
    }


    console.log(
      (
        "XPAND UNIFIED VOICE | preflight_success"
        +
        " | bytes="
        +
        result.blobSize
      )
    );


    return true;
  }


  unifiedVoiceReady =
    false;


  if (
    remoteAudio
  ) {

    await setRemoteAudioMutedForUnifiedVoice(
      false
    );
  }


  console.log(
    (
      "XPAND UNIFIED VOICE | preflight_failed"
      +
      " | status="
      +
      String(
        result?.status
        ??
        ""
      )
    )
  );


  return false;
}


// =========================================================
// TTS QUEUE
// =========================================================

async function drainUnifiedVoiceTtsQueue() {

  if (
    !isUnifiedVoiceEnabled()

    ||

    !unifiedVoiceReady

    ||

    ttsQueueDraining
  ) {

    return;
  }


  ttsQueueDraining =
    true;


  try {

    while (
      ttsPendingQueue.length
    ) {

      const next =
        ttsPendingQueue.shift();


      if (
        !next
      ) {

        continue;
      }


      const {
        text,
        dedupKey
      } =
        next;


      const fingerprint =
        unifiedVoiceTextFingerprint(
          text
        );


      if (
        !text

        ||

        !dedupKey

        ||

        ttsCompletedResponseKeys.has(
          dedupKey
        )

        ||

        ttsCompletedTextFingerprints.has(
          fingerprint
        )
      ) {

        continue;
      }


      if (
        ttsInFlight
      ) {

        ttsPendingQueue.unshift(
          next
        );


        return;
      }


      await playUnifiedVoiceTts(
        text,
        dedupKey
      );
    }


  } finally {

    ttsQueueDraining =
      false;
  }
}


function enqueueUnifiedVoiceTts(
  text,
  dedupKey
) {

  if (
    !isUnifiedVoiceEnabled()

    ||

    !unifiedVoiceReady
  ) {

    return;
  }


  const safeText =
    cleanText(
      text,
      4000
    );


  const safeKey =
    cleanText(
      dedupKey,
      300
    );


  const fingerprint =
    unifiedVoiceTextFingerprint(
      safeText
    );


  if (
    !safeText

    ||

    !safeKey

    ||

    ttsCompletedResponseKeys.has(
      safeKey
    )

    ||

    ttsCompletedTextFingerprints.has(
      fingerprint
    )
  ) {

    return;
  }


  if (
    ttsPendingQueue.some(
      item =>
        item?.dedupKey
        ===
        safeKey

        ||

        unifiedVoiceTextFingerprint(
          item?.text
        )
        ===
        fingerprint
    )
  ) {

    return;
  }


  ttsPendingQueue.push({

    text:
      safeText,

    dedupKey:
      safeKey
  });


  drainUnifiedVoiceTtsQueue()
    .catch(
      () => {}
    );
}


// =========================================================
// ASSISTANT TEXT EXTRACTION
// =========================================================

function extractAssistantTextFromEvent(
  event
) {

  const candidates =
    [];


  candidates.push(
    event?.transcript,
    event?.delta,
    event?.text,
    event?.content?.text,
    event?.response?.output_text,
    event?.response?.output?.[0]?.content?.[0]?.transcript,
    event?.response?.output?.[0]?.content?.[0]?.text,
    event?.response?.output?.[0]?.text,
    event?.response?.output?.[0]?.content
      ?.map?.(
        part =>
          part?.transcript
          ||
          part?.text
          ||
          ""
      )
      .join(
        " "
      )
  );


  for (
    const candidate
    of candidates
  ) {

    const text =
      cleanText(
        candidate,
        8000
      );


    if (
      text
    ) {

      return text;
    }
  }


  return "";
}


// =========================================================
// PLAY IAPETUS
// =========================================================

async function playUnifiedVoiceTts(
  text,
  dedupKey
) {

  if (
    !isUnifiedVoiceEnabled()

    ||

    !unifiedVoiceReady
  ) {

    return;
  }


  const safeText =
    cleanText(
      text,
      4000
    );


  const safeDedupKey =
    cleanText(
      dedupKey,
      300
    );


  const fingerprint =
    unifiedVoiceTextFingerprint(
      safeText
    );


  if (
    !safeText

    ||

    !safeDedupKey

    ||

    ttsCompletedResponseKeys.has(
      safeDedupKey
    )

    ||

    ttsCompletedTextFingerprints.has(
      fingerprint
    )

    ||

    ttsInFlight
  ) {

    console.log(
      (
        "XPAND UNIFIED VOICE | tts_skip_duplicate"
        +
        " | id="
        +
        safeDedupKey
      )
    );


    return;
  }


  // Stop previous Gemini playback BEFORE marking new request
  // as in-flight.
  stopGeminiTtsPlayback();


  ttsInFlight =
    true;


  ttsCurrentResponseKey =
    safeDedupKey;


  ttsAbortController =
    new AbortController();


  let playbackStarted =
    false;


  let requestFailed =
    false;


  try {

    // CRITICAL V2.5:
    // OpenAI must remain muted while Gemini is the selected
    // voice.
    await setRemoteAudioMutedForUnifiedVoice(
      true
    );


    console.log(
      (
        "XPAND UNIFIED VOICE | tts_start"
        +
        " | id="
        +
        safeDedupKey
      )
    );


    const result =
      await requestUnifiedVoiceTts(
        safeText,
        ttsAbortController.signal
      );


    if (
      result?.aborted
    ) {

      return;
    }


    if (
      !result?.ok
    ) {

      requestFailed =
        true;


      throw new Error(
        (
          "TTS request failed"
          +
          (
            result?.status
              ?
              (
                " HTTP "
                +
                result.status
              )
              :
              ""
          )
        )
      );
    }


    if (
      ttsAbortController
        ?.signal
        ?.aborted
    ) {

      return;
    }


    const wavBlob =
      result.blob;


    const objectUrl =
      URL.createObjectURL(
        wavBlob
      );


    ttsObjectUrl =
      objectUrl;


    const audio =
      new Audio(
        objectUrl
      );


    ttsAudio =
      audio;


    audio.preload =
      "auto";


    audio.autoplay =
      true;


    audio.playsInline =
      true;


    audio.muted =
      false;


    audio.addEventListener(
      "ended",
      () => {

        try {

          URL.revokeObjectURL(
            objectUrl
          );


        } catch {}


        if (
          ttsObjectUrl
          ===
          objectUrl
        ) {

          ttsObjectUrl =
            null;
        }


        if (
          ttsAudio
          ===
          audio
        ) {

          ttsAudio =
            null;
        }
      },
      {
        once:
          true
      }
    );


    audio.addEventListener(
      "error",
      () => {

        try {

          URL.revokeObjectURL(
            objectUrl
          );


        } catch {}


        if (
          ttsObjectUrl
          ===
          objectUrl
        ) {

          ttsObjectUrl =
            null;
        }
      },
      {
        once:
          true
      }
    );


    await audio.play();


    playbackStarted =
      true;


    ttsCompletedResponseKeys.add(
      safeDedupKey
    );


    ttsCompletedTextFingerprints.add(
      fingerprint
    );


    console.log(
      (
        "XPAND UNIFIED VOICE | tts_success"
        +
        " | id="
        +
        safeDedupKey
        +
        " | bytes="
        +
        result.blobSize
      )
    );


    // IMPORTANT:
    // DO NOT unmute OpenAI here.
    //
    // audio.play() resolves when playback starts, not when it
    // ends. Unmuting OpenAI in finally causes the female voice
    // to become audible under/after Iapetus.
    await setRemoteAudioMutedForUnifiedVoice(
      true
    );


  } catch (
    error
  ) {

    if (
      error?.name
      ===
      "AbortError"
    ) {

      return;
    }


    console.log(
      (
        "XPAND UNIFIED VOICE | tts_failed"
        +
        " | id="
        +
        safeDedupKey
        +
        " | error="
        +
        cleanText(
          error?.message,
          300
        )
      )
    );


    if (
      requestFailed
    ) {

      // Real Gemini failure:
      // fall back to OpenAI audio so the call does not become
      // silent.
      unifiedVoiceReady =
        false;


      await setRemoteAudioMutedForUnifiedVoice(
        false
      );
    }


  } finally {

    // Do not revoke an Object URL while the audio is actively
    // playing. ended/error/stopGeminiTtsPlayback owns cleanup.
    if (
      !playbackStarted
      &&
      ttsObjectUrl
    ) {

      try {

        URL.revokeObjectURL(
          ttsObjectUrl
        );


      } catch {}


      ttsObjectUrl =
        null;
    }


    ttsInFlight =
      false;


    ttsAbortController =
      null;


    ttsCurrentResponseKey =
      null;
  }
}


// =========================================================
// AUDIO OUTPUT DEVICE
// =========================================================

function normalizeDeviceLabel(
  label
) {

  return String(
    label
    ||
    ""
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
    id
    ===
    "communications"

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
    id
    ===
    "default"

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
      "built-in"
    )
  );
}


function updateAudioOutputButton() {

  if (
    !audioOutputButton
    ||
    !audioOutputIcon
    ||
    !audioOutputLabel
  ) {

    return;
  }


  if (
    audioRouteMode
    ===
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
      item.kind
      ===
      "audiooutput"
  );
}


async function setOutputDevice(
  deviceId
) {

  const audio =
    ensureRemoteAudioElement();


  if (
    typeof audio.setSinkId
    !==
    "function"
  ) {

    return false;
  }


  await audio.setSinkId(
    deviceId
  );


  return true;
}


async function routeToEarpiece() {

  const outputs =
    await getAudioOutputDevices();


  let device =
    outputs.find(
      item =>
        item.deviceId
        ===
        selectedEarpieceDeviceId
    );


  if (
    !device
  ) {

    device =
      outputs.find(
        looksLikeEarpiece
      );
  }


  if (
    !device?.deviceId
  ) {

    return false;
  }


  const changed =
    await setOutputDevice(
      device.deviceId
    );


  if (
    !changed
  ) {

    return false;
  }


  selectedEarpieceDeviceId =
    device.deviceId;


  audioRouteMode =
    "earpiece";


  updateAudioOutputButton();


  return true;
}


async function routeToSpeaker() {

  const outputs =
    await getAudioOutputDevices();


  let device =
    outputs.find(
      item =>
        item.deviceId
        ===
        selectedSpeakerDeviceId
    );


  if (
    !device
  ) {

    device =
      outputs.find(
        looksLikeSpeaker
      );
  }


  try {

    if (
      device?.deviceId
    ) {

      await setOutputDevice(
        device.deviceId
      );


      selectedSpeakerDeviceId =
        device.deviceId;

    } else {

      await setOutputDevice(
        "default"
      );
    }


  } catch {}


  audioRouteMode =
    "speaker";


  updateAudioOutputButton();


  return true;
}


async function toggleAudioRoute() {

  if (
    audioRouteMode
    ===
    "speaker"
  ) {

    const changed =
      await routeToEarpiece();


    if (
      !changed
    ) {

      setCaption(
        "الجهاز ما أعطانا سماعة اتصال منفصلة.",
        false
      );
    }


  } else {

    await routeToSpeaker();
  }
}


// =========================================================
// CALL EVIDENCE
// =========================================================

async function reportEvidence(
  eventType,
  metadata = {}
) {

  if (
    !evidenceEnabled
    ||
    !callId
    ||
    !callSecret
  ) {

    return false;
  }


  try {

    const response =
      await fetch(
        "/api/call/evidence",
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

              eventType,

              metadata
            })
        }
      );


    return response.ok;


  } catch (
    error
  ) {

    console.log(
      (
        "Evidence "
        +
        eventType
        +
        ": "
        +
        error.message
      )
    );


    return false;
  }
}


function reportEvidenceOnce(
  eventType,
  metadata = {}
) {

  if (
    reportedEvidence.has(
      eventType
    )
  ) {

    return;
  }


  if (
    !callId
    ||
    !callSecret
  ) {

    return;
  }


  reportEvidence(
    eventType,
    metadata
  )
    .then(
      success => {

        if (
          success
        ) {

          reportedEvidence.add(
            eventType
          );
        }
      }
    )
    .catch(
      () => {}
    );
}


// =========================================================
// DATA CHANNEL SEND
// =========================================================

function sendRealtimeEvent(
  event
) {

  if (
    !dataChannel
    ||
    dataChannel.readyState
    !==
    "open"
  ) {

    return false;
  }


  try {

    dataChannel.send(
      JSON.stringify(
        event
      )
    );


    return true;


  } catch (
    error
  ) {

    console.log(
      "Realtime send:",
      error
    );


    return false;
  }
}


// =========================================================
// GREETING
// =========================================================

function maybeSendGreeting() {

  if (
    !pendingGreeting
  ) {

    return;
  }


  if (
    !dataChannel
    ||
    dataChannel.readyState
    !==
    "open"
  ) {

    return;
  }


  pendingGreeting =
    false;


  sendRealtimeEvent({

    type:
      "response.create",

    response: {

      output_modalities: [
        "audio"
      ],

      instructions:
        (
          "ابدأ المكالمة الآن بتحية قصيرة جداً وطبيعية "
          +
          "باسم "
          +
          agentLabel()
          +
          ". لا تشرح النظام، وبعد التحية انتظر المستخدم."
        )
    }
  });
}


// =========================================================
// USER TRANSCRIPTION
// =========================================================

function handleUserTranscriptDelta(
  event
) {

  const itemId =
    cleanText(
      event?.item_id
      ||
      "current-user",
      300
    );


  const delta =
    cleanText(
      event?.delta,
      4000
    );


  if (
    !delta
  ) {

    return;
  }


  const current =
    userTranscriptByItem.get(
      itemId
    )
    ||
    "";


  const merged =
    mergeTranscriptText(
      current,
      delta
    );


  userTranscriptByItem.set(
    itemId,
    merged
  );


  pendingUserText =
    merged;


  setCaption(
    (
      "إنت: "
      +
      merged
    )
  );
}


function handleUserTranscriptCompleted(
  event
) {

  const itemId =
    cleanText(
      event?.item_id
      ||
      "current-user",
      300
    );


  const text =
    cleanText(
      event?.transcript
      ||
      userTranscriptByItem.get(
        itemId
      )
      ||
      pendingUserText,
      8000
    );


  if (
    !text
  ) {

    return;
  }


  userTranscriptByItem.delete(
    itemId
  );


  pendingUserText =
    "";


  addTranscriptTurn(
    "user",
    text
  );


  setCaption(
    (
      "إنت: "
      +
      text
    )
  );


  reportEvidenceOnce(
    "user_audio_transcript",
    {

      textLength:
        text.length
    }
  );
}


// =========================================================
// ASSISTANT TRANSCRIPTION
// =========================================================

function assistantEventKey(
  event
) {

  return cleanText(
    event?.item_id
    ||
    event?.response_id
    ||
    "current-assistant",
    300
  );
}


function handleAssistantTranscriptDelta(
  event
) {

  const key =
    assistantEventKey(
      event
    );


  const delta =
    cleanText(
      event?.delta,
      4000
    );


  if (
    !delta
  ) {

    return;
  }


  const current =
    assistantTranscriptByItem.get(
      key
    )
    ||
    "";


  const merged =
    mergeTranscriptText(
      current,
      delta
    );


  assistantTranscriptByItem.set(
    key,
    merged
  );


  pendingAssistantText =
    merged;


  setVisualState(
    "speaking",
    (
      agentLabel()
      +
      " يحكي..."
    )
  );


  setCaption(
    (
      agentLabel()
      +
      ": "
      +
      merged
    )
  );
}


function handleAssistantTranscriptDone(
  event
) {

  const key =
    assistantEventKey(
      event
    );


  const text =
    cleanText(
      event?.transcript
      ||
      assistantTranscriptByItem.get(
        key
      )
      ||
      pendingAssistantText,
      8000
    );


  if (
    !text
  ) {

    return;
  }


  assistantTranscriptByItem.delete(
    key
  );


  pendingAssistantText =
    "";


  addTranscriptTurn(
    "assistant",
    text
  );


  setCaption(
    (
      agentLabel()
      +
      ": "
      +
      text
    )
  );


  reportEvidenceOnce(
    "assistant_audio_transcript",
    {

      textLength:
        text.length,

      provider:
        "openai",

      model:
        runtimeModel
    }
  );


  if (
    isUnifiedVoiceEnabled()
    &&
    unifiedVoiceReady
  ) {

    const dedupKey =
      cleanText(
        event?.item_id
        ||
        event?.response_id
        ||
        event?.response?.id
        ||
        event?.id
        ||
        key,
        300
      );


    console.log(
      (
        "XPAND UNIFIED VOICE | transcript_done"
        +
        " | id="
        +
        dedupKey
      )
    );


    if (
      dedupKey
    ) {

      enqueueUnifiedVoiceTts(
        text,
        dedupKey
      );
    }
  }
}


// =========================================================
// FALLBACK ASSISTANT TRANSCRIPT
// =========================================================

function inspectCompletedOutput(
  event
) {

  const output =
    event?.response?.output;


  if (
    !Array.isArray(
      output
    )
  ) {

    return "";
  }


  for (
    const item
    of output
  ) {

    const content =
      item?.content;


    if (
      !Array.isArray(
        content
      )
    ) {

      continue;
    }


    for (
      const part
      of content
    ) {

      const transcriptText =
        cleanText(
          part?.transcript,
          8000
        );


      if (
        transcriptText
      ) {

        addTranscriptTurn(
          "assistant",
          transcriptText
        );


        setCaption(
          (
            agentLabel()
            +
            ": "
            +
            transcriptText
          )
        );


        reportEvidenceOnce(
          "assistant_audio_transcript",
          {

            textLength:
              transcriptText.length,

            source:
              "response.done"
          }
        );


        return transcriptText;
      }


      const outputText =
        cleanText(
          part?.text,
          8000
        );


      if (
        outputText
      ) {

        addTranscriptTurn(
          "assistant",
          outputText
        );


        return outputText;
      }
    }
  }


  return "";
}


function getResponseDedupKey(
  event
) {

  return cleanText(
    event?.response?.id
    ||
    event?.response_id
    ||
    event?.id
    ||
    "",
    300
  );
}


// =========================================================
// REALTIME EVENT HANDLER
// =========================================================

function handleRealtimeEvent(
  event
) {

  if (
    !event
    ||
    typeof event
    !==
    "object"
  ) {

    return;
  }


  const type =
    cleanText(
      event.type,
      200
    );


  if (
    !type
  ) {

    return;
  }


  switch (
    type
  ) {

    case "session.created": {

      console.log(
        (
          "✅ OPENAI REALTIME SESSION CREATED | "
          +
          runtimeModel
        )
      );


      reportEvidenceOnce(
        "openai_session_created",
        {

          provider:
            "openai",

          model:
            runtimeModel,

          sessionId:
            cleanText(
              event?.session?.id,
              300
            )
        }
      );


      maybeSendGreeting();

      break;
    }


    case "session.updated": {

      console.log(
        "✅ OpenAI Realtime session updated"
      );

      break;
    }


    case "input_audio_buffer.speech_started": {

      commitPendingAssistant();


      if (
        isUnifiedVoiceEnabled()
      ) {

        stopGeminiTtsPlayback();


        const audio =
          ensureRemoteAudioElement();


        // CRITICAL V2.5:
        // User interruption must NOT bring the female OpenAI
        // voice back when Iapetus is healthy.
        try {

          audio.muted =
            Boolean(
              unifiedVoiceReady
            );


          remoteAudioMutedForUnifiedVoice =
            Boolean(
              unifiedVoiceReady
            );


        } catch {}
      }


      setVisualState(
        "listening",
        (
          agentLabel()
          +
          " يسمعك..."
        )
      );


      setCaption(
        "إنت بتحكي..."
      );


      reportEvidenceOnce(
        "user_audio_started",
        {

          audioStartMs:
            event?.audio_start_ms
            ??
            null
        }
      );


      break;
    }


    case "input_audio_buffer.speech_stopped": {

      reportEvidenceOnce(
        "user_audio_stopped",
        {

          audioEndMs:
            event?.audio_end_ms
            ??
            null
        }
      );


      break;
    }


    case "conversation.item.input_audio_transcription.delta": {

      handleUserTranscriptDelta(
        event
      );

      break;
    }


    case "conversation.item.input_audio_transcription.completed": {

      handleUserTranscriptCompleted(
        event
      );

      break;
    }


    case "response.created": {

      setVisualState(
        "thinking",
        (
          agentLabel()
          +
          " يرد..."
        )
      );


      // Keep OpenAI inaudible while unified voice is healthy.
      if (
        isUnifiedVoiceEnabled()
        &&
        unifiedVoiceReady
      ) {

        setRemoteAudioMutedForUnifiedVoice(
          true
        ).catch(
          () => {}
        );
      }


      break;
    }


    case "response.output_audio.delta": {

      reportEvidenceOnce(
        "assistant_audio_received",
        {

          provider:
            "openai",

          model:
            runtimeModel,

          source:
            "realtime_event"
        }
      );


      setVisualState(
        "speaking",
        (
          agentLabel()
          +
          " يحكي..."
        )
      );


      break;
    }


    case "response.output_audio_transcript.delta": {

      handleAssistantTranscriptDelta(
        event
      );

      break;
    }


    case "response.output_audio_transcript.done": {

      handleAssistantTranscriptDone(
        event
      );

      break;
    }


    case "response.done": {

      const dedupKey =
        getResponseDedupKey(
          event
        );


      const responseText =
        extractAssistantTextFromEvent(
          event
        );


      const pendingTextBeforeCommit =
        cleanText(
          pendingAssistantText,
          4000
        );


      const inspectedText =
        inspectCompletedOutput(
          event
        );


      commitPendingAssistant();


      if (
        isUnifiedVoiceEnabled()
        &&
        unifiedVoiceReady
      ) {

        const fallbackText =
          cleanText(
            responseText
            ||
            inspectedText
            ||
            pendingTextBeforeCommit,
            4000
          );


        const safeDedupKey =
          dedupKey
          ||
          cleanText(
            (
              event?.response?.id
              ||
              event?.response_id
              ||
              event?.id
              ||
              "response.done"
            ),
            300
          );


        if (
          fallbackText
          &&
          safeDedupKey
        ) {

          enqueueUnifiedVoiceTts(
            fallbackText,
            safeDedupKey
          );
        }
      }


      reportEvidenceOnce(
        "openai_response_done",
        {

          provider:
            "openai",

          model:
            runtimeModel,

          responseId:
            cleanText(
              event?.response?.id,
              300
            ),

          status:
            cleanText(
              event?.response?.status,
              100
            )
        }
      );


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
            (
              agentLabel()
              +
              " يسمعك..."
            )
        );
      }


      break;
    }


    case "error": {

      const message =
        cleanText(
          event?.error?.message
          ||
          "OpenAI Realtime error",
          1200
        );


      console.error(
        "OpenAI Realtime:",
        message
      );


      reportEvidenceOnce(
        "call_client_error",
        {

          source:
            "openai",

          message
        }
      );


      setCaption(
        (
          "صار خلل مؤقت بالمكالمة: "
          +
          message
        ),
        false
      );


      break;
    }


    default:

      break;
  }
}


// =========================================================
// DATA CHANNEL
// =========================================================

function configureDataChannel(
  channel
) {

  dataChannel =
    channel;


  dataChannel.addEventListener(
    "open",
    () => {

      console.log(
        "✅ OPENAI REALTIME DATA CHANNEL OPEN"
      );


      maybeSendGreeting();
    }
  );


  dataChannel.addEventListener(
    "message",
    event => {

      try {

        const payload =
          JSON.parse(
            event.data
          );


        handleRealtimeEvent(
          payload
        );


      } catch (
        error
      ) {

        console.log(
          "Realtime event parse:",
          error
        );
      }
    }
  );


  dataChannel.addEventListener(
    "close",
    () => {

      console.log(
        "ℹ️ OpenAI Realtime data channel closed"
      );
    }
  );


  dataChannel.addEventListener(
    "error",
    event => {

      console.error(
        "Realtime data channel:",
        event
      );


      reportEvidenceOnce(
        "call_client_error",
        {

          source:
            "data_channel"
        }
      );
    }
  );
}


// =========================================================
// PEER CONNECTION
// =========================================================

function createPeerConnection() {

  const pc =
    new RTCPeerConnection();


  const audio =
    ensureRemoteAudioElement();


  // CRITICAL V2.5:
  // Set mute state before remote track arrives.
  audio.muted =
    shouldMuteOpenAiRemoteAudio();


  remoteAudioMutedForUnifiedVoice =
    Boolean(
      audio.muted
    );


  pc.ontrack =
    event => {

      const stream =
        event.streams?.[0];


      // Apply mute BEFORE assigning the stream.
      if (
        isUnifiedVoiceEnabled()
        &&
        unifiedVoiceReady
      ) {

        audio.muted =
          true;


        remoteAudioMutedForUnifiedVoice =
          true;

      } else {

        audio.muted =
          false;


        remoteAudioMutedForUnifiedVoice =
          false;
      }


      if (
        stream
      ) {

        audio.srcObject =
          stream;

      } else {

        audio.srcObject =
          new MediaStream(
            [
              event.track
            ]
          );
      }


      reportEvidenceOnce(
        "assistant_audio_received",
        {

          provider:
            "openai",

          model:
            runtimeModel,

          source:
            "webrtc_track"
        }
      );


      // The OpenAI remote stream can keep playing silently in
      // unified mode. This preserves WebRTC timing/transcript.
      audio.play()
        .catch(
          error => {

            console.log(
              "Remote audio play:",
              error
            );
          }
        );
    };


  pc.onconnectionstatechange =
    () => {

      const state =
        pc.connectionState;


      console.log(
        (
          "WebRTC connection: "
          +
          state
        )
      );


      if (
        state
        ===
        "connected"
      ) {

        console.log(
          "✅ WEBRTC CONNECTED V2.5"
        );


        reportEvidenceOnce(
          "webrtc_connected",
          {

            provider:
              "openai",

            model:
              runtimeModel
          }
        );


        if (
          isUnifiedVoiceEnabled()
          &&
          unifiedVoiceReady
        ) {

          setRemoteAudioMutedForUnifiedVoice(
            true
          ).catch(
            () => {}
          );
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
            (
              agentLabel()
              +
              " يسمعك..."
            )
        );
      }


      if (
        (
          state
          ===
          "failed"

          ||

          state
          ===
          "closed"
        )

        &&

        callActive

        &&

        !endingCall
      ) {

        reportEvidenceOnce(
          "call_client_error",
          {

            source:
              "webrtc",

            state
          }
        );


        showError(
          "انقطع اتصال المكالمة."
        );
      }
    };


  pc.oniceconnectionstatechange =
    () => {

      console.log(
        (
          "ICE: "
          +
          pc.iceConnectionState
        )
      );
    };


  pc.onicegatheringstatechange =
    () => {

      console.log(
        (
          "ICE gathering: "
          +
          pc.iceGatheringState
        )
      );
    };


  return pc;
}


// =========================================================
// WAIT FOR DATA CHANNEL
// =========================================================

async function waitForDataChannelOpen(
  timeoutMs = 12000
) {

  const started =
    Date.now();


  while (
    (
      Date.now()
      -
      started
    )
    <
    timeoutMs
  ) {

    if (
      dataChannel?.readyState
      ===
      "open"
    ) {

      return true;
    }


    if (
      endingCall
    ) {

      return false;
    }


    await sleep(
      100
    );
  }


  return false;
}


// =========================================================
// LOAD HEALTH
// =========================================================

async function loadAgentHealth() {

  try {

    const response =
      await fetch(
        "/api/health",
        {

          method:
            "GET",

          cache:
            "no-store"
        }
      );


    const data =
      await response.json();


    if (
      response.ok
      &&
      data?.ok
    ) {

      updateAgentIdentity(
        data.agentName,
        data.agentId,
        data.model
      );


      console.log(
        (
          "✅ Agent: "
          +
          agentLabel()
          +
          " | "
          +
          cleanText(
            data.provider
          )
          +
          " | "
          +
          cleanText(
            data.model
          )
        )
      );


      return data;
    }


  } catch (
    error
  ) {

    console.log(
      "Health warning:",
      error
    );
  }


  return null;
}


// =========================================================
// RESET SESSION
// =========================================================

function resetSessionState() {

  transcript =
    [];


  pendingUserText =
    "";


  pendingAssistantText =
    "";


  userTranscriptByItem.clear();


  assistantTranscriptByItem.clear();


  reportedEvidence.clear();


  evidenceEnabled =
    true;


  callId =
    null;


  callSecret =
    null;


  currentContinuity =
    null;


  pendingGreeting =
    false;


  muted =
    false;


  callActive =
    false;


  ttsCompletedResponseKeys =
    new Set();


  ttsCompletedTextFingerprints =
    new Set();


  ttsPendingQueue =
    [];


  ttsQueueDraining =
    false;


  unifiedVoiceReady =
    false;


  unifiedVoicePreflightDone =
    false;


  remoteAudioMutedForUnifiedVoice =
    false;


  stopGeminiTtsPlayback();


  if (
    remoteAudio
  ) {

    try {

      remoteAudio.muted =
        false;


    } catch {}
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


  resetSessionState();


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


  try {

    await loadUnifiedVoiceConfig();


    const initData =
      tg?.initData
      ||
      "";


    if (
      !initData
    ) {

      throw new Error(
        (
          "افتح المكالمة من زر "
          +
          agentLabel()
          +
          " داخل تيليغرام."
        )
      );
    }


    // =====================================================
    // UNIFIED VOICE PREFLIGHT
    //
    // This happens BEFORE RTCPeerConnection is created.
    // Therefore if Iapetus works, OpenAI audio is muted from
    // the first remote audio frame.
    // =====================================================

    if (
      isUnifiedVoiceEnabled()
    ) {

      setCaption(
        "جاري تجهيز صوت XPAND...",
        false
      );


      await prepareUnifiedVoiceForCall();
    }


    // =====================================================
    // MICROPHONE
    // =====================================================

    microphoneStream =
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


    await requestWakeLock();


    // =====================================================
    // WEBRTC
    // =====================================================

    peerConnection =
      createPeerConnection();


    for (
      const track
      of microphoneStream.getAudioTracks()
    ) {

      peerConnection.addTrack(
        track,
        microphoneStream
      );
    }


    const channel =
      peerConnection.createDataChannel(
        "oai-events"
      );


    configureDataChannel(
      channel
    );


    // =====================================================
    // LOCAL SDP OFFER
    // =====================================================

    const offer =
      await peerConnection.createOffer();


    await peerConnection.setLocalDescription(
      offer
    );


    const localSdp =
      peerConnection
        .localDescription
        ?.sdp
      ||
      offer.sdp;


    if (
      !localSdp
    ) {

      throw new Error(
        "ما قدرنا نجهز WebRTC offer."
      );
    }


    console.log(
      (
        "📤 LOCAL SDP READY V2.5"
        +
        " | chars="
        +
        localSdp.length
      )
    );


    // =====================================================
    // SERVER -> OPENAI
    // =====================================================

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

              initData,

              sdp:
                localSdp
            })
        }
      );


    let callData;


    try {

      callData =
        await startResponse.json();


    } catch {

      throw new Error(
        (
          "الخادم رجع رد غير صالح. HTTP "
          +
          startResponse.status
        )
      );
    }


    if (
      !startResponse.ok
      ||
      !callData?.ok
    ) {

      throw new Error(
        callData?.error
        ||
        "فشل بدء OpenAI Realtime."
      );
    }


    if (
      callData.provider
      !==
      "openai"
    ) {

      throw new Error(
        (
          "Provider verification failed: "
          +
          cleanText(
            callData.provider
          )
        )
      );
    }


    if (
      callData.transport
      !==
      "webrtc"
    ) {

      throw new Error(
        "WebRTC verification failed."
      );
    }


    updateAgentIdentity(
      callData.agentName,
      callData.agentId,
      callData.model
    );


    callId =
      callData.callId;


    callSecret =
      callData.callSecret;


    currentContinuity =
      callData.continuity
      ||
      null;


    pendingGreeting =
      (
        currentContinuity
          ?.shouldGreet
        ===
        true
      );


    const sdpAnswer =
      normalizeRemoteSdp(
        callData.sdpAnswer
      );


    console.log(
      "🔧 Applying OpenAI remote SDP V2.5..."
    );


    await peerConnection.setRemoteDescription({

      type:
        "answer",

      sdp:
        sdpAnswer
    });


    console.log(
      "✅ REMOTE SDP APPLIED V2.5"
    );


    callActive =
      true;


    // Final guard:
    // keep OpenAI muted after remote SDP if Iapetus is ready.
    if (
      isUnifiedVoiceEnabled()
      &&
      unifiedVoiceReady
    ) {

      await setRemoteAudioMutedForUnifiedVoice(
        true
      );
    }


    // =====================================================
    // UI
    // =====================================================

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
      (
        agentLabel()
        +
        " يسمعك..."
      )
    );


    if (
      pendingGreeting
    ) {

      setCaption(
        (
          "اتصلنا بـ "
          +
          agentLabel()
          +
          "..."
        )
      );

    } else {

      setCaption(
        (
          "رجعنا لنفس حكي "
          +
          agentLabel()
          +
          ". كمل طبيعي."
        )
      );
    }


    const channelReady =
      await waitForDataChannelOpen();


    if (
      !channelReady
    ) {

      console.log(
        "⚠️ Data channel open timeout"
      );


      setCaption(
        "الاتصال الصوتي فتح، جاري تجهيز قناة المحادثة...",
        false
      );

    } else {

      maybeSendGreeting();
    }


    console.log(
      (
        "📞 OPENAI LIVE CALL STARTED V2.5"
        +
        " | "
        +
        runtimeAgentId
        +
        " | "
        +
        runtimeModel
        +
        " | unified="
        +
        String(
          isUnifiedVoiceEnabled()
        )
        +
        " | iapetusReady="
        +
        String(
          unifiedVoiceReady
        )
      )
    );


  } catch (
    error
  ) {

    console.error(
      "❌ Start call V2.5:",
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

  if (
    !callActive
  ) {

    return;
  }


  muted =
    !muted;


  microphoneStream
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
      (
        agentLabel()
        +
        " يسمعك..."
      )
  );
}


// =========================================================
// SAVE CALL TRANSCRIPT
// =========================================================

async function saveCallTranscript() {

  if (
    !callId
    ||
    !callSecret
  ) {

    return null;
  }


  commitAllPending();


  try {

    const response =
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


    const data =
      await response.json();


    if (
      response.ok
      &&
      data?.ok
    ) {

      return data;
    }


    console.log(
      "Call save failed:",
      data
    );


  } catch (
    error
  ) {

    console.log(
      "Call save:",
      error
    );
  }


  return null;
}


// =========================================================
// STOP MEDIA
// =========================================================

function stopMedia() {

  try {

    microphoneStream
      ?.getTracks()
      .forEach(
        track =>
          track.stop()
      );


  } catch {}


  microphoneStream =
    null;


  try {

    dataChannel?.close();


  } catch {}


  dataChannel =
    null;


  try {

    peerConnection?.close();


  } catch {}


  peerConnection =
    null;


  try {

    if (
      remoteAudio
    ) {

      remoteAudio.pause();

      remoteAudio.srcObject =
        null;

      remoteAudio.muted =
        false;
    }


  } catch {}


  remoteAudioMutedForUnifiedVoice =
    false;


  stopGeminiTtsPlayback();
}


// =========================================================
// CLEANUP AFTER FAILURE
// =========================================================

async function cleanupAfterFailure() {

  const hadServerSession =
    Boolean(
      callId
      &&
      callSecret
    );


  callActive =
    false;


  stopTimer();


  if (
    hadServerSession
  ) {

    try {

      await saveCallTranscript();


    } catch {}
  }


  evidenceEnabled =
    false;


  stopMedia();


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


  callId =
    null;


  callSecret =
    null;


  currentContinuity =
    null;


  pendingGreeting =
    false;
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


  setVisualState(
    "idle",
    "جاري إنهاء المكالمة..."
  );


  stopTimer();


  callActive =
    false;


  const result =
    await saveCallTranscript();


  evidenceEnabled =
    false;


  stopMedia();


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


  setVisualState(
    "idle",
    "انتهت المكالمة"
  );


  if (
    result?.verification
      ?.realCallCandidate
    ===
    true
  ) {

    setCaption(
      "المكالمة انحفظت وتم تسجيل دليل الاتصال الحقيقي.",
      false
    );

  } else {

    setCaption(
      "المكالمة انحفظت.",
      false
    );
  }


  callId =
    null;


  callSecret =
    null;


  currentContinuity =
    null;


  pendingGreeting =
    false;


  endingCall =
    false;
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
      document.visibilityState
      !==
      "visible"
    ) {

      return;
    }


    if (
      callActive
      &&
      remoteAudio
    ) {

      try {

        // Re-assert mute before resuming the remote stream.
        if (
          isUnifiedVoiceEnabled()
          &&
          unifiedVoiceReady
        ) {

          remoteAudio.muted =
            true;


          remoteAudioMutedForUnifiedVoice =
            true;
        }


        await remoteAudio.play();


      } catch {}
    }


    if (
      callActive
      &&
      !wakeLock
    ) {

      requestWakeLock()
        .catch(
          () => {}
        );
    }
  }
);


// =========================================================
// INITIALIZE
// =========================================================

async function initializePage() {

  await loadUnifiedVoiceConfig();


  createAudioOutputButton();


  setVisualState(
    "idle",
    "جاهز للمكالمة"
  );


  setCaption(
    "اضغط ابدأ، واحكي معه طبيعي.",
    false
  );


  const health =
    await loadAgentHealth();


  if (
    health?.provider
    &&
    health.provider
    !==
    "openai"
  ) {

    showError(
      (
        "Provider غير صحيح: "
        +
        cleanText(
          health.provider
        )
      )
    );


    if (
      startCallButton
    ) {

      startCallButton.disabled =
        true;
    }


    return;
  }


  if (
    health?.transport
    &&
    health.transport
    !==
    "webrtc"
  ) {

    showError(
      "الخدمة ليست على WebRTC."
    );


    if (
      startCallButton
    ) {

      startCallButton.disabled =
        true;
    }


    return;
  }


  setVisualState(
    "idle",
    (
      agentLabel()
      +
      " جاهز للمكالمة"
    )
  );


  setCaption(
    (
      "اضغط ابدأ واحكي مع "
      +
      agentLabel()
      +
      " طبيعي."
    ),
    false
  );


  console.log(
    "=============================================="
  );


  console.log(
    " XPAND AGENT LIVE CALL UI V2.5"
  );


  console.log(
    " OPENAI REALTIME / WEBRTC + GEMINI IAPETUS"
  );


  console.log(
    " OPENAI REMOTE AUDIO MUTED IN UNIFIED MODE"
  );


  console.log(
    "=============================================="
  );


  console.log(
    (
      "🤖 Agent: "
      +
      agentLabel()
    )
  );


  console.log(
    (
      "🆔 Agent ID: "
      +
      runtimeAgentId
    )
  );


  console.log(
    (
      "🧠 Provider: OPENAI | "
      +
      runtimeModel
    )
  );


  console.log(
    (
      "🎙️ Unified Voice Flag: "
      +
      String(
        isUnifiedVoiceEnabled()
      )
    )
  );


  console.log(
    "✅ Microphone -> WebRTC"
  );


  console.log(
    "✅ OpenAI Realtime processing preserved"
  );


  console.log(
    "✅ Gemini Iapetus playback supported"
  );


  console.log(
    "✅ OpenAI remote audio muted when Iapetus ready"
  );


  console.log(
    "✅ OpenAI server VAD / interruption"
  );


  console.log(
    "✅ OpenAI live transcription"
  );


  console.log(
    "✅ Remote SDP normalization: CRLF SAFE"
  );


  console.log(
    "✅ Final SDP CRLF preserved"
  );


  console.log(
    "✅ callActive only after remote SDP"
  );


  console.log(
    "🔒 No OpenAI API key in browser"
  );


  console.log(
    "🔒 No Gemini API key in browser"
  );


  console.log(
    "🔒 No XPAND personal memory"
  );
}


// =========================================================
// START PAGE
// =========================================================

initializePage()
  .catch(
    error => {

      console.error(
        "Page initialization:",
        error
      );


      showError(
        "صار خلل أثناء تجهيز صفحة المكالمة."
      );
    }
  );


// =========================================================
// END
// =========================================================
