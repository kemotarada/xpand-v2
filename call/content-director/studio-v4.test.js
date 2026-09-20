import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { parseModelObject } from "./model-output.js";
import { validateCampaignPlan } from "./campaign-plan.js";
import { compactStoryboard } from "../content-command/compact-view.js";
import { Worker } from "./worker.js";
import { fixture, workerFor, mockProvider } from "./test-support.js";

const response = (text) => ({
  candidates: [{ finishReason: "STOP", content: { parts: [{ text }] } }],
});
test("model JSON accepts a whole fenced object but never partial/fake results", () => {
  assert.deepEqual(parseModelObject(response('```json\n{"title":"ok"}\n```')), {
    title: "ok",
  });
  for (const value of ['{"title":', "[]", "null", 'prefix {"title":"ok"}'])
    assert.throws(() => parseModelObject(response(value)));
  assert.throws(() =>
    parseModelObject({ candidates: [{ finishReason: "MAX_TOKENS" }] }),
  );
});
test("malformed output gets only one persisted, normally billed repair", async () => {
  let calls = 0;
  const job = { id: "test", checkpoint: {} };
  const worker = Object.create(Worker.prototype);
  worker.geminiKey = "test-only";
  worker.store = {
    checkpoint: async (j, s, data) => Object.assign(j.checkpoint, data),
  };
  worker.request = async () => {
    calls++;
    return response('{"broken":');
  };
  await assert.rejects(worker.modelJSON(job, "package", {}, "test"));
  assert.equal(calls, 2);
  assert.equal(job.checkpoint.output_repair_package, true);
  await assert.rejects(worker.modelJSON(job, "package", {}, "test"));
  assert.equal(calls, 3); // resume does not grant another repair
});
const sources = [{ id: "source" }];
function plan() {
  return {
    title: "حملة",
    objective: "تعريف بالخدمة",
    items: [
      {
        title: "رسالة ضائعة",
        format: "video",
        day: 1,
        concept: "رسالة تبحث عن صاحبها",
        mechanism: "قصة عكسية",
        message: "نوضح رسالتك",
        visual_direction: "ورق يتحرك",
        caption: "لنوضح فكرتك",
        source_ids: ["source"],
        duration_seconds: 6,
        scenes: [0, 2, 4].map((start) => ({
          start,
          end: start + 2,
          visual: "صورة",
          sound: "صوت",
          emotion: "فضول",
        })),
      },
      {
        title: "بوستر المسافة",
        format: "static",
        day: 2,
        concept: "المسافة بين سطرين تصبح بابا",
        mechanism: "استعارة بصرية",
        message: "نفتح فرصة",
        visual_direction: "حروف ومسافات",
        caption: "مساحة لفكرتك",
        composition: "عنوان فوق باب",
        source_ids: ["source"],
      },
    ],
  };
}
test("campaign plans need distinct mixed assets within duration and complete shot coverage", () => {
  assert.equal(validateCampaignPlan(plan(), 7, sources).items.length, 2);
  let p = plan();
  p.items[1].concept = p.items[0].concept;
  assert.throws(() => validateCampaignPlan(p, 7, sources), /تكرر/);
  p = plan();
  p.items[0].scenes[1].start = 3;
  assert.throws(() => validateCampaignPlan(p, 7, sources), /تسلسل/);
  p = plan();
  p.items[1].day = 8;
  assert.throws(() => validateCampaignPlan(p, 7, sources), /خارج/);
  p = plan();
  p.items[1].source_ids = ["fake"];
  assert.throws(() => validateCampaignPlan(p, 7, sources), /مراجع/);
});
test("compact storyboard escapes content and shows timed scenes without technical tables", () => {
  const esc = (v) => String(v).replaceAll("<", "&lt;");
  const result = plan().items[0];
  result.scenes[0].visual = "<script>";
  const html = compactStoryboard(result, esc);
  assert.ok(html.includes("&lt;script>"));
  assert.ok(!html.includes("<table"));
  assert.ok(html.includes("0–2 ثانية"));
});
test("home has today only and notifications own their navigation", () => {
  const html = fs.readFileSync(
    new URL("../content-command/index.html", import.meta.url),
    "utf8",
  );
  const home = html.split('id="home-view"')[1].split('id="campaigns-view"')[0];
  assert.ok(home.includes('id="today"'));
  assert.ok(!home.includes('id="operations"'));
  assert.ok(!html.includes('id="campaign-preview"'));
  assert.match(html.split("<nav")[1], /data-view="notifications"/);
});
test("goal-duration API persists a mixed campaign, no invented booked tasks and rejects another owner's alternative", async () => {
  const f = await fixture();
  try {
    const normal = mockProvider();
    const worker = workerFor(f, async (url, opts) => {
      if (!url.includes("tavily") && opts?.body) {
        const body = JSON.parse(opts.body);
        const prompt = JSON.parse(body.contents[0].parts[0].text);
        if (prompt.instruction.startsWith("CAMPAIGN_PLAN:")) {
          const p = plan();
          for (const item of p.items)
            item.source_ids = [prompt.trusted_context.sources[0].id];
          return Response.json(response(JSON.stringify(p)));
        }
      }
      return normal(url, opts);
    });
    const bad = await f.api(
      "/campaigns",
      "POST",
      { request: "حملة تعريف بشركة", campaign_days: 29 },
      { "Idempotency-Key": "invalid-days" },
    );
    assert.equal(bad.status, 400);
    const made = await f.api(
      "/campaigns",
      "POST",
      { request: "حملة تعريف بشركة XPAND", campaign_days: 7 },
      { "Idempotency-Key": "bundle" },
    );
    assert.ok(made.campaign);
    await worker.run(await worker.claim());
    const detail = await f.api("/campaigns/" + made.campaign.id);
    assert.equal(
      detail.campaign.status,
      "completed",
      JSON.stringify(detail.campaign),
    );
    assert.equal(detail.campaign.result.items.length, 2);
    assert.equal(
      (
        await f.pool.query(
          "SELECT count(*)::int AS n FROM xpand_content_tasks WHERE campaign_id=$1",
          [made.campaign.id],
        )
      ).rows[0].n,
      0,
    );
    const alt = await f.api(
      "/campaigns",
      "POST",
      {
        request: "بديل مختلف للحملة",
        alternative_to: made.campaign.id,
        campaign_days: 7,
      },
      { "Idempotency-Key": "alternative" },
    );
    const checkpoint = (
      await f.pool.query(
        "SELECT checkpoint FROM xpand_content_campaigns WHERE id=$1",
        [alt.campaign.id],
      )
    ).rows[0].checkpoint;
    assert.equal(checkpoint.excluded_concept.items.length, 2);
    const unavailable = await f.api(
      "/campaigns",
      "POST",
      {
        request: "بديل مختلف للحملة",
        alternative_to: "11111111-1111-4111-8111-111111111111",
      },
      { "Idempotency-Key": "not-owned" },
    );
    assert.equal(unavailable.status, 400);
  } finally {
    await f.close();
  }
});
