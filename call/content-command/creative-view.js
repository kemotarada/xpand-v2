export function creativeView(r, process, { esc, listHTML, effortLabel }) {
  const map = (obj, labels) =>
    Object.entries(labels)
      .filter(([k]) => obj?.[k])
      .map(([k, l]) => `<article><b>${l}</b><p>${esc(obj[k])}</p></article>`)
      .join("");
  let html = "";
  if (process?.insights) {
    const insight = process.insights;
    html += `<details><summary>01 · فهم المهمة وما كشفه البحث</summary><div class="detail-grid">${map(insight.brief, { service: "الخدمة", objective: "الهدف", audience: "الجمهور", current_belief: "الاعتقاد الحالي — يحتاج دليلًا", desired_belief: "ما نريد إيصاله", desired_feeling: "الشعور المستهدف", desired_action: "الفعل المطلوب", resources: "إمكانات التنفيذ", production_method: "طريقة الإنتاج" })}</div>${(insight.findings || []).map((f) => `<article class="scene"><span class="badge">${esc({ fact: "حقيقة موثقة", interpretation: "تفسير", hypothesis: "فرضية تحتاج اختبارًا" }[f.evidence_type])}</span><h3>${esc(f.observation)}</h3>${f.quote ? `<blockquote>${esc(f.quote)}</blockquote>` : ""}<p><b>الفرصة الإبداعية:</b> ${esc(f.creative_opportunity)}</p><p><b>ترجمتها للتنفيذ:</b> ${esc(f.execution_translation)}</p><p class="small-note">مراجع: ${(f.source_ids || []).map((id) => `<a href="#source-${esc(id)}">فتح المصدر</a>`).join(" · ") || "لا مصدر؛ ليست حقيقة مثبتة"}</p></article>`).join("")}${listHTML(insight.unanswered_questions || [])}</details>`;
  }
  if (process?.directions)
    html += `<details><summary>02 · الاتجاهات التي قورنت ولماذا اختير هذا الاتجاه</summary>${(process.directions.directions || []).map((d) => `<h3>${esc(d.title)}</h3><div class="detail-grid">${map(d, { concept: "الفكرة", mechanism: "الآلية السردية", human_observation: "الملاحظة الإنسانية", brand_role: "لماذا XPAND أساسية هنا؟", story: "ملخص القصة", emotion: "الإحساس المقصود", distinctive_device: "ما يميزها", execution_challenge: "تحدي التنفيذ" })}</div>`).join("")}${(process.selection?.comparisons || []).map((c) => `<article class="scene"><h3>${esc(c.title)}</h3><p>القوة: ${esc(c.strength)}<br>الضعف: ${esc(c.weakness)}<br>اختبار استبدال الشعار: ${esc(c.logo_swap_test)}<br>قابلية التنفيذ: ${esc(c.feasibility_test)}<br>القرار: ${esc(c.decision)}</p></article>`).join("")}<p>${esc(process.selection?.decision_rationale)}</p></details>`;
  if (r.treatment)
    html += `<details open><summary>03 · المعالجة الإبداعية والإخراجية</summary><div class="detail-grid">${map(r.treatment, { world: "عالم الإعلان", characters: "الشخصيات والعناصر", visual_system: "الكادر والألوان والإضاءة", pacing: "إيقاع الإعلان", sound_design: "الموسيقى والمؤثرات والصمت", ending: "النهاية ودور العلامة", production_method: "طريقة التنفيذ", continuity: "استمرارية العناصر والحركة", feasible_alternative: "بديل قابل للتنفيذ للجزء الأصعب" })}</div><h3>رحلة المشاعر المستهدفة — وليست نتائج مضمونة</h3>${(r.emotion_arc || []).map((e) => `<p><b>${esc(e.moment)} · ${esc(e.feeling)}</b><br>${esc(e.cue)}</p>`).join("")}</details>`;
  if (r.storyboard) {
    const s = r.storyboard;
    html += `<section class="storyboard"><h3>04 · الستوري بورد التنفيذي</h3><div class="info-strip"><span>مدة الفيديو على الشاشة <b>${esc(s.duration_seconds)} ثانية</b></span><span>الجهد التقديري للفريق <b>${esc(effortLabel(r.effort_hours * 60))}</b></span></div><p class="small-note">خط زمني يغطي الفيديو كاملًا. استمرار اللقطة لا يعني قطعًا كل ثانية. سرعة الكلام فحص تقديري؛ اقرأ النص بصوت مسموع قبل التسجيل.</p>${s.scenes.map((shot, i) => `<details class="shot" ${i === 0 ? "open" : ""}><summary>اللقطة ${i + 1} · <bdi>${esc(shot.start)}–${esc(shot.end)}</bdi> ثانية · ${esc(shot.visual)}</summary><div class="detail-grid">${map(shot, { framing: "حجم الكادر وزاويته", focal_point: "نقطة جذب العين", camera: "حركة الكاميرا وسرعتها", action: "الحركة وتطورها", performance: "التعبير والأداء", lighting: "الإضاءة واللون والخامة", sound: "الصوت والإيقاع", transition: "الانتقال", transition_reason: "لماذا هذا الانتقال؟", emotion: "الإحساس المستهدف", purpose: "وظيفة اللقطة", production_note: "ملاحظة تنفيذية" })}</div></details>`).join("")}<details open><summary>كل ثانية: الصورة، الصوت، والإحساس</summary><div class="timeline-scroll" tabindex="0" aria-label="جدول تفاصيل الثواني"><table><thead><tr><th>الثانية</th><th>تطور الصورة</th><th>الصوت أو الصمت</th><th>الإحساس والهدف</th></tr></thead><tbody>${s.beats.map((b) => `<tr><th><bdi>${esc(b.start)}–${esc(b.end)}</bdi></th><td>${esc(b.visual_change)}</td><td>${esc(b.sound_change)}</td><td><b>${esc(b.emotion)}</b><br>${esc(b.purpose)}</td></tr>`).join("")}</tbody></table></div></details>${[
      ["voiceover", "التعليق الصوتي النهائي"],
      ["screen_text", "النص الظاهر على الشاشة"],
    ]
      .map(
        ([k, l]) =>
          `<details><summary>${l}</summary>${s[k].length ? s[k].map((t) => `<article class="scene"><b><bdi>${esc(t.start)}–${esc(t.end)}</bdi> ثانية</b><p>${esc(t.text)}</p>${t.delivery ? `<p>الأداء: ${esc(t.delivery)}</p>` : ""}</article>`).join("") : `<p>لا يوجد ${l}؛ يُعتمد على الصورة والصوت المحددين في اللقطات.</p>`}</details>`,
      )
      .join("")}</section>`;
  }
  if (r.effort_breakdown)
    html += `<details open><summary>05 · وقت العمل المطلوب من الفريق</summary><p>هذه أوقات تنفيذ تقديرية، وليست مدة الفيديو ولا موعد نشره. الإجمالي يشمل التكييف للمنصات؛ لا تضفه مرة أخرى.</p>${r.effort_breakdown.map((x) => `<p class="effort-row"><span>${esc(x.task)}</span><b>${esc(effortLabel(x.minutes))}</b></p>`).join("")}<p><b>الإجمالي: ${esc(effortLabel(r.effort_hours * 60))}</b></p></details>`;
  return html;
}
