import { availableWeek, dayOf } from "../content-command/planning.js";
import { WEEK_PROMPT, validateWeek } from "./creative.js";
import { transaction, id } from "./store.js";
export async function planWeek(worker, job, ctx, sources) {
  const records = await worker.store.records(job.user_id, "day_plan");
  const dates = availableWeek(
    job.checkpoint.start_date,
    ctx.tasks,
    records,
    ctx.profile,
  );
  const scheduledVideos = new Set(
    ctx.tasks
      .filter(
        (t) =>
          t.metadata?.format === "video" &&
          t.planned_at &&
          dates.some((d) => d.date === dayOf(t.planned_at)),
      )
      .map((t) => t.campaign_id || t.id),
  ).size;
  const weekProfile = {
    ...ctx.profile,
    weekly_videos: Math.max(0, ctx.profile.weekly_videos - scheduledVideos),
  };
  let result = job.checkpoint.week_plan;
  if (!result) {
    await worker.store.checkpoint(job, "planning_week", {});
    result = await worker.modelJSON(
      job,
      "week_plan",
      {
        ...ctx,
        profile: weekProfile,
        sources,
        dates,
        already_scheduled_videos: scheduledVideos,
      },
      WEEK_PROMPT,
    );
    validateWeek(
      result,
      dates,
      sources,
      weekProfile,
      ctx.previous_campaigns.map((c) => c.id),
    );
    await worker.store.checkpoint(job, "saving_week", { week_plan: result });
  }
  await transaction(worker.pool, async (tx) => {
    await tx.query("SELECT pg_advisory_xact_lock($1::bigint)", [job.user_id]);
    const own = await tx.query(
      "SELECT id FROM xpand_content_campaigns WHERE id=$1 AND worker_id=$2 AND status='running' FOR UPDATE",
      [job.id, job.worker_id],
    );
    if (!own.rowCount) throw new Error("توقفت ملكية خطة الأسبوع.");
    const current = (
      await tx.query(
        "SELECT * FROM xpand_content_tasks WHERE user_id=$1 AND status NOT IN ('published','cancelled','postponed')",
        [job.user_id],
      )
    ).rows;
    const saved = await worker.store.records(job.user_id, "day_plan", tx);
    const fresh = availableWeek(
      job.checkpoint.start_date,
      current,
      saved,
      ctx.profile,
    );
    const skipped = [];
    for (const d of result.days) {
      if (saved.some((r) => r.record_key === d.date)) {
        skipped.push(d.date);
        continue;
      }
      if (d.minutes > fresh.find((x) => x.date === d.date).remaining_minutes)
        throw new Error(
          "تغيرت قدرة الإنتاج أثناء التخطيط؛ لم نستبدل أعمالك. أعد المحاولة بعد مراجعة المهام.",
        );
      await worker.store.record(
        job.user_id,
        "day_plan",
        d.date,
        { ...d, status: "planned", week_id: job.id },
        tx,
      );
    }
    result = {
      ...result,
      skipped_dates: skipped,
      research_mode: job.checkpoint.research_mode,
    };
    await tx.query(
      "UPDATE xpand_content_campaigns SET status='completed',stage='completed',result=$3,completed_at=NOW(),updated_at=NOW(),lease_until=NULL WHERE id=$1 AND worker_id=$2",
      [job.id, job.worker_id, JSON.stringify(result)],
    );
    await worker.store.notify(
      job.user_id,
      "week-ready:" + job.id,
      "جهزت خطة شغل متنوعة لسبعة أيام: إنتاج ومراجعة وأفكار وتصاميم. افتح التقويم لمراجعة تفاصيل كل يوم. لم ننشر أي محتوى تلقائيًا.",
      job.id,
      tx,
    );
  });
}
export function registerWeekRoutes(route, store, ownedId) {
  const db = store.pool;
  route("post", "/week-plan", async (r) => {
    const { dateOnly, localClock, text } = await import("./core.js");
    const start = r.body.start_date || localClock().localDate;
    if (
      !dateOnly(start) ||
      start < localClock().localDate ||
      start > new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10)
    )
      throw new Error("اختر بداية من اليوم وحتى 90 يومًا قادمة.");
    const key = text(r.get("Idempotency-Key"), 100);
    if (!key) throw new Error("مفتاح الطلب مفقود.");
    return transaction(db, async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock($1::bigint)", [
        r.contentUser,
      ]);
      const old = (
        await tx.query(
          "SELECT id,status FROM xpand_content_campaigns WHERE user_id=$1 AND idempotency_key=$2",
          [r.contentUser, key],
        )
      ).rows[0];
      if (old) return { campaign: old };
      await store.assertAllowance(r.contentUser, null, tx);
      const active = (
        await tx.query(
          "SELECT count(*)::int AS n FROM xpand_content_campaigns WHERE user_id=$1 AND status IN ('queued','running')",
          [r.contentUser],
        )
      ).rows[0].n;
      if (active >= 3) throw new Error("انتظر انتهاء إحدى المهام الجارية.");
      const campaign = (
        await tx.query(
          "INSERT INTO xpand_content_campaigns(id,user_id,kind,request_text,status,stage,idempotency_key,checkpoint) VALUES($1,$2,'week',$3,'queued','queued',$4,$5) RETURNING id,status",
          [
            id(),
            r.contentUser,
            "خطة شغل يومي متنوعة لشركة XPAND لمدة أسبوع. " +
              text(r.body.request, 2000),
            key,
            JSON.stringify({ start_date: start, mode: "week" }),
          ],
        )
      ).rows[0];
      return { campaign };
    });
  });
  route("patch", "/plan-days/:id", async (r) =>
    transaction(db, async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock($1::bigint)", [
        r.contentUser,
      ]);
      const old = (
        await tx.query(
          "SELECT * FROM xpand_director_records WHERE id=$1 AND user_id=$2 AND kind='day_plan' FOR UPDATE",
          [ownedId(r), r.contentUser],
        )
      ).rows[0];
      if (!old || old.version !== Number(r.body.version))
        throw new Error("خطة اليوم تغيرت؛ حدّث الصفحة.");
      if (!["planned", "done"].includes(r.body.status))
        throw new Error("حالة غير صالحة.");
      await store.version(r.contentUser, old.id, "day_plan", old, tx);
      return {
        record: await store.record(
          r.contentUser,
          "day_plan",
          old.record_key,
          { ...old.data, status: r.body.status },
          tx,
        ),
      };
    }),
  );
}
