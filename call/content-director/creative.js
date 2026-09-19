// Executable contracts complement the director policy; verbosity alone is not quality.
export const CREATIVE_POLICY = `
XPAND production edition 3. Market only XPAND, never invent clients, past work or results.
Understand the brief: service, true benefit, audience, objective, current belief, desired belief/feeling/action, platform, duration, resources and production method. Essential unknowns need a question; optional assets are dependencies, not reasons to stop an original-motion concept.
Research is evidence, not decoration. For each useful observation distinguish fact, interpretation and hypothesis; cite an existing source ID and a short exact supporting quote for facts. Explain the creative opportunity and how the proposed picture, situation or sound transforms that observation. General references are not local audience research. Never claim to have watched reference video/audio from page text.
Generate materially different mechanisms (human situation, visual metaphor, sensory reveal, narrative reversal, demonstration). Avoid repeatedly comparing a bad logo with a good logo. No gratuitous shock. Explain the human observation, brand-specific role, emotional intent, memorable device and execution challenge for each direction.
For an agency introduction, an elegant line becoming a logo, glowing letters, opacity layers or blue shapes assembling are visual finishes, NOT an advertising idea. Unless the brief explicitly requests only a logo ident, the story must demonstrate a service solving a concrete communication problem before the end card. Do not claim blue/cyan, geometric accuracy or an XPAND wordmark make a concept proprietary. A logo-swap test is a criticism exercise, not a required compliment. Audience beliefs are hypotheses unless supported by audience evidence. Quotes about one brand do not prove a universal psychological or commercial effect.
Critique logo-swap interchangeability, service indispensability, message intelligibility without our explanation, originality relative to stored work, purposeful surprise and feasibility. Comparative scores are editorial judgments, never forecasts of success. Reject unsupported claims such as guaranteed sales, instant trust, fastest or best without evidence.
Write a coherent treatment: world, characters or graphic elements, performance, camera, lighting, palette, texture, pacing, sound, product role and ending. A design adjective alone is not a direction. Make shot choices operational: direction, speed, reveal and purpose. Adapt to real filming, motion, 3D or AI-assisted production, and describe a feasible alternate shot for difficult interactions. Keep assets/rights/approvals explicit. No media generation or execution prompts unless separately requested.
Sound belongs to the concept: musical development, ambience, near sounds, transitions, silence and voice tone. Feelings are intended, not guaranteed. Specify what audiovisual cue is intended to produce each feeling.
Storyboard: one continuous exact timeline from zero through duration. Cover each second (subseconds allowed); a held shot can evolve without a cut every second. Each shot specifies framing, focal point, camera movement, action/performance, lighting/materials, transition and its reason. Each beat explains image evolution, sound and intended feeling/message. Voice and screen text have their own time spans, paced for natural speech and reading.
Review factual support, causal link from research, non-generic idea, complete timings, speech/readability, continuity and removable filler. Repair defects before delivering. Save key stage outputs, not private chain of thought. Keep feedback preferences, project conditions, brand rules and observed outcomes separate; do not infer commercial effectiveness from approval.
Arabic should be concrete and human. Explain effort in minutes/hours for the whole team, distinct from screen duration. No invented market trends, asset availability, posting-time superiority or guaranteed psychological effects.
`;

