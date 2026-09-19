import test from "node:test";
import assert from "node:assert/strict";
import {
  fixture,
  enqueue,
  workerFor,
  mockProvider,
  TEST_USER,
} from "./test-support.js";
import { defaultSettings, defaultProfile } from "./core.js";
test("real SQL migration, authenticated API, durable pipeline and task history", async () => {
  const f = await fixture();
  try {
    await f.store.migrate();
    assert.equal(
      (
        await f.api("/dashboard", "GET", undefined, {
          "x-telegram-init-data": "",
        })
      ).status,
      401,
    );
    const first = await f.api(
      "/campaigns",
      "POST",
      { request: "حملة تصميم أصلية للاختبار" },
      { "Idempotency-Key": "same" },
    );
    const duplicate = await f.api(
      "/campaigns",
      "POST",
      { request: "حملة تصميم أصلية للاختبار" },
      { "Idempotency-Key": "same" },
    );
    assert.equal(first.campaign.id, duplicate.campaign.id);
    const calls = {};
    const worker = workerFor(f, mockProvider(calls));
    const job = await worker.claim();
    assert.equal(job.status, "running");
    await worker.run(job);
    const details = await f.api("/campaigns/" + job.id);
    assert.equal(
      details.campaign.status,
      "completed",
      details.campaign.limitations,
    );
    assert.equal(details.sources.length, 1);
    assert.equal(calls.model, 4);
    assert.equal(calls.search, 2);
    let dash = await f.api("/dashboard");
    assert.equal(dash.tasks.length, 1);
    assert.equal(dash.metrics.planned, 1);
    assert.equal(dash.tasks[0].actual_published_at, null);
    assert.equal(await worker.claim(), null);
    let t = dash.tasks[0];
    const started = await f.api("/tasks/" + t.id, "PATCH", {
      status: "in_production",
      version: t.version,
    });
    assert.equal(started.task.locked, true);
    assert.equal(
      (
        await f.api("/tasks/" + t.id, "PATCH", {
          status: "in_review",
          version: 1,
        })
      ).status,
      400,
    );
    t = started.task;
    assert.equal(
      (
        await f.api("/tasks/" + t.id, "PATCH", {
          status: "published",
          version: t.version,
        })
      ).status,
      400,
    );
    const published = await f.api("/tasks/" + t.id, "PATCH", {
      status: "published",
      version: t.version,
      confirm_published: true,
    });
    assert.ok(published.task.actual_published_at);
    assert.equal((await f.api("/dashboard")).metrics.published, 1);
    assert.equal(
      (
        await f.pool.query(
          "SELECT count(*)::int n FROM xpand_director_versions",
        )
      ).rows[0].n,
      2,
    );
    worker.stop();
  } finally {
    await f.close();
  }
});
test("restart reclaims expired lease; checkpoints resume, no duplicate final task", async () => {
  const f = await fixture();
  try {
    const campaignId = await enqueue(f);
    const first = workerFor(f);
    const job = await first.claim();
    const ctx = await first.context(job);
    first.active.set(job.id, new AbortController());
    await first.collect(job, ctx);
    first.stop();
    await f.pool.query(
      "UPDATE xpand_content_campaigns SET lease_until=NOW()-INTERVAL '1 minute' WHERE id=$1",
      [campaignId],
    );
    const calls = {};
    const second = workerFor(f, mockProvider(calls));
    const resumed = await second.claim();
    assert.equal(resumed.id, campaignId);
    assert.equal(resumed.attempts, 2);
    await second.run(resumed);
    assert.equal(calls.search, undefined);
    assert.equal((await f.api("/dashboard")).tasks.length, 1);
    assert.equal(
      (await f.api("/campaigns/" + campaignId)).campaign.status,
      "completed",
    );
    second.stop();
  } finally {
    await f.close();
  }
});
test("search failure is visible; cancellation prevents later stages", async () => {
  const f = await fixture();
  try {
    const campaignId = await enqueue(f);
    const worker = workerFor(f, async () =>
      Response.json({ error: "denied" }, { status: 429 }),
    );
    await worker.run(await worker.claim());
    const c = await f.api("/campaigns/" + campaignId);
    assert.equal(c.campaign.status, "blocked");
    assert.match(c.campaign.limitations, /429/);
    assert.equal((await f.api("/dashboard")).tasks.length, 0);
    const secondId = await enqueue(f);
    const claimed = await worker.claim();
    assert.equal(claimed.id, secondId);
    await f.api("/campaigns/" + secondId + "/cancel", "POST");
    await worker.run(claimed);
    assert.equal(
      (await f.api("/campaigns/" + secondId)).campaign.status,
      "cancelled",
    );
    assert.equal((await f.api("/campaigns/" + secondId)).calls.length, 0);
    worker.stop();
  } finally {
    await f.close();
  }
});
test("budget reservations stop model execution; retry does not erase spend", async () => {
  const f = await fixture();
  try {
    await f.store.record(TEST_USER, "settings", "main", {
      ...defaultSettings,
      daily_calls: 1,
    });
    const campaignId = await enqueue(f);
    const worker = workerFor(f);
    await worker.run(await worker.claim());
    assert.equal(
      (await f.api("/campaigns/" + campaignId)).campaign.status,
      "blocked",
    );
    assert.equal((await f.api("/dashboard")).usage.daily_calls, 1);
    await f.api("/campaigns/" + campaignId + "/retry", "POST");
    await worker.run(await worker.claim());
    assert.equal((await f.api("/dashboard")).usage.daily_calls, 1);
    worker.stop();
  } finally {
    await f.close();
  }
});
test("scheduler deduplicates lateness and never auto-publishes; no filler cycles", async () => {
  const f = await fixture();
  try {
    await f.api("/tasks", "POST", {
      title: "مهمة متأخرة",
      planned_at: "2026-01-01T12:00",
    });
    const worker = workerFor(f);
    await worker.schedule();
    await worker.schedule();
    let dash = await f.api("/dashboard");
    assert.equal(dash.tasks[0].status, "planned");
    assert.equal(
      dash.records.filter((r) => r.kind === "notification").length,
      1,
    );
    assert.equal(dash.campaigns.length, 0);
    await f.store.record(TEST_USER, "settings", "main", {
      ...defaultSettings,
      recurring: true,
      pricing_confirmed: true,
    });
    await worker.schedule();
    await worker.schedule();
    dash = await f.api("/dashboard");
    assert.equal(dash.campaigns.length, 1);
    await worker.run(await worker.claim());
    dash = await f.api("/dashboard");
    assert.equal(dash.records.filter((r) => r.kind === "idea").length, 0);
    assert.equal(
      dash.records.filter((r) => r.kind === "notification").length,
      1,
    );
    worker.stop();
  } finally {
    await f.close();
  }
});
test("company facts, occasion validation and versioned changes persist", async () => {
  const f = await fixture();
  try {
    await f.api("/profile", "PUT", {
      ...defaultProfile,
      preferences: "لا تهنئة عامة بلا خدمة",
    });
    assert.equal(
      (await f.api("/dashboard")).profile.preferences,
      "لا تهنئة عامة بلا خدمة",
    );
    assert.equal(
      (
        await f.api("/occasions", "POST", {
          name: "مثال",
          date: "2026-02-30",
          source: "https://example.com",
          status: "confirmed",
        })
      ).status,
      400,
    );
    const data = {
      name: "حدث اختباري",
      date: "2026-12-01",
      source: "https://example.com/date",
      geography: "فلسطين",
      status: "provisional",
    };
    await f.api("/occasions", "POST", data);
    await f.api("/occasions", "POST", { ...data, date: "2026-12-02" });
    const dash = await f.api("/dashboard");
    assert.equal(dash.records.filter((r) => r.kind === "occasion").length, 1);
    assert.equal(
      dash.records.filter((r) => r.kind === "notification").length,
      1,
    );
  } finally {
    await f.close();
  }
});
test("paid reservation cap blocks before external call, other worker cannot finalize cancelled job", async () => {
  const f = await fixture();
  try {
    await f.store.record(TEST_USER, "settings", "main", {
      ...defaultSettings,
      pricing_confirmed: true,
      search_call_usd: 1,
      daily_usd: 0.5,
      monthly_usd: 1,
    });
    let calls = 0;
    const worker = workerFor(f, async () => {
      calls++;
      return Response.json({});
    });
    const campaignId = await enqueue(f);
    await worker.run(await worker.claim());
    assert.equal(calls, 0);
    assert.equal(
      (await f.api("/campaigns/" + campaignId)).campaign.status,
      "blocked",
    );
    const secondId = await enqueue(f);
    const job = await worker.claim();
    await f.api("/campaigns/" + secondId + "/cancel", "POST");
    await assert.rejects(f.store.checkpoint(job, "saving_plan", {}));
    assert.equal((await f.api("/dashboard")).tasks.length, 0);
    worker.stop();
  } finally {
    await f.close();
  }
});
test("Telegram quiet hours and delivery reservation prevent duplicate sends", async () => {
  const f = await fixture();
  try {
    const worker = workerFor(f, async () => Response.json({ ok: true }));
    await f.store.notify(TEST_USER, "one", "تذكير اختباري");
    await worker.deliver({ ...defaultSettings, notification_cap: 1 });
    await worker.deliver({ ...defaultSettings, notification_cap: 1 });
    const rows = await f.store.records(TEST_USER, "notification");
    assert.equal(rows.length, 1);
    assert.equal(rows[0].data.delivery, "sent");
    await f.store.notify(TEST_USER, "two", "تذكير اختباري آخر");
    await worker.deliver({ ...defaultSettings, notification_cap: 1 });
    assert.equal(
      (await f.store.records(TEST_USER, "notification")).find(
        (x) => x.record_key === "two",
      ).data.delivery,
      "pending",
    );
    worker.stop();
  } finally {
    await f.close();
  }
});
