// ======================================================
// XPAND UNIFIED CALL SERVER V7.0
//
// ONE XPAND
//
// Unified:
// - Telegram text
// - Telegram voice
// - Live call
// - Shared PostgreSQL memory
// - Shared conversation history
// - Shared primary user: Ihab
// - Shared voice configuration
//
// Live-call features:
// - Real-time call turn persistence
// - Persistent-memory learning queue
// - Send messages/links from call to Telegram
// - Reminders
// - Web search
// - Desktop control
// - Chrome direct control
//
// Compatibility:
// Legacy KEMO_* environment variable names are supported.
// ======================================================

import express from "express";
import pg from "pg";
import crypto from "node:crypto";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const { Pool } = pg;


// ======================================================
// IDENTITY
// ======================================================

const AGENT_NAME = "XPAND";
const PRIMARY_USER_NAME = "إيهاب";
const COMPANY_NAME = "XPAND";

const SERVER_VERSION = "7.0-unified-xpand";


// ======================================================
// ENV
// ======================================================

const PORT = Number(
  process.env.PORT || 3000
);

const TELEGRAM_BOT_TOKEN = String(
  process.env.TELEGRAM_BOT_TOKEN || ""
).trim();

const TELEGRAM_ALLOWED_USER_ID = String(
  process.env.TELEGRAM_ALLOWED_USER_ID || ""
).trim();

const GEMINI_API_KEY = String(
  process.env.GEMINI_API_KEY || ""
).trim();

const DATABASE_URL = String(
  process.env.DATABASE_URL || ""
).trim();

const TAVILY_API_KEY = String(
  process.env.TAVILY_API_KEY || ""
).trim();

const XPAND_TIMEZONE = String(
  process.env.XPAND_TIMEZONE
  ||
  process.env.KEMO_TIMEZONE
  ||
  "Asia/Hebron"
).trim();

const LIVE_MODEL = String(
  process.env.XPAND_LIVE_MODEL
  ||
  process.env.KEMO_LIVE_MODEL
  ||
  "gemini-3.1-flash-live-preview"
).trim();

//
// One technical voice identity for all channels.
//
// Preferred:
// XPAND_VOICE_ID
//
// Compatibility:
// KEMO_VOICE / KEMO_LIVE_VOICE
//
const XPAND_VOICE_ID = String(
  process.env.XPAND_VOICE_ID
  ||
  process.env.KEMO_VOICE
  ||
  process.env.KEMO_LIVE_VOICE
  ||
  "Iapetus"
).trim();

const TOOL_MODEL = String(
  process.env.XPAND_TOOL_MODEL
  ||
  process.env.KEMO_TOOL_MODEL
  ||
  "gemini-3.5-flash-lite"
).trim();

const DESKTOP_URL = String(
  process.env.XPAND_DESKTOP_URL
  ||
  process.env.KEMO_DESKTOP_URL
  ||
  ""
)
  .trim()
  .replace(/\/+$/g, "");

const DESKTOP_KEY = String(
  process.env.XPAND_DESKTOP_KEY
  ||
  process.env.KEMO_DESKTOP_KEY
  ||
  ""
).trim();

const DESKTOP_DEVICE_ID = String(
  process.env.XPAND_DESKTOP_DEVICE_ID
  ||
  process.env.KEMO_DESKTOP_DEVICE_ID
  ||
  "main-pc"
).trim();

const CALL_CONTINUITY_MINUTES = Math.max(
  1,
  Number(
    process.env.XPAND_CALL_CONTINUITY_MINUTES
    ||
    process.env.KEMO_CALL_CONTINUITY_MINUTES
    ||
    15
  ) || 15
);

const DESKTOP_SYNC_TIMEOUT_MS = 30000;


// ======================================================
// PATHS
// ======================================================

const __filename =
  fileURLToPath(import.meta.url);

const __dirname =
  path.dirname(__filename);

const DIST_INDEX =
  path.join(
    __dirname,
    "dist",
    "index.html"
  );

const ROOT_INDEX =
  path.join(
    __dirname,
    "index.html"
  );

const STATIC_DIR =
  fs.existsSync(DIST_INDEX)
    ? path.join(__dirname, "dist")
    : __dirname;

const INDEX_FILE =
  fs.existsSync(DIST_INDEX)
    ? DIST_INDEX
    : ROOT_INDEX;


// ======================================================
// DATABASE
// ======================================================

const pool =
  new Pool({
    connectionString: DATABASE_URL,
    max: 8,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 10000
  });


// ======================================================
// HELPERS
// ======================================================

function cleanText(
  value,
  maxLength = 4000
) {
  return String(
    value ?? ""
  )
    .replace(/\u0000/g, "")
    .trim()
    .slice(0, maxLength);
}