export const INSIGHTS_PROMPT = `INSIGHTS_V3: Return {brief:{service,objective,audience,current_belief,desired_belief,desired_feeling,desired_action,resources,production_method,assumptions:[]}, findings:[{observation,evidence_type:"fact"|"interpretation"|"hypothesis",source_ids:[],quote,creative_opportunity,execution_translation}], contradictions:[], unanswered_questions:[], missing_essential_information:[]}. At least 3 distinct useful findings. Facts require an exact short quote found in a supplied source. Source IDs must exist. No fabricated audience interviews, competitor or video inspection. Explain the link to creative decisions, not source summaries alone.`;
export const STORYBOARD_PROMPT = `STORYBOARD_V3: Return JSON {duration_seconds:number,scenes:[{id,start,end,visual,framing,focal_point,camera,action,performance,lighting,sound,transition,transition_reason,emotion,purpose,production_note}],beats:[{start,end,shot_id,visual_change,sound_change,emotion,purpose}],voiceover:[{start,end,text,delivery}],screen_text:[{start,end,text}]}. Use the proposed package duration (integer 6–60). Scenes and beats must each start at 0, end at duration, be ordered and contiguous without gaps/overlaps. Return exactly duration_seconds beats using integer windows [0,1],[1,2],...,[duration-1,duration]; keep scene cuts on those integer boundaries. Sustained shots use the same shot_id across beats and describe progression, not identical filler. At least 3 shots. Every field must be concrete, using 'غير مطلوب' for inapplicable live-actor elements. Voiceover is the FINAL spoken text; at most 3 words/second per segment and at least 1 second per segment. Screen text reading at most 3 words/second, at least 1 second. Silence is valid. Preserve the package's actual concept and service demonstration; do not replace it with a generic logo reveal. Avoid decorative cuts; integrate sound, emotion and service in one clear idea. If previous_storyboard and a validation error are supplied, repair that board without changing the passed treatment or duration.`;
export const DIRECTIONS_PROMPT = `Develop 3 genuinely distinct executable advertising concepts, not three motion styles. JSON {directions:[{title,concept,service,hook,feasibility,originality,mechanism_type:"demonstration"|"narrative_reversal"|"sound_led",mechanism,human_observation,brand_role,story,emotion,distinctive_device,execution_challenge,problem,change,service_proof,opening_action,final_reveal,source_ids:[]}],missing_essential_information:[]}. Use EACH mechanism_type exactly once: one demonstration of a communication decision, one reversal of an initial interpretation, and one idea whose sound reveals meaning (with a silent-viewing solution). All can be original motion/typography if assets are limited. For each, name the concrete communication problem, what changes for the viewer, and which XPAND service causes that change ON SCREEN. Write exact words/objects/actions, not abstract promises of professionalism. A sequence of a line, logo and CTA is only an ident, not a campaign. Do not substitute arbitrary 'cinematic', 'precise', 'elegant' adjectives for an event or meaning. End-card branding is permitted, but it cannot be the entire idea. Avoid the same story with different speed/colors. Treat audience assumptions as hypotheses; use only existing source IDs. No chain-of-thought.`;
export const QUALITY_PROMPT = `Review the finished package as a skeptical creative editor, not its salesperson. Return JSON {pass:boolean,issues:string[],summary:string,assessments:[{criterion:"idea"|"service"|"evidence"|"execution",score:0|1|2|3,reason:string}]}. Include each criterion once. Score 0 missing, 1 generic/unsupported, 2 concrete usable, 3 concrete and justified. Pass only when every score>=2 and issues is empty. IDEA: explain the specific event/reversal/demonstration in one sentence; color, logo formation, glow and smooth typography alone are not an idea unless expressly requested as a pure ident. SERVICE: name what the business owner learns about the service before the CTA; don't praise a logo-swap test merely because palette/name are XPAND. EVIDENCE: verify observation claims are actually entailed by the quoted passage; don't turn a brand case into proof of local audience psychology or guaranteed trust/sales. EXECUTION: compare storyboard against treatment, show concrete motion direction/change, sound event and semantic payoff, timed speech/readability and realistic total adaptation effort. 'A gentle sound', 'professional feeling' and many seconds of cosmetic logo polishing do not justify 2. No invented assets, actors, facts or inspection. Identify exact defects; be willing to reject your earlier candidate. Scores are editorial judgments, not performance predictions.`;
export const DEEP_PACKAGE_CONTRACT = `Also include treatment:{world,characters,visual_system,pacing,sound_design,ending,production_method,continuity,feasible_alternative}, emotion_arc:[{moment,feeling,cue}], effort_breakdown:[{task,minutes}], and explicit assumptions/dependencies. Breakdown minutes must sum to effort_hours*60 (within 2 minutes), including adaptations. Use integer video duration 6–60. No timed storyboard needed in this stage: scenes can be 3 summary shots, detailed timing is authored next. Concrete execution, not slogans or subjective superlatives.`;

