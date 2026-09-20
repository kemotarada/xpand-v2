import { taskEvents, effortLabel } from "./planning.js";
import { creativeView } from "./creative-view.js";
import { compactStoryboard } from "./compact-view.js";
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
tg?.setHeaderColor("#062968");
tg?.setBackgroundColor("#062968");
const $ = (s) => document.querySelector(s),
  dialog = $("#command-dialog");
const readable = (v) =>
  v == null
    ? ""
    : typeof v === "object"
      ? v.message
        ? readable(v.message)
        : v.error
          ? readable(v.error)
          : JSON.stringify(v, null, 2)
      : String(v);
const esc = (v) =>
  readable(v).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const ZONE = "Asia/Hebron",
  empty = (m) => `<p class="empty">${esc(m)}</p>`;
let state = null,
  loading = false,
  month = null,
  selectedDay = null,
  serverAt = 0,
  receivedAt = 0,
  lastDay = "",
  activeCampaign = null,
  toastTimer;
const labels = {
  queued: "بانتظار التنفيذ",
  running: "يعمل الآن",
  completed: "اكتملت",
  failed: "تعذرت",
  blocked: "متوقفة — تحتاج معالجة",
  unverified_result: "سجل قديم — البحث غير مكتمل",
  needs_information: "تحتاج معلومات",
  cancelled: "ملغاة",
  planned: "مخطط",
  awaiting_start: "بانتظار البدء",
  in_production: "قيد التنفيذ",
  in_review: "قيد المراجعة",
  ready_to_publish: "جاهز للنشر",
  published: "منشور فعليًا",
  postponed: "مؤجل",
  confirmed: "مؤكد",
  provisional: "متوقع",
  unverified: "غير متحقق",
  new: "جديدة",
  reviewed: "تمت المراجعة",
  archived: "مؤرشفة",
};
const stages = {
  queued: "الانتظار",
  understanding: "فهم الطلب والسياق",
  collecting_references: "جمع المراجع",
  reading_references: "قراءة مراجع إبداعية عامة مباشرة",
  reading_sources: "فتح نصوص المصادر ومقارنتها",
  extracting_insights: "ربط ملاحظات البحث بفرص إبداعية",
  writing_storyboard: "كتابة الستوري بورد ثانية بثانية",
  checking_timing: "فحص التوقيت والكلام والنصوص",
  planning_week: "توزيع شغل متنوع على أيام الأسبوع",
  saving_week: "حفظ خطة الأيام دون استبدال أعمالك",
  developing_directions: "تطوير اتجاهات مختلفة",
  evaluating: "تقييم واختيار الاتجاه",
  preparing_plan: "كتابة خطة الإنتاج",
  quality_review: "مراجعة الجودة",
  improving: "تحسين النتيجة",
  saving_plan: "حفظ الحملة والمهام",
  reviewing_opportunities: "مراجعة الفرص",
  saving_scan: "حفظ الفحص",
  completed: "اكتمل الحفظ",
};
const fmt = (v) =>
  v
    ? new Intl.DateTimeFormat("ar-PS", {
        timeZone: ZONE,
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(v))
    : "لم يُحدد";
function localDate(v) {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(v))
      .map((p) => [p.type, p.value]),
  );
  return {
    date: `${p.year}-${p.month}-${p.day}`,
    time: `${p.hour}:${p.minute}`,
  };
}
const inputDate = (v) => (v ? `${localDate(v).date}T${localDate(v).time}` : "");
const badge = (s, warning = false) =>
  `<span class="badge ${warning ? "warning" : ""}">${esc(labels[s] || s)}</span>`;
function toast(m) {
  $("#toast").textContent = m;
  $("#toast").classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 5500);
}
async function api(path, options = {}) {
  const r = await fetch("/api/content" + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-telegram-init-data": tg?.initData || "",
      ...(options.headers || {}),
    },
    signal: AbortSignal.timeout(25000),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(readable(data.error) || "تعذر إتمام الطلب.");
  return data;
}
function open(title, body) {
  $("#dialog-content").innerHTML =
    `<p class="eyebrow">XPAND CONTENT DIRECTOR</p><h2>${esc(title)}</h2>${body}<p class="form-message" role="alert"></p>`;
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
}
const button = (action, label, id = "", className = "ghost") =>
  `<button class="${className}" data-action="${action}" data-id="${esc(id)}">${esc(label)}</button>`;
const field = (name, label, value = "", type = "text", full = false) =>
  `<label class="${full ? "full" : ""}">${esc(label)}<input name="${name}" type="${type}" value="${esc(value)}"></label>`;
const area = (name, label, value = "", full = true) =>
  `<label class="${full ? "full" : ""}">${esc(label)}<textarea name="${name}">${esc(value)}</textarea></label>`;
function showView(name) {
  document
    .querySelectorAll(".view")
    .forEach((e) => (e.hidden = e.id !== name + "-view"));
  document
    .querySelectorAll("[data-view]")
    .forEach((e) => e.classList.toggle("active", e.dataset.view === name));
  if (name !== "home")
    $("#" + name + "-view").scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
}
const taskEntry = (t) =>
  `<article class="entry"><div>${badge(t.status)}${t.locked ? badge("اتجاه مثبت") : ""}</div><h3>${esc(t.title)}</h3><p>${esc(t.description)}</p><p class="small-note">إنتاج: ${fmt(t.production_at)}<br>مراجعة: ${fmt(t.review_at)}<br>نشر مقترح: ${fmt(t.planned_at)}${t.actual_published_at ? "<br>النشر الفعلي: " + fmt(t.actual_published_at) : ""}</p><div class="actions">${t.campaign_id ? button("campaign", "الفكرة والستوري بورد", t.campaign_id) : ""}${button("task", "الحالة والمواعيد", t.id)}</div></article>`;