function normalizeArabic(
  value
) {
  return String(
    value || ""
  )
    .toLowerCase()
    .replace(/[أإآ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .replace(/[\u064B-\u065F]/g, "")
    .replace(/[^\p{L}\p{N}_.\s:/-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}


function containsAny(
  text,
  markers
) {
  const source =
    normalizeArabic(text);

  return markers.some(
    marker =>
      source.includes(
        normalizeArabic(marker)
      )
  );
}


function clamp(
  value,
  min,
  max
) {
  return Math.max(
    min,
    Math.min(max, value)
  );
}


function sha256(
  value
) {
  return crypto
    .createHash("sha256")
    .update(
      String(value || "")
    )
    .digest("hex");
}


// ======================================================
// SENSITIVE ACTIONS
// ======================================================

function actionNeedsConfirmation(
  text
) {
  return containsAny(
    text,
    [
      "ادفع",
      "دفع",
      "pay",
      "payment",
      "purchase",
      "اشتري",
      "شراء",
      "checkout",

      "احذف",
      "حذف",
      "delete",
      "remove permanently",

      "ارسل",
      "ابعث",
      "ابعت",
      "send",
      "send message",
      "send email",

      "انشر",
      "نشر",
      "publish",
      "post",

      "submit",
      "قدم الطلب",
      "تقديم الطلب",

      "create account",
      "انشئ حساب",
      "اعمل حساب",

      "transfer",
      "تحويل",
      "حول المصاري"
    ]
  );
}


// ======================================================
// TIME
// ======================================================

function localIsoString(
  date = new Date()
) {
  const formatter =
    new Intl.DateTimeFormat(
      "en-CA",
      {
        timeZone: XPAND_TIMEZONE,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hourCycle: "h23"
      }
    );

  const parts = {};

  for (
    const part
    of formatter.formatToParts(date)
  ) {
    if (
      part.type !== "literal"
    ) {
      parts[part.type] =
        part.value;
    }
  }

  return (
    `${parts.year}-${parts.month}-${parts.day}`
    +
    `T${parts.hour}:${parts.minute}:${parts.second}`
  );
}


function humanLocalTime(
  date = new Date()
) {
  try {
    return new Intl.DateTimeFormat(
      "ar-PS",
      {
        timeZone: XPAND_TIMEZONE,
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
      }
    ).format(date);

  } catch {
    return localIsoString(date);
  }
}


// ======================================================
// DATABASE INIT
// ======================================================

async function initDatabase() {

  await pool.query(`
    CREATE TABLE IF NOT EXISTS messages (
      id BIGSERIAL PRIMARY KEY,
      chat_id BIGINT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS
    idx_messages_chat_id_id
    ON messages(chat_id, id DESC);
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS memories (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      category TEXT NOT NULL DEFAULT 'other',
      content TEXT NOT NULL,
      importance SMALLINT NOT NULL DEFAULT 3,
      source TEXT NOT NULL DEFAULT 'auto',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS profile_facts (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      fact_key TEXT NOT NULL,
      fact_value TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, fact_key)
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS lessons (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      content TEXT NOT NULL,
      active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS call_sessions (
      id TEXT PRIMARY KEY,
      telegram_user_id BIGINT NOT NULL,
      session_secret_hash TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'active',
      transcript JSONB NOT NULL DEFAULT '[]'::jsonb,
      started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      ended_at TIMESTAMPTZ
    );
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS
    idx_call_sessions_user_started
    ON call_sessions(
      telegram_user_id,
      started_at DESC
    );
  `);


  //
  // One record for every completed live-call turn.
  //
  // This makes call → Telegram memory persistence
  // real-time and idempotent.
  //
  await pool.query(`
    CREATE TABLE IF NOT EXISTS call_turns (
      id BIGSERIAL PRIMARY KEY,
      call_id TEXT NOT NULL,
      turn_id TEXT NOT NULL,
      user_id BIGINT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      message_id BIGINT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(call_id, turn_id)
    );
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS
    idx_call_turns_call_created
    ON call_turns(
      call_id,
      created_at ASC
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS scheduled_jobs (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      chat_id BIGINT NOT NULL,
      job_type TEXT NOT NULL DEFAULT 'reminder',
      title TEXT,
      message TEXT NOT NULL,
      run_at TIMESTAMPTZ NOT NULL,
      timezone TEXT NOT NULL DEFAULT 'Asia/Hebron',
      status TEXT NOT NULL DEFAULT 'pending',
      source TEXT NOT NULL DEFAULT 'user',
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      attempts INTEGER NOT NULL DEFAULT 0,
      max_attempts INTEGER NOT NULL DEFAULT 5,
      next_attempt_at TIMESTAMPTZ,
      locked_at TIMESTAMPTZ,
      sent_at TIMESTAMPTZ,
      cancelled_at TIMESTAMPTZ,
      last_error TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS kemo_events (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      chat_id BIGINT,
      event_type TEXT NOT NULL,
      content TEXT NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS kemo_config (
      config_key TEXT PRIMARY KEY,
      config_value TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS dialect_terms (
      user_id BIGINT NOT NULL,
      term TEXT NOT NULL,
      use_count INTEGER NOT NULL DEFAULT 1,
      first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY(user_id, term)
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS canonical_facts (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      fact_key TEXT NOT NULL,
      subject TEXT NOT NULL DEFAULT '',
      predicate TEXT NOT NULL DEFAULT '',
      category TEXT NOT NULL DEFAULT 'other',
      value_json JSONB NOT NULL DEFAULT 'null'::jsonb,
      value_text TEXT NOT NULL DEFAULT '',
      search_text TEXT NOT NULL DEFAULT '',
      confidence SMALLINT NOT NULL DEFAULT 100,
      source TEXT NOT NULL DEFAULT 'user',
      source_message_id BIGINT,
      source_text TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, fact_key)
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS memory_archive (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      source_type TEXT NOT NULL,
      source_id BIGINT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      normalized_content TEXT NOT NULL DEFAULT '',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, source_type, source_id)
    );
  `);


  await pool.query(`
    CREATE TABLE IF NOT EXISTS memory_learning_jobs (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      chat_id BIGINT NOT NULL,
      source_message_id BIGINT,
      source_hash TEXT NOT NULL,
      text TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      attempts INTEGER NOT NULL DEFAULT 0,
      next_attempt_at TIMESTAMPTZ,
      locked_at TIMESTAMPTZ,
      last_error TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(user_id, source_hash)
    );
  `);


  console.log(
    "✅ XPAND shared database ready"
  );
}


// ======================================================
// SAFE DB
// ======================================================

async function safeRows(
  query,
  params = []
) {
  try {
    const result =
      await pool.query(
        query,
        params
      );

    return result.rows;

  } catch (error) {
    console.log(
      "⚠️ DB:",
      error.message
    );

    return [];
  }
}


// ======================================================
// MASTER PROMPT
// ======================================================

let masterPromptCache = {
  prompt: "",
  version: "",
  loadedAt: 0
};


async function loadSharedMasterPrompt(
  required = false
) {

  if (
    masterPromptCache.prompt
    &&
    Date.now()
    -
    masterPromptCache.loadedAt
    <
    60000
  ) {
    return {
      ok: true,
      prompt:
        masterPromptCache.prompt,
      version:
        masterPromptCache.version
    };
  }


  const [
    promptRows,
    versionRows
  ] =
    await Promise.all([

      safeRows(`
        SELECT config_value
        FROM kemo_config
        WHERE config_key =
          'master_system_prompt'
        LIMIT 1
      `),

      safeRows(`
        SELECT config_value
        FROM kemo_config
        WHERE config_key =
          'master_system_prompt_version'
        LIMIT 1
      `)

    ]);


  const prompt =
    cleanText(
      promptRows[0]?.config_value,
      100000
    );

  const version =
    cleanText(
      versionRows[0]?.config_value,
      300
    );


  if (
    required
    &&
    !prompt
  ) {
    throw new Error(
      "Shared master_system_prompt missing"
    );
  }


  if (prompt) {
    masterPromptCache = {
      prompt,
      version,
      loadedAt: Date.now()
    };
  }


  return {
    ok: Boolean(prompt),
    prompt,
    version
  };
}


// ======================================================
// DIALECT
// ======================================================

async function loadDialectProfile(
  userId
) {

  const rows =
    await safeRows(
      `
      SELECT
        term,
        use_count
      FROM dialect_terms
      WHERE user_id = $1
      ORDER BY
        use_count DESC,
        last_seen_at DESC
      LIMIT 20
      `,
      [
        userId
      ]
    );


  if (!rows.length) {
    return {
      context:
        "لا توجد بصمة لهجة إضافية محفوظة."
    };
  }


  return {
    context:
      [
        "=== تعبيرات إيهاب ===",

        ...rows.map(
          row =>
            "- "
            +
            cleanText(
              row.term,
              100
            )
        )
      ].join("\n")
  };
}


// ======================================================
// TELEGRAM WEB APP AUTH
// ======================================================

function verifyTelegramInitData(
  initData
) {

  if (
    typeof initData !== "string"
    ||
    !initData.trim()
  ) {
    throw new Error(
      "Telegram initData missing"
    );
  }


  const params =
    new URLSearchParams(
      initData
    );


  const receivedHash =
    params.get("hash");


  if (!receivedHash) {
    throw new Error(
      "Telegram hash missing"
    );
  }


  params.delete("hash");


  const dataCheckString =
    [...params.entries()]
      .sort(
        ([a], [b]) =>
          a.localeCompare(b)
      )
      .map(
        ([key, value]) =>
          `${key}=${value}`
      )
      .join("\n");


  const secretKey =
    crypto
      .createHmac(
        "sha256",
        "WebAppData"
      )
      .update(
        TELEGRAM_BOT_TOKEN
      )
      .digest();


  const calculatedHash =
    crypto
      .createHmac(
        "sha256",
        secretKey
      )
      .update(
        dataCheckString
      )
      .digest("hex");


  const a =
    Buffer.from(
      receivedHash,
      "hex"
    );

  const b =
    Buffer.from(
      calculatedHash,
      "hex"
    );


  if (
    !a.length
    ||
    a.length !== b.length
    ||
    !crypto.timingSafeEqual(
      a,
      b
    )
  ) {
    throw new Error(
      "Telegram signature invalid"
    );
  }


  const rawUser =
    params.get("user");


  if (!rawUser) {
    throw new Error(
      "Telegram user missing"
    );
  }


  const user =
    JSON.parse(rawUser);


  const userId =
    String(
      user?.id || ""
    );


  if (!userId) {
    throw new Error(
      "Telegram user id missing"
    );
  }


  if (
    TELEGRAM_ALLOWED_USER_ID
    &&
    userId !==
      TELEGRAM_ALLOWED_USER_ID
  ) {
    throw new Error(
      "Unauthorized Telegram user"
    );
  }


  return {
    userId,
    user
  };
}


// ======================================================
// CALL AUTH
// ======================================================

function createCallSecret() {
  return crypto
    .randomBytes(32)
    .toString("base64url");
}


function hashCallSecret(
  value
) {
  return sha256(value);
}


function secureEqualHex(
  a,
  b
) {
  try {
    const left =
      Buffer.from(a, "hex");

    const right =
      Buffer.from(b, "hex");

    return (
      left.length > 0
      &&
      left.length === right.length
      &&
      crypto.timingSafeEqual(
        left,
        right
      )
    );

  } catch {
    return false;
  }
}


async function getCallSession(
  callId,
  callSecret,
  requireActive = true
) {

  const rows =
    await safeRows(
      `
      SELECT
        id,
        telegram_user_id,
        session_secret_hash,
        status
      FROM call_sessions
      WHERE id = $1
      LIMIT 1
      `,
      [
        cleanText(
          callId,
          200
        )
      ]
    );


  const row =
    rows[0];


  if (!row) {
    throw new Error(
      "Call session not found"
    );
  }


  if (
    !secureEqualHex(
      hashCallSecret(
        cleanText(
          callSecret,
          500
        )
      ),
      row.session_secret_hash
    )
  ) {
    throw new Error(
      "Invalid call secret"
    );
  }


  if (
    requireActive
    &&
    row.status !== "active"
  ) {
    throw new Error(
      "Call session is closed"
    );
  }


  return {
    callId:
      row.id,

    userId:
      String(
        row.telegram_user_id
      ),

    status:
      row.status
  };
}


// ======================================================
// SHARED MESSAGES
// ======================================================

async function saveMessageWithArchive(
  db,
  userId,
  role,
  content
) {

  const text =
    cleanText(
      content,
      12000
    );


  if (!text) {
    return null;
  }


  const inserted =
    await db.query(
      `
      INSERT INTO messages
      (
        chat_id,
        role,
        content
      )
      VALUES (
        $1,
        $2,
        $3
      )
      RETURNING
        id,
        created_at
      `,
      [
        userId,
        role,
        text
      ]
    );


  const messageId =
    Number(
      inserted.rows[0].id
    );


  await db.query(
    `
    INSERT INTO memory_archive
    (
      user_id,
      source_type,
      source_id,
      role,
      content,
      normalized_content,
      created_at
    )
    VALUES (
      $1,
      'message',
      $2,
      $3,
      $4,
      $5,
      $6
    )
    ON CONFLICT(
      user_id,
      source_type,
      source_id
    )
    DO NOTHING
    `,
    [
      userId,
      messageId,
      role,
      text,
      normalizeArabic(text),
      inserted.rows[0]
        .created_at
    ]
  );


  return messageId;
}


async function saveSharedMessage(
  userId,
  role,
  content
) {
  return await saveMessageWithArchive(
    pool,
    userId,
    role,
    content
  );
}


// ======================================================
// MEMORY LEARNING QUEUE
// ======================================================

async function enqueueMemoryLearning(
  db,
  userId,
  text,
  sourceMessageId
) {

  const clean =
    cleanText(
      text,
      8000
    );


  if (!clean) {
    return;
  }


  const sourceHash =
    sha256(
      String(userId)
      +
      "|"
      +
      normalizeArabic(clean)
    );


  await db.query(
    `
    INSERT INTO memory_learning_jobs
    (
      user_id,
      chat_id,
      source_message_id,
      source_hash,
      text,
      status
    )
    VALUES (
      $1,
      $1,
      $2,
      $3,
      $4,
      'pending'
    )
    ON CONFLICT(
      user_id,
      source_hash
    )
    DO NOTHING
    `,
    [
      userId,
      sourceMessageId,
      sourceHash,
      clean
    ]
  );
}


// ======================================================
// REAL-TIME CALL TURN PERSISTENCE
// ======================================================

async function persistCallTurn(
  session,
  {
    turnId,
    role,
    text
  }
) {

  const normalizedRole =
    role === "assistant"
      ? "assistant"
      : "user";


  const clean =
    cleanText(
      text,
      8000
    );


  if (!clean) {
    return {
      ok: true,
      saved: false,
      reason: "empty"
    };
  }


  const safeTurnId =
    cleanText(
      turnId
      ||
      sha256(
        normalizedRole
        +
        "|"
        +
        clean
      ).slice(0, 32),
      200
    );


  const client =
    await pool.connect();


  try {
    await client.query("BEGIN");


    const reserved =
      await client.query(
        `
        INSERT INTO call_turns
        (
          call_id,
          turn_id,
          user_id,
          role,
          content
        )
        VALUES (
          $1,
          $2,
          $3,
          $4,
          $5
        )
        ON CONFLICT(
          call_id,
          turn_id
        )
        DO NOTHING
        RETURNING id
        `,
        [
          session.callId,
          safeTurnId,
          session.userId,
          normalizedRole,
          clean
        ]
      );


    //
    // Already saved.
    //
    if (
      !reserved.rows.length
    ) {
      await client.query("COMMIT");

      return {
        ok: true,
        saved: false,
        duplicate: true
      };
    }


    const messageId =
      await saveMessageWithArchive(
        client,
        session.userId,
        normalizedRole,
        clean
      );


    await client.query(
      `
      UPDATE call_turns
      SET message_id = $3
      WHERE
        call_id = $1
        AND turn_id = $2
      `,
      [
        session.callId,
        safeTurnId,
        messageId
      ]
    );


    //
    // User speech enters the same memory-learning queue
    // used by Telegram text/voice.
    //
    if (
      normalizedRole === "user"
    ) {
      await enqueueMemoryLearning(
        client,
        session.userId,
        clean,
        messageId
      );
    }


    await client.query("COMMIT");


    return {
      ok: true,
      saved: true,
      messageId
    };


  } catch (error) {

    try {
      await client.query(
        "ROLLBACK"
      );
    } catch {}


    throw error;


  } finally {
    client.release();
  }
}


// ======================================================
// PERSISTENT MEMORY
// ======================================================

async function savePersistentMemory(
  userId,
  content,
  {
    category = "other",
    importance = 4,
    source = "live_call"
  } = {}
) {

  const text =
    cleanText(
      content,
      5000
    );


  if (!text) {
    return null;
  }


  const existing =
    await safeRows(
      `
      SELECT id
      FROM memories
      WHERE
        user_id = $1
        AND LOWER(content) =
            LOWER($2)
      LIMIT 1
      `,
      [
        userId,
        text
      ]
    );


  if (existing.length) {

    await pool.query(
      `
      UPDATE memories
      SET
        importance =
          GREATEST(
            importance,
            $1
          ),
        updated_at =
          NOW()
      WHERE id = $2
      `,
      [
        importance,
        existing[0].id
      ]
    );


    return Number(
      existing[0].id
    );
  }


  const result =
    await pool.query(
      `
      INSERT INTO memories
      (
        user_id,
        category,
        content,
        importance,
        source
      )
      VALUES (
        $1,
        $2,
        $3,
        $4,
        $5
      )
      RETURNING id
      `,
      [
        userId,
        category,
        text,
        importance,
        source
      ]
    );


  return Number(
    result.rows[0].id
  );
}


async function recallMemory(
  userId,
  query
) {

  const cleanQuery =
    cleanText(
      query,
      700
    );


  const memories =
    await safeRows(
      `
      SELECT
        category,
        content,
        importance,
        updated_at
      FROM memories
      WHERE
        user_id = $1
        AND content ILIKE $2
      ORDER BY
        importance DESC,
        updated_at DESC
      LIMIT 15
      `,
      [
        userId,
        `%${cleanQuery}%`
      ]
    );


  const archive =
    await safeRows(
      `
      SELECT
        role,
        content,
        created_at
      FROM memory_archive
      WHERE
        user_id = $1
        AND normalized_content
          ILIKE $2
      ORDER BY
        created_at DESC
      LIMIT 15
      `,
      [
        userId,
        `%${normalizeArabic(
          cleanQuery
        )}%`
      ]
    );


  return {
    ok: true,
    query:
      cleanQuery,
    memories,
    archiveEvidence:
      archive
  };
}


// ======================================================
// MEMORY CONTEXT
// ======================================================

async function buildMemoryContext(
  userId
) {

  const [
    canonical,
    profile,
    memories,
    messages,
    reminders
  ] =
    await Promise.all([

      safeRows(
        `
        SELECT
          fact_key,
          predicate,
          value_text
        FROM canonical_facts
        WHERE
          user_id = $1
          AND status = 'active'
        ORDER BY updated_at DESC
        LIMIT 70
        `,
        [
          userId
        ]
      ),


      safeRows(
        `
        SELECT
          fact_key,
          fact_value
        FROM profile_facts
        WHERE user_id = $1
        ORDER BY updated_at DESC
        LIMIT 30
        `,
        [
          userId
        ]
      ),


      safeRows(
        `
        SELECT
          category,
          content
        FROM memories
        WHERE user_id = $1
        ORDER BY
          importance DESC,
          updated_at DESC
        LIMIT 30
        `,
        [
          userId
        ]
      ),


      safeRows(
        `
        SELECT
          role,
          content,
          created_at
        FROM messages
        WHERE chat_id = $1
        ORDER BY id DESC
        LIMIT 40
        `,
        [
          userId
        ]
      ),


      safeRows(
        `
        SELECT
          id,
          message,
          run_at
        FROM scheduled_jobs
        WHERE
          user_id = $1
          AND status = 'pending'
        ORDER BY run_at ASC
        LIMIT 10
        `,
        [
          userId
        ]
      )

    ]);


  const sections = [];


  if (canonical.length) {
    sections.push(
      [
        "=== CANONICAL FACTS — إيهاب ===",

        ...canonical.map(
          item =>
            (
              `- ${item.fact_key}: `
              +
              `${item.predicate || ""} = `
              +
              cleanText(
                item.value_text,
                800
              )
            )
        )
      ].join("\n")
    );
  }


  if (profile.length) {
    sections.push(
      [
        "=== ملف إيهاب ===",

        ...profile.map(
          item =>
            (
              `- ${item.fact_key}: `
              +
              cleanText(
                item.fact_value,
                800
              )
            )
        )
      ].join("\n")
    );
  }


  if (memories.length) {
    sections.push(
      [
        "=== ذاكرة XPAND المشتركة ===",

        ...memories.map(
          item =>
            (
              `- [${item.category}] `
              +
              cleanText(
                item.content,
                900
              )
            )
        )
      ].join("\n")
    );
  }


  if (messages.length) {
    sections.push(
      [
        "=== آخر المحادثة الموحدة من جميع القنوات ===",

        ...[
          ...messages
        ]
          .reverse()
          .map(
            item =>
              (
                item.role ===
                "assistant"
                  ?
                  "XPAND"
                  :
                  "إيهاب"
              )
              +
              ": "
              +
              cleanText(
                item.content,
                1200
              )
          )
      ].join("\n")
    );
  }


  if (reminders.length) {
    sections.push(
      [
        "=== التذكيرات النشطة ===",

        ...reminders.map(
          item =>
            (
              `- #${item.id}: `
              +
              cleanText(
                item.message,
                1000
              )
              +
              " | "
              +
              humanLocalTime(
                new Date(
                  item.run_at
                )
              )
            )
        )
      ].join("\n")
    );
  }


  return (
    sections.join("\n\n")
    ||
    "لا توجد ذاكرة إضافية محفوظة حتى الآن."
  ).slice(
    0,
    36000
  );
}


// ======================================================
// CONTINUITY
// ======================================================

async function getConversationContinuity(
  userId
) {

  const [
    messages,
    calls
  ] =
    await Promise.all([

      safeRows(
        `
        SELECT created_at
        FROM messages
        WHERE chat_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        `,
        [
          userId
        ]
      ),


      safeRows(
        `
        SELECT
          COALESCE(
            ended_at,
            started_at
          ) AS interaction_at
        FROM call_sessions
        WHERE
          telegram_user_id = $1
          AND status = 'ended'
        ORDER BY
          COALESCE(
            ended_at,
            started_at
          ) DESC
        LIMIT 1
        `,
        [
          userId
        ]
      )

    ]);


  const dates = [];


  if (
    messages[0]?.created_at
  ) {
    dates.push(
      new Date(
        messages[0]
          .created_at
      )
    );
  }


  if (
    calls[0]?.interaction_at
  ) {
    dates.push(
      new Date(
        calls[0]
          .interaction_at
      )
    );
  }


  dates.sort(
    (a, b) =>
      b.getTime()
      -
      a.getTime()
  );


  const last =
    dates[0];


  if (!last) {
    return {
      isContinuation:
        false,

      shouldGreet:
        true,

      gapMinutes:
        null
    };
  }


  const gapMinutes =
    (
      Date.now()
      -
      last.getTime()
    )
    /
    60000;


  return {
    isContinuation:
      gapMinutes <
      CALL_CONTINUITY_MINUTES,

    shouldGreet:
      gapMinutes >=
      CALL_CONTINUITY_MINUTES,

    gapMinutes:
      Math.round(
        gapMinutes * 10
      ) / 10
  };
}


// ======================================================
// EVENTS
// ======================================================

async function recordEvent(
  userId,
  chatId,
  eventType,
  content,
  metadata = {}
) {

  try {
    await pool.query(
      `
      INSERT INTO kemo_events
      (
        user_id,
        chat_id,
        event_type,
        content,
        metadata
      )
      VALUES (
        $1,
        $2,
        $3,
        $4,
        $5::jsonb
      )
      `,
      [
        userId,
        chatId,
        cleanText(
          eventType,
          100
        ),
        cleanText(
          content,
          5000
        ),
        JSON.stringify(
          metadata || {}
        )
      ]
    );

  } catch (error) {
    console.log(
      "⚠️ Event:",
      error.message
    );
  }
}


// ======================================================
// GEMINI EPHEMERAL TOKEN
// ======================================================

async function createEphemeralToken() {

  const expireTime =
    new Date(
      Date.now()
      +
      30 * 60 * 1000
    ).toISOString();


  const newSessionExpireTime =
    new Date(
      Date.now()
      +
      2 * 60 * 1000
    ).toISOString();


  const response =
    await fetch(
      "https://generativelanguage.googleapis.com/v1beta/auth_tokens",
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",

          "x-goog-api-key":
            GEMINI_API_KEY
        },

        body:
          JSON.stringify({
            uses: 1,
            expireTime,
            newSessionExpireTime
          })
      }
    );


  const data =
    await response.json();


  if (
    !response.ok
    ||
    !data?.name
  ) {
    throw new Error(
      data?.error?.message
      ||
      "Gemini ephemeral token failed"
    );
  }


  return data.name;
}


// ======================================================
// GEMINI VISION FALLBACK
// ======================================================

function toolModels() {
  return [
    TOOL_MODEL,
    "gemini-3.7-flash",
    "gemini-3.5-flash"
  ].filter(
    (
      item,
      index,
      array
    ) =>
      item
      &&
      array.indexOf(item)
      === index
  );
}


function extractGeminiText(
  data
) {
  return (
    data?.candidates?.[0]
      ?.content?.parts
    ||
    []
  )
    .map(
      part =>
        part?.text || ""
    )
    .join("\n")
    .trim();
}


function parseJsonText(
  value
) {

  const text =
    cleanText(
      value,
      20000
    )
      .replace(
        /^```(?:json)?\s*/i,
        ""
      )
      .replace(
        /\s*```$/,
        ""
      )
      .trim();


  try {
    return JSON.parse(text);

  } catch {}


  const start =
    text.indexOf("{");

  const end =
    text.lastIndexOf("}");


  if (
    start >= 0
    &&
    end > start
  ) {
    return JSON.parse(
      text.slice(
        start,
        end + 1
      )
    );
  }


  throw new Error(
    "Invalid Gemini JSON"
  );
}


async function callGeminiVisionJson(
  imageBase64,
  prompt
) {

  let lastError = null;


  for (
    const model
    of toolModels()
  ) {
    try {

      const response =
        await fetch(
          (
            "https://generativelanguage.googleapis.com/"
            +
            "v1beta/models/"
            +
            encodeURIComponent(model)
            +
            ":generateContent"
          ),
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",

              "x-goog-api-key":
                GEMINI_API_KEY
            },

            body:
              JSON.stringify({
                contents: [
                  {
                    role: "user",

                    parts: [
                      {
                        text: prompt
                      },

                      {
                        inlineData: {
                          mimeType:
                            "image/png",

                          data:
                            imageBase64
                        }
                      }
                    ]
                  }
                ],

                generationConfig: {
                  temperature: 0,
                  maxOutputTokens: 1200,
                  responseMimeType:
                    "application/json"
                }
              })
          }
        );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data?.error?.message
          ||
          "Vision failed"
        );
      }


      return parseJsonText(
        extractGeminiText(data)
      );


    } catch (error) {
      lastError = error;

      console.log(
        (
          "⚠️ Vision "
          +
          model
          +
          ": "
          +
          error.message
        )
      );
    }
  }


  throw (
    lastError
    ||
    new Error(
      "Vision failed"
    )
  );
}


