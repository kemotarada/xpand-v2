// Provider responses are untrusted. Persist actionable categories, never raw bodies/keys.
export function messageText(value, fallback = "تعذر إتمام الطلب.") {
  if (typeof value === "string") return value.trim() || fallback;
  if (Array.isArray(value))
    return (
      value
        .map((x) => messageText(x, ""))
        .filter(Boolean)
        .join("؛ ") || fallback
    );
  if (value && typeof value === "object") {
    for (const key of ["message", "detail", "error", "description"])
      if (value[key] && value[key] !== value)
        return messageText(value[key], fallback);
  }
  return fallback;
}

export function providerIssue(
  service,
  status,
  body = {},
  retryAfter = null,
  now = Date.now(),
) {
  const name =
    service === "tavily"
      ? "Tavily"
      : service.startsWith("grounding:")
        ? "بحث Google عبر Gemini"
        : "Gemini";
  const raw = messageText(body, "");
  let code = "provider_error",
    action = "حاول لاحقًا؛ حُفظ العمل الجزئي.",
    cooldown = 60000;
  if (status === 432 || status === 433) {
    code = "plan_limit";
    cooldown = 6 * 3600000;
    action =
      "بلغ حساب Tavily حد الخطة. يلزم تجدد الحصة أو تعديلها لدى المزود؛ إعادة المحاولة وحدها لا تعالج ذلك. لم تُفعّل فوترة إضافية.";
  } else if (status === 429) {
    const violations =
      body?.error?.details?.flatMap((x) => x.violations || []) || [];
    const zero =
      violations.some((x) => String(x.quotaValue) === "0") ||
      /limit\s*:\s*0\b/i.test(raw);
    code = zero ? "quota_unavailable" : "rate_or_quota_limit";
    cooldown = zero ? 6 * 3600000 : 15 * 60000;
    action = zero
      ? "الحصة المتاحة لهذا النموذج أو أداة البحث صفر في المشروع الحالي. يلزم نموذج أو مشروع بحصة متاحة؛ الانتظار القصير لا يكفي."
      : "الحصة أو معدل الطلبات غير متاح. أوقفنا الطلبات المتكررة مؤقتًا؛ راجع حصة المشروع قبل إعادة الفحص.";
  } else if (status === 401 || status === 403) {
    code = "access_denied";
    cooldown = 6 * 3600000;
    action =
      "المفتاح أو صلاحية الخدمة غير متاحين؛ راجع إعدادات الخدمة دون مشاركة المفتاح في المحادثة.";
  } else if (status === 404) {
    code = "model_unavailable";
    cooldown = 6 * 3600000;
    action =
      "النموذج المحدد غير متاح لهذا المشروع. يلزم اختيار نموذج متاح، وليس تكرار الطلب نفسه.";
  } else if (status === 400) {
    code = "unsupported_request";
    cooldown = 3600000;
    action =
      "النموذج لا يقبل إعدادات الطلب الحالية؛ يلزم مراجعة دعم أداة البحث وإعدادات النموذج.";
  }
  const seconds = Number(retryAfter);
  if (Number.isFinite(seconds) && seconds > 0)
    cooldown = Math.max(cooldown, Math.min(seconds * 1000, 86400000));
  return {
    service,
    code,
    http_status: status,
    message: `${name}: HTTP ${status}. ${action}`,
    retry_at: new Date(now + cooldown).toISOString(),
    checked_at: new Date(now).toISOString(),
    status: "blocked",
  };
}

export class ProviderError extends Error {
  constructor(issue) {
    super(issue.message);
    this.name = "ProviderError";
    this.issue = issue;
  }
}

export function campaignPresentation(c) {
  let limitations = messageText(c.limitations, "");
  const lostDetail = limitations.includes("[object Object]");
  if (lostDetail)
    limitations =
      "سجل قديم: تعذر البحث الخارجي، ولم يحفظ الإصدار السابق تفاصيل الخطأ. المحتوى المحفوظ ليس نتيجة بحث موثّق؛ ابدأ بحثًا جديدًا بعد معالجة الخدمة.";
  // Keep original records/result intact; never certify a legacy degraded completion.
  const unverified =
    c.status === "completed" &&
    (lostDetail || /تعذر.*البحث|HTTP\s*(432|433|429)/.test(limitations));
  const { checkpoint, worker_id, lease_until, ...publicCampaign } = c;
  return {
    ...publicCampaign,
    limitations,
    display_status: unverified ? "unverified_result" : c.status,
    issue: checkpoint?.provider_issue || null,
  };
}

export function groundedResults(data) {
  const c = data.candidates?.[0],
    g = c?.groundingMetadata;
  if (
    c?.finishReason !== "STOP" ||
    !g?.webSearchQueries?.length ||
    !g.groundingChunks?.length
  )
    throw new Error(
      "لم يُرجع Gemini بحثًا موثّقًا بمصادر؛ لم نعتبر نص النموذج بحثًا على الإنترنت.",
    );
  const results = g.groundingChunks.flatMap((chunk, index) => {
    let url;
    try {
      url = new URL(chunk.web?.uri);
    } catch {
      return [];
    }
    if (url.protocol !== "https:" || url.username || url.password) return [];
    const supported = (g.groundingSupports || [])
      .filter((s) => s.groundingChunkIndices?.includes(index))
      .map((s) => s.segment?.text || "")
      .filter(Boolean)
      .join("\n");
    if (!supported) return [];
    return [
      {
        title: String(chunk.web.title || url.hostname).slice(0, 300),
        url: url.href,
        content: supported.slice(0, 2400),
      },
    ];
  });
  if (!results.length)
    throw new Error(
      "لم تصل مقتطفات مرتبطة بالمراجع؛ أوقفنا البحث بدل اختلاق مصادر.",
    );
  return {
    results,
    engine: "gemini_grounding",
    queries: g.webSearchQueries,
    search_suggestions: g.searchEntryPoint?.renderedContent || "",
    usage: data.usageMetadata || {},
  };
}