function campaignEntry(c) {
  const status = c.display_status || c.status;
  const card = libraryCard(c, state?.usage, state?.settings);
  const task = state?.tasks.find((t) => t.campaign_id === c.id);
  return `<article class="card spaced ${c.status === "running" ? "job running" : ""}">${badge(status, !card.complete)}${badge(card.complete ? "ملف محفوظ" : "طلب — ليس فكرة جاهزة")}<h3>${esc(card.heading)}</h3><p class="muted">${card.complete ? "النتيجة محفوظة للمراجعة؛ التنفيذ والنشر في التقويم والمهام." : "لم تكتمل النتيجة بعد. النص داخل «الطلب الأصلي» هو ما طُلب من الوكيل، وليس فكرة أنتجها."}</p><details><summary>الطلب الأصلي</summary><p>${esc(card.request)}</p></details><p class="small-note">المرحلة: ${esc(stages[c.stage] || labels[c.stage] || c.stage)} · اتصالات هذا الطلب: ${esc(c.call_count ?? "—")}<br>آخر تحديث: ${fmt(c.updated_at)}</p>${task ? `<p>بدء التنفيذ: ${fmt(task.production_at)} · النشر المقترح: ${fmt(task.planned_at)}</p>` : ""}${c.limitations ? `<p class="error">${esc(c.limitations)}</p>` : ""}${card.budgetReason && !card.complete ? `<p class="info-strip">${esc(card.budgetReason)} العمل المحفوظ لم يُحذف.</p>` : ""}<div class="actions">${button("campaign", card.complete ? "افتح الفكرة وملف الإنتاج" : "المراحل المحفوظة وسبب التوقف", c.id)}${task ? button("task", "مهمة التنفيذ المرتبطة", c.id === task.campaign_id ? task.id : "") : ""}${["queued", "running"].includes(c.status) ? button("cancel", "إلغاء البحث", c.id) : ""}${card.canRetry ? button("retry", "استكمال العمل المحفوظ", c.id) : ""}${card.budgetReason && !card.complete ? button("profile", "مراجعة حدود التشغيل") : ""}</div></article>`;
}
function notificationEntry(n) {
  return `<article class="entry">${!n.data.read ? badge("جديد") : ""}<p>${esc(n.data.message)}</p><small class="muted">${fmt(n.created_at)} · تيليجرام: ${esc({ pending: "بانتظار التفعيل أو وقت الإرسال", sent: "أُرسلت", sending: "إرسال غير مؤكد بعد", uncertain: "نتيجة الإرسال غير مؤكدة؛ لم نكرر الرسالة", failed: "تعذر الإرسال" }[n.data.delivery] || "غير مرسلة")}</small><div class="actions">${n.data.entity_id ? button("notice-target", "فتح السجل", n.data.entity_id) : ""}${!n.data.read ? button("read", "تمت القراءة", n.id) : ""}</div></article>`;
}
function render() {
  if (!state) return;
  const s = state;
  $("#metrics").innerHTML = [
    ["planned", "محتوى مخطط"],
    ["production", "قيد التنفيذ والمراجعة"],
    ["overdue", "مواعيد متأخرة"],
    ["published", "منشور بتأكيدكم"],
  ]
    .map(
      ([k, l]) =>
        `<article><strong>${s.metrics[k]}</strong><span>${l}</span></article>`,
    )
    .join("");
  $("#today").innerHTML = dayAgenda(s.now.localDate, true);
  $("#jobs").innerHTML = s.campaigns
    .filter((c) => ["running", "queued"].includes(c.status))
    .map(campaignEntry)
    .join("");
  $("#campaigns").innerHTML =
    s.campaigns
      .filter(
        (c) =>
          c.kind === "campaign" && !["running", "queued"].includes(c.status),
      )
      .map(campaignEntry)
      .join("") || empty("لا حملات محفوظة بعد.");
  const ns = s.records.filter((r) => r.kind === "notification");
  $("#notifications").innerHTML =
    ns.map(notificationEntry).join("") || empty("لا تنبيهات مسجلة.");
  const runtime = s.records.find((r) => r.kind === "worker")?.data;
  const workerAlive =
    runtime?.last_tick &&
    Date.parse(s.now.iso) - Date.parse(runtime.last_tick) < 180000;
  const p = s.settings;
  const providerRows = s.records.filter((r) => r.kind === "provider");
  const blockedProviders = providerRows.filter(
    (r) => r.data.status === "blocked",
  );
  const referenceReady = providerRows.some(
    (r) =>
      r.record_key === "direct_references" && r.data.status === "available",
  );
  $("#operations").innerHTML =
    `<p>${badge(runtime?.paused_for_provider ? "البحث متوقف عند مزود الخدمة" : p.recurring && workerAlive ? "البحث الدوري يعمل" : p.recurring ? "البحث مفعّل؛ نبض العامل غير حديث" : "البحث الدوري غير مفعّل", !p.recurring || !workerAlive || runtime?.paused_for_provider)} ${p.recurring ? `كل ${p.interval_hours} ساعة، ضمن الحدود` : "يلزم اعتماد حدود التشغيل في الإعدادات."}</p><p>تنبيهات تيليجرام: ${p.telegram ? `مفعّلة · بحد ${p.notification_cap} رسائل يوميًا · هدوء ${p.quiet_start}:00–${p.quiet_end}:00` : "غير مفعّلة"}</p><p class="muted">طلبات الخدمات اليوم: <bdi>${s.usage.daily_calls} / ${p.daily_calls}</bdi> · هذا الشهر: <bdi>${s.usage.monthly_calls} / ${p.monthly_calls}</bdi><br>تكلفة محجوزة تقديرية: ${Number(s.usage.daily_reserved_usd).toFixed(3)} دولار اليوم. ليست فاتورة المزود ولا دليل حصة متاحة.<br>تحليلات الحسابات غير مربوطة حاليًا. النشر يدوي؛ لا أرقام أداء افتراضية.</p>${blockedProviders.map((r) => `<div class="error"><bdi>${esc(r.record_key)}</bdi><p>${esc(r.data.message)}</p><small>آخر فحص: ${fmt(r.data.checked_at)} · إعادة محاولة مؤهلة بعد: ${fmt(r.data.retry_at)}</small></div>`).join("")}${blockedProviders.length ? button("provider-recheck", "أعد التحقق بعد معالجة حصة المزود") : ""}${button("profile", "ضبط المعرفة والقدرة والحدود")}`;
  renderTasks();
  const productionNote = document.createElement("p");
  const remaining = Math.max(
    0,
    Math.min(
      p.daily_calls - s.usage.daily_calls,
      p.monthly_calls - s.usage.monthly_calls,
    ),
  );
  productionNote.className = remaining ? "info-strip" : "error";
  productionNote.textContent = remaining
    ? `توليد الأفكار عند الطلب: متاح ضمن الحدود — المتبقي ${remaining} طلب خدمة. الفيديو المفصل يحتاج عدة طلبات، وليس طلبًا واحدًا. هذا مستقل عن فحص المناسبات الدوري.`
    : "توليد الأفكار متوقف حاليًا عند حد الأداة الداخلي. حد اليوم يتجدد عند منتصف الليل بتوقيت الخليل. الاستكمال لا يمسح الاستهلاك السابق.";
  $("#operations").prepend(productionNote);
  if (runtime?.paused_for_provider)
    $("#operations .badge").textContent = "البحث الشامل / الدوري متوقف";
  if (["auto", "direct"].includes(p.search_provider)) {
    const note = document.createElement("p");
    note.className = "small-note";
    note.textContent = referenceReady
      ? "قراءة المراجع المباشرة متاحة: يمكن للحملات استخدام هذا المسار ضمن حصة توليد النص وحدود التشغيل. لا يرصد الترندات أو المناسبات الجديدة. تعطل البحث الشامل لا يوقف هذا البديل."
      : "عند تعطل البحث الشامل، تحاول الحملات قراءة مراجع إبداعية عامة مباشرة ثم توليد فكرة وخطة إنتاج. لا تُختلق ترندات أو مناسبات. توليد النص يبقى ضمن حصة Gemini وحدود التشغيل.";
    $("#operations").prepend(note);
  }
  $("#operations")
    .querySelectorAll(".error")
    .forEach((error) => {
      const details = document.createElement("details"),
        summary = document.createElement("summary");
      summary.textContent =
        "تفاصيل تعطل المزود · " + error.querySelector("bdi").textContent;
      error.replaceWith(details);
      details.append(summary, error);
    });
  renderCalendar();
  renderIdeas();
}
function renderTasks() {
  if (!state) return;
  const f = $("#task-filter").value;
  const list = state.tasks.filter(
    (t) =>
      f === "all" ||
      (f === "published" && t.status === "published") ||
      (f === "active" && !["published", "cancelled"].includes(t.status)),
  );
  $("#tasks").innerHTML =
    list.map(taskEntry).join("") || empty("لا مهام بهذه الحالة.");
}
function renderCalendar() {
  if (!state) return;
  month ||= state.now.localDate.slice(0, 7);
  if (!selectedDay || !selectedDay.startsWith(month))
    selectedDay =
      month === state.now.localDate.slice(0, 7)
        ? state.now.localDate
        : month + "-01";
  const start = new Date(month + "-01T12:00:00Z");
  const days = new Date(
    Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0),
  ).getUTCDate();
  $("#calendar-title").textContent = new Intl.DateTimeFormat("ar-PS", {
    timeZone: "UTC",
    month: "long",
    year: "numeric",
  }).format(start);
  let html = [
    "الأحد",
    "الإثنين",
    "الثلاثاء",
    "الأربعاء",
    "الخميس",
    "الجمعة",
    "السبت",
  ]
    .map((d) => `<div class="calendar-weekday">${d}</div>`)
    .join("");
  html += Array.from(
    { length: start.getUTCDay() },
    () => '<div class="calendar-day empty-day"></div>',
  ).join("");
  for (let day = 1; day <= days; day++) {
    const date = month + "-" + String(day).padStart(2, "0");
    const events = taskEvents(state.tasks, date),
      plan = state.records.find(
        (r) => r.kind === "day_plan" && r.record_key === date,
      );
    const kinds = [
      ...new Set(events.map((e) => e.kind)),
      ...(plan ? ["daily"] : []),
    ];
    const description = kinds.length
      ? kinds
          .map(
            (k) =>
              ({
                production: "إنتاج",
                review: "مراجعة",
                publish: "نشر مقترح",
                actual: "منشور",
                daily: plan?.data.status === "done" ? "أُنجز" : "شغل يومي",
              })[k],
          )
          .join("، ")
      : "غير مخطط";
    html += `<button class="calendar-day ${date === state.now.localDate ? "today" : ""} ${date === selectedDay ? "selected" : ""}" data-action="select-day" data-id="${date}" aria-label="${date}: ${description}" aria-pressed="${date === selectedDay}"><strong>${day}</strong><span class="day-dots">${kinds.map((k) => `<i class="${k}"></i>`).join("")}</span><small>${description}</small></button>`;
  }
  $("#calendar").innerHTML = html;
  $("#day-detail").innerHTML =
    `<p class="eyebrow">تفاصيل اليوم المحدد</p><h2>${new Intl.DateTimeFormat("ar-PS", { timeZone: "UTC", weekday: "long", day: "numeric", month: "long" }).format(new Date(selectedDay + "T12:00:00Z"))}</h2>${dayAgenda(selectedDay)}`;
}
const activityLabel = {
  idea: "تطوير فكرة",
  production: "إنتاج",
  review: "مراجعة",
  publish: "تحضير للنشر",
  engagement: "تفاعل ومتابعة",
};
function dayAgenda(date, compact = false) {
  const plan = state.records.find(
    (r) => r.kind === "day_plan" && r.record_key === date,
  );
  const events = taskEvents(state.tasks, date);
  let html = "";
  if (plan) {
    const p = plan.data;
    html += `<article class="daily-plan">${badge(p.status === "done" ? "أُنجز شغل اليوم" : activityLabel[p.activity])}<h3>${esc(p.title)}</h3><p>${esc(p.idea)}</p><p><b>المطلوب تسليمه:</b> ${esc(p.deliverable)}</p><p class="small-note">وقت إضافي مقدّر: ${esc(effortLabel(p.minutes))}. ${p.minutes === 0 ? "لا نضيف وقتًا فوق الأعمال المحجوزة لهذا اليوم." : "هذا جهد عمل، وليس مدة فيديو."}</p>${compact ? "" : `<ol>${p.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol><p class="small-note">سبب توزيع هذا العمل اليوم: ${esc(p.why_this_day)}</p>`}<div class="actions">${p.campaign_id ? button("campaign", "الفكرة الكاملة والستوري بورد", p.campaign_id) : button("develop-day", "طوّر هذه الفكرة إلى ملف إنتاج", plan.id)}${button("day-status", p.status === "done" ? "إعادة فتح العمل" : "أنجزت شغل اليوم", plan.id)}${compact ? button("open-day", "تفاصيل اليوم", date) : button("campaign", "مراجع خطة الأسبوع", p.week_id)}</div><p class="small-note">فكرة اليوم بريف عمل؛ زر التطوير يبحث ويكتب المعالجة التفصيلية. الجدولة النهائية تراعي القدرة ولا تضمن التسليم في اليوم نفسه.</p></article>`;
  }
  for (const e of events) {
    if (e.kind === "production")
      html +=
        '<p class="small-note">استكمال إنتاج العمل المحجوز أدناه؛ ظهور الحملة في أكثر من يوم لا يعني أنها فكرة جديدة أو فيديو جديد كل يوم.</p>';
    html += `<article class="agenda-event ${e.kind}"><span class="badge">${e.label}${e.at ? " · " + localDate(e.at).time : ""}</span><h3>${esc(e.task.title)}</h3><div class="actions">${e.task.campaign_id ? button("campaign", "الفكرة وتعليمات التنفيذ", e.task.campaign_id) : ""}${button("task", "تحديث المهمة والمواعيد", e.task.id)}</div></article>`;
  }
  if (!plan && !events.length) {
    const next = state.tasks
      .filter(
        (t) =>
          !["cancelled", "published", "postponed"].includes(t.status) &&
          t.production_at &&
          localDate(t.production_at).date > date,
      )
      .sort(
        (a, b) => Date.parse(a.production_at) - Date.parse(b.production_at),
      )[0];
    html =
      empty(
        "لم تُخصّص أعمال لهذا اليوم بعد؛ لا يعني ذلك أنه يوم راحة أو أن عليك نشر فيديو.",
      ) +
      (next
        ? `<p class="small-note">أقرب بدء إنتاج: ${fmt(next.production_at)} — ${esc(next.title)}</p>`
        : "") +
      button("plan-week", "جهّز خطة شغل متنوعة لسبعة أيام");
  }
  if (compact) {
    const late = state.tasks.filter(
      (t) =>
        !["published", "cancelled", "postponed"].includes(t.status) &&
        t.planned_at &&
        localDate(t.planned_at).date < date,
    );
    if (late.length)
      html += `<p class="error">${late.length} موعد نشر سابق يحتاج متابعة — ليس عملًا جديدًا لليوم.</p>${button("show-tasks", "راجع المهام المتأخرة")}`;
  }
  return html;
}
function safeURL(v) {
  try {
    const u = new URL(v);
    return ["https:", "http:"].includes(u.protocol) ? u.href : "#";
  } catch {
    return "#";
  }
}
function renderIdeas() {
  const ideas = state.records.filter((r) => r.kind === "idea");
  $("#ideas").innerHTML =
    ideas
      .map(
        (r) =>
          `<article class="card spaced">${badge(r.data.status)}<h3>${esc(r.data.title)}</h3><p class="muted">${esc(r.data.concept)}</p><p>${esc(r.data.reason)} · ${esc(r.data.service)}</p><p class="small-note">نافذة الاستفادة: ${esc(r.data.best_use || "غير محددة")} · مراجعة/انتهاء: ${esc(r.data.expiry_date || "غير محدد")}</p><div class="actions">${button("develop-idea", "تطوير كحملة", r.id)}${button("review-idea", "تمت المراجعة", r.id)}${button("archive-idea", "أرشفة", r.id)}${button("campaign", "مراجع الاكتشاف", r.data.campaign_id)}</div></article>`,
      )
      .join("") || empty("لا فرص محفوظة بعد. لا نملأ البنك بأفكار افتراضية.");
  $("#occasions").innerHTML =
    state.records
      .filter((r) => r.kind === "occasion")
      .map((r) => {
        const d = r.data;
        const countdown =
          d.status === "confirmed" && d.verified_at
            ? Math.round(
                (Date.parse(d.date + "T12:00:00Z") -
                  Date.parse(state.now.localDate + "T12:00:00Z")) /
                  86400000,
              )
            : null;
        return `<article class="card spaced">${badge(d.status, d.status !== "confirmed")}<h3>${esc(d.name)}</h3><p>${esc(d.date)} · ${esc(d.geography)}${countdown !== null ? ` · ${countdown >= 0 ? "متبقي " + countdown + " يوم" : "انقضت"}` : ""}</p><p class="muted">${esc(d.relevance || "")}<br>${esc(d.preparation || "")}<br>${esc(d.verification_note || "")}</p><p class="small-note">آخر تحقق: ${fmt(d.verified_at)}</p><a href="${esc(safeURL(d.source))}" target="_blank" rel="noopener noreferrer">مصدر التاريخ ↗</a><div class="actions">${button("occasion-edit", "مراجعة وتوثيق الموعد", r.id)}</div></article>`;
      })
      .join("") ||
    empty("لا مناسبة موثّقة. لا يوجد عيد أو موعد مفترض من أمثلة سابقة.");
}
async function load() {
  if (loading) return;
  loading = true;
  try {
    const d = await api("/dashboard");
    serverAt = Date.parse(d.now.iso);
    receivedAt = performance.now();
    state = d;
    lastDay = d.now.localDate;
    $("#connection").innerHTML = "";
    render();
    tickClock();
    if (
      dialog.open &&
      activeCampaign &&
      ["queued", "running"].includes(activeCampaign.campaign.status) &&
      !dialog.querySelector("form")
    ) {
      const latest = d.campaigns.find(
        (c) => c.id === activeCampaign.campaign.id,
      );
      if (latest && latest.updated_at !== activeCampaign.campaign.updated_at)
        await openCampaign(latest.id);
    }
  } catch (e) {
    $("#connection").innerHTML =
      `<p class="error">${esc(e.message)}${state ? "<br>السجلات المعروضة آخر نسخة وصلت؛ لا نعتبر الاتصال سليمًا." : ""}</p>`;
  } finally {
    loading = false;
  }
}
function tickClock() {
  if (!state) return;
  const now = new Date(serverAt + performance.now() - receivedAt);
  const d = localDate(now);
  $("#clock").textContent =
    new Intl.DateTimeFormat("ar-PS", {
      timeZone: ZONE,
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(now) + " · الخليل";
  if (d.date !== lastDay) {
    lastDay = d.date;
    load();
  }
}
function campaignForm(autonomous = false, brief = "", dayPlanId = "") {
  open(
    autonomous ? "خطّط حملة مناسبة الآن" : "أنشئ حملة جديدة",
    `<p class="muted">يُحفظ الطلب ثم يجري البحث على الخادم. تستطيع إغلاق الأداة والعودة. لا يوجد تأخير مصطنع ولا نشر تلقائي.</p><form data-form="campaign" data-mode="${autonomous ? "autonomous" : "brief"}" data-key="${crypto.randomUUID()}"><div class="fields">${area("request", "الهدف أو الطلب", brief || (autonomous ? "اختر حملة مناسبة الآن لتسويق XPAND بحسب ملف الشركة والمحتوى السابق والفرص الموثّقة." : ""))}${field("service", "الخدمة (اختياري)")}${field("audience", "الجمهور (اختياري)", state?.profile.audience || "")}${field("timeframe", "مدة الحملة أو قيد زمني (اختياري)")}</div><p class="small-note">حتى ${state?.settings.task_calls || 10} طلبات خدمات للمهمة ضمن الحد اليومي والشهري. مراجع البحث نصية؛ لا ندّعي مشاهدة فيديوهات.</p><button class="primary dialog-submit">ابدأ البحث الحقيقي ←</button></form>`,
  );
  dialog.querySelector("form").dataset.day = dayPlanId;
  if (!brief && !autonomous) {
    const label = document.createElement("label");
    label.textContent = "مدة الحملة بالأيام (2–28)";
    const input = document.createElement("input");
    Object.assign(input, {
      name: "campaign_days",
      type: "number",
      min: "2",
      max: "28",
      value: "7",
      required: true,
    });
    label.append(input);
    dialog.querySelector(".fields").append(label);
  }
  dialog.querySelector(".muted").textContent =
    "بحث وقراءة مصادر ← استخلاص فرص ← 3 اتجاهات ← نقد واختيار ← معالجة ← ستوري بورد ← فحص الجودة. المراحل محفوظة على الخادم حتى لو أغلقت الأداة.";
  dialog.querySelector(".small-note").textContent =
    `الفيديو المفصّل يحتاج عادة 6 طلبات للنموذج إضافة للبحث، ضمن حد المهمة (${state?.settings.task_calls || 10}) وحدود اليوم والشهر. إذا انتهت الحصة تُحفظ المراحل. الناتج ملف إنتاج، وليس فيديو مولّدًا أو منشورًا تلقائيًا.`;
  if (!brief && !autonomous) {
    dialog.querySelector(".muted").textContent =
      "نبحث ونجهز أفكار فيديوهات وبوسترات مترابطة ومختلفة خلال مدة الحملة. يمكنك إغلاق الأداة؛ العمل محفوظ على الخادم.";
    dialog.querySelector(".small-note").textContent =
      "الأيام في الخطة مقترحة وليست مواعيد إنتاج محجوزة. اختر الفكرة التي تريد تنفيذها لتجهيز مهمتها ضمن قدرة الفريق. استهلاك البحث والنموذج يُحسب ضمن حدودك الحالية.";
    dialog.querySelector('[name="timeframe"]').closest("label").remove();
  }
}
const listHTML = (v) =>
  Array.isArray(v)
    ? `<ul>${v.map((x) => `<li>${esc(typeof x === "object" ? JSON.stringify(x) : x)}</li>`).join("")}</ul>`
    : `<p>${esc(v)}</p>`;
async function openCampaign(id) {
  open("جارٍ تحميل الحملة…", "");
  const d = await api("/campaigns/" + id);
  activeCampaign = d;
  const c = d.campaign,
    r = c.result || {};
  const sections = {
    objective: "الهدف",
    message: "الرسالة",
    concept: "الفكرة الإبداعية",
    visual_direction: "الستايل",
    duration_seconds: "المدة بالثواني",
    headline: "العنوان الرئيسي",
    composition: "تكوين التصميم",
    caption: "الكابشن",
  };
  let body = `${badge(c.display_status || c.status)}<p class="muted">${esc(c.request_text)}</p><p class="small-note">بدأ: ${fmt(c.started_at)} · آخر نشاط: ${fmt(c.updated_at)} · محاولة ${c.attempts} من 3</p>${c.limitations ? `<p class="error">${esc(c.limitations)}</p>` : ""}<p>${esc(c.display_status === "unverified_result" ? "بحث سابق غير مكتمل" : stages[c.stage] || labels[c.stage] || c.stage)}</p>`;
  if (r.research_mode === "direct_references")
    body +=
      '<p class="small-note">حملة مبنية على قراءة مباشرة لمراجع إبداعية عامة وملف XPAND. ليست دراسة حديثة للسوق أو المناسبات. المقترح يحتاج مراجعة الفريق قبل الإنتاج والنشر.</p>';
  if (r.title) {
    if (r.items?.length)
      body += `<p>${esc(r.summary)}</p><p class="info-strip">حملة ${esc(r.campaign_days)} أيام · التوزيع التالي مقترح، وليس مهام مستحقة اليوم. تجهيز مهمة التنفيذ يحدد المواعيد حسب قدرة الفريق.</p>${r.items.map((item, index) => `<article class="card spaced">${badge(`اليوم ${item.day} · ${item.format === "video" ? "فيديو" : "بوستر"}`)}<h3>${esc(item.title)}</h3><p><b>الفكرة:</b> ${esc(item.concept)}</p><p><b>الرسالة:</b> ${esc(item.message)}</p><p><b>الستايل:</b> ${esc(item.visual_direction)}</p>${item.duration_seconds ? `<p>مدة الفيديو: ${esc(item.duration_seconds)} ثانية</p>` : `<p>${esc(item.composition)}</p>`}<p><b>الكابشن:</b> ${esc(item.caption)}</p>${compactStoryboard(item, esc)}${button("develop-asset", "جهّز مهمة تنفيذ هذه الفكرة", String(index))}</article>`).join("")}`;
    body += `<div class="detail-grid">${Object.entries(sections)
      .filter(([k]) => r[k] !== null && r[k] !== undefined)
      .map(
        ([k, l]) =>
          `<article><b>${l}</b><p>${esc(k === "effort_hours" ? effortLabel(r[k] * 60) + " — جهد للفريق وليس مدة الفيديو" : k === "format" ? { video: "فيديو", static: "تصميم ثابت", carousel: "منشور شرائح", story: "ستوري" }[r[k]] || r[k] : r[k])}</p></article>`,
      )
      .join("")}</div>`;
    body += compactStoryboard(r, esc);
    body += `<div class="actions">${button("research-again", "ابحث عن فكرة مختلفة بالكامل ↻", c.id)}</div><details><summary>تفاصيل إضافية للمخرج وسجل البحث (اختياري)</summary>`;
    body += creativeView(r, d.process, { esc, listHTML, effortLabel });
    if (!r.storyboard && r.scenes?.length)
      body +=
        `<h3>ملخص اللقطات — ليس ستوري بورد تفصيليًا</h3><p class="small-note">ملف محفوظ من المسار السابق. التطوير الجديد يحفظ هذا الأصل دون استبداله.</p>${button("research-again", "طوّر معالجة تفصيلية جديدة", c.id)}` +
        r.scenes
          .map(
            (s, i) =>
              `<article class="scene"><b>${i + 1} · ${esc(s.timing)}</b><p>${esc(s.visual)}</p>${s.on_screen ? `<p>على الشاشة: ${esc(s.on_screen)}</p>` : ""}${s.voiceover ? `<p>التعليق الصوتي: ${esc(s.voiceover)}</p>` : ""}</article>`,
          )
          .join("");
    for (const [k, l] of [
      ["platforms", "المنصات"],
      ["adaptations", "التكييف لكل منصة"],
      ["assets", "مواد ومعلومات مطلوبة"],
      ["additional_resources", "موارد إضافية"],
      ["assumptions", "افتراضات"],
      ["limitations", "القيود"],
    ])
      body += `<details><summary>${l}</summary>${k === "adaptations" ? (r[k] || []).map((a) => `<p><b>${esc(a.platform)}</b>: ${esc(a.instructions)}<br>إعداد هذه النسخة: ${esc(effortLabel(a.effort_hours * 60))} — محسوب ضمن الإجمالي.</p>`).join("") : listHTML(r[k] || [])}</details>`;
    if (r.schedule)
      body += `<details open><summary>الخطة الأصلية · توقيت الخليل</summary><p>بدء الإنتاج: ${fmt(r.schedule.production_at)}<br>المراجعة: ${fmt(r.schedule.review_at)}<br>النشر المقترح: ${fmt(r.schedule.planned_at)}</p><p>${esc(r.schedule.rationale)}</p><p class="small-note">التعديلات اللاحقة على المواعيد تظهر في المهمة والتقويم.</p></details>`;
  } else if (c.result)
    body += `<details open><summary>${c.kind === "scan" ? "نتيجة الدورة" : "السجل الأصلي المحفوظ قبل الترقية"}</summary>${Object.entries(
      r,
    )
      .map(([k, v]) => `<h3>${esc(k)}</h3>${listHTML(v)}`)
      .join("")}</details>`;
  if (c.kind === "week" && r.days)
    body += `<p>${esc(r.summary)}</p><p class="small-note">أفكار يومية أولية ضمن القدرة. لا تعني فيديو جديدًا كل يوم، ولا نشرًا تلقائيًا.</p>${r.days.map((day) => `<article class="scene"><b>${esc(day.date)} · ${esc(activityLabel[day.activity])}</b><h3>${esc(day.title)}</h3><p>${esc(day.idea)}</p><p>التسليم: ${esc(day.deliverable)}</p><p>جهد إضافي: ${esc(effortLabel(day.minutes))}</p>${listHTML(day.steps)}${r.skipped_dates?.includes(day.date) ? '<p class="error">لهذا اليوم خطة سابقة محفوظة؛ لم نستبدلها بهذا الاقتراح.</p>' : ""}${button("open-day", "فتح هذا اليوم في التقويم", day.date)}</article>`).join("")}`;
  if (!r.title && d.process?.insights)
    body += creativeView({}, d.process, { esc, listHTML, effortLabel });
  body += `<details><summary>المراجع التي وصلت فعليًا (${d.sources.length})</summary>${
    d.sources
      .map((s) => {
        let meta = {};
        try {
          meta = JSON.parse(s.observation);
        } catch {
          meta = {
            observation: s.observation,
            inspected: "مقتطف نصي من الإصدار السابق",
          };
        }
        return `<article class="entry" id="source-${esc(s.id)}"><a href="${esc(safeURL(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a><p>${esc(meta.observation)}</p><p class="small-note">${esc(meta.inspected)}<br>${esc(meta.limitations || "")}<br>الوصول: ${fmt(s.accessed_at)} · تاريخ النشر: ${esc(meta.published_at || "غير متاح")}${meta.reused ? " · أُعيد استخدام بحث حديث" : ""}</p></article>`;
      })
      .join("") || empty("لا مراجع محفوظة بعد.")
  }</details>`;
  const suggestions = [
    ...new Set(
      d.sources
        .map((s) => {
          try {
            return JSON.parse(s.observation).search_suggestions;
          } catch {
            return null;
          }
        })
        .filter(Boolean),
    ),
  ];
  if (suggestions.length)
    body += `<section><h3>اقتراحات Google Search</h3>${suggestions.map((html) => `<iframe title="اقتراحات البحث من Google" sandbox="allow-popups allow-popups-to-escape-sandbox" referrerpolicy="no-referrer" style="width:100%;height:150px;border:0;background:white;border-radius:12px" srcdoc="${esc(`<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data:; base-uri 'none'; form-action 'none'">` + html)}"></iframe>`).join("")}</section>`;
  body += `<details><summary>سجل اتصالات البحث والنموذج (${d.calls.length})</summary>${d.calls.map((x) => `<article class="entry"><b>${esc(x.provider)} · ${esc(x.status)}</b><p>${fmt(x.created_at)}<br>${esc(x.error || "")}</p><pre class="audit">${esc(JSON.stringify(x.usage || {}, null, 2))}</pre></article>`).join("") || empty("لم تُنفذ اتصالات بعد.")}<p class="small-note">حصة الطلب تُحجز قبل الاتصال لمنع تجاوز الحدود عند إعادة التشغيل. الحجز لا يعني نجاح الطلب.</p></details>`;
  if (c.status === "completed" && c.kind === "campaign")
    body += `<div class="actions">${button("edit-campaign", "تعديل المحتوى مع حفظ نسخة")}${button("feedback", "تقييم الفكرة أو تسجيل نتيجة")}${button("export", "تنزيل التفاصيل JSON")}</div><details><summary>الملاحظات والإصدارات (${d.feedback.length} / ${d.versions.length})</summary>${d.feedback.map((f) => `<p>${esc(f.data.type)}: ${esc(f.data.note)} · ${fmt(f.created_at)}</p>`).join("")}${d.versions.map((v) => `<details><summary>نسخة محفوظة ${fmt(v.created_at)}</summary><pre class="audit">${esc(JSON.stringify(v.snapshot.result || v.snapshot, null, 2))}</pre></details>`).join("")}</details>`;
  if (r.title) body += "</details>";
  open(r.title || r.الاسم || "تفاصيل البحث", body);
}
function taskForm(t = null) {
  open(
    t ? "الحالة والمواعيد" : "مهمة إنتاج جديدة",
    `<form data-form="task" data-id="${t?.id || ""}" data-version="${t?.version || ""}"><div class="fields">${field("title", "اسم المهمة", t?.title || "", "text", true)}${area("description", "تعليمات المهمة", t?.description || "")}${t ? `<label class="full">الحالة<select name="status">${["planned", "awaiting_start", "in_production", "in_review", "ready_to_publish", "published", "postponed", "cancelled"].map((s) => `<option value="${s}" ${t.status === s ? "selected" : ""}>${labels[s]}</option>`).join("")}</select></label>` : ""}${field("production_at", "بدء الإنتاج · الخليل", inputDate(t?.production_at), "datetime-local")}${field("review_at", "المراجعة · الخليل", inputDate(t?.review_at), "datetime-local")}${field("planned_at", "النشر المقترح · الخليل", inputDate(t?.planned_at), "datetime-local")}</div>${t ? '<label class="check-label"><input type="checkbox" name="confirm_published"> أؤكد أن المحتوى نُشر فعلًا (عند اختيار «منشور»).</label>' : ""}<p class="small-note">الاتجاه يثبت عند التنفيذ. تعديلاتك الصريحة محفوظة بإصدارات.</p><button class="primary dialog-submit">حفظ المهمة</button></form>`,
  );
}
function profileForm() {
  const p = state.profile,
    s = state.settings;
  const fields = {
    facts: "حقائق مؤكدة عن الشركة",
    services: "الخدمات",
    audience: "الجمهور",
    tone: "نبرة الكتابة",
    portfolio: "أعمال متاحة وروابط معتمدة",
    contacts: "قنوات تواصل مثبتة",
    preferences: "تفضيلات",
    assumptions: "افتراضات غير مؤكدة",
  };
  const nums = {
    interval_hours: "كل كم ساعة؟ (2–24)",
    daily_calls: "حد طلبات الخدمات يوميًا",
    monthly_calls: "حد الطلبات شهريًا",
    task_calls: "حد الطلبات لكل مهمة",
    rounds: "جولات التطوير (1–3)",
    concurrency: "مهام متزامنة (1–2)",
    timeout_minutes: "مهلة المهمة بالدقائق",
    daily_usd: "ميزانية يومية بالدولار",
    monthly_usd: "ميزانية شهرية بالدولار",
    search_call_usd: "أقصى تكلفة طلب بحث بالدولار",
    model_call_usd: "أقصى تكلفة طلب نموذج بالدولار",
    quiet_start: "بدء الهدوء (ساعة 0–23)",
    quiet_end: "نهاية الهدوء (ساعة 0–23)",
    notification_cap: "أقصى رسائل تيليجرام يوميًا",
  };
  open(
    "معرفة XPAND وحدود التشغيل",
    `<form data-form="profile"><div class="fields">${Object.entries(fields)
      .map(([k, l]) => area(k, l, p[k]))
      .join(
        "",
      )}${field("daily_hours", "إجمالي ساعات الفريق المتاحة يوميًا", p.daily_hours, "number")}${field("weekly_videos", "الحد التقريبي للفيديوهات أسبوعيًا", p.weekly_videos, "number")}</div><button class="primary dialog-submit">حفظ ملف الشركة</button></form><hr class="divider"><form data-form="settings"><h3>البحث الدوري والحدود</h3><p class="small-note">ابدأ بحدود منخفضة. تكلفة الطلب القصوى يجب أن تطابق تسعير المزود وعمق البحث. صفر فقط إذا تأكدت من الحصة المجانية أو عطلت الفوترة عند المزود. هذه حدود حجز تقديرية وليست قراءة لحساب الفوترة.</p><div class="fields">${Object.entries(
      nums,
    )
      .map(([k, l]) => field(k, l, s[k], "number"))
      .join(
        "",
      )}<label>عمق البحث<select name="depth"><option value="basic" ${s.depth === "basic" ? "selected" : ""}>أساسي</option><option value="advanced" ${s.depth === "advanced" ? "selected" : ""}>متقدم (تحقق من التكلفة)</option></select></label></div><label class="check-label"><input type="checkbox" name="pricing_confirmed" ${s.pricing_confirmed ? "checked" : ""}> تحققت من الأسعار / الحصة المجانية وحدود الإنفاق.</label><label class="check-label"><input type="checkbox" name="recurring" ${s.recurring ? "checked" : ""}> تفعيل البحث الدوري في الخلفية</label><label class="check-label"><input type="checkbox" name="telegram" ${s.telegram ? "checked" : ""}> إرسال تنبيهات لهذا المستخدم على تيليجرام</label><p class="small-note">كل الأوقات حسب الخليل. لا رسائل في ساعات الهدوء ولا رسائل إلى العملاء.</p><button class="primary dialog-submit">اعتماد إعدادات التشغيل</button></form>`,
  );
  dialog.querySelector('[data-form="settings"] .fields').insertAdjacentHTML(
    "afterbegin",
    `<label class="full">مصدر البحث<select name="search_provider">${[
      ["auto", "تلقائي: بحث شامل ثم مراجع عامة مباشرة للحملات عند التعذر"],
      ["direct", "مراجع عامة مباشرة للحملات — دون بحث ترندات أو مناسبات"],
      ["tavily", "Tavily فقط"],
      ["gemini", "بحث Google عبر Gemini فقط"],
    ]
      .map(
        ([v, name]) =>
          `<option value="${v}" ${s.search_provider === v ? "selected" : ""}>${name}</option>`,
      )
      .join(
        "",
      )}</select><small>النموذج يحتاج حصة لأداة البحث نفسها. البديل ليس ضمانًا للمجانية أو تجاوزًا للحصة؛ يحتسب ضمن حدودك.</small></label>`,
  );
  dialog
    .querySelectorAll("input[type=number]")
    .forEach(
      (x) =>
        (x.step = x.name.includes("usd")
          ? "0.001"
          : x.name === "daily_hours"
            ? "0.5"
            : "1"),
    );
}
function occasionForm(r = null) {
  const d = r?.data || {};
  open(
    "توثيق مناسبة من مصدر",
    `<form data-form="occasion"><input type="hidden" name="key" value="${esc(r?.record_key || "")}"><div class="fields">${field("name", "اسم المناسبة", d.name)}${field("date", "تاريخ محلي (يوم كامل)", d.date, "date")}${field("geography", "النطاق الجغرافي", d.geography || "فلسطين")}${field("source", "رابط المصدر", d.source, "url")}${area("relevance", "علاقتها بخدمات XPAND", d.relevance)}${area("preparation", "متطلبات التحضير والوقت اللازم", d.preparation)}<label>حالة الموعد<select name="status">${["unverified", "provisional", "confirmed"].map((s) => `<option value="${s}" ${d.status === s ? "selected" : ""}>${labels[s]}</option>`).join("")}</select></label></div><p class="small-note">«مؤكد» يعني أنك راجعت مصدر التاريخ. الأعياد الدينية تبقى متوقعة حتى الإعلان الرسمي. تغيير التاريخ ينبهك ولا يغيّر العمل الجاري.</p><button class="primary dialog-submit">حفظ التوثيق</button></form>`,
  );
}
document.addEventListener("click", async (e) => {
  const sourceLink = e.target.closest('a[href^="#source-"]');
  if (sourceLink) {
    const source = document.getElementById(
      sourceLink.getAttribute("href").slice(1),
    );
    if (source) {
      e.preventDefault();
      source.closest("details").open = true;
      source.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return;
  }
  const nav = e.target.closest("[data-view]");
  if (nav) {
    showView(nav.dataset.view);
    return;
  }
  const b = e.target.closest("[data-action]");
  if (!b) return;
  const a = b.dataset.action,
    id = b.dataset.id;
  try {
    if (a === "close") {
      dialog.close();
      return;
    }
    if (a === "refresh") {
      await load();
      return;
    }
    if (!state) throw new Error("افتح الأداة من تيليجرام وانتظر تحميل سجلاتك.");
    if (a === "new") campaignForm();
    else if (a === "plan-week")
      open(
        "خطة شغل متنوع لسبعة أيام",
        `<p class="muted">أفكار وتصاميم وستوري وإنتاج ومراجعة، ضمن ${state.profile.daily_hours} ساعة يوميًا وحد ${state.profile.weekly_videos} فيديوهات أسبوعيًا. نحافظ على الأيام المخططة سابقًا. يُحفظ البحث والجدول على الخادم.</p><form data-form="week" data-key="${crypto.randomUUID()}">${field("start_date", "بداية الأسبوع · الخليل", state.now.localDate, "date")}${area("request", "أولوية الأسبوع (اختياري)", "التعريف بخدمات XPAND لأصحاب الأعمال في الخليل، مع تنويع الفكرة والمخرج اليومي.")}<button class="primary dialog-submit">ابدأ تخطيط الأسبوع</button></form>`,
      );
    else if (a === "select-day" || a === "open-day") {
      selectedDay = id;
      month = id.slice(0, 7);
      renderCalendar();
      if (a === "open-day") {
        dialog.close();
        showView("calendar");
      }
    } else if (a === "show-tasks") showView("tasks");
    else if (a === "develop-day") {
      const p = state.records.find((r) => r.id === id);
      campaignForm(
        false,
        `${p.data.title}\nالفكرة: ${p.data.idea}\nالتسليم: ${p.data.deliverable}\n${p.data.steps.join("\n")}\nنوع المحتوى: ${p.data.format}. طوّر معالجة تنفيذية مع مراعاة السعة الفعلية.`,
        p.id,
      );
    } else if (a === "day-status") {
      const p = state.records.find((r) => r.id === id);
      await api("/plan-days/" + id, {
        method: "PATCH",
        body: JSON.stringify({
          version: p.version,
          status: p.data.status === "done" ? "planned" : "done",
        }),
      });
      await load();
    } else if (a === "autonomous") campaignForm(true);
    else if (a === "campaign") await openCampaign(id);
    else if (a === "profile") profileForm();
    else if (a === "develop-asset") {
      const item = activeCampaign?.campaign?.result?.items?.[Number(id)];
      if (!item) throw new Error("حدّث الحملة ثم اختر الفكرة.");
      campaignForm(
        false,
        "جهّز معالجة تنفيذية لهذه الفكرة المختارة دون تغيير الحدث أو الرسالة. نوع المحتوى: " +
          item.format +
          "\n" +
          JSON.stringify(item),
      );
    } else if (a === "research-again") {
      const old =
        activeCampaign?.campaign?.id === id
          ? activeCampaign.campaign
          : state.campaigns.find((c) => c.id === id);
      campaignForm(
        false,
        (old?.request_text || "") +
          "\nأريد فكرة بديلة بالكامل، لا إعادة صياغة أو تغيير الألوان. حافظ على الهدف، وغيّر الحدث والاستعارة والافتتاحية والنهاية. لا تكرر هذه الفكرة: " +
          (old?.result?.concept || old?.result?.title || ""),
      );
      dialog.querySelector("form").dataset.alternative = id;
      if (old?.result?.campaign_days)
        dialog.querySelector("form").dataset.days = old.result.campaign_days;
    } else if (a === "provider-recheck") {
      await api("/providers/recheck", { method: "POST" });
      toast(
        "أُتيح فحص الخدمة عند استكمال الحملة. لم يُمسح الاستهلاك ولم تُفعّل فوترة.",
      );
      await load();
    } else if (a === "new-task") taskForm();
    else if (a === "task") taskForm(state.tasks.find((t) => t.id === id));
    else if (a === "cancel" || a === "retry") {
      await api(`/campaigns/${id}/${a}`, { method: "POST" });
      toast(
        a === "cancel"
          ? "أُلغي البحث؛ تتوقف المراحل التالية."
          : "أُعيد إلى قائمة التنفيذ مع حفظ العمل والاستهلاك السابق.",
      );
      await load();
    } else if (a === "read") {
      await api("/records/" + id, { method: "PATCH", body: "{}" });
      await load();
    } else if (a === "notice-target") {
      if (state.tasks.some((t) => t.id === id))
        taskForm(state.tasks.find((t) => t.id === id));
      else if (state.campaigns.some((c) => c.id === id)) await openCampaign(id);
      else {
        dialog.close();
        showView("ideas");
      }
    } else if (a === "develop-idea") {
      const r = state.records.find((r) => r.id === id);
      campaignForm(
        false,
        `${r.data.title}: ${r.data.concept}\nالخدمة: ${r.data.service}`,
      );
    } else if (a === "review-idea" || a === "archive-idea") {
      await api("/records/" + id, {
        method: "PATCH",
        body: JSON.stringify({
          status: a === "review-idea" ? "reviewed" : "archived",
        }),
      });
      await load();
    } else if (a === "occasion-new") occasionForm();
    else if (a === "occasion-edit")
      occasionForm(state.records.find((r) => r.id === id));
    else if (a.includes("month")) {
      const d = new Date(
        (month || state.now.localDate.slice(0, 7)) + "-01T12:00:00Z",
      );
      d.setUTCMonth(d.getUTCMonth() + (a === "prev-month" ? -1 : 1));
      month =
        a === "this-month"
          ? state.now.localDate.slice(0, 7)
          : d.toISOString().slice(0, 7);
      renderCalendar();
    } else if (a === "feedback")
      open(
        "ملاحظات تحسّن التوصيات",
        `<form data-form="feedback"><label>نطاق الملاحظة<select name="scope"><option value="project">لهذا المشروع فقط</option><option value="preference">تفضيل شخصي</option><option value="brand">قاعدة دائمة لهوية XPAND</option></select></label><label>نوع الملاحظة<select name="type"><option value="accepted">فكرة مقبولة</option><option value="rejected">رفض مع السبب</option><option value="revision">تفضيل أو تصحيح</option><option value="outcome">نتيجة فعلية مُدخلة يدويًا</option></select></label>${area("note", "التفاصيل والسبب / النتائج الموثّقة")}<label>نوع الأداء عند تسجيل نتيجة<select name="measurement_type"><option value="organic">عضوي</option><option value="paid">ممول</option></select></label>${field("period", "فترة القياس عند تسجيل نتيجة")}<button class="primary dialog-submit">حفظ الملاحظة</button></form>`,
      );
    else if (a === "edit-campaign") {
      const r = activeCampaign.campaign.result;
      open(
        "تعديل المحتوى وحفظ النسخة السابقة",
        `<form data-form="edit-campaign">${Object.entries(r)
          .filter(([k, v]) => typeof v === "string" && k !== "format")
          .map(([k, v]) =>
            area(
              k,
              {
                title: "اسم الحملة",
                caption: "الكابشن",
                concept: "الفكرة",
                production_instructions: "تعليمات التنفيذ",
                hook: "الافتتاحية",
                cta: "دعوة التواصل",
              }[k] || k,
              v,
            ),
          )
          .join(
            "",
          )}<button class="primary dialog-submit">حفظ إصدار جديد</button></form>`,
      );
    } else if (a === "export") {
      const blob = new Blob([JSON.stringify(activeCampaign, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "xpand-campaign.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  } catch (err) {
    toast(err.message);
  }
});
document.addEventListener("submit", async (e) => {
  const f = e.target.closest("[data-form]");
  if (!f) return;
  e.preventDefault();
  const submit = f.querySelector("button[type=submit],button:not([type])");
  if (submit) submit.disabled = true;
  const v = Object.fromEntries(new FormData(f));
  try {
    const type = f.dataset.form;
    if (type === "campaign") {
      const request = [
        v.request,
        v.service && "الخدمة: " + v.service,
        v.audience && "الجمهور: " + v.audience,
        v.timeframe && "المدة: " + v.timeframe,
      ]
        .filter(Boolean)
        .join("\n");
      await api("/campaigns", {
        method: "POST",
        headers: { "Idempotency-Key": f.dataset.key },
        body: JSON.stringify({
          request,
          mode: f.dataset.mode,
          day_plan_id: f.dataset.day || undefined,
          alternative_to: f.dataset.alternative || undefined,
          campaign_days:
            v.campaign_days || f.dataset.days
              ? Number(v.campaign_days || f.dataset.days)
              : undefined,
        }),
      });
    } else if (type === "week")
      await api("/week-plan", {
        method: "POST",
        headers: { "Idempotency-Key": f.dataset.key },
        body: JSON.stringify(v),
      });
    else if (type === "task")
      await api("/tasks" + (f.dataset.id ? "/" + f.dataset.id : ""), {
        method: f.dataset.id ? "PATCH" : "POST",
        body: JSON.stringify({
          ...v,
          version: Number(f.dataset.version),
          confirm_published: v.confirm_published === "on",
        }),
      });
    else if (type === "profile")
      await api("/profile", {
        method: "PUT",
        body: JSON.stringify({
          ...v,
          daily_hours: Number(v.daily_hours),
          weekly_videos: Number(v.weekly_videos),
        }),
      });
    else if (type === "settings")
      await api("/settings", {
        method: "PUT",
        body: JSON.stringify({
          ...v,
          recurring: v.recurring === "on",
          telegram: v.telegram === "on",
          pricing_confirmed: v.pricing_confirmed === "on",
        }),
      });
    else if (type === "occasion")
      await api("/occasions", { method: "POST", body: JSON.stringify(v) });
    else if (type === "feedback")
      await api("/campaigns/" + activeCampaign.campaign.id + "/feedback", {
        method: "POST",
        body: JSON.stringify(v),
      });
    else if (type === "edit-campaign")
      await api("/campaigns/" + activeCampaign.campaign.id, {
        method: "PATCH",
        body: JSON.stringify({
          revision: activeCampaign.campaign.revision,
          result: { ...activeCampaign.campaign.result, ...v },
        }),
      });
    dialog.close();
    toast(
      type === "campaign" || type === "week"
        ? "حُفظ طلب البحث. تظهر الحالة هنا حتى لو أغلقت الأداة."
        : "حُفظ التغيير في قاعدة البيانات.",
    );
    await load();
  } catch (err) {
    dialog.querySelector(".form-message").textContent = err.message;
  } finally {
    if (submit) submit.disabled = false;
  }
});
$("#task-filter").addEventListener("change", renderTasks);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) load();
});
load();
setInterval(tickClock, 1000);
setInterval(() => {
  if (!document.hidden) load();
}, 10000);
import { libraryCard } from "./library.js";