// ======================================================
// TELEGRAM
// ======================================================

async function telegramRequest(
  method,
  payload
) {

  const response =
    await fetch(
      (
        "https://api.telegram.org/bot"
        +
        TELEGRAM_BOT_TOKEN
        +
        "/"
        +
        method
      ),
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify(payload)
      }
    );


  const data =
    await response.json();


  if (
    !response.ok
    ||
    !data?.ok
  ) {
    throw new Error(
      data?.description
      ||
      "Telegram request failed"
    );
  }


  return data;
}


async function sendTelegramMessage(
  chatId,
  text
) {

  const clean =
    cleanText(
      text,
      12000
    );


  if (!clean) {
    throw new Error(
      "Telegram message is empty"
    );
  }


  for (
    let i = 0;
    i < clean.length;
    i += 4000
  ) {

    await telegramRequest(
      "sendMessage",
      {
        chat_id:
          chatId,

        text:
          clean.slice(
            i,
            i + 4000
          ),

        disable_web_page_preview:
          true
      }
    );
  }


  return {
    ok: true
  };
}


async function sendChatMessageFromCall(
  userId,
  args
) {

  const title =
    cleanText(
      args?.title,
      500
    );

  const message =
    cleanText(
      args?.message,
      8000
    );

  const url =
    cleanText(
      args?.url,
      4000
    );


  if (
    url
    &&
    !/^https?:\/\//i.test(url)
  ) {
    throw new Error(
      "Only http/https URLs are allowed"
    );
  }


  let finalText = "";


  if (message) {
    finalText = message;
  }


  if (
    title
    &&
    !finalText
  ) {
    finalText = title;
  }


  if (url) {

    if (!finalText) {
      finalText =
        "تفضل إيهاب، هذا الرابط اللي طلبته بالمكالمة:";
    }


    if (
      title
      &&
      !finalText.includes(title)
    ) {
      finalText +=
        "\n\n"
        +
        title;
    }


    finalText +=
      "\n"
      +
      url;
  }


  if (!finalText) {
    throw new Error(
      "Message or URL is required"
    );
  }


  await sendTelegramMessage(
    userId,
    finalText
  );


  //
  // The outgoing Telegram message is also part of
  // the unified conversation.
  //
  await saveSharedMessage(
    userId,
    "assistant",
    finalText
  );


  await recordEvent(
    userId,
    userId,
    "call_to_chat_message",
    finalText,
    {
      sourceChannel:
        cleanText(
          args?.source_channel
          ||
          "live_call",
          100
        ),

      url:
        url || null
    }
  );


  return {
    ok: true,
    sent: true,
    channel: "telegram",
    message: finalText,
    url:
      url || null
  };
}


