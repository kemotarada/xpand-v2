// The production record stays intact; this is the everyday reading view.
function prompts(scene, esc) {
  return [
    ["image_prompt", "برومبت إنشاء الصورة"],
    ["motion_prompt", "برومبت تحريك المشهد"],
  ]
    .filter(([key]) => scene[key])
    .map(
      ([key, label]) =>
        `<details class="scene-prompt"><summary>${label} · English</summary><p class="small-note">يتضمن هوية XPAND المشتركة وإخراج هذا المشهد. انسخه كاملًا.</p><textarea readonly dir="ltr" aria-label="${label}" style="width:100%;min-height:220px;line-height:1.7;text-align:left">${esc(scene[key])}</textarea><button data-action="copy-scene-prompt">نسخ البرومبت</button></details>`,
    )
    .join("");
}
export function compactStoryboard(result, esc) {
  const board = result.storyboard;
  const shots = board?.scenes || result.scenes || [];
  if (result.format === "static" && result.headline)
    return `<p><b>النص على البوستر:</b> ${esc(result.headline)}</p>${prompts(result, esc)}`;
  if (!shots.length) return "";
  return `<section class="compact-storyboard"><h3>الستوري بورد · كيف سيبدو الإعلان؟</h3>${shots
    .map((s, i) => {
      const text =
        (board?.screen_text || [])
          .filter((t) => t.start < s.end && t.end > s.start)
          .map((t) => t.text)
          .join(" / ") || s.on_screen;
      const voice =
        (board?.voiceover || [])
          .filter((t) => t.start < s.end && t.end > s.start)
          .map((t) => t.text)
          .join(" ") || s.voiceover;
      return `<article class="scene"><span class="badge">المشهد ${i + 1} · <bdi>${esc(s.start != null ? `${s.start}–${s.end} ثانية` : s.timing || "")}</bdi></span><h4>${esc(s.visual)}</h4>${s.action && s.action !== s.visual ? `<p><b>الحركة:</b> ${esc(s.action)}</p>` : ""}${s.sound ? `<p><b>الصوت:</b> ${esc(s.sound)}</p>` : ""}${voice ? `<p><b>التعليق:</b> ${esc(voice)}</p>` : ""}${text ? `<p><b>على الشاشة:</b> ${esc(text)}</p>` : ""}${s.emotion ? `<p class="small-note">الإحساس المقصود: ${esc(s.emotion)}</p>` : ""}</article>`;
    })
    .map((html, i) =>
      html.replace(/<\/article>$/, prompts(shots[i], esc) + "</article>"),
    )
    .join("")}</section>`;
}
