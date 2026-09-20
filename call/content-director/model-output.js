export function parseModelObject(data) {
  const candidate = data?.candidates?.[0];
  if (candidate?.finishReason && candidate.finishReason !== "STOP") {
    const e = new Error("النموذج لم يكمل النتيجة: " + candidate.finishReason);
    e.outputRepairable = candidate.finishReason === "MAX_TOKENS";
    throw e;
  }
  const raw = (candidate?.content?.parts || [])
    .filter((p) => !p.thought)
    .map((p) => p.text || "")
    .join("")
    .trim();
  // Only remove a complete wrapping fence, never fabricate missing JSON content.
  const json = raw.replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/i, "$1");
  try {
    const value = JSON.parse(json);
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error();
    return value;
  } catch {
    const e = new Error(
      "رد النموذج غير مكتمل؛ المراحل السابقة محفوظة ولم تُعتمد فكرة ناقصة.",
    );
    e.outputRepairable = true;
    throw e;
  }
}