// ======================================================
// SEARCH WEB
// ======================================================

async function searchWeb(
  query
) {

  if (!TAVILY_API_KEY) {
    throw new Error(
      "Tavily is not configured"
    );
  }


  const cleanQuery =
    cleanText(
      query,
      700
    );


  if (!cleanQuery) {
    throw new Error(
      "Search query missing"
    );
  }


  const response =
    await fetch(
      "https://api.tavily.com/search",
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",

          "Authorization":
            `Bearer ${TAVILY_API_KEY}`
        },

        body:
          JSON.stringify({
            query:
              cleanQuery,

            search_depth:
              "basic",

            max_results:
              5,

            include_answer:
              false,

            include_raw_content:
              false
          })
      }
    );


  const data =
    await response.json();


  if (!response.ok) {
    throw new Error(
      data?.detail
      ||
      "Web search failed"
    );
  }


  return {
    ok: true,

    results:
      (
        Array.isArray(
          data?.results
        )
          ?
          data.results
          :
          []
      ).slice(0, 5)
  };
}


// ======================================================
// REMINDERS
// ======================================================

async function localTimestampToUtc(
  value
) {

  const result =
    await pool.query(
      `
      SELECT
        (
          $1::timestamp
          AT TIME ZONE $2
        ) AS utc_time
      `,
      [
        cleanText(
          value,
          50
        ),

        XPAND_TIMEZONE
      ]
    );


  return new Date(
    result.rows[0]
      .utc_time
  );
}


