// ======================================================
// KEMO HUMAN CALL SERVER V6.1
//
// ONE KEMO
// WHOLE-PC REALTIME CONTROL
//
// Features:
// - Same Telegram + Call memory
// - 15-minute conversation continuity
// - Reminders
// - Web search
// - Telegram messaging
//
// Desktop:
// - Persistent WebSocket transport
// - Open installed Windows programs
// - Bring windows to foreground
// - Read Windows UI via UI Automation
// - Click / invoke / type / select Windows controls
//
// Browser:
// - Chrome CDP direct control
// - DOM read
// - DOM click
// - Search
// - Type
// - Scroll
// - Video control
// - Back / forward / reload
// - Open URL and bring Chrome to foreground
//
// Fallback:
// - Screenshot Vision only when DOM/UIA cannot do it
//
// Safety:
// - No arbitrary shell
// - No arbitrary remote JavaScript tool
// - Explicit actions only
// - Confirmation for sensitive irreversible actions
// ======================================================

import express from "express";
import pg from "pg";
import crypto from "node:crypto";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const { Pool } = pg;


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

const KEMO_TIMEZONE = String(
  process.env.KEMO_TIMEZONE || "Asia/Hebron"
).trim();

const LIVE_MODEL = String(
  process.env.KEMO_LIVE_MODEL
  ||
  "gemini-3.1-flash-live-preview"
).trim();

const KEMO_VOICE = String(
  process.env.KEMO_VOICE
  ||
  process.env.KEMO_LIVE_VOICE
  ||
  "Iapetus"
).trim();

const KEMO_TOOL_MODEL = String(
  process.env.KEMO_TOOL_MODEL
  ||
  "gemini-3.5-flash-lite"
).trim();

const KEMO_DESKTOP_URL = String(
  process.env.KEMO_DESKTOP_URL || ""
)
  .trim()
  .replace(/\/+$/g, "");

const KEMO_DESKTOP_KEY = String(
  process.env.KEMO_DESKTOP_KEY || ""
).trim();

const KEMO_DESKTOP_DEVICE_ID = String(
  process.env.KEMO_DESKTOP_DEVICE_ID || "main-pc"
).trim();

const CALL_CONTINUITY_MINUTES = Math.max(
  1,
  Number(
    process.env.KEMO_CALL_CONTINUITY_MINUTES || 15
  ) || 15
);


// ======================================================
// SPEED / SAFETY
// ======================================================

const DESKTOP_SYNC_TIMEOUT_MS = 30000;

const VISUAL_MIN_CONFIDENCE = Math.max(
  0.65,
  Math.min(
    0.99,
    Number(
      process.env.KEMO_VISUAL_MIN_CONFIDENCE || 0.84
    ) || 0.84
  )
);


// ======================================================
// PATHS
// ======================================================

const __filename =
  fileURLToPath(
    import.meta.url
  );

const __dirname =
  path.dirname(
    __filename
  );

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
  fs.existsSync(
    DIST_INDEX
  )
    ?
    path.join(
      __dirname,
      "dist"
    )
    :
    __dirname;

const INDEX_FILE =
  fs.existsSync(
    DIST_INDEX
  )
    ?
    DIST_INDEX
    :
    ROOT_INDEX;


// ======================================================
// DATABASE
// ======================================================

