import test from "node:test";
import assert from "node:assert/strict";
import { fixture, enqueue, workerFor, TEST_USER } from "./test-support.js";
import { defaultSettings, settingsInput } from "./core.js";
import { libraryCard } from "../content-command/library.js";

test("unlimited requests bypass count ceilings, preserve accounting and money protection", async () => {
  const f = await fixture();
  try {
    const settings = settingsInput({
      ...defaultSettings,
      unlimited_calls: true,
      daily_calls: 1,
      monthly_calls: 1,
      task_calls: 4,
    });
    await f.api("/settings", "PUT", settings);
    assert.equal((await f.api("/dashboard")).settings.unlimited_calls, true);
    const campaign = await enqueue(f);
    const worker = workerFor(f);
    const job = await worker.claim();
    for (let i = 0; i < 5; i++) await f.store.reserve(job, "model", "test");
    await f.store.assertAllowance(TEST_USER, campaign);
    assert.equal((await f.api("/dashboard")).usage.daily_calls, 5);
    assert.equal(
      libraryCard(
        { status: "blocked", attempts: 1, call_count: 5 },
        { daily_calls: 5, monthly_calls: 5 },
        settings,
      ).canRetry,
      true,
    );
    await f.api("/settings", "PUT", {
      ...settings,
      model_call_usd: 1,
      pricing_confirmed: true,
    });
    await assert.rejects(f.store.reserve(job, "model", "paid"), /الاستهلاك/);
    assert.equal((await f.api("/dashboard")).usage.daily_calls, 5);
    await f.api("/settings", "PUT", { ...settings, unlimited_calls: false });
    await assert.rejects(
      f.store.assertAllowance(TEST_USER, campaign),
      /حد اليوم/,
    );
    worker.stop();
  } finally {
    await f.close();
  }
});

test("unlimited mode requires explicit boolean opt-in", () => {
  assert.equal(settingsInput({}).unlimited_calls, false);
  assert.equal(
    settingsInput({ unlimited_calls: "true" }).unlimited_calls,
    false,
  );
});