async function createReminder(
  userId,
  callId,
  args
) {

  const reason =
    cleanText(
      args?.reason,
      1500
    );


  if (!reason) {
    throw new Error(
      "Reminder reason missing"
    );
  }


  let runAt;


  if (
    args?.delaySeconds !==
      undefined
  ) {

    const seconds =
      Number(
        args.delaySeconds
      );


    if (
      !Number.isFinite(seconds)
      ||
      seconds < 1
    ) {
      throw new Error(
        "Invalid reminder delay"
      );
    }


    runAt =
      new Date(
        Date.now()
        +
        seconds * 1000
      );


  } else if (
    args?.runAtLocal
  ) {

    runAt =
      await localTimestampToUtc(
        args.runAtLocal
      );


  } else {

    throw new Error(
      "Reminder time missing"
    );
  }


  const result =
    await pool.query(
      `
      INSERT INTO scheduled_jobs
      (
        user_id,
        chat_id,
        job_type,
        title,
        message,
        run_at,
        timezone,
        status,
        source,
        metadata
      )
      VALUES (
        $1,
        $1,
        'reminder',
        $2,
        $3,
        $4,
        $5,
        'pending',
        'live_call',
        $6::jsonb
      )
      RETURNING
        id,
        run_at
      `,
      [
        userId,

        cleanText(
          args?.title
          ||
          "تذكير",
          300
        ),

        cleanText(
          args?.message
          ||
          `إيهاب، تذكيرك: ${reason}`,
          2000
        ),

        runAt,

        XPAND_TIMEZONE,

        JSON.stringify({
          reason,
          callId,
          sourceChannel:
            "live_call"
        })
      ]
    );


  return {
    ok: true,

    jobId:
      Number(
        result.rows[0].id
      ),

    humanTime:
      humanLocalTime(
        new Date(
          result.rows[0]
            .run_at
        )
      )
  };
}


async function listReminders(
  userId
) {

  const rows =
    await safeRows(
      `
      SELECT
        id,
        title,
        message,
        run_at
      FROM scheduled_jobs
      WHERE
        user_id = $1
        AND status = 'pending'
      ORDER BY run_at ASC
      LIMIT 30
      `,
      [
        userId
      ]
    );


  return {
    ok: true,
    reminders:
      rows
  };
}


async function cancelReminder(
  userId,
  args
) {

  let rows = [];


  if (args?.jobId) {

    rows =
      await safeRows(
        `
        UPDATE scheduled_jobs
        SET
          status = 'cancelled',
          cancelled_at = NOW(),
          updated_at = NOW()
        WHERE
          user_id = $1
          AND id = $2
          AND status = 'pending'
        RETURNING id
        `,
        [
          userId,
          Number(
            args.jobId
          )
        ]
      );


  } else if (
    args?.latest
  ) {

    rows =
      await safeRows(
        `
        UPDATE scheduled_jobs
        SET
          status = 'cancelled',
          cancelled_at = NOW(),
          updated_at = NOW()
        WHERE id = (
          SELECT id
          FROM scheduled_jobs
          WHERE
            user_id = $1
            AND status = 'pending'
          ORDER BY created_at DESC
          LIMIT 1
        )
        RETURNING id
        `,
        [
          userId
        ]
      );
  }


  return {
    ok:
      rows.length > 0,

    cancelled:
      rows.length > 0
  };
}


// ======================================================
// DESKTOP BRIDGE
// ======================================================

function desktopConfigured() {
  return Boolean(
    DESKTOP_URL
    &&
    DESKTOP_KEY
  );
}


async function desktopFetch(
  endpoint,
  {
    method = "GET",
    body = null,
    authenticated = true,
    timeout = 15000
  } = {}
) {

  if (!DESKTOP_URL) {
    throw new Error(
      "Desktop URL is not configured"
    );
  }


  const controller =
    new AbortController();


  const timer =
    setTimeout(
      () =>
        controller.abort(),
      timeout
    );


  try {

    const headers = {
      "Accept":
        "application/json"
    };


    if (authenticated) {
      headers[
        "X-Kemo-Desktop-Key"
      ] =
        DESKTOP_KEY;
    }


    if (body !== null) {
      headers[
        "Content-Type"
      ] =
        "application/json";
    }


    const response =
      await fetch(
        DESKTOP_URL
        +
        endpoint,
        {
          method,
          headers,

          body:
            body === null
              ?
              undefined
              :
              JSON.stringify(
                body
              ),

          signal:
            controller.signal
        }
      );


    const raw =
      await response.text();


    let data = {};


    if (raw) {
      try {
        data =
          JSON.parse(raw);

      } catch {
        data = {
          raw
        };
      }
    }


    if (!response.ok) {
      throw new Error(
        data?.error
        ||
        `Desktop HTTP ${response.status}`
      );
    }


    return data;


  } catch (error) {

    if (
      error?.name ===
      "AbortError"
    ) {
      throw new Error(
        "Desktop request timed out"
      );
    }


    throw error;


  } finally {
    clearTimeout(timer);
  }
}


async function runDesktopCommand(
  action,
  args = {},
  timeoutMs =
    DESKTOP_SYNC_TIMEOUT_MS
) {

  const started =
    Date.now();


  const response =
    await desktopFetch(
      "/api/command-sync",
      {
        method: "POST",
        timeout:
          timeoutMs + 5000,

        body: {
          action,
          deviceId:
            DESKTOP_DEVICE_ID,
          args,
          timeoutMs
        }
      }
    );


  const elapsed =
    Date.now()
    -
    started;


  console.log(
    (
      "⚡ PC "
      +
      action
      +
      " | "
      +
      elapsed
      +
      "ms | "
      +
      (
        response?.transport
        ||
        "unknown"
      )
    )
  );


  if (
    response?.status ===
    "failed"
  ) {
    throw new Error(
      response?.result?.error
      ||
      response?.error
      ||
      "Desktop command failed"
    );
  }


  return {
    ...(
      response?.result
      ||
      {}
    ),

    _transport:
      response?.transport,

    _elapsedMs:
      elapsed
  };
}


async function desktopHealth() {

  if (!desktopConfigured()) {
    return {
      ok: false,
      configured: false
    };
  }


  try {
    return {
      ...await desktopFetch(
        "/api/health",
        {
          authenticated:
            false,

          timeout:
            5000
        }
      ),

      configured:
        true
    };


  } catch (error) {

    return {
      ok: false,
      configured: true,
      error:
        error.message
    };
  }
}


// ======================================================
// SCREENSHOT VISION
// ======================================================

async function inspectScreen(
  question
) {

  const screenshot =
    await runDesktopCommand(
      "screenshot",
      {},
      30000
    );


  const imageBase64 =
    cleanText(
      screenshot?.imageBase64,
      20000000
    );


  if (!imageBase64) {
    throw new Error(
      "Screenshot missing"
    );
  }


  const result =
    await callGeminiVisionJson(
      imageBase64,
      `
أنت ترى Screenshot الحالية فقط من كمبيوتر إيهاب.

سؤال إيهاب:
${cleanText(
  question,
  1000
)}

جاوب فقط حسب الصورة الحالية.
لا تعتمد على الذاكرة.
لا تخمن.

JSON:
{
  "answer": "جواب فلسطيني قصير ودقيق"
}
`
    );


  return {
    ok: true,

    screenAnalysis:
      cleanText(
        result?.answer,
        2500
      )
  };
}


// ======================================================
// LIVE RUNTIME RULES
//
// These are operational call rules.
// The personality itself comes from the shared
// master_system_prompt in PostgreSQL.
// ======================================================

const CALL_RUNTIME_RULES = `
==================================================
XPAND UNIFIED LIVE CALL RUNTIME
==================================================

أنت XPAND نفسه الموجود في Telegram.

المستخدم هو إيهاب.

هذه المكالمة ليست شخصية أو ذاكرة منفصلة.

المحادثة النصية، الرسائل الصوتية والمكالمة
كلها محادثة واحدة مستمرة مبنية على نفس user_id.

لا تعرّف حالك من جديد إذا السياق مستمر.

لا تنادِ المستخدم باسم كريم.

لا تستخدم شخصية Kemo.

==================================================
المحادثة الموحدة
==================================================

استخدم آخر المحادثة المشتركة والذاكرة الموجودة أدناه.

إذا إيهاب ذكر:
- الرابط
- المشروع
- الملف
- آخر حكي
- الشي اللي كنا بنشتغل عليه

راجع السياق والذاكرة أولاً قبل سؤاله من جديد.

==================================================
إرسال شيء إلى الشات أثناء المكالمة
==================================================

إذا إيهاب قال مثلاً:

- ابعثلي الرابط
- ابعثه على المحادثة
- ابعثلي الموقع
- حط الرابط بالشات
- بدي الرابط مكتوب
- ابعثلي التفاصيل على Telegram

استخدم أداة:

send_chat_message

فوراً.

إذا الرابط ناتج من search_web،
خذ URL الصحيح من نتيجة الأداة
ثم استخدم send_chat_message.

لا تقرأ الرابط الطويل بصوتك.

بعد نجاح send_chat_message فقط:
أكد لإيهاب صوتياً إنه انبعث.

إذا الأداة فشلت:
لا تقل إنه انبعث.

==================================================
الذاكرة
==================================================

كل كلام مهم من إيهاب في المكالمة يدخل
إلى نفس سجل messages وmemory_archive.

كلام إيهاب المكتمل يدخل أيضاً إلى
memory_learning_jobs لكي يتعلمه نفس
محرك الذاكرة المستخدم في Telegram.

استخدم remember_information فقط
عندما يطلب إيهاب صراحة حفظ شيء مهم
أو عندما تكون المعلومة واضحة وطويلة الأمد.

==================================================
الصوت
==================================================

الصوت التقني لهذه المكالمة هو نفس هوية الصوت
المستخدمة في XPAND.

لا تغيّر شخصية الكلام بسبب القناة.

احكي فلسطيني طبيعي، واضح، هادئ وواثق.

الجمل في المكالمة تكون أقصر من النص.

لا تقرأ روابط طويلة أو رموز تقنية بصوتك.

==================================================
الكمبيوتر
==================================================

عندك مساران مباشران:

1. Chrome CDP / DOM Direct
2. Windows UI Automation Direct

Screenshot/Vision هو fallback فقط.

داخل Chrome:
استخدم browser_* أولاً.

داخل برامج Windows:
استخدم desktop_* أولاً.

لا تأخذ Screenshot قبل كل عملية.

==================================================
فتح البرامج
==================================================

إذا إيهاب طلب فتح برنامج:

desktop_open_program

مثال:
app = "Calculator"

==================================================
Windows UI Automation
==================================================

لقراءة برنامج:
desktop_read_app

للضغط:
desktop_app_click

للكتابة:
desktop_app_type

للاختيار:
desktop_app_select

لإحضار النافذة:
desktop_focus_window

==================================================
Chrome
==================================================

لفتح رابط:
browser_open_url

لقراءة الصفحة:
browser_read_page

للضغط:
browser_click

للبحث:
browser_search

لتشغيل فيديو:
browser_play_video

لإيقاف فيديو:
browser_pause_video

للتمرير:
browser_scroll

للرجوع:
browser_back

للتقدم:
browser_forward

لإعادة التحميل:
browser_reload

==================================================
الصدق التنفيذي
==================================================

لا تقل إن إجراء تم إلا بعد نجاح الأداة.

لا تقل:
"بعثتلك"
إلا بعد نجاح send_chat_message.

لا تقل:
"فتحت"
إلا بعد نجاح أداة الفتح.

==================================================
الأفعال الحساسة
==================================================

قبل:
- الدفع
- الشراء
- الحذف النهائي
- إرسال رسالة إلى شخص خارجي
- النشر
- Submit نهائي
- إنشاء حساب
- تحويل أموال

اطلب موافقة إيهاب قبل الخطوة النهائية.

إرسال رابط أو معلومة إلى نفس محادثة إيهاب
بناءً على طلبه المباشر أثناء المكالمة
لا يحتاج موافقة إضافية.
`;