const pool =
  new Pool({
    connectionString:
      DATABASE_URL,

    max:
      6,

    idleTimeoutMillis:
      30000,

    connectionTimeoutMillis:
      10000
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
    .slice(
      0,
      maxLength
    );
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
    .replace(/[\u064B-\u065F]/g, "")
    .replace(/[^\p{L}\p{N}_.\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}


function containsAny(
  text,
  markers
) {
  const source =
    normalizeArabic(
      text
    );

  return markers.some(
    marker =>
      source.includes(
        normalizeArabic(
          marker
        )
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
    Math.min(
      max,
      value
    )
  );
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
        timeZone:
          KEMO_TIMEZONE,

        year:
          "numeric",

        month:
          "2-digit",

        day:
          "2-digit",

        hour:
          "2-digit",

        minute:
          "2-digit",

        second:
          "2-digit",

        hourCycle:
          "h23"
      }
    );

  const parts = {};

  for (
    const part
    of formatter.formatToParts(
      date
    )
  ) {
    if (
      part.type !==
      "literal"
    ) {
      parts[
        part.type
      ] = part.value;
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
        timeZone:
          KEMO_TIMEZONE,

        weekday:
          "long",

        year:
          "numeric",

        month:
          "long",

        day:
          "numeric",

        hour:
          "numeric",

        minute:
          "2-digit",

        second:
          "2-digit",

        hour12:
          true
      }
    ).format(
      date
    );

  } catch {
    return localIsoString(
      date
    );
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
    "✅ Shared database ready"
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
  prompt:
    "",

  version:
    "",

  loadedAt:
    0
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
      ok:
        true,

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
        WHERE config_key = 'master_system_prompt'
        LIMIT 1
      `),

      safeRows(`
        SELECT config_value
        FROM kemo_config
        WHERE config_key = 'master_system_prompt_version'
        LIMIT 1
      `)

    ]);

  const prompt =
    cleanText(
      promptRows[0]?.config_value,
      70000
    );

  const version =
    cleanText(
      versionRows[0]?.config_value,
      200
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

  if (
    prompt
  ) {
    masterPromptCache = {
      prompt,
      version,
      loadedAt:
        Date.now()
    };
  }

  return {
    ok:
      Boolean(
        prompt
      ),

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

  if (
    !rows.length
  ) {
    return {
      context:
        "لا توجد بصمة لهجة إضافية."
    };
  }

  return {
    context:
      [
        "=== تعبيرات كريم ===",

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
    typeof initData !==
      "string"
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
    params.get(
      "hash"
    );

  if (
    !receivedHash
  ) {
    throw new Error(
      "Telegram hash missing"
    );
  }

  params.delete(
    "hash"
  );

  const dataCheckString =
    [...params.entries()]
      .sort(
        ([a], [b]) =>
          a.localeCompare(
            b
          )
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
      .digest(
        "hex"
      );

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
    a.length !==
      b.length
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
    params.get(
      "user"
    );

  if (
    !rawUser
  ) {
    throw new Error(
      "Telegram user missing"
    );
  }

  const user =
    JSON.parse(
      rawUser
    );

  const userId =
    String(
      user?.id || ""
    );

  if (
    !userId
  ) {
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
    .randomBytes(
      32
    )
    .toString(
      "base64url"
    );
}


function hashCallSecret(
  value
) {
  return crypto
    .createHash(
      "sha256"
    )
    .update(
      String(
        value || ""
      )
    )
    .digest(
      "hex"
    );
}


function secureEqualHex(
  a,
  b
) {
  try {
    const left =
      Buffer.from(
        a,
        "hex"
      );

    const right =
      Buffer.from(
        b,
        "hex"
      );

    return (
      left.length > 0
      &&
      left.length ===
        right.length
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

  if (
    !row
  ) {
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
    row.status !==
      "active"
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

  if (
    !text
  ) {
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
      VALUES ($1, $2, $3)
      RETURNING id, created_at
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
      normalizeArabic(
        text
      ),
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
// MEMORY
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

  if (
    !text
  ) {
    return null;
  }

  const existing =
    await safeRows(
      `
      SELECT id
      FROM memories
      WHERE
        user_id = $1
        AND LOWER(content) = LOWER($2)
      LIMIT 1
      `,
      [
        userId,
        text
      ]
    );

  if (
    existing.length
  ) {
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
        AND normalized_content ILIKE $2
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
    ok:
      true,

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
        LIMIT 25
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
        LIMIT 30
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

  if (
    canonical.length
  ) {
    sections.push(
      [
        "=== CANONICAL FACTS ===",

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

  if (
    profile.length
  ) {
    sections.push(
      [
        "=== ملف كريم ===",

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

  if (
    memories.length
  ) {
    sections.push(
      [
        "=== ذكريات ===",

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

  if (
    messages.length
  ) {
    sections.push(
      [
        "=== آخر المحادثة المشتركة ===",

        ...[
          ...messages
        ]
          .reverse()
          .map(
            item =>
              (
                (
                  item.role ===
                  "assistant"
                    ?
                    "Kemo"
                    :
                    "كريم"
                )
                +
                ": "
                +
                cleanText(
                  item.content,
                  1000
                )
              )
          )
      ].join("\n")
    );
  }

  if (
    reminders.length
  ) {
    sections.push(
      [
        "=== التذكيرات ===",

        ...reminders.map(
          item =>
            (
              `- #${item.id}: `
              +
              item.message
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
    sections.join(
      "\n\n"
    )
    ||
    "لا توجد ذاكرة إضافية."
  ).slice(
    0,
    28000
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

  if (
    !last
  ) {
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
// EVENT
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
            uses:
              1,

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
    KEMO_TOOL_MODEL,
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
      array.indexOf(
        item
      ) ===
        index
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
    return JSON.parse(
      text
    );

  } catch {}

  const start =
    text.indexOf(
      "{"
    );

  const end =
    text.lastIndexOf(
      "}"
    );

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
            encodeURIComponent(
              model
            )
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
                    role:
                      "user",

                    parts: [
                      {
                        text:
                          prompt
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
                  temperature:
                    0,

                  maxOutputTokens:
                    1200,

                  responseMimeType:
                    "application/json"
                }
              })
          }
        );

      const data =
        await response.json();

      if (
        !response.ok
      ) {
        throw new Error(
          data?.error?.message
          ||
          "Vision failed"
        );
      }

      return parseJsonText(
        extractGeminiText(
          data
        )
      );

    } catch (error) {
      lastError =
        error;

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
          JSON.stringify(
            payload
          )
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
          )
      }
    );
  }

  return {
    ok:
      true
  };
}


