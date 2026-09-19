import test from "node:test";
import assert from "node:assert/strict";
import {
  validateStoryboard,
  validateInsights,
  validateTreatment,
  validateWeek,
  validateDirections,
  reviewIssue,
} from "./creative.js";
import {
  availableWeek,
  taskEvents,
  addDays,
  effortLabel,
} from "../content-command/planning.js";
import {
  fixture,
  workerFor,
  enqueue,
  mockStoryboard,
  TEST_USER,
  mockProvider,
} from "./test-support.js";
import { localClock } from "./core.js";
import { creativeView } from "../content-command/creative-view.js";
import { libraryCard } from "../content-command/library.js";
test("library distinguishes unfinished requests from results and explains each exhausted cap", () => {
  const c = {
    status: "blocked",
    attempts: 1,
    request_text: "طلب طويل ".repeat(50),
    call_count: 10,
  };
  const limits = { daily_calls: 20, monthly_calls: 200, task_calls: 10 };
  let card = libraryCard(c, { daily_calls: 27, monthly_calls: 27 }, limits);
  assert.ok(card.heading.length < 60);
  assert.equal(card.complete, false);
  assert.equal(card.canRetry, false);
  assert.match(card.budgetReason, /حد اليوم/);
  card = libraryCard(c, { daily_calls: 2, monthly_calls: 2 }, limits);
  assert.match(card.budgetReason, /حد المهمة/);
  assert.equal(
    libraryCard(
      { ...c, status: "completed", result: { title: "فكرة محفوظة" } },
      {},
      limits,
    ).heading,
    "فكرة محفوظة",
  );
});
test("exhausted retry/new/week requests do not consume attempts or create junk cards", async () => {
  const f = await fixture();
  const w = workerFor(f);
  try {
    const id = await enqueue(f);
    await w.run(await w.claim());
    const initial = await f.api("/campaigns/" + id);
    await f.pool.query(
      "UPDATE xpand_content_campaigns SET status='blocked' WHERE id=$1",
      [id],
    );
    const settings = (await f.store.config(TEST_USER)).settings;
    await f.store.record(TEST_USER, "settings", "main", {
      ...settings,
      daily_calls: 1,
    });
    assert.equal(
      (await f.api("/campaigns/" + id + "/retry", "POST")).status,
      400,
    );
    assert.equal(
      (
        await f.api(
          "/campaigns",
          "POST",
          { request: "فكرة جديدة لا تنشأ فوق الحد" },
          { "Idempotency-Key": "blocked-new" },
        )
      ).status,
      400,
    );
    assert.equal(
      (
        await f.api(
          "/week-plan",
          "POST",
          {},
          { "Idempotency-Key": "blocked-week" },
        )
      ).status,
      400,
    );
    const after = await f.api("/campaigns/" + id);
    assert.equal(after.campaign.attempts, initial.campaign.attempts);
    assert.equal(after.calls.length, initial.calls.length);
    assert.equal((await f.api("/dashboard")).campaigns.length, 1);
  } finally {
    w.stop();
    await f.close();
  }
});
test("creative gates require distinct mechanisms and a justified review, not automatic praise", () => {
  const r = {
    directions: ["demonstration", "narrative_reversal", "sound_led"].map(
      (mechanism_type) => ({
        mechanism_type,
        problem: "مشكلة واضحة",
        change: "تغير محدد",
        service_proof: "إثبات للخدمة",
        opening_action: "فعل افتتاحي",
        final_reveal: "كشف واضح",
        source_ids: [],
      }),
    ),
  };
  validateDirections(r, []);
  r.directions[2].mechanism_type = "demonstration";
  assert.throws(() => validateDirections(r, []));
  assert.ok(reviewIssue({ pass: true, summary: "رائع" }));
  const review = {
    pass: true,
    issues: [],
    assessments: ["idea", "service", "evidence", "execution"].map(
      (criterion) => ({
        criterion,
        score: 2,
        reason: "قرار محدد قابل للمراجعة",
      }),
    ),
  };
  assert.equal(reviewIssue(review), "");
  review.assessments[0].score = 1;
  assert.ok(reviewIssue(review));
  review.assessments[0].score = 2;
  review.issues = ["اعتماد غير مبرر على كشف الشعار وحده"];
  assert.ok(reviewIssue(review));
});
test("timing repair reuses the passed treatment and repairs only the storyboard within the existing cap", async () => {
  const f = await fixture();
  const normal = mockProvider();
  let packages = 0,
    boards = 0,
    reviews = 0;
  const w = workerFor(f, async (url, options) => {
    if (url.includes("tavily")) return normal(url, options);
    const prompt = JSON.parse(
      JSON.parse(options.body).contents[0].parts[0].text,
    );
    if (prompt.instruction.startsWith("Return JSON with")) packages++;
    if (prompt.instruction.startsWith("Review")) reviews++;
    if (prompt.instruction.startsWith("STORYBOARD_V3")) {
      boards++;
      if (boards === 1) {
        const broken = mockStoryboard();
        broken.beats[2].end = 4;
        return Response.json({
          candidates: [
            {
              finishReason: "STOP",
              content: { parts: [{ text: JSON.stringify(broken) }] },
            },
          ],
        });
      }
      assert.ok(prompt.trusted_context.previous_storyboard);
    }
    return normal(url, options);
  });
  try {
    const id = await enqueue(f);
    await w.run(await w.claim());
    const d = await f.api("/campaigns/" + id);
    assert.equal(d.campaign.status, "completed", d.campaign.limitations);
    assert.equal(packages, 1);
    assert.equal(boards, 2);
    assert.equal(reviews, 1);
    assert.ok(d.calls.length <= 10);
    validateStoryboard(d.campaign.result.storyboard, 20);
  } finally {
    w.stop();
    await f.close();
  }
});
test("storyboard presentation escapes untrusted text and manually edited time fields", () => {
  const storyboard = mockStoryboard();
  storyboard.duration_seconds = "<img src=x onerror=alert(1)>";
  storyboard.scenes[0].visual = "<script>alert(1)</script>";
  storyboard.beats[0].start = "<b>bad</b>";
  const esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const html = creativeView(
    { storyboard, effort_hours: 2 },
    {},
    { esc, listHTML: () => "", effortLabel },
  );
  assert.doesNotMatch(html, /<script>|<img src=x|<b>bad/);
  assert.match(html, /&lt;script&gt;/);
});
test("storyboard covers every second, links shots and enforces feasible speech/read timing", () => {
  validateStoryboard(mockStoryboard(), 20);
  for (const mutate of [
    (s) => (s.beats[2].start = 2.2),
    (s) => (s.scenes[1].start = 2.5),
    (s) => s.beats.pop(),
    (s) => (s.beats[4].shot_id = "missing"),
    (s) => (s.scenes[1].camera = ""),
    (s) => (s.voiceover[0].end = 13),
    (s) => (s.screen_text[0].end = 12.5),
    (s) => (s.duration_seconds = 30),
  ]) {
    const s = mockStoryboard();
    mutate(s);
    assert.throws(() => validateStoryboard(s, 20));
  }
  assert.equal(mockStoryboard().scenes.length, 3);
  assert.equal(mockStoryboard().beats.length, 20); // coverage does not force 20 cuts
});
test("research facts require retrieved evidence and a creative translation; effort must add up", () => {
  const sources = [
    {
      id: "source",
      observation: "This exact retrieved statement supports the observation.",
    },
  ];
  const finding = {
    observation: "ملاحظة مستندة إلى النص",
    evidence_type: "fact",
    source_ids: ["source"],
    quote: "exact retrieved statement",
    creative_opportunity: "فرصة تنبع من البحث",
    execution_translation: "صورة تحوّل الملاحظة إلى إعلان",
  };
  const r = { brief: {}, findings: [finding, finding, finding] };
  validateInsights(r, sources);
  assert.throws(() =>
    validateInsights(
      { ...r, findings: [{ ...finding, quote: "invented" }, finding, finding] },
      sources,
    ),
  );
  assert.throws(() =>
    validateInsights(
      {
        ...r,
        findings: [{ ...finding, source_ids: ["fake"] }, finding, finding],
      },
      sources,
    ),
  );
  assert.throws(() => validateTreatment({ treatment: {}, effort_hours: 3 }));
  assert.equal(effortLabel(252), "4 ساعات و12 دقيقة");
});
test("Hebron daily agenda includes multi-day production; a blank day is unplanned, not rest", () => {
  const task = {
    id: "t",
    production_at: "2026-09-19T07:00:00Z",
    review_at: "2026-09-22T09:00:00Z",
    planned_at: "2026-09-23T15:00:00Z",
    status: "awaiting_start",
    metadata: { effort_hours: 4.2 },
  };
  assert.equal(taskEvents([task], "2026-09-20")[0].label, "استكمال الإنتاج");
  assert.equal(taskEvents([task], "2026-09-22")[0].kind, "review");
  assert.equal(taskEvents([task], "2026-09-23")[0].kind, "publish");
  assert.equal(taskEvents([task], "2026-09-24").length, 0);
  const week = availableWeek("2026-09-19", [task], [], { daily_hours: 2 });
  assert.deepEqual(
    week.slice(0, 3).map((d) => d.remaining_minutes),
    [0, 0, 108],
  );
  assert.equal(addDays("2026-10-24", 1), "2026-10-25");
});
test("weekly plan persists 7 varied days, protects existing work, validates versions and links one development job", async () => {
  const f = await fixture();
  try {
    const start = localClock().localDate;
    const body = { start_date: start };
    const a = await f.api("/week-plan", "POST", body, {
      "Idempotency-Key": "week-1",
    });
    assert.equal(a.status, 200);
    assert.equal(
      (await f.api("/week-plan", "POST", body, { "Idempotency-Key": "week-1" }))
        .campaign.id,
      a.campaign.id,
    );
    const w = workerFor(f);
    await w.run(await w.claim());
    let d = await f.api("/dashboard");
    assert.equal(
      d.campaigns[0].status,
      "completed",
      d.campaigns[0].limitations,
    );
    assert.equal(d.records.filter((r) => r.kind === "day_plan").length, 7);
    const p = d.records.find(
      (r) => r.kind === "day_plan" && r.record_key === start,
    );
    assert.equal(
      (
        await f.api("/plan-days/" + p.id, "PATCH", {
          version: 0,
          status: "done",
        })
      ).status,
      400,
    );
    assert.equal(
      (
        await f.api("/plan-days/" + p.id, "PATCH", {
          version: p.version,
          status: "done",
        })
      ).status,
      200,
    );
    const request = {
      request: "طوّر فكرة اليوم إلى فيديو إعلاني لشركة XPAND",
      day_plan_id: p.id,
    };
    const c = await f.api("/campaigns", "POST", request, {
      "Idempotency-Key": "develop-1",
    });
    const twice = await f.api("/campaigns", "POST", request, {
      "Idempotency-Key": "develop-2",
    });
    assert.equal(c.campaign.id, twice.campaign.id);
    await w.run(await w.claim());
    const deep = await f.api("/campaigns/" + c.campaign.id);
    assert.equal(deep.campaign.status, "completed", deep.campaign.limitations);
    assert.equal(deep.campaign.result.storyboard.beats.length, 20);
    assert.ok(
      deep.process.insights &&
        deep.process.directions &&
        deep.process.selection,
    );
    await f.api("/week-plan", "POST", body, { "Idempotency-Key": "week-2" });
    await w.run(await w.claim());
    d = await f.api("/dashboard");
    assert.equal(d.records.filter((r) => r.kind === "day_plan").length, 7);
    assert.equal(d.records.find((r) => r.id === p.id).data.status, "done");
    assert.equal(
      d.records.find((r) => r.id === p.id).data.campaign_id,
      c.campaign.id,
    );
    w.stop();
  } finally {
    await f.close();
  }
});
test("week contract rejects unknown dates, invented links and over-capacity", () => {
  const days = availableWeek("2026-09-19", [], [], { daily_hours: 2 });
  const r = {
    title: "أسبوع عمل",
    days: days.map((d) => ({
      date: d.date,
      title: "عمل واضح",
      activity: "idea",
      format: "story",
      minutes: 30,
      idea: "فكرة مفيدة",
      deliverable: "ستوري قابل للمراجعة",
      steps: ["جهز العناصر", "راجع الكلمات"],
      why_this_day: "تنويع المحتوى",
      source_ids: [],
      campaign_id: null,
    })),
  };
  validateWeek(r, days, [], { weekly_videos: 3 }, []);
  for (const mutate of [
    (x) => (x.days[0].minutes = 121),
    (x) => (x.days[0].date = "2026-10-01"),
    (x) => (x.days[0].campaign_id = "fake"),
    (x) => x.days.forEach((d) => (d.format = "video")),
  ]) {
    const x = structuredClone(r);
    mutate(x);
    assert.throws(() => validateWeek(x, days, [], { weekly_videos: 3 }, []));
  }
});