// ======================================================
// LIVE INSTRUCTIONS
// ======================================================

function buildLiveInstructions(
  masterPrompt,
  memoryContext,
  dialectContext,
  continuity
) {

  const continuityText =
    continuity?.isContinuation
      ?
      `
هذه المكالمة تكملة مباشرة للمحادثة السابقة مع إيهاب.

لا تبدأ تعارفاً جديداً.
لا تسأل "كيف أقدر أساعدك؟".
كمل من السياق الحالي مباشرة.
`
      :
      `
هذه بداية تفاعل جديد نسبياً.

مسموح تحية فلسطينية قصيرة واحدة فقط.
بعدها ادخل مباشرة في الحديث.
`;


  return `
${masterPrompt}

${CALL_RUNTIME_RULES}

==================================================
CONTINUITY
==================================================

${continuityText}

==================================================
CURRENT PALESTINE TIME
==================================================

${humanLocalTime()}

Timezone:
${XPAND_TIMEZONE}

==================================================
IHAB DIALECT PROFILE
==================================================

${dialectContext}

==================================================
UNIFIED XPAND MEMORY
==================================================

${memoryContext}
`.trim();
}


// ======================================================
// LIVE TOOLS
// ======================================================

function buildLiveTools() {

  return [
    {
      functionDeclarations: [

        {
          name:
            "get_current_time",

          description:
            "يعطي الوقت الحقيقي الحالي في فلسطين.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "create_reminder",

          description:
            "ينشئ تذكيراً دائماً لإيهاب في نفس نظام XPAND.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              reason: {
                type: "string"
              },

              message: {
                type: "string"
              },

              delaySeconds: {
                type: "integer"
              },

              runAtLocal: {
                type: "string"
              },

              title: {
                type: "string"
              }
            },

            required: [
              "reason"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "list_reminders",

          description:
            "يعرض التذكيرات المعلقة لإيهاب.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "cancel_reminder",

          description:
            "يلغي تذكيراً.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              jobId: {
                type: "integer"
              },

              latest: {
                type: "boolean"
              }
            },

            additionalProperties:
              false
          }
        },


        {
          name:
            "search_web",

          description:
            "بحث حديث على الإنترنت. النتائج تتضمن الروابط ويمكن إرسال الرابط إلى الشات.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              query: {
                type: "string"
              }
            },

            required: [
              "query"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "recall_memory",

          description:
            "يبحث في ذاكرة XPAND المشتركة الخاصة بإيهاب.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              query: {
                type: "string"
              }
            },

            required: [
              "query"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "remember_information",

          description:
            "يحفظ معلومة مهمة في ذاكرة XPAND الدائمة لإيهاب.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              content: {
                type: "string"
              },

              category: {
                type: "string"
              }
            },

            required: [
              "content"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "send_chat_message",

          description:
            "يرسل رسالة أو رابط مباشرة من المكالمة إلى نفس محادثة إيهاب على Telegram. استخدمه فوراً عندما يطلب إيهاب إرسال الرابط أو التفاصيل إلى الشات.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              message: {
                type: "string"
              },

              url: {
                type: "string"
              },

              title: {
                type: "string"
              },

              source_channel: {
                type: "string"
              }
            },

            additionalProperties:
              false
          }
        },


        //
        // Legacy alias for compatibility.
        //
        {
          name:
            "send_telegram_message",

          description:
            "يرسل رسالة إلى نفس محادثة إيهاب على Telegram.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              text: {
                type: "string"
              }
            },

            required: [
              "text"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_open_program",

          description:
            "يفتح برنامجاً مثبتاً على كمبيوتر إيهاب أو يجلب نافذته للمقدمة.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              app: {
                type: "string"
              }
            },

            required: [
              "app"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_list_windows",

          description:
            "يعرض النوافذ والبرامج المفتوحة.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              query: {
                type: "string"
              }
            },

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_focus_window",

          description:
            "يجلب نافذة برنامج محدد إلى المقدمة.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              window: {
                type: "string"
              }
            },

            required: [
              "window"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_read_app",

          description:
            "يقرأ عناصر نافذة برنامج Windows عبر UI Automation.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              window: {
                type: "string"
              },

              query: {
                type: "string"
              },

              limit: {
                type: "integer"
              }
            },

            required: [
              "window"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_app_click",

          description:
            "يضغط على عنصر داخل برنامج Windows عبر UI Automation.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              window: {
                type: "string"
              },

              name: {
                type: "string"
              },

              controlType: {
                type: "string"
              },

              occurrence: {
                type: "integer"
              },

              confirmed: {
                type: "boolean"
              }
            },

            required: [
              "window",
              "name"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_app_type",

          description:
            "يكتب داخل حقل في برنامج Windows.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              window: {
                type: "string"
              },

              field: {
                type: "string"
              },

              text: {
                type: "string"
              },

              controlType: {
                type: "string"
              },

              clear: {
                type: "boolean"
              },

              pressEnter: {
                type: "boolean"
              }
            },

            required: [
              "window",
              "field",
              "text"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_app_select",

          description:
            "يختار عنصراً داخل برنامج Windows.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              window: {
                type: "string"
              },

              name: {
                type: "string"
              },

              controlType: {
                type: "string"
              },

              occurrence: {
                type: "integer"
              }
            },

            required: [
              "window",
              "name"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "desktop_screenshot",

          description:
            "يلتقط Screenshot ويحلل الشاشة. يستخدم عند الحاجة فقط.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              question: {
                type: "string"
              }
            },

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_status",

          description:
            "يفحص حالة Chrome Direct.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_read_page",

          description:
            "يقرأ الصفحة الحالية مباشرة من DOM.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              query: {
                type: "string"
              },

              limit: {
                type: "integer"
              }
            },

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_open_url",

          description:
            "يفتح رابطاً داخل Chrome ويجلب Chrome للمقدمة.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              url: {
                type: "string"
              }
            },

            required: [
              "url"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_click",

          description:
            "يضغط على عنصر في Chrome حسب النص.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              text: {
                type: "string"
              },

              occurrence: {
                type: "integer"
              },

              confirmed: {
                type: "boolean"
              }
            },

            required: [
              "text"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_search",

          description:
            "يبحث داخل مربع البحث بالموقع الحالي.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              text: {
                type: "string"
              }
            },

            required: [
              "text"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_play_video",

          description:
            "يشغل الفيديو الحالي.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_pause_video",

          description:
            "يوقف الفيديو الحالي.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_scroll",

          description:
            "يمرر صفحة Chrome. الموجب للأسفل والسالب للأعلى.",

          parametersJsonSchema: {
            type: "object",

            properties: {
              amount: {
                type: "integer"
              }
            },

            required: [
              "amount"
            ],

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_back",

          description:
            "يرجع صفحة للخلف.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_forward",

          description:
            "يتقدم صفحة للأمام.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_reload",

          description:
            "يعيد تحميل الصفحة الحالية.",

          parametersJsonSchema: {
            type: "object",
            properties: {},
            additionalProperties:
              false
          }
        }

      ]
    }
  ];
}


// ======================================================
// EXECUTE LIVE TOOL
// ======================================================