// ======================================================
// SEARCH WEB
// ======================================================

async function searchWeb(
  query
) {

  if (
    !TAVILY_API_KEY
  ) {
    throw new Error(
      "Tavily is not configured"
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
              cleanText(
                query,
                700
              ),

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

  if (
    !response.ok
  ) {
    throw new Error(
      data?.detail
      ||
      "Web search failed"
    );
  }

  return {
    ok:
      true,

    results:
      (
        Array.isArray(
          data?.results
        )
          ?
          data.results
          :
          []
      ).slice(
        0,
        5
      )
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

        KEMO_TIMEZONE
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

  if (
    !reason
  ) {
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
      !Number.isFinite(
        seconds
      )
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
          `كريم، تذكيرك: ${reason}`,
          2000
        ),

        runAt,

        KEMO_TIMEZONE,

        JSON.stringify({
          reason,
          callId
        })
      ]
    );

  return {
    ok:
      true,

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
    ok:
      true,

    reminders:
      rows
  };
}


async function cancelReminder(
  userId,
  args
) {

  let rows = [];

  if (
    args?.jobId
  ) {
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
    KEMO_DESKTOP_URL
    &&
    KEMO_DESKTOP_KEY
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

    if (
      authenticated
    ) {
      headers[
        "X-Kemo-Desktop-Key"
      ] =
        KEMO_DESKTOP_KEY;
    }

    if (
      body !== null
    ) {
      headers[
        "Content-Type"
      ] =
        "application/json";
    }

    const response =
      await fetch(
        KEMO_DESKTOP_URL
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

    const data =
      raw
        ?
        JSON.parse(
          raw
        )
        :
        {};

    if (
      !response.ok
    ) {
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
    clearTimeout(
      timer
    );
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
        method:
          "POST",

        timeout:
          timeoutMs + 5000,

        body: {
          action,

          deviceId:
            KEMO_DESKTOP_DEVICE_ID,

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

  if (
    !desktopConfigured()
  ) {
    return {
      ok:
        false,

      configured:
        false
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
      ok:
        false,

      configured:
        true,

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

  if (
    !imageBase64
  ) {
    throw new Error(
      "Screenshot missing"
    );
  }

  const result =
    await callGeminiVisionJson(
      imageBase64,
      `
أنت ترى Screenshot الحالية فقط من كمبيوتر كريم.

سؤال كريم:
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
    ok:
      true,

    screenAnalysis:
      cleanText(
        result?.answer,
        2500
      )
  };
}


// ======================================================
// LIVE RUNTIME RULES
// ======================================================

const CALL_RUNTIME_RULES = `
==================================================
KEMO WHOLE-PC LIVE CONTROL
==================================================

أنت نفس Kemo الموجود في Telegram.

احكي مع كريم بشكل فلسطيني طبيعي ومختصر.

نفّذ طلبه مباشرة.
لا تدعي أن عملية نجحت إلا بعد نجاح الأداة.

==================================================
أنت تتحكم بالكمبيوتر كامل
==================================================

عندك مساران مباشران:

1. Chrome CDP / DOM Direct
2. Windows UI Automation Direct

والـScreenshot والماوس البصري هما fallback فقط.

==================================================
فتح البرامج
==================================================

إذا كريم قال:
"افتح Photoshop"
"افتح الحاسبة"
"افتح VS Code"
"افتح TradingView"

استخدم:
desktop_open_program

هذه الأداة:
- تبحث عن البرنامج المثبت
- تفتحه
- أو إذا كان مفتوحاً تجيبه للواجهة أمام كريم

لا تستخدم Screenshot لفتح البرامج.

==================================================
التعامل مع برامج Windows
==================================================

إذا كريم يريد الضغط أو الكتابة داخل برنامج:

استخدم Windows UI Automation أولاً.

إذا تحتاج تعرف الموجود:
desktop_read_app

إذا يريد الضغط:
desktop_app_click

إذا يريد الكتابة:
desktop_app_type

إذا يريد اختيار عنصر:
desktop_app_select

إذا يريد فقط إحضار نافذة للواجهة:
desktop_focus_window

==================================================
مثال
==================================================

كريم:
"افتح الحاسبة"

desktop_open_program:
app = "Calculator"

كريم:
"اضغط 7"

desktop_app_click:
window = "Calculator"
name = "7"

==================================================
Chrome / المواقع
==================================================

إذا الطلب داخل موقع أو Chrome:
استخدم browser_* أولاً.

browser_open_url
يفتح الرابط ويجيب Chrome للواجهة.

browser_read_page
يقرأ عناصر DOM مباشرة.

browser_click
يضغط العنصر مباشرة.

browser_search
يبحث مباشرة.

browser_type
يكتب مباشرة.

browser_play_video
يشغل الفيديو.

browser_pause_video
يوقف الفيديو.

browser_scroll
يحرك الصفحة.

==================================================
مثال Google
==================================================

كريم:
"افتح جوجل"

استخدم:
browser_open_url
url=https://www.google.com/

Chrome يجب أن يظهر أمام كريم.

==================================================
مثال YouTube
==================================================

كريم:
"افتح يوتيوب وابحث عن سورة مريم"

نفذ:
browser_open_url
ثم:
browser_search

إذا كريم قال بعدها:
"شغل أول فيديو"

استخدم:
browser_read_page
إذا احتجت النص
ثم:
browser_click

==================================================
قاعدة السرعة
==================================================

لا تأخذ Screenshot قبل كل عملية.

داخل Chrome:
DOM أولاً.

داخل برامج Windows:
UI Automation أولاً.

Screenshot/Vision فقط إذا فشلت الأدوات المباشرة.

==================================================
قاعدة الالتزام
==================================================

نفذ ما طلبه كريم فقط.

لا تعمل ضغطات إضافية.
لا تفتح أشياء لم يطلبها.
لا تكمل خطوات من نفسك.

==================================================
الأفعال الحساسة
==================================================

قبل:
- دفع
- شراء
- حذف نهائي
- إرسال رسالة
- نشر
- Submit نهائي
- إنشاء حساب
- تحويل أموال

اطلب تأكيد كريم قبل تنفيذ الخطوة النهائية.

==================================================
الشاشة
==================================================

إذا قال:
"شو ظاهر على شاشة الكمبيوتر؟"

استخدم:
desktop_screenshot

إذا قال:
"شو موجود ببرنامج Photoshop؟"

استخدم:
desktop_read_app

إذا قال:
"شو موجود بصفحة Chrome؟"

استخدم:
browser_read_page
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
هذا الاتصال تكملة مباشرة لتفاعل سابق.
لا تسلم على كريم من جديد.
كمل مباشرة من السياق.
`
      :
      `
مسموح تحية فلسطينية قصيرة مرة واحدة.
`;

  return `
${masterPrompt}

${CALL_RUNTIME_RULES}

==================================================
CONTINUITY
==================================================

${continuityText}

==================================================
PALESTINE TIME
==================================================

${humanLocalTime()}

Timezone:
${KEMO_TIMEZONE}

==================================================
DIALECT
==================================================

${dialectContext}

==================================================
MEMORY
==================================================

${memoryContext}
`;
}


// ======================================================
// LIVE TOOLS
// ======================================================

function buildLiveTools() {

  return [
    {
      functionDeclarations: [

        // ==================================================
        // TIME
        // ==================================================

        {
          name:
            "get_current_time",

          description:
            "يعطي الوقت الحقيقي الحالي في فلسطين.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        // ==================================================
        // REMINDERS
        // ==================================================

        {
          name:
            "create_reminder",

          description:
            "ينشئ تذكيراً دائماً.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              reason: {
                type:
                  "string"
              },

              message: {
                type:
                  "string"
              },

              delaySeconds: {
                type:
                  "integer"
              },

              runAtLocal: {
                type:
                  "string"
              },

              title: {
                type:
                  "string"
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
            "يعرض التذكيرات المعلقة.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

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
            type:
              "object",

            properties: {
              jobId: {
                type:
                  "integer"
              },

              latest: {
                type:
                  "boolean"
              }
            },

            additionalProperties:
              false
          }
        },


        // ==================================================
        // WEB SEARCH
        // ==================================================

        {
          name:
            "search_web",

          description:
            "بحث حديث على الإنترنت.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              query: {
                type:
                  "string"
              }
            },

            required: [
              "query"
            ],

            additionalProperties:
              false
          }
        },


        // ==================================================
        // MEMORY
        // ==================================================

        {
          name:
            "recall_memory",

          description:
            "يبحث في ذاكرة Kemo المشتركة.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              query: {
                type:
                  "string"
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
            "يحفظ معلومة مهمة في الذاكرة الدائمة.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              content: {
                type:
                  "string"
              },

              category: {
                type:
                  "string"
              }
            },

            required: [
              "content"
            ],

            additionalProperties:
              false
          }
        },


        // ==================================================
        // TELEGRAM
        // ==================================================

        {
          name:
            "send_telegram_message",

          description:
            "يرسل رسالة إلى Telegram.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              text: {
                type:
                  "string"
              }
            },

            required: [
              "text"
            ],

            additionalProperties:
              false
          }
        },


        // ==================================================
        // WINDOWS WHOLE-PC
        // ==================================================

        {
          name:
            "desktop_open_program",

          description:
            (
              "يفتح أي برنامج مثبت على كمبيوتر كريم "
              +
              "أو يجلبه إلى مقدمة الشاشة إذا كان مفتوحاً."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              app: {
                type:
                  "string",

                description:
                  "اسم البرنامج مثل Photoshop أو Calculator أو Visual Studio Code."
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
            "يعرض النوافذ والبرامج المفتوحة حالياً.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              query: {
                type:
                  "string"
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
            (
              "يجلب نافذة برنامج محدد إلى واجهة الشاشة "
              +
              "ويجعلها النافذة النشطة أمام كريم."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              window: {
                type:
                  "string"
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
            (
              "يقرأ عناصر وأزرار وحقول نافذة برنامج Windows "
              +
              "مباشرة عبر UI Automation بدون Screenshot."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              window: {
                type:
                  "string"
              },

              query: {
                type:
                  "string"
              },

              limit: {
                type:
                  "integer"
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
            (
              "يضغط مباشرة على زر أو عنصر داخل برنامج Windows "
              +
              "باستخدام UI Automation."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              window: {
                type:
                  "string"
              },

              name: {
                type:
                  "string"
              },

              controlType: {
                type:
                  "string"
              },

              occurrence: {
                type:
                  "integer"
              },

              confirmed: {
                type:
                  "boolean"
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
            (
              "يكتب مباشرة داخل حقل في برنامج Windows "
              +
              "باستخدام UI Automation."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              window: {
                type:
                  "string"
              },

              field: {
                type:
                  "string"
              },

              text: {
                type:
                  "string"
              },

              controlType: {
                type:
                  "string"
              },

              clear: {
                type:
                  "boolean"
              },

              pressEnter: {
                type:
                  "boolean"
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
            "يختار عنصراً من قائمة أو Tab داخل برنامج Windows.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              window: {
                type:
                  "string"
              },

              name: {
                type:
                  "string"
              },

              controlType: {
                type:
                  "string"
              },

              occurrence: {
                type:
                  "integer"
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
            (
              "يلتقط Screenshot حقيقي للشاشة ويحلله. "
              +
              "استخدمه فقط عندما يحتاج كريم رؤية الشاشة كاملة "
              +
              "أو عندما DOM/UIA غير قادرين."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              question: {
                type:
                  "string"
              }
            },

            additionalProperties:
              false
          }
        },


        // ==================================================
        // BROWSER DIRECT
        // ==================================================

        {
          name:
            "browser_status",

          description:
            "يفحص Chrome Direct ويعرض التبويب الحالي.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_read_page",

          description:
            (
              "يقرأ عناصر الصفحة الحالية مباشرة من DOM "
              +
              "بدون Screenshot."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              query: {
                type:
                  "string"
              },

              limit: {
                type:
                  "integer"
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
            (
              "يفتح رابطاً داخل Chrome ويجلب Chrome "
              +
              "إلى واجهة الشاشة أمام كريم."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              url: {
                type:
                  "string"
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
            (
              "يضغط مباشرة على عنصر داخل صفحة Chrome "
              +
              "حسب النص الظاهر في العنصر."
            ),

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              text: {
                type:
                  "string"
              },

              occurrence: {
                type:
                  "integer"
              },

              confirmed: {
                type:
                  "boolean"
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
            "يبحث داخل مربع البحث الموجود في الموقع الحالي.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              text: {
                type:
                  "string"
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
            "يشغل الفيديو الحالي مباشرة.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_pause_video",

          description:
            "يوقف الفيديو الحالي مباشرة.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_scroll",

          description:
            "يحرك صفحة Chrome، موجب للأسفل وسالب للأعلى.",

          parametersJsonSchema: {
            type:
              "object",

            properties: {
              amount: {
                type:
                  "integer"
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
            "يرجع صفحة للخلف في Chrome.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_forward",

          description:
            "يتقدم صفحة للأمام في Chrome.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

            additionalProperties:
              false
          }
        },


        {
          name:
            "browser_reload",

          description:
            "يعيد تحميل صفحة Chrome الحالية.",

          parametersJsonSchema: {
            type:
              "object",

            properties:
              {},

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


  switch (
    toolName
  ) {

    // ==================================================
    // TIME
    // ==================================================

    case "get_current_time":

      return {
        ok:
          true,

        timezone:
          KEMO_TIMEZONE,

        localIso:
          localIsoString(),

        human:
          humanLocalTime(),

        utc:
          new Date()
            .toISOString()
      };


    // ==================================================
    // REMINDERS
    // ==================================================

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


    // ==================================================
    // SEARCH
    // ==================================================

    case "search_web":

      return await searchWeb(
        args?.query
      );


    // ==================================================
    // MEMORY
    // ==================================================

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

            importance:
              5,

            source:
              "live_call"
          }
        );

      return {
        ok:
          true,

        memoryId
      };
    }


    // ==================================================
    // TELEGRAM
    // ==================================================

    case "send_telegram_message": {

      const text =
        cleanText(
          args?.text,
          12000
        );

      await sendTelegramMessage(
        userId,
        text
      );

      await saveSharedMessage(
        userId,
        "assistant",
        text
      );

      return {
        ok:
          true,

        sent:
          true
      };
    }


    // ==================================================
    // WHOLE-PC WINDOWS
    // ==================================================

    case "desktop_open_program": {

      const app =
        cleanText(
          args?.app,
          300
        );

      if (
        !app
      ) {
        throw new Error(
          "Program name missing"
        );
      }

      console.log(
        (
          "🚀 OPEN PROGRAM | "
          +
          app
        )
      );

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


    case "desktop_focus_window": {

      const window =
        cleanText(
          args?.window,
          500
        );

      console.log(
        (
          "🎯 FOCUS WINDOW | "
          +
          window
        )
      );

      return await runDesktopCommand(
        "window_activate",
        {
          window
        },
        15000
      );
    }


    case "desktop_read_app": {

      const window =
        cleanText(
          args?.window,
          500
        );

      const result =
        await runDesktopCommand(
          "uia_snapshot",
          {
            window,

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

      console.log(
        (
          "🪟 UIA READ | "
          +
          window
          +
          " | elements="
          +
          (
            result?.count
            ??
            "?"
          )
        )
      );

      return result;
    }


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
        actionNeedsConfirmation(
          name
        )
        &&
        args?.confirmed !==
          true
      ) {
        return {
          ok:
            true,

          completed:
            false,

          needsConfirmation:
            true,

          message:
            "هاي ضغطة حساسة أو نهائية. أكدلي أول."
        };
      }

      console.log(
        (
          "🖱️ UIA CLICK | "
          +
          window
          +
          " | "
          +
          name
        )
      );

      return await runDesktopCommand(
        "uia_execute",
        {
          action:
            "click",

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


    case "desktop_app_type": {

      const window =
        cleanText(
          args?.window,
          500
        );

      const field =
        cleanText(
          args?.field,
          500
        );

      const text =
        cleanText(
          args?.text,
          6000
        );

      console.log(
        (
          "⌨️ UIA TYPE | "
          +
          window
          +
          " | "
          +
          field
        )
      );

      return await runDesktopCommand(
        "uia_execute",
        {
          action:
            "type",

          window,

          name:
            field,

          value:
            text,

          controlType:
            cleanText(
              args?.controlType,
              100
            ),

          clear:
            args?.clear !==
            false,

          pressEnter:
            args?.pressEnter ===
            true
        },
        15000
      );
    }


    case "desktop_app_select": {

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

      return await runDesktopCommand(
        "uia_execute",
        {
          action:
            "select",

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


    case "desktop_screenshot":

      return await inspectScreen(
        cleanText(
          args?.question,
          1000
        )
        ||
        "شو ظاهر على الشاشة؟"
      );


    // ==================================================
    // BROWSER
    // ==================================================

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
          .test(
            url
          )
      ) {
        throw new Error(
          "Only http/https URLs allowed"
        );
      }

      console.log(
        (
          "🌐 OPEN URL | "
          +
          url
        )
      );

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
        actionNeedsConfirmation(
          text
        )
        &&
        args?.confirmed !==
          true
      ) {
        return {
          ok:
            true,

          completed:
            false,

          needsConfirmation:
            true,

          message:
            "هاي خطوة حساسة أو نهائية. أكدلي أول."
        };
      }

      console.log(
        (
          "🌐 DOM CLICK | "
          +
          text
        )
      );

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
    .slice(
      0,
      500
    )
    .map(
      item => {

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

        if (
          !text
        ) {
          return null;
        }

        return {
          role,
          text
        };
      }
    )
    .filter(
      Boolean
    );
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
      "4mb"
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

      res.json({
        ok:
          true,

        service:
          "kemo-call",

        version:
          "6.1-whole-pc-direct",

        model:
          LIVE_MODEL,

        voice:
          KEMO_VOICE,

        continuityMinutes:
          CALL_CONTINUITY_MINUTES,

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
          ok:
            false,

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
        "بدأت مكالمة Kemo Whole-PC",
        {
          callId,

          version:
            "6.1",

          wholePc:
            true
        }
      );

      res.json({
        ok:
          true,

        callId,

        callSecret,

        ephemeralToken,

        model:
          LIVE_MODEL,

        voice:
          KEMO_VOICE,

        timezone:
          KEMO_TIMEZONE,

        systemInstruction,

        liveTools:
          buildLiveTools(),

        continuity,

        permanentMemoryV2:
          true,

        sharedConversation:
          true,

        realtimeDesktop:
          true,

        wholePcDirect:
          true,

        browserDirect:
          true,

        windowsUIAutomation:
          true,

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
          ok:
            false,

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
          "🛠️ Live tool: "
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
              typeof req.body.args ===
                "object"
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
          ok:
            true,

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
          ok:
            false,

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
          ok:
            false,

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
          ok:
            false,

          error:
            error.message
        });
    }

    if (
      session.status ===
      "ended"
    ) {
      return res.json({
        ok:
          true,

        alreadySaved:
          true
      });
    }

    const transcript =
      sanitizeTranscript(
        req.body?.transcript
      );

    const client =
      await pool.connect();

    try {
      await client.query(
        "BEGIN"
      );

      for (
        const turn
        of transcript
      ) {
        await saveMessageWithArchive(
          client,
          session.userId,
          turn.role,
          turn.text
        );
      }

      await client.query(
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

      await client.query(
        "COMMIT"
      );

      res.json({
        ok:
          true,

        savedTurns:
          transcript.length,

        sharedConversation:
          true
      });

    } catch (error) {

      try {
        await client.query(
          "ROLLBACK"
        );
      } catch {}

      res
        .status(500)
        .json({
          ok:
            false,

          error:
            error.message
        });

    } finally {
      client.release();
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
      index:
        false
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
      req.method ===
        "GET"
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

  if (
    !TELEGRAM_BOT_TOKEN
  ) {
    missing.push(
      "TELEGRAM_BOT_TOKEN"
    );
  }

  if (
    !GEMINI_API_KEY
  ) {
    missing.push(
      "GEMINI_API_KEY"
    );
  }

  if (
    !DATABASE_URL
  ) {
    missing.push(
      "DATABASE_URL"
    );
  }

  if (
    missing.length
  ) {
    console.error(
      (
        "❌ Missing variables: "
        +
        missing.join(
          ", "
        )
      )
    );

    process.exit(
      1
    );
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
        " KEMO HUMAN CALL SERVER V6.1"
      );
      console.log(
        " WHOLE-PC REALTIME DIRECT CONTROL"
      );
      console.log(
        "======================================="
      );
      console.log("");

      console.log(
        `✅ Port: ${PORT}`
      );

      console.log(
        `✅ Live model: ${LIVE_MODEL}`
      );

      console.log(
        `✅ Voice: ${KEMO_VOICE}`
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
        "✅ Shared Telegram + Call conversation"
      );

      console.log(
        "✅ Shared Permanent Memory"
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

      console.log(
        (
          "🎯 Foreground control: "
          +
          (
            desktop?.foregroundControl
              ?
              "READY"
              :
              "not ready"
          )
        )
      );

      console.log(
        "🚀 Installed app launcher: READY"
      );

      console.log(
        "🖼️ Screenshot Vision: FALLBACK ONLY"
      );

      console.log(
        "🛡️ Sensitive final actions require confirmation"
      );

      console.log(
        (
          "✅ Tavily: "
          +
          (
            TAVILY_API_KEY
              ?
              "configured"
              :
              "MISSING"
          )
        )
      );

      console.log(
        (
          "✅ Shared Master Prompt: "
          +
          (
            master.ok
              ?
              "ready"
              :
              "MISSING"
          )
        )
      );

      console.log("");
    }
  );
}


start().catch(
  error => {
    console.error(
      "❌ Startup failed:",
      error
    );

    process.exit(
      1
    );
  }
);
