import crypto from "node:crypto";

export const ZONE = "Asia/Hebron";
export const text = (v, max = 2000) =>
  String(v ?? "")
    .trim()
    .slice(0, max);
export const uuid = (v) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    v || "",
  );
export const hash = (v) =>
  crypto.createHash("sha256").update(JSON.stringify(v)).digest("hex");
export function localClock(instant = new Date()) {
  const d = new Date(instant);
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(d)
      .map((x) => [x.type, x.value]),
  );
  return {
    iso: d.toISOString(),
    timezone: ZONE,
    localDate: `${p.year}-${p.month}-${p.day}`,
    time: `${p.hour}:${p.minute}:${p.second}`,
    weekday: new Intl.DateTimeFormat("ar-PS", {
      timeZone: ZONE,
      weekday: "long",
    }).format(d),
  };
}
export function dateOnly(v) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v || "")) return false;
  const n = new Date(`${v}T12:00:00Z`);
  return !isNaN(n) && n.toISOString().slice(0, 10) === v;
}
export function daysUntil(date, now = new Date()) {
  return dateOnly(date)
    ? Math.round(
        (Date.parse(date + "T12:00:00Z") -
          Date.parse(localClock(now).localDate + "T12:00:00Z")) /
          86400000,
      )
    : null;
}
// Enumerate offsets using IANA data; reject both gaps and ambiguous DST wall times.
export function fromLocal(value) {
  if (
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value || "") ||
    !dateOnly(value.slice(0, 10))
  )
    throw new Error("موعد محلي غير صالح");
  const candidates = [];
  const base = Date.parse(value + "Z");
  for (let offset = -14 * 60; offset <= 14 * 60; offset += 15) {
    const d = new Date(base - offset * 60000);
    const c = localClock(d);
    if (`${c.localDate}T${c.time.slice(0, 5)}` === value)
      candidates.push(d.toISOString());
  }
  if (candidates.length !== 1)
    throw new Error(
      "هذه الساعة غير موجودة أو ملتبسة بسبب تغيير التوقيت؛ اختر ساعة أخرى.",
    );
  return candidates[0];
}
export function webAppUser(raw, token, allowed, now = Date.now()) {
  try {
    if (!token || !allowed || !raw || raw.length > 16000) return null;
    const p = new URLSearchParams(raw);
    if ([...p.keys()].length !== new Set(p.keys()).size) return null;
    const received = p.get("hash");
    if (!/^[0-9a-f]{64}$/i.test(received || "")) return null;
    const age = now / 1000 - Number(p.get("auth_date"));
    if (!Number.isFinite(age) || age < -60 || age > 86400) return null;
    p.delete("hash");
    const check = [...p]
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([k, v]) => `${k}=${v}`)
      .join("\n");
    const secret = crypto
      .createHmac("sha256", "WebAppData")
      .update(token)
      .digest();
    const expected = crypto.createHmac("sha256", secret).update(check).digest();
    if (!crypto.timingSafeEqual(Buffer.from(received, "hex"), expected))
      return null;
    const user = JSON.parse(p.get("user"));
    return Number.isSafeInteger(user.id) && String(user.id) === String(allowed)
      ? user
      : null;
  } catch {
    return null;
  }
}
export const taskStates = [
  "planned",
  "awaiting_start",
  "in_production",
  "in_review",
  "ready_to_publish",
  "published",
  "postponed",
  "cancelled",
];
export const activeStates = [
  "planned",
  "awaiting_start",
  "in_production",
  "in_review",
  "ready_to_publish",
];
export const defaultProfile = {
  services:
    "التصميم الجرافيكي، الشعارات والهويات البصرية، تحريك الشعارات، الموشن جرافيك، الفيديوهات الإعلانية والحملات",
  audience: "أصحاب الأعمال في فلسطين، خصوصًا الخليل",
  tone: "عربية مهنية طبيعية؛ فلسطينية خفيفة بحسب الفكرة",
  facts: "XPAND شركة إبداعية في الخليل، فلسطين. التسويق للشركة نفسها فقط.",
  preferences: "",
  assumptions:
    "توزيع الساعتين بين المصمم ومنتج الفيديو غير محسوم؛ لا تضاعف الوقت.",
  portfolio: "",
  contacts: "",
  daily_hours: 2,
  weekly_videos: 3,
};
export const defaultSettings = {
  search_provider: "auto",
  recurring: false,
  interval_hours: 2,
  daily_calls: 20,
  monthly_calls: 200,
  task_calls: 10,
  unlimited_calls: false,
  rounds: 2,
  depth: "basic",
  concurrency: 1,
  timeout_minutes: 20,
  daily_usd: 0,
  monthly_usd: 0,
  search_call_usd: 0,
  model_call_usd: 0,
  pricing_confirmed: false,
  telegram: false,
  quiet_start: 21,
  quiet_end: 9,
  notification_cap: 4,
};
export function settingsInput(v = {}) {
  const o = { ...defaultSettings };
  o.search_provider = ["auto", "tavily", "gemini", "direct"].includes(
    v.search_provider,
  )
    ? v.search_provider
    : "auto";
  for (const k of [
    "recurring",
    "pricing_confirmed",
    "telegram",
    "unlimited_calls",
  ])
    o[k] = v[k] === true;
  const ranges = {
    interval_hours: [2, 24],
    daily_calls: [1, 100],
    monthly_calls: [1, 2000],
    task_calls: [4, 20],
    rounds: [1, 3],
    concurrency: [1, 2],
    timeout_minutes: [3, 30],
    daily_usd: [0, 100],
    monthly_usd: [0, 1000],
    search_call_usd: [0, 10],
    model_call_usd: [0, 10],
    quiet_start: [0, 23],
    quiet_end: [0, 23],
    notification_cap: [1, 10],
  };
  for (const [k, [min, max]] of Object.entries(ranges)) {
    const n = Number(v[k] ?? o[k]);
    if (!Number.isFinite(n) || n < min || n > max)
      throw new Error(`قيمة غير صالحة: ${k}`);
    o[k] = k.includes("usd") ? n : Math.floor(n);
  }
  o.depth = v.depth === "advanced" ? "advanced" : "basic";
  if (
    o.recurring &&
    (!o.pricing_confirmed ||
      (!o.unlimited_calls && o.daily_calls > o.monthly_calls))
  )
    throw new Error(
      "اضبط حدود الاستهلاك وأكّد أسعار الخدمات أو حصتها المجانية قبل البحث الدوري.",
    );
  if (
    o.recurring &&
    o.search_call_usd + o.model_call_usd > 0 &&
    (o.daily_usd <= 0 || o.monthly_usd <= 0)
  )
    throw new Error(
      "حدد ميزانية مالية للخدمات المدفوعة قبل تفعيل البحث الدوري.",
    );
  return o;
}
export function safeURL(v) {
  try {
    const u = new URL(v);
    return ["https:", "http:"].includes(u.protocol) &&
      !u.username &&
      !u.password
      ? u.href
      : null;
  } catch {
    return null;
  }
}
export function quiet(now, s) {
  const h = Number(localClock(now).time.slice(0, 2));
  return s.quiet_start === s.quiet_end
    ? false
    : s.quiet_start > s.quiet_end
      ? h >= s.quiet_start || h < s.quiet_end
      : h >= s.quiet_start && h < s.quiet_end;
}
export const packageFields = [
  "title",
  "objective",
  "service",
  "audience",
  "why_now",
  "message",
  "concept",
  "visual_direction",
  "hook",
  "format",
  "caption",
  "cta",
  "production_instructions",
  "effort_hours",
  "schedule_rationale",
  "research_summary",
  "success_criterion",
  "decision_rationale",
];
export function validatePackage(r, sources) {
  const missing = packageFields.filter(
    (k) => typeof r?.[k] === "undefined" || String(r[k]).trim().length === 0,
  );
  for (const k of [
    "platforms",
    "adaptations",
    "assets",
    "assumptions",
    "limitations",
    "additional_resources",
  ])
    if (!Array.isArray(r?.[k])) missing.push(k);
  if (!r?.platforms?.length || !r?.adaptations?.length)
    missing.push("platform plan");
  if (!["video", "static", "carousel", "story"].includes(r?.format))
    missing.push("format");
  if (
    !Number.isFinite(Number(r?.effort_hours)) ||
    Number(r.effort_hours) <= 0 ||
    Number(r.effort_hours) > 100
  )
    missing.push("effort_hours");
  if (
    r?.format === "video" &&
    (!Array.isArray(r.scenes) ||
      r.scenes.length < 3 ||
      r.scenes.some((s) => !s.visual || !s.timing))
  )
    missing.push("scenes");
  if (
    ["static", "carousel"].includes(r?.format) &&
    (!r.headline || !r.composition)
  )
    missing.push("headline/composition");
  if (
    !Array.isArray(r?.source_ids) ||
    !r.source_ids.length ||
    r.source_ids.some((id) => !sources.some((s) => s.id === id))
  )
    missing.push("source_ids");
  if (missing.length)
    throw new Error("نتيجة غير مكتملة: " + [...new Set(missing)].join(", "));
  return r;
}