async function executeLiveTool(
  sessionInfo,
  toolName,
  args
) {

  const {
    userId,
    callId
  } =
    sessionInfo;


  switch (toolName) {

    case "get_current_time":

      return {
        ok: true,
        timezone:
          XPAND_TIMEZONE,
        localIso:
          localIsoString(),
        human:
          humanLocalTime(),
        utc:
          new Date()
            .toISOString()
      };


    case "create_reminder":

      return await createReminder(
        userId,
        callId,
        args || {}
      );


    case "list_reminders":

      return await listReminders(
        userId
      );


    case "cancel_reminder":

      return await cancelReminder(
        userId,
        args || {}
      );


    case "search_web":

      return await searchWeb(
        args?.query
      );


    case "recall_memory":

      return await recallMemory(
        userId,
        args?.query
      );


    case "remember_information": {

      const memoryId =
        await savePersistentMemory(
          userId,
          args?.content,
          {
            category:
              cleanText(
                args?.category
                ||
                "fact",
                100
              ),

            importance: 5,
            source:
              "live_call"
          }
        );


      return {
        ok: true,
        memoryId
      };
    }


    case "send_chat_message":

      return await sendChatMessageFromCall(
        userId,
        args || {}
      );


    case "send_telegram_message":

      return await sendChatMessageFromCall(
        userId,
        {
          message:
            args?.text,
          source_channel:
            "live_call"
        }
      );


    case "desktop_open_program": {

      const app =
        cleanText(
          args?.app,
          300
        );


      if (!app) {
        throw new Error(
          "Program name missing"
        );
      }


      return await runDesktopCommand(
        "open_installed_app",
        {
          app
        },
        30000
      );
    }


    case "desktop_list_windows":

      return await runDesktopCommand(
        "window_list",
        {
          query:
            cleanText(
              args?.query,
              500
            )
        },
        15000
      );


    case "desktop_focus_window":

      return await runDesktopCommand(
        "window_activate",
        {
          window:
            cleanText(
              args?.window,
              500
            )
        },
        15000
      );


    case "desktop_read_app":

      return await runDesktopCommand(
        "uia_snapshot",
        {
          window:
            cleanText(
              args?.window,
              500
            ),

          query:
            cleanText(
              args?.query,
              500
            ),

          limit:
            clamp(
              Number(
                args?.limit || 180
              ),
              20,
              250
            )
        },
        20000
      );


    case "desktop_app_click": {

      const window =
        cleanText(
          args?.window,
          500
        );

      const name =
        cleanText(
          args?.name,
          500
        );


      if (
        actionNeedsConfirmation(name)
        &&
        args?.confirmed !== true
      ) {
        return {
          ok: true,
          completed: false,
          needsConfirmation: true,
          message:
            "هاي خطوة حساسة أو نهائية. أكدلي أول."
        };
      }


      return await runDesktopCommand(
        "uia_execute",
        {
          action: "click",
          window,
          name,

          controlType:
            cleanText(
              args?.controlType,
              100
            ),

          occurrence:
            Math.max(
              1,
              Number(
                args?.occurrence
                ||
                1
              )
            )
        },
        15000
      );
    }


    case "desktop_app_type":

      return await runDesktopCommand(
        "uia_execute",
        {
          action: "type",

          window:
            cleanText(
              args?.window,
              500
            ),

          name:
            cleanText(
              args?.field,
              500
            ),

          value:
            cleanText(
              args?.text,
              6000
            ),

          controlType:
            cleanText(
              args?.controlType,
              100
            ),

          clear:
            args?.clear !== false,

          pressEnter:
            args?.pressEnter === true
        },
        15000
      );


    case "desktop_app_select":

      return await runDesktopCommand(
        "uia_execute",
        {
          action: "select",

          window:
            cleanText(
              args?.window,
              500
            ),

          name:
            cleanText(
              args?.name,
              500
            ),

          controlType:
            cleanText(
              args?.controlType,
              100
            ),

          occurrence:
            Math.max(
              1,
              Number(
                args?.occurrence
                ||
                1
              )
            )
        },
        15000
      );


    case "desktop_screenshot":

      return await inspectScreen(
        cleanText(
          args?.question,
          1000
        )
        ||
        "شو ظاهر على الشاشة؟"
      );


    case "browser_status":

      return await runDesktopCommand(
        "browser_status",
        {},
        10000
      );


    case "browser_read_page":

      return await runDesktopCommand(
        "browser_snapshot",
        {
          query:
            cleanText(
              args?.query,
              500
            ),

          limit:
            clamp(
              Number(
                args?.limit || 180
              ),
              20,
              250
            )
        },
        15000
      );


    case "browser_open_url": {

      const url =
        cleanText(
          args?.url,
          3000
        );


      if (
        !/^https?:\/\//i
          .test(url)
      ) {
        throw new Error(
          "Only http/https URLs allowed"
        );
      }


      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "open_url",
          url
        },
        15000
      );
    }


    case "browser_click": {

      const text =
        cleanText(
          args?.text,
          1000
        );


      if (
        actionNeedsConfirmation(text)
        &&
        args?.confirmed !== true
      ) {
        return {
          ok: true,
          completed: false,
          needsConfirmation: true,
          message:
            "هاي خطوة حساسة أو نهائية. أكدلي أول."
        };
      }


      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "click_text",
          text,

          occurrence:
            Math.max(
              1,
              Number(
                args?.occurrence
                ||
                1
              )
            )
        },
        15000
      );
    }


    case "browser_search":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "search",

          text:
            cleanText(
              args?.text,
              3000
            )
        },
        15000
      );


    case "browser_play_video":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "media_play"
        },
        10000
      );


    case "browser_pause_video":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "media_pause"
        },
        10000
      );


    case "browser_scroll":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "scroll",

          amount:
            clamp(
              Number(
                args?.amount
                ||
                700
              ),
              -5000,
              5000
            )
        },
        10000
      );


    case "browser_back":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "back"
        },
        10000
      );


    case "browser_forward":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "forward"
        },
        10000
      );


    case "browser_reload":

      return await runDesktopCommand(
        "browser_execute",
        {
          action:
            "reload"
        },
        10000
      );


    default:

      throw new Error(
        `Unknown live tool: ${toolName}`
      );
  }
}


// ======================================================
// TRANSCRIPT
// ======================================================

function sanitizeTranscript(
  transcript
) {

  if (
    !Array.isArray(
      transcript
    )
  ) {
    return [];
  }


  return transcript
    .slice(0, 500)
    .map(
      (
        item,
        index
      ) => {

        const role =
          item?.role ===
          "assistant"
            ?
            "assistant"
            :
            "user";


        const text =
          cleanText(
            item?.text,
            8000
          );


        if (!text) {
          return null;
        }


        return {
          turnId:
            cleanText(
              item?.turnId
              ||
              `final-${index}`,
              200
            ),

          role,
          text
        };
      }
    )
    .filter(Boolean);
}


// ======================================================
// EXPRESS
// ======================================================

const app =
  express();


app.disable(
  "x-powered-by"
);


app.use(
  express.json({
    limit:
      "6mb"
  })
);


app.use(
  (
    req,
    res,
    next
  ) => {

    res.setHeader(
      "X-Content-Type-Options",
      "nosniff"
    );

    res.setHeader(
      "Referrer-Policy",
      "no-referrer"
    );

    res.setHeader(
      "Permissions-Policy",
      "microphone=(self)"
    );

    res.setHeader(
      "Cache-Control",
      "no-store"
    );

    next();
  }
);


// ======================================================
// HEALTH
// ======================================================

app.get(
  "/api/health",
  async (
    req,
    res
  ) => {

    try {

      await pool.query(
        "SELECT 1"
      );


      const desktop =
        await desktopHealth();


      const master =
        await loadSharedMasterPrompt(
          false
        );


      res.json({
        ok: true,

        service:
          "xpand-call",

        version:
          SERVER_VERSION,

        agent:
          AGENT_NAME,

        primaryUser:
          PRIMARY_USER_NAME,

        company:
          COMPANY_NAME,

        model:
          LIVE_MODEL,

        voice:
          XPAND_VOICE_ID,

        timezone:
          XPAND_TIMEZONE,

        continuityMinutes:
          CALL_CONTINUITY_MINUTES,

        sharedMasterPrompt:
          Boolean(
            master?.prompt
          ),

        masterPromptVersion:
          master?.version
          ||
          "",

        realtimeCallMemory:
          true,

        sendChatMessage:
          true,

        desktopOnline:
          Boolean(
            desktop?.agentOnline
          ),

        realtimeWebSocket:
          Boolean(
            desktop?.realtimeWebSocket
          ),

        wholePcDirect:
          Boolean(
            desktop?.wholePcDirect
          ),

        chromeDirect:
          Boolean(
            desktop?.chromeDirect
          ),

        windowsUIAutomation:
          Boolean(
            desktop?.windowsUIAutomation
          ),

        foregroundControl:
          Boolean(
            desktop?.foregroundControl
          ),

        agentInfo:
          desktop?.lastAgentInfo
          ||
          null,

        localTime:
          localIsoString()
      });


    } catch (error) {

      res
        .status(500)
        .json({
          ok: false,
          error:
            error.message
        });
    }
  }
);


// ======================================================
// START CALL
// ======================================================

