// Isolated PostgreSQL-WASM fixture. Never connects to DATABASE_URL or external APIs.
import { PGlite } from "@electric-sql/pglite";
import express from "express";
import fs from "node:fs";
import crypto from "node:crypto";
import { Store, id } from "./store.js";
import { registerRoutes } from "./routes.js";
import { Worker } from "./worker.js";
import { packageFields } from "./core.js";
export const TEST_TOKEN = "123456:test-only-not-a-real-token",
  TEST_USER = 42;
export function signedData(user = TEST_USER, age = 0) {
  const p = new URLSearchParams({
    auth_date: String(Math.floor(Date.now() / 1000) - age),
    user: JSON.stringify({ id: user, first_name: "مستخدم اختبار" }),
  });
  const check = [...p]
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");
  const key = crypto
    .createHmac("sha256", "WebAppData")
    .update(TEST_TOKEN)
    .digest();
  p.set("hash", crypto.createHmac("sha256", key).update(check).digest("hex"));
  return p.toString();
}
export async function fixture() {
  const pg = new PGlite();
  const wrap = (r) => ({
    ...r,
    rowCount: r.affectedRows || r.rows?.length || 0,
  });
  const pool = {
    query: async (sql, params) =>
      params?.length
        ? wrap(await pg.query(sql, params))
        : wrap((await pg.exec(sql)).at(-1)),
    connect: async () => ({ query: pool.query, release() {} }),
  };
  const server = fs.readFileSync(
    new URL("../server.js", import.meta.url),
    "utf8",
  );
  const start = server.indexOf(
    "CREATE TABLE IF NOT EXISTS xpand_content_campaigns",
  );
  const end =
    server.indexOf(
      "ON xpand_content_campaigns(user_id, created_at DESC);",
      start,
    ) + "ON xpand_content_campaigns(user_id, created_at DESC);".length;
  const statements = server.slice(start, end).replace(/`;\s*\n/g, "");
  for (const match of statements.matchAll(
    /CREATE (?:TABLE|INDEX) IF NOT EXISTS[\s\S]*?;/g,
  ))
    await pg.exec(match[0]);
  const store = new Store(pool);
  await store.migrate();
  const app = express();
  app.use(express.json());
  registerRoutes(app, store, { token: TEST_TOKEN, allowed: String(TEST_USER) });
  const http = app.listen(0, "127.0.0.1");
  await new Promise((r) => http.once("listening", r));
  const url = "http://127.0.0.1:" + http.address().port;
  const api = async (path, method = "GET", body, headers = {}) => {
    const response = await fetch(url + "/api/content" + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        "x-telegram-init-data": signedData(),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return { status: response.status, ...(await response.json()) };
  };
  return {
    pg,
    pool,
    store,
    app,
    http,
    url,
    api,
    close: async () => {
      await new Promise((r) => http.close(r));
      await pg.close();
    },
  };
}
export function mockProvider(counters = {}) {
  return async (url, options) => {
    if (url.includes("tavily")) {
      counters.search = (counters.search || 0) + 1;
      return Response.json({
        results: [
          {
            title: "مرجع اختباري فقط",
            url: "https://example.com/creative-reference",
            content:
              "A test description of a type-driven agency self promotion campaign. No effectiveness claims.",
          },
        ],
        usage: { credits: 1 },
      });
    }
    const prompt = JSON.parse(
        JSON.parse(options.body).contents[0].parts[0].text,
      ),
      c = prompt.trusted_context,
      i = prompt.instruction;
    let result;
    counters.model = (counters.model || 0) + 1;
    if (i.startsWith("Develop 3"))
      result = {
        directions: [0, 1, 2].map((n) => ({
          title: "اتجاه اختبار " + n,
          concept: "تصور إبداعي للاختبار فقط",
        })),
        missing_essential_information: [],
      };
    else if (i.startsWith("Evaluate"))
      result = {
        selected_index: 0,
        decision_rationale: "اختيار تجريبي لا يمثل بحثًا حقيقيًا",
        duplicate: false,
      };
    else if (i.startsWith("Review"))
      result = { pass: true, summary: "فحص آلي تجريبي", issues: [] };
    else if (i.startsWith("Identify"))
      result = {
        summary: "لا تغيير مفيد في الاختبار",
        no_change: true,
        ideas: [],
        occasions: [],
      };
    else
      result = {
        ...Object.fromEntries(
          packageFields.map((k) => [k, "محتوى اختباري · " + k]),
        ),
        title: "حملة اختبار معزولة · من التشويش إلى الوضوح",
        format: "video",
        platforms: ["Instagram", "Facebook", "TikTok"],
        scenes: [
          {
            timing: "0–3",
            visual: "تزاحم عناصر الإعلان",
            on_screen: "مين فهم الرسالة؟",
          },
          {
            timing: "3–12",
            visual: "المصمم يعيد تنظيم العناصر",
            on_screen: "قرار تصميم واضح",
          },
          {
            timing: "12–20",
            visual: "كشف الهوية وترتيب الرسالة",
            on_screen: "XPAND",
          },
        ],
        adaptations: [
          {
            platform: "Instagram",
            instructions: "نسخة عمودية",
            effort_hours: 0.5,
          },
        ],
        assets: ["الشعار الأصلي"],
        assumptions: ["اختبار فقط"],
        limitations: ["ليس بحثًا فعليًا"],
        effort_hours: 4,
        additional_resources: [],
        source_ids: [c.sources[0].id],
      };
    return Response.json({
      candidates: [
        {
          finishReason: "STOP",
          content: { parts: [{ text: JSON.stringify(result) }] },
        },
      ],
      usageMetadata: { totalTokenCount: 100 },
    });
  };
}
export const workerFor = (f, fetcher = mockProvider()) =>
  new Worker(f.store, {
    geminiKey: "test",
    searchKey: "test",
    model: "test-model",
    token: TEST_TOKEN,
    allowed: TEST_USER,
    fetcher,
  });
export async function enqueue(
  f,
  request = "حملة اختبار لخدمة الفيديو الإعلاني",
) {
  const r = await f.api(
    "/campaigns",
    "POST",
    { request },
    { "Idempotency-Key": id() },
  );
  if (!r.campaign) throw new Error(JSON.stringify(r));
  return r.campaign.id;
}
