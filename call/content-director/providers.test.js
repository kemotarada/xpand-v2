import test from "node:test";
import assert from "node:assert/strict";
import {
  messageText,
  providerIssue,
  campaignPresentation,
  groundedResults,
} from "./providers.js";
import {
  fixture,
  workerFor,
  enqueue,
  mockProvider,
  TEST_USER,
} from "./test-support.js";
import { defaultSettings } from "./core.js";

const ground = () => ({
  candidates: [
    {
      finishReason: "STOP",
      content: { parts: [{ text: "A source-backed description." }] },
      groundingMetadata: {
        webSearchQueries: ["agency self promotion"],
        groundingChunks: [
          {
            web: {
              title: "Actual API citation",
              uri: "https://example.com/research",
            },
          },
        ],
        groundingSupports: [
          {
            segment: {
              text: "An agency uses a type-led self-promotion concept.",
            },
            groundingChunkIndices: [0],
          },
        ],
        searchEntryPoint: {
          renderedContent:
            '<a href="https://www.google.com/search?q=agency" target="_blank">Google Search</a>',
        },
      },
    },
  ],
  usageMetadata: { totalTokenCount: 250 },
});

test("structured provider errors are readable, categorized, and do not disclose raw secrets", () => {
  assert.equal(messageText({ error: { detail: "شرح السبب" } }), "شرح السبب");
  assert.equal(messageText({}), "تعذر إتمام الطلب.");
  const issue = providerIssue("tavily", 432, {
    error: { message: "secret-key-value" },
  });
  assert.equal(issue.code, "plan_limit");
  assert.doesNotMatch(issue.message, /object Object|secret-key-value/);
  assert.equal(
    providerIssue("gemini:m", 429, {
      error: { details: [{ violations: [{ quotaValue: 0 }] }] },
    }).code,
    "quota_unavailable",
  );
  assert.equal(providerIssue("gemini:m", 404).code, "model_unavailable");
  assert.equal(providerIssue("tavily", 433).code, "plan_limit");
});

test("legacy degraded completions remain saved but cannot appear verified", () => {
  const old = {
    status: "completed",
    limitations: "تعذر الوصول إلى البحث الخارجي: [object Object]",
    result: { title: "محفوظ" },
    checkpoint: { private: true },
  };
  const view = campaignPresentation(old);
  assert.equal(view.display_status, "unverified_result");
  assert.equal(view.status, "completed");
  assert.doesNotMatch(view.limitations, /object Object/);
  assert.equal(view.result, old.result);
  assert.equal(view.checkpoint, undefined);
  assert.match(old.limitations, /object Object/);
});

test("search fallback accepts only provider grounding citations, not model-written URLs", () => {
  assert.equal(groundedResults(ground()).results.length, 1);
  assert.throws(() =>
    groundedResults({
      candidates: [
        {
          finishReason: "STOP",
          content: { parts: [{ text: "https://invented.example" }] },
        },
      ],
    }),
  );
  const bad = ground();
  bad.candidates[0].groundingMetadata.groundingSupports = [];
  assert.throws(() => groundedResults(bad));
});

test("Tavily 432 uses bounded Gemini fallback, caches citations and completes a full package", async () => {
  const f = await fixture();
  try {
    const calls = { tavily: 0, grounding: 0 };
    const normal = mockProvider(calls);
    const worker = workerFor(f, async (url, opts) => {
      if (url.includes("tavily")) {
        calls.tavily++;
        return Response.json(
          { error: { message: "plan quota" } },
          { status: 432 },
        );
      }
      if (JSON.parse(opts.body).tools) {
        calls.grounding++;
        return Response.json(ground());
      }
      return normal(url, opts);
    });
    const campaignId = await enqueue(f);
    await worker.run(await worker.claim());
    let details = await f.api("/campaigns/" + campaignId);
    assert.equal(
      details.campaign.status,
      "completed",
      details.campaign.limitations,
    );
    assert.equal(details.campaign.limitations, "");
    assert.equal(calls.tavily, 1); // second query respects the persisted provider cooldown
    assert.equal(calls.grounding, 2);
    assert.equal(details.calls.length, 7);
    assert.equal(details.sources.length, 1);
    assert.equal(
      JSON.parse(details.sources[0].observation).engine,
      "gemini_grounding",
    );
    assert.ok(JSON.parse(details.sources[0].observation).search_suggestions);
    const next = await enqueue(f);
    await worker.run(await worker.claim());
    assert.equal(
      (await f.api("/campaigns/" + next)).campaign.status,
      "completed",
    );
    assert.equal(calls.grounding, 2); // reused cache is auditable
    worker.stop();
  } finally {
    await f.close();
  }
});

test("both providers blocked: no fake campaign, no rapid retries, scheduler pauses without quota churn", async () => {
  const f = await fixture();
  try {
    await f.store.record(TEST_USER, "settings", "main", {
      ...defaultSettings,
      recurring: true,
      pricing_confirmed: true,
      search_provider: "gemini",
    });
    let outbound = 0;
    const worker = workerFor(f, async (url) => {
      outbound++;
      return Response.json(
        { error: { message: "denied" } },
        { status: url.includes("tavily") ? 432 : 429 },
      );
    });
    const cid = await enqueue(f);
    await worker.run(await worker.claim());
    assert.equal((await f.api("/campaigns/" + cid)).campaign.status, "blocked");
    assert.equal(
      (await f.api("/campaigns/" + cid + "/retry", "POST")).status,
      400,
    );
    await worker.schedule();
    await worker.schedule();
    const dash = await f.api("/dashboard");
    assert.equal(dash.campaigns.length, 1);
    assert.equal(dash.tasks.length, 0);
    assert.equal(dash.usage.daily_calls, 1);
    assert.equal(
      dash.records.find((r) => r.kind === "worker").data.paused_for_provider,
      true,
    );
    assert.equal(outbound, 1);
    await f.api("/providers/recheck", "POST");
    assert.equal(
      (await f.api("/campaigns/" + cid + "/retry", "POST")).status,
      200,
    );
    assert.equal((await f.api("/dashboard")).usage.daily_calls, 1);
    worker.stop();
  } finally {
    await f.close();
  }
});

test("Telegram opt-in does not send old pending notifications or reset its activation cutoff", async () => {
  const f = await fixture();
  try {
    await f.store.notify(TEST_USER, "before-opt-in", "تنبيه قديم");
    await f.pool.query(
      "UPDATE xpand_director_records SET created_at=NOW()-INTERVAL '1 day' WHERE record_key='before-opt-in'",
    );
    let databaseClockReads = 0;
    const query = f.pool.query;
    f.pool.query = async (sql, params) => {
      if (sql.includes("clock_timestamp() AS instant")) databaseClockReads++;
      return query(sql, params);
    };
    await f.api("/settings", "PUT", { ...defaultSettings, telegram: true });
    assert.equal(
      databaseClockReads,
      1,
      "cutoff must use the same database clock as notification creation",
    );
    const first = (await f.store.config(TEST_USER)).settings;
    await f.api("/settings", "PUT", { ...first, daily_calls: 19 });
    assert.equal(
      (await f.store.config(TEST_USER)).settings.telegram_since,
      first.telegram_since,
    );
    let sends = 0;
    const worker = workerFor(f, async () => {
      sends++;
      return Response.json({ ok: true });
    });
    await worker.deliver(first);
    assert.equal(sends, 0);
    await f.store.notify(TEST_USER, "after-opt-in", "تنبيه جديد");
    await worker.deliver(first);
    await worker.deliver(first);
    assert.equal(sends, 1);
    worker.stop();
  } finally {
    await f.close();
  }
});