app.post(
  "/api/call/start",
  async (
    req,
    res
  ) => {

    try {

      const {
        userId,
        user
      } =
        verifyTelegramInitData(
          req.body?.initData
        );


      const [
        master,
        memoryContext,
        dialect,
        continuity,
        ephemeralToken
      ] =
        await Promise.all([

          loadSharedMasterPrompt(
            true
          ),

          buildMemoryContext(
            userId
          ),

          loadDialectProfile(
            userId
          ),

          getConversationContinuity(
            userId
          ),

          createEphemeralToken()

        ]);


      const callId =
        crypto.randomUUID();


      const callSecret =
        createCallSecret();


      const systemInstruction =
        buildLiveInstructions(
          master.prompt,
          memoryContext,
          dialect.context,
          continuity
        );


      await pool.query(
        `
        INSERT INTO call_sessions
        (
          id,
          telegram_user_id,
          session_secret_hash,
          status
        )
        VALUES (
          $1,
          $2,
          $3,
          'active'
        )
        `,
        [
          callId,
          userId,
          hashCallSecret(
            callSecret
          )
        ]
      );


      await recordEvent(
        userId,
        userId,
        "live_call_started",
        "بدأت مكالمة XPAND الموحدة",
        {
          callId,
          version:
            SERVER_VERSION,
          sharedConversation:
            true
        }
      );


      res.json({
        ok: true,

        callId,
        callSecret,
        ephemeralToken,

        model:
          LIVE_MODEL,

        voice:
          XPAND_VOICE_ID,

        voiceId:
          XPAND_VOICE_ID,

        timezone:
          XPAND_TIMEZONE,

        systemInstruction,

        liveTools:
          buildLiveTools(),

        continuity,

        permanentMemoryV2:
          true,

        sharedConversation:
          true,

        realtimeCallMemory:
          true,

        sendChatMessage:
          true,

        agent:
          AGENT_NAME,

        primaryUser:
          PRIMARY_USER_NAME,

        user: {
          id:
            userId,

          firstName:
            user?.first_name
            ||
            ""
        }
      });


    } catch (error) {

      console.error(
        "❌ Call start:",
        error
      );


      res
        .status(500)
        .json({
          ok: false,
          error:
            error.message
        });
    }
  }
);


// ======================================================
// REAL-TIME CALL TURN
// ======================================================

app.post(
  "/api/call/turn",
  async (
    req,
    res
  ) => {

    try {

      const session =
        await getCallSession(
          req.body?.callId,
          req.body?.callSecret,
          true
        );


      const result =
        await persistCallTurn(
          session,
          {
            turnId:
              req.body?.turnId,

            role:
              req.body?.role,

            text:
              req.body?.text
          }
        );


      res.json({
        ok: true,
        ...result
      });


    } catch (error) {

      console.error(
        "❌ Call turn:",
        error
      );


      res
        .status(400)
        .json({
          ok: false,
          error:
            error.message
        });
    }
  }
);


// ======================================================
// CALL TOOL
// ======================================================

app.post(
  "/api/call/tool",
  async (
    req,
    res
  ) => {

    try {

      const session =
        await getCallSession(
          req.body?.callId,
          req.body?.callSecret,
          true
        );


      const toolName =
        cleanText(
          req.body?.toolName,
          100
        );


      console.log(
        (
          "🛠️ XPAND live tool: "
          +
          toolName
        )
      );


      const started =
        Date.now();


      try {

        const result =
          await executeLiveTool(
            session,
            toolName,
            (
              req.body?.args
              &&
              typeof req.body.args
              === "object"
            )
              ?
              req.body.args
              :
              {}
          );


        const elapsed =
          Date.now()
          -
          started;


        console.log(
          (
            "✅ Tool "
            +
            toolName
            +
            " | "
            +
            elapsed
            +
            "ms"
          )
        );


        res.json({
          ok: true,
          tool:
            toolName,
          elapsedMs:
            elapsed,
          result
        });


      } catch (toolError) {

        const elapsed =
          Date.now()
          -
          started;


        console.error(
          (
            "❌ Tool "
            +
            toolName
            +
            " | "
            +
            elapsed
            +
            "ms | "
            +
            toolError.message
          )
        );


        res.json({
          ok: false,
          tool:
            toolName,
          elapsedMs:
            elapsed,
          error:
            toolError.message
        });
      }


    } catch (error) {

      res
        .status(401)
        .json({
          ok: false,
          error:
            error.message
        });
    }
  }
);


// ======================================================
// END CALL
// ======================================================

app.post(
  "/api/call/end",
  async (
    req,
    res
  ) => {

    let session;


    try {

      session =
        await getCallSession(
          req.body?.callId,
          req.body?.callSecret,
          false
        );


    } catch (error) {

      return res
        .status(401)
        .json({
          ok: false,
          error:
            error.message
        });
    }


    if (
      session.status ===
      "ended"
    ) {
      return res.json({
        ok: true,
        alreadySaved:
          true
      });
    }


    const transcript =
      sanitizeTranscript(
        req.body?.transcript
      );


    try {

      //
      // Save anything that was not already persisted
      // live through /api/call/turn.
      //
      for (
        const turn
        of transcript
      ) {

        await persistCallTurn(
          session,
          turn
        );
      }


      await pool.query(
        `
        UPDATE call_sessions
        SET
          status = 'ended',
          transcript = $2::jsonb,
          ended_at = NOW()
        WHERE id = $1
        `,
        [
          session.callId,
          JSON.stringify(
            transcript
          )
        ]
      );


      await recordEvent(
        session.userId,
        session.userId,
        "live_call_ended",
        "انتهت مكالمة XPAND الموحدة",
        {
          callId:
            session.callId,

          savedTurns:
            transcript.length
        }
      );


      res.json({
        ok: true,

        savedTurns:
          transcript.length,

        sharedConversation:
          true,

        realtimeCallMemory:
          true
      });


    } catch (error) {

      console.error(
        "❌ End call:",
        error
      );


      res
        .status(500)
        .json({
          ok: false,
          error:
            error.message
        });
    }
  }
);


// ======================================================
// STATIC UI
// ======================================================

app.use(
  express.static(
    STATIC_DIR,
    {
      index: false
    }
  )
);


app.use(
  (
    req,
    res,
    next
  ) => {

    if (
      req.method === "GET"
      &&
      !req.path.startsWith(
        "/api/"
      )
      &&
      fs.existsSync(
        INDEX_FILE
      )
    ) {
      return res.sendFile(
        INDEX_FILE
      );
    }


    next();
  }
);


// ======================================================
// START
// ======================================================

async function start() {

  const missing = [];


  if (!TELEGRAM_BOT_TOKEN) {
    missing.push(
      "TELEGRAM_BOT_TOKEN"
    );
  }


  if (!GEMINI_API_KEY) {
    missing.push(
      "GEMINI_API_KEY"
    );
  }


  if (!DATABASE_URL) {
    missing.push(
      "DATABASE_URL"
    );
  }


  if (
    !TELEGRAM_ALLOWED_USER_ID
  ) {
    missing.push(
      "TELEGRAM_ALLOWED_USER_ID"
    );
  }


  if (missing.length) {

    console.error(
      (
        "❌ Missing variables: "
        +
        missing.join(", ")
      )
    );


    process.exit(1);
  }


  await initDatabase();


  const master =
    await loadSharedMasterPrompt(
      false
    );


  app.listen(
    PORT,
    "0.0.0.0",
    async () => {

      const desktop =
        await desktopHealth();


      console.log("");
      console.log(
        "======================================="
      );
      console.log(
        " XPAND UNIFIED CALL SERVER V7.0"
      );
      console.log(
        " TEXT + VOICE + LIVE CALL = ONE XPAND"
      );
      console.log(
        "======================================="
      );
      console.log("");

      console.log(
        `✅ Port: ${PORT}`
      );

      console.log(
        `✅ Agent: ${AGENT_NAME}`
      );

      console.log(
        `✅ Primary user: ${PRIMARY_USER_NAME}`
      );

      console.log(
        `✅ Live model: ${LIVE_MODEL}`
      );

      console.log(
        `✅ Unified voice: ${XPAND_VOICE_ID}`
      );

      console.log(
        `✅ Timezone: ${XPAND_TIMEZONE}`
      );

      console.log(
        (
          "✅ Continuity: "
          +
          CALL_CONTINUITY_MINUTES
          +
          " minutes"
        )
      );

      console.log(
        (
          "✅ Shared master prompt: "
          +
          (
            master?.prompt
              ?
              "LOADED"
              :
              "missing"
          )
        )
      );

      console.log(
        (
          "✅ Master prompt version: "
          +
          (
            master?.version
            ||
            "unknown"
          )
        )
      );

      console.log(
        "✅ Shared Telegram + Voice + Call conversation"
      );

      console.log(
        "✅ Real-time call turn persistence"
      );

      console.log(
        "✅ Shared Permanent Memory"
      );

      console.log(
        "✅ Call → Telegram send_chat_message"
      );

      console.log(
        (
          "💻 Desktop Agent: "
          +
          (
            desktop?.agentOnline
              ?
              "ONLINE"
              :
              "offline"
          )
        )
      );

      console.log(
        (
          "⚡ Realtime WebSocket: "
          +
          (
            desktop?.realtimeWebSocket
              ?
              "CONNECTED"
              :
              "not connected"
          )
        )
      );

      console.log(
        (
          "🌐 Chrome Direct: "
          +
          (
            desktop?.chromeDirect
              ?
              "READY"
              :
              "not ready"
          )
        )
      );

      console.log(
        (
          "🪟 Windows UI Automation: "
          +
          (
            desktop?.windowsUIAutomation
              ?
              "READY"
              :
              "not ready"
          )
        )
      );

      console.log("");
    }
  );
}


// ======================================================
// START SERVER
// ======================================================

start()
  .catch(
    error => {

      console.error(
        "❌ XPAND call server startup failed:",
        error
      );

      process.exit(1);
    }
  );