const meaningful = (v) => typeof v === "string" && v.trim().length >= 3;
export function validateDirections(r, sources) {
  const types = new Set();
  if (r?.directions?.length !== 3)
    throw new Error("يلزم ثلاثة اتجاهات سردية مختلفة.");
  for (const d of r.directions) {
    if (
      !["demonstration", "narrative_reversal", "sound_led"].includes(
        d.mechanism_type,
      ) ||
      types.has(d.mechanism_type)
    )
      throw new Error("الاتجاهات تكرر الآلية نفسها؛ اختلاف الستايل لا يكفي.");
    types.add(d.mechanism_type);
    for (const key of [
      "problem",
      "change",
      "service_proof",
      "opening_action",
      "final_reveal",
    ])
      if (!meaningful(d[key]))
        throw new Error(
          "الاتجاه ناقص في المشكلة أو الحدث أو إثبات الخدمة: " + key,
        );
    if (
      !Array.isArray(d.source_ids) ||
      d.source_ids.some((id) => !sources.some((s) => s.id === id))
    )
      throw new Error("مرجع غير موجود في الاتجاه الإبداعي.");
  }
  return r;
}
export function reviewIssue(review) {
  const criteria = ["idea", "service", "evidence", "execution"];
  const a = review?.assessments;
  if (
    !Array.isArray(a) ||
    a.length !== 4 ||
    criteria.some((k) => a.filter((x) => x.criterion === k).length !== 1) ||
    a.some(
      (x) =>
        !Number.isInteger(x.score) ||
        x.score < 0 ||
        x.score > 3 ||
        !meaningful(x.reason),
    )
  )
    return "مراجعة الجودة لم تقدم تقييمًا مبررًا للفكرة والخدمة والدليل والتنفيذ.";
  const issues = [
    ...(Array.isArray(review.issues) ? review.issues : []),
    ...a.filter((x) => x.score < 2).map((x) => x.reason),
  ];
  if (review.pass !== true || issues.length)
    return issues.join("؛ ") || "لم تجتز الفكرة المراجعة الإبداعية.";
  return "";
}
export function validateInsights(r, sources) {
  if (!r?.brief || !Array.isArray(r.findings) || r.findings.length < 3)
    throw new Error("استخلاص البحث غير مكتمل.");
  for (const f of r.findings) {
    if (
      !["fact", "interpretation", "hypothesis"].includes(f.evidence_type) ||
      !meaningful(f.observation) ||
      !meaningful(f.creative_opportunity) ||
      !meaningful(f.execution_translation)
    )
      throw new Error("ملاحظة بحث بلا تفسير إبداعي قابل للاستخدام.");
    if (
      !Array.isArray(f.source_ids) ||
      f.source_ids.some((id) => !sources.some((s) => s.id === id))
    )
      throw new Error("مرجع غير موجود في استخلاص البحث.");
    if (
      f.evidence_type === "fact" &&
      (!meaningful(f.quote) ||
        !f.source_ids.some((id) =>
          sources.find((s) => s.id === id)?.observation.includes(f.quote),
        ))
    )
      throw new Error("حقيقة بحثية بلا مقتطف يدعمها من المصادر المقروءة.");
  }
  return r;
}
export function validateTreatment(r) {
  for (const field of [
    "world",
    "characters",
    "visual_system",
    "pacing",
    "sound_design",
    "ending",
    "production_method",
    "continuity",
    "feasible_alternative",
  ])
    if (!meaningful(r.treatment?.[field]))
      throw new Error("المعالجة ناقصة: " + field);
  if (
    !r.emotion_arc?.length ||
    r.emotion_arc.some((e) => !meaningful(e.feeling) || !meaningful(e.cue))
  )
    throw new Error("رحلة المشاعر تحتاج قرائن بصرية أو صوتية واضحة.");
  if (
    !r.effort_breakdown?.length ||
    r.effort_breakdown.some(
      (x) =>
        !meaningful(x.task) || !Number.isFinite(x.minutes) || x.minutes <= 0,
    )
  )
    throw new Error("تقدير جهد الفريق غير مفصل.");
  if (
    Math.abs(
      r.effort_breakdown.reduce((n, x) => n + x.minutes, 0) -
        Number(r.effort_hours) * 60,
    ) > 2
  )
    throw new Error("مجموع دقائق العمل لا يطابق جهد الإنتاج الإجمالي.");
}
function coverage(items, duration, name, maxLength = duration) {
  if (!Array.isArray(items) || !items.length)
    throw new Error(name + " غير موجود.");
  let end = 0;
  for (const x of items) {
    if (
      !Number.isFinite(x.start) ||
      !Number.isFinite(x.end) ||
      Math.abs(x.start - end) > 0.001 ||
      x.end <= x.start ||
      x.end - x.start > maxLength + 0.001 ||
      x.end > duration + 0.001
    )
      throw new Error(name + ": توجد فجوة أو تداخل أو مدة غير صالحة.");
    end = x.end;
  }
  if (Math.abs(end - duration) > 0.001)
    throw new Error(name + " لا يغطي نهاية الفيديو.");
}
export function validateStoryboard(r, duration) {
  if (
    !Number.isInteger(duration) ||
    duration < 6 ||
    duration > 60 ||
    r.duration_seconds !== duration
  )
    throw new Error("مدة الستوري بورد يجب أن تطابق مدة الفيديو (6–60 ثانية).");
  coverage(r.scenes, duration, "اللقطات");
  coverage(r.beats, duration, "تفاصيل الثواني", 1);
  if (
    r.scenes.length < 3 ||
    new Set(r.scenes.map((s) => s.id)).size !== r.scenes.length
  )
    throw new Error("معرفات اللقطات غير صالحة.");
  for (const s of r.scenes)
    for (const k of [
      "visual",
      "framing",
      "focal_point",
      "camera",
      "action",
      "performance",
      "lighting",
      "sound",
      "transition",
      "transition_reason",
      "emotion",
      "purpose",
      "production_note",
    ])
      if (!meaningful(s[k])) throw new Error("تفاصيل اللقطة ناقصة: " + k);
  if (r.scenes.some((s) => typeof s.id !== "string" || !s.id.trim()))
    throw new Error("معرّف اللقطة مفقود.");
  for (const b of r.beats) {
    const shot = r.scenes.find((s) => s.id === b.shot_id);
    if (!shot || b.start < shot.start || b.end > shot.end)
      throw new Error("الثانية لا تنتمي إلى توقيت اللقطة المحددة.");
    if (
      ["visual_change", "sound_change", "emotion", "purpose"].some(
        (k) => !meaningful(b[k]),
      )
    )
      throw new Error("ثانية بلا تطور بصري أو صوت أو هدف واضح.");
  }
  for (const kind of ["voiceover", "screen_text"]) {
    if (!Array.isArray(r[kind]))
      throw new Error("توقيت النصوص والصوت غير مكتمل.");
    let end = 0;
    for (const x of r[kind]) {
      if (
        !Number.isFinite(x.start) ||
        !Number.isFinite(x.end) ||
        x.start < end ||
        x.end > duration ||
        x.end - x.start < 1 ||
        !meaningful(x.text)
      )
        throw new Error("توقيت الكلام أو النص الظاهر غير صالح.");
      if (x.text.trim().split(/\s+/u).length / (x.end - x.start) > 3)
        throw new Error("النص أطول من الوقت المتاح لقراءته أو نطقه طبيعيًا.");
      if (kind === "voiceover" && !meaningful(x.delivery))
        throw new Error("نبرة أداء التعليق الصوتي مفقودة.");
      end = x.end;
    }
  }
  return r;
}

