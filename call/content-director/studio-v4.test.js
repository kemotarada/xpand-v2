import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { parseModelObject } from "./model-output.js";
import { outputSchema } from "./output-schema.js";
import {
  validateCampaignPlan,
  stockMechanismIssue,
  validateOrRepairPlan,
} from "./campaign-plan.js";
import { selectReferences } from "./references.js";
import { compactStoryboard } from "../content-command/compact-view.js";
import { Worker } from "./worker.js";
import { fixture, workerFor, mockProvider } from "./test-support.js";

const response = (text) => ({
  candidates: [{ finishReason: "STOP", content: { parts: [{ text }] } }],
});
test("storyboard generation constrains every field and resumes with saved proposal", async () => {
  const schema = outputSchema("storyboard", {
    proposal: { duration_seconds: 15 },
  });
  assert.deepEqual(schema.properties.duration_seconds.enum, [15]);
  assert.equal(schema.properties.beats.minItems, undefined);
  assert.equal(schema.properties.beats.maxItems, undefined);
  assert.equal(outputSchema("storyboard", { proposal: { duration_seconds: 60 } }).properties.beats.maxItems, undefined);
  assert.ok(schema.properties.scenes.items.required.includes("visual"));
  assert.ok(schema.properties.beats.items.required.includes("visual_change"));
  assert.equal(outputSchema("insights", {}), undefined);
  const worker = Object.create(Worker.prototype);
  worker.geminiKey = "test-only";
  const proposal = { duration_seconds: 15, concept: "saved concept" };
  const job = {
    id: "test",
    checkpoint: { proposal, output_repair_storyboard: true },
  };
  let calls = 0;
  worker.request = async (j, provider, stage, url, body) => {
    calls++;
    assert.deepEqual(body.generationConfig.responseJsonSchema, schema);
    assert.deepEqual(
      JSON.parse(body.contents[0].parts[0].text).trusted_context.proposal,
      proposal,
    );
    return response('{"duration_seconds":15}');
  };
  await worker.modelJSON(job, "storyboard", { proposal }, "test");
  assert.equal(calls, 1);
  assert.equal(job.checkpoint.output_repair_storyboard, true);
});
test("temporary model errors retry once after cooldown, quota errors never spin", async () => {
  const worker = Object.create(Worker.prototype);
  worker.geminiKey = "test-only";
  worker.active = new Map([["test", new AbortController()]]);
  worker.store = {
    checkpoint: async (j, s, d) => Object.assign(j.checkpoint, d),
  };
  let calls = 0;
  const job = { id: "test", checkpoint: {} };
  worker.request = async () => {
    calls++;
    if (calls === 1) {
      const e = new Error("temporary");
      e.issue = { http_status: 503, retry_at: new Date().toISOString() };
      throw e;
    }
    return response('{"ok":true}');
  };
  assert.deepEqual(await worker.modelJSON(job, "review", {}, "test"), {
    ok: true,
  });
  assert.equal(calls, 2);
  assert.equal(job.checkpoint.transient_retry_review, true);
  calls = 0;
  worker.request = async () => {
    calls++;
    const e = new Error("quota");
    e.issue = { http_status: 429, retry_at: new Date().toISOString() };
    throw e;
  };
  await assert.rejects(
    worker.modelJSON({ id: "test", checkpoint: {} }, "review", {}, "test"),
  );
  assert.equal(calls, 1);
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
        headline: "اترك مساحة لفكرتك",
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
  const repetitive = plan();
  repetitive.items[0].concept = "فوضى تتحول إلى ترتيب واضح";
  assert.match(stockMechanismIssue(repetitive), /قالبًا/);
  assert.equal(stockMechanismIssue(plan()), null);
  const promise = plan();
  promise.items[0].caption = "يجعل العميل يشتري بلا تردد";
  assert.match(stockMechanismIssue(promise), /غير مثبت/);
  const vague = plan();
  vague.items[0].scenes[0].visual = "ظهور موشن جرافيك تفاعلي يختصر الخدمة";
  assert.match(stockMechanismIssue(vague), /لا تحدد/);
  const leakedBrand = plan();
  leakedBrand.items[0].concept = "منيو مطعم يحمل شعار XPAND";
  assert.match(stockMechanismIssue(leakedBrand), /تخلط دور XPAND/);
  const fragileMotion = plan();
  fragileMotion.items[0].scenes[0].action = "يد صاحب العمل تفتح مقبض باب زجاجي";
  assert.match(stockMechanismIssue(fragileMotion), /تفاعل يد/);
  assert.match(selectReferences("فيديو لا تكرر الشعار")[0].url, /google/);
  assert.equal(validateCampaignPlan(plan(), 7, sources).items.length, 2);
  const clockPlan = plan();
  for (const s of clockPlan.items[0].scenes) {
    s.start = `00:0${s.start}`;
    s.end = `00:0${s.end}`;
  }
  assert.equal(
    validateCampaignPlan(clockPlan, 7, sources).items[0].scenes[1].start,
    2,
  );
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
test("a missing campaign field is repaired once without accepting a partial plan", async () => {
  const bad = plan();
  delete bad.items[0].visual_direction;
  let calls = 0;
  const job = { checkpoint: {} };
  const worker = {
    store: { checkpoint: async (j, s, d) => Object.assign(j.checkpoint, d) },
    modelJSON: async () => {
      calls++;
      return plan();
    },
  };
  assert.equal(
    (await validateOrRepairPlan(worker, job, bad, 7, sources, {}, "test")).items
      .length,
    2,
  );
  assert.equal(calls, 1);
  await assert.rejects(
    validateOrRepairPlan(worker, job, bad, 7, sources, {}, "test"),
  );
  assert.equal(calls, 1);
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
