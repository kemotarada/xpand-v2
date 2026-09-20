import test from "node:test";
import assert from "node:assert/strict";
import {
  composePrompts,
  visualSchema,
  VISUAL_DNA,
  addVisualPrompts,
} from "./visual-prompts.js";
import { compactStoryboard } from "../content-command/compact-view.js";
import { fixture, workerFor, TEST_USER } from "./test-support.js";
import { randomUUID } from "node:crypto";
import {settingsInput} from "./core.js";
test("selected fallback resumes 503 jobs without resetting attempts or saved directions",async()=>{
 const f=await fixture();
 try {
  const settings=settingsInput({visual_engine:true,visual_model:"gemini-3.5-flash-lite"});
  await f.store.record(TEST_USER,"settings","main",settings);
  const id=randomUUID();
  await f.pool.query("INSERT INTO xpand_content_campaigns(id,user_id,request_text,status,stage,attempts,checkpoint) VALUES($1,$2,$3,$4,$4,1,$5)",[id,TEST_USER,"prompts","blocked",JSON.stringify({visual_prompts:true,model:"gemini-3.8-flash",saved_direction:"keep",provider_issue:{http_status:503,service:"gemini:gemini-3.8-flash"}})]);
  assert.equal((await f.api(`/campaigns/${id}/retry`,"POST",{})).status,200);
  const row=(await f.pool.query("SELECT attempts,checkpoint FROM xpand_content_campaigns WHERE id=$1",[id])).rows[0];
  assert.equal(row.attempts,1);
  assert.equal(row.checkpoint.model,"gemini-3.5-flash-lite");
  assert.equal(row.checkpoint.saved_direction,"keep");
  assert.equal(settingsInput({visual_model:"https://bad.example"}).visual_model,"gemini-3.8-flash");
 } finally {await f.close();}
});
const fill = (schema) =>
  Object.fromEntries(
    Object.keys(schema.properties).map((k) => [
      k,
      "Precise scene direction with physically plausible lighting and natural detail.",
    ]),
  );
const dna = fill(visualSchema("visual_dna"));
const direction = {
  image: fill(visualSchema("visual_scene").properties.image),
  motion: fill(visualSchema("visual_scene").properties.motion),
};
test("prompt-only API preserves the parent, prevents duplicate queueing and creates no production task", async () => {
  const f = await fixture();
  try {
    const parent = randomUUID();
    await f.pool.query(
      "INSERT INTO xpand_content_campaigns(id,user_id,request_text,status,stage,result) VALUES($1,$2,$3,$4,$4,$5)",
      [
        parent,
        TEST_USER,
        "Original request",
        "completed",
        JSON.stringify({
          title: "Ad",
          storyboard: {
            scenes: [{ id: 1, start: 0, end: 4, visual: "Original" }],
          },
        }),
      ],
    );
    const first = await f.api(`/campaigns/${parent}/prompts`, "POST", {});
    const second = await f.api(`/campaigns/${parent}/prompts`, "POST", {});
    assert.equal(first.campaign.id, second.campaign.id);
    const w = workerFor(f, () => {
      throw new Error("Unexpected network");
    });
    w.modelJSON = async (j, s) =>
      s.startsWith("visual_dna")
        ? dna
        : s.startsWith("visual_scene")
          ? direction
          : { pass: true, issues: [] };
    await w.run(await w.claim());
    const saved = await f.api(`/campaigns/${parent}`);
    assert.ok(saved.campaign.result.storyboard.scenes[0].image_prompt);
    assert.equal((await f.api("/dashboard")).tasks.length, 0);
    assert.equal(
      (await f.api(`/campaigns/${first.campaign.id}`)).campaign.status,
      "completed",
    );
    w.stop();
  } finally {
    await f.close();
  }
});
test("each standalone prompt includes the locked palette and campaign DNA", () => {
  const p = composePrompts(dna, direction, 4);
  for (const key of ["image_prompt", "motion_prompt"])
    for (const colour of Object.values(VISUAL_DNA.palette))
      assert.ok(p[key].includes(colour));
  assert.match(p.motion_prompt, /4-second/);
  assert.throws(() => composePrompts(dna, { image: {} }, 4), /ناقصة/);
});
test("prompt generation preserves the original story and resumes saved scene directions", async () => {
  const original = {
    title: "Ad",
    storyboard: {
      scenes: [{ id: 1, start: 0, end: 4, visual: "Original scene" }],
    },
  };
  const job = { checkpoint: {} };
  let calls = 0;
  const worker = {
    store: {
      checkpoint: async (j, s, data) => Object.assign(j.checkpoint, data),
    },
    modelJSON: async (j, stage) => {
      calls++;
      return stage.startsWith("visual_dna")
        ? dna
        : stage.startsWith("visual_scene")
          ? direction
          : { pass: true, issues: [] };
    },
  };
  const result = await addVisualPrompts(worker, job, original);
  assert.equal(original.storyboard.scenes[0].image_prompt, undefined);
  assert.equal(result.storyboard.scenes[0].visual, "Original scene");
  assert.ok(result.storyboard.scenes[0].image_prompt);
  await addVisualPrompts(worker, job, original);
  assert.equal(calls, 3);
});
test("prompt UI escapes text and puts both copy controls in the scene", () => {
  const esc = (s) =>
    String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  const html = compactStoryboard(
    {
      scenes: [
        {
          visual: "Shot",
          image_prompt: "</textarea><script>bad</script>",
          motion_prompt: "Move slowly",
        },
      ],
    },
    esc,
  );
  assert.ok(!html.includes("<script>"));
  assert.equal(
    (html.match(/data-action="copy-scene-prompt"/g) || []).length,
    2,
  );
  assert.ok(html.indexOf("scene-prompt") < html.indexOf("</article>"));
});
