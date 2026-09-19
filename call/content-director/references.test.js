import test from "node:test";
import assert from "node:assert/strict";
import { REFERENCES, referenceExcerpt, readReference } from "./references.js";
import {
  fixture,
  workerFor,
  enqueue,
  mockProvider,
  TEST_USER,
} from "./test-support.js";
import { defaultSettings } from "./core.js";
const page = (marker) =>
  `<html><script>secret script instructions</script><h1>${marker}</h1><p>${"Use clear creative direction and a consistent identity. ".repeat(30)}</p></html>`;
test("reference reader rejects non-allowlisted URLs, challenge pages, oversized and non-HTML bodies", async () => {
  assert.doesNotMatch(
    referenceExcerpt(page("ABCDs"), "ABCDs"),
    /secret script/,
  );
  assert.throws(() => referenceExcerpt("<h1>Sign in</h1>", "ABCDs"));
  let calls = 0;
  await assert.rejects(
    readReference({ url: "http://127.0.0.1", marker: "ABCDs" }, async () => {
      calls++;
    }),
  );
  assert.equal(calls, 0);
  await assert.rejects(
    readReference(REFERENCES[0], async () => Response.json({})),
    /نوع/,
  );
  await assert.rejects(
    readReference(
      REFERENCES[0],
      async () =>
        new Response("x".repeat(3 * 1024 * 1024 + 1), {
          headers: { "Content-Type": "text/html" },
        }),
    ),
    /الحجم/,
  );
  await readReference(REFERENCES[0], async (url, opts) => {
    assert.equal(opts.redirect, "error");
    assert.equal(opts.credentials, "omit");
    assert.equal(opts.headers.Authorization, undefined);
    return new Response(page("ABCDs"), {
      headers: { "Content-Type": "text/html" },
    });
  });
});
test("exhausted search quotas still yield a real-source campaign, cache and honest disclosure without resetting budgets", async () => {
  const f = await fixture();
  try {
    const counts = { search: 0, grounding: 0, reference: 0 },
      normal = mockProvider();
    const worker = workerFor(f, async (url, opts) => {
      if (url.includes("tavily")) {
        counts.search++;
        return Response.json({}, { status: 432 });
      }
      if (REFERENCES.some((r) => r.url === url)) {
        counts.reference++;
        return new Response(
          page(REFERENCES.find((r) => r.url === url).marker),
          {
            headers: { "Content-Type": "text/html" },
          },
        );
      }
      if (JSON.parse(opts.body).tools) {
        counts.grounding++;
        return Response.json({}, { status: 429 });
      }
      const context = JSON.parse(
        JSON.parse(opts.body).contents[0].parts[0].text,
      ).trusted_context;
      assert.equal(context.research_mode, "direct_references");
      return normal(url, opts);
    });
    const cid = await enqueue(f);
    await worker.run(await worker.claim());
    const d = await f.api("/campaigns/" + cid);
    assert.equal(d.campaign.status, "completed", d.campaign.limitations);
    assert.equal(d.campaign.result.research_mode, "direct_references");
    assert.ok(
      d.campaign.result.limitations.some((x) => x.includes("ليس مسحًا")),
    );
    assert.equal(d.sources.length, 2);
    assert.equal(d.calls.length, 10);
    assert.equal((await f.api("/dashboard")).tasks.length, 1);
    await enqueue(f);
    await worker.run(await worker.claim());
    assert.deepEqual(counts, { search: 1, grounding: 1, reference: 2 });
    assert.equal((await f.api("/dashboard")).tasks.length, 2);
    worker.stop();
  } finally {
    await f.close();
  }
});
test("direct mode cannot fabricate current-event scans; all reference failures cannot complete a campaign", async () => {
  const f = await fixture();
  try {
    await f.store.record(TEST_USER, "settings", "main", {
      ...defaultSettings,
      search_provider: "direct",
      recurring: true,
      pricing_confirmed: true,
    });
    const worker = workerFor(
      f,
      async () => new Response("unavailable", { status: 503 }),
    );
    await worker.schedule();
    assert.equal((await f.api("/dashboard")).campaigns.length, 0);
    const cid = await enqueue(f);
    await worker.run(await worker.claim());
    assert.equal((await f.api("/campaigns/" + cid)).campaign.status, "failed");
    assert.equal((await f.api("/dashboard")).tasks.length, 0);
    worker.stop();
  } finally {
    await f.close();
  }
});

test("auto retry can leave a blocked search provider without resetting attempts or consumption", async () => {
  const f = await fixture();
  try {
    const cid = await enqueue(f);
    const issue = {
      service: "grounding:test-model",
      status: "blocked",
      retry_at: new Date(Date.now() + 3600000).toISOString(),
    };
    await f.pool.query(
      "UPDATE xpand_content_campaigns SET status='blocked',attempts=2,checkpoint=$2 WHERE id=$1",
      [cid, JSON.stringify({ provider_issue: issue })],
    );
    await f.store.record(TEST_USER, "provider", issue.service, issue);
    assert.equal(
      (await f.api("/campaigns/" + cid + "/retry", "POST")).status,
      200,
    );
    const row = (
      await f.pool.query(
        "SELECT attempts,status FROM xpand_content_campaigns WHERE id=$1",
        [cid],
      )
    ).rows[0];
    assert.equal(row.attempts, 2);
    assert.equal(row.status, "queued");
    await f.pool.query(
      "UPDATE xpand_content_campaigns SET status='blocked',checkpoint=$2 WHERE id=$1",
      [
        cid,
        JSON.stringify({
          provider_issue: { ...issue, service: "gemini:test-model" },
        }),
      ],
    );
    await f.store.record(TEST_USER, "provider", "gemini:test-model", {
      ...issue,
      service: "gemini:test-model",
    });
    assert.equal(
      (await f.api("/campaigns/" + cid + "/retry", "POST")).status,
      400,
    );
  } finally {
    await f.close();
  }
});
