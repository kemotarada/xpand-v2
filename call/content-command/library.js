// Presentation only: a submitted brief must never look like a finished idea.
export function libraryCard(c, usage = {}, settings = {}) {
  const complete =
    c.status === "completed" &&
    !!c.result &&
    c.display_status !== "unverified_result";
  const request = String(c.request_text || "").trim();
  const heading = complete
    ? c.result.title || c.result.الاسم || "ملف محفوظ"
    : c.kind === "week"
      ? "طلب خطة أسبوع — غير مكتمل"
      : c.kind === "scan"
        ? "فحص فرص — غير مكتمل"
        : "طلب تطوير فكرة — غير مكتمل";
  const budgetReason =
    Number(usage.daily_calls) >= Number(settings.daily_calls)
      ? "اكتمل حد اليوم؛ يتجدد عند منتصف الليل بتوقيت الخليل، أو بعد تعديل الحد المعتمد."
      : Number(usage.monthly_calls) >= Number(settings.monthly_calls)
        ? "اكتمل حد الشهر؛ انتظر تجدد الحد أو عدّل الحد المعتمد."
        : Number(c.call_count) >= Number(settings.task_calls)
          ? "بلغ هذا الطلب حد المهمة؛ رفع حد اليوم وحده لا يكفي لاستكماله."
          : "";
  return {
    heading,
    request,
    complete,
    budgetReason,
    canRetry:
      ["failed", "blocked", "needs_information", "cancelled"].includes(
        c.status,
      ) &&
      c.attempts < 3 &&
      !budgetReason,
  };
}