export const WEEK_PROMPT = `WEEK_PLAN_V3: Create 7 DIFFERENT daily work plans for the supplied dates, not 7 mandatory videos. Return {title,summary,days:[{date,title,activity:"idea"|"production"|"review"|"publish"|"engagement",format:"video"|"static"|"carousel"|"story"|"work",minutes:number,idea,deliverable,steps:string[],why_this_day,source_ids:[],campaign_id:string|null}]}. Mix creative development, production, review, stories/designs and community work. Use existing campaigns/tasks when appropriate; do not assign new video ideas beyond weekly_videos. Each day's minutes must fit the supplied remaining_minutes. A daily idea is a brief, not a finished screenplay; never call it production-ready. Avoid repeating concepts. New execution-dependent publication should be review/planning instead of pretending the asset is ready. Source IDs must exist. campaign_id can ONLY be one of the supplied existing campaign IDs. Dates come from the supplied list exactly. Do not infer holidays. Every day gets a concrete task, actionable steps and a distinct deliverable; full days with 0 remaining minutes must describe following existing work with minutes=0, never invent additional capacity.`;
export function validateWeek(r, days, sources, profile, existingIds) {
  if (!r?.title || !Array.isArray(r.days) || r.days.length !== 7)
    throw new Error("الخطة يجب أن تحتوي سبعة أيام واضحة.");
  const expected = new Map(days.map((d) => [d.date, d.remaining_minutes]));
  const seen = new Set();
  let videos = 0;
  for (const d of r.days) {
    if (!expected.has(d.date) || seen.has(d.date))
      throw new Error("تاريخ ناقص أو مكرر في خطة الأسبوع.");
    seen.add(d.date);
    if (
      !Number.isFinite(d.minutes) ||
      d.minutes < 0 ||
      d.minutes > expected.get(d.date)
    )
      throw new Error("خطة اليوم تتجاوز الوقت المتاح للفريق.");
    if (
      !["idea", "production", "review", "publish", "engagement"].includes(
        d.activity,
      ) ||
      !["video", "static", "carousel", "story", "work"].includes(d.format) ||
      ["title", "idea", "deliverable", "why_this_day"].some(
        (k) => !meaningful(d[k]),
      ) ||
      !Array.isArray(d.steps) ||
      d.steps.length < 2
    )
      throw new Error("خطة يوم غير قابلة للتنفيذ.");
    if (d.campaign_id && !existingIds.includes(d.campaign_id))
      throw new Error("الحملة المرتبطة باليوم غير موجودة.");
    if (
      !Array.isArray(d.source_ids) ||
      d.source_ids.some((id) => !sources.some((s) => s.id === id))
    )
      throw new Error("مرجع غير موجود في خطة الأسبوع.");
    if (d.format === "video" && !d.campaign_id) videos++;
  }
  if (videos > profile.weekly_videos)
    throw new Error("الخطة تقترح فيديوهات جديدة أكثر من قدرة الأسبوع.");
  return r;
}
