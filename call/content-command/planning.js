// Shared, deterministic calendar logic; dates are civil dates in Asia/Hebron.
export const ZONE = "Asia/Hebron";
export function dayOf(value) {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
      .formatToParts(new Date(value))
      .map((p) => [p.type, p.value]),
  );
  return `${p.year}-${p.month}-${p.day}`;
}
export const addDays = (date, n) =>
  new Date(Date.parse(date + "T12:00:00Z") + n * 86400000)
    .toISOString()
    .slice(0, 10);
export function taskEvents(tasks, date) {
  const events = [];
  for (const task of tasks.filter(
    (t) => !["cancelled", "postponed"].includes(t.status),
  )) {
    for (const [key, kind, label] of [
      ["review_at", "review", "مراجعة واعتماد"],
      ["planned_at", "publish", "نشر مقترح"],
      ["actual_published_at", "actual", "نُشر فعليًا"],
    ]) {
      if (task[key] && dayOf(task[key]) === date)
        events.push({ task, kind, label, at: task[key] });
    }
    const start = task.production_at && dayOf(task.production_at);
    const end = task.review_at && dayOf(task.review_at);
    if (
      start &&
      (start === date || (date > start && end && date < end)) &&
      task.status !== "published"
    )
      events.push({
        task,
        kind: "production",
        label: start === date ? "بدء الإنتاج" : "استكمال الإنتاج",
        at: start === date ? task.production_at : null,
      });
  }
  return events;
}
export function availableWeek(start, tasks, records, profile) {
  const capacity = Math.round(profile.daily_hours * 60);
  return Array.from({ length: 7 }, (_, i) => {
    const date = addDays(start, i);
    const saved = records.find((r) => r.record_key === date);
    let used = 0;
    for (const { task, kind } of taskEvents(tasks, date)) {
      if (kind === "production") {
        const elapsed = Math.round(
          (Date.parse(date + "T12:00:00Z") -
            Date.parse(dayOf(task.production_at) + "T12:00:00Z")) /
            86400000,
        );
        const total = Number(task.metadata?.effort_hours) * 60;
        used +=
          Number.isFinite(total) && total > 0
            ? Math.min(capacity, Math.max(0, total - elapsed * capacity))
            : capacity;
      } else if (kind === "review") used += 30;
      else if (kind === "publish") used += 15;
    }
    return {
      date,
      remaining_minutes: saved ? 0 : Math.max(0, capacity - used),
      existing_plan: !!saved,
      scheduled: taskEvents(tasks, date).map((e) => ({
        title: e.task.title,
        kind: e.kind,
      })),
    };
  });
}
export function effortLabel(minutes) {
  const n = Math.max(0, Math.round(Number(minutes) || 0)),
    h = Math.floor(n / 60),
    m = n % 60;
  return (
    [h ? `${h} ${h === 1 ? "ساعة" : "ساعات"}` : "", m ? `${m} دقيقة` : ""]
      .filter(Boolean)
      .join(" و") || "ضمن العمل المجدول"
  );
}
