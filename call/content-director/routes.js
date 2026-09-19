import {
  text,
  uuid,
  webAppUser,
  settingsInput,
  defaultProfile,
  taskStates,
  fromLocal,
  safeURL,
  dateOnly,
  hash,
} from "./core.js";
import { id, transaction } from "./store.js";
import { campaignPresentation, messageText } from "./providers.js";

export function registerRoutes(app, store, { token, allowed }) {
  const db = store.pool;
  app.get("/api/content/health", async (req, res) => {
    res.set("Cache-Control", "no-store");
    try {
      await db.query("SELECT 1");
      const status = (await store.records(allowed, "worker"))[0]?.data;
      res.json({
        ok: true,
        version: "content-director-v2",
        database: true,
        worker_last_tick: status?.last_tick || null,
        worker_healthy:
          !!status?.last_tick &&
          Date.now() - Date.parse(status.last_tick) < 180000,
      });
    } catch {
      res.status(503).json({ ok: false, version: "content-director-v2" });
    }
  });
  app.use("/api/content", (req, res, next) => {
    res.set("Cache-Control", "no-store");
    const u = webAppUser(req.get("x-telegram-init-data"), token, allowed);
    if (!u)
      return res.status(401).json({
        ok: false,
        error:
          "افتح الأداة من زر تيليجرام. إذا بقيت مفتوحة أكثر من يوم أغلقها وأعد فتحها.",
      });
    req.contentUser = u.id;
    next();
  });
  const route = (method, path, fn) =>
    app[method]("/api/content" + path, async (req, res) => {
      try {
        res.json({ ok: true, ...(await fn(req, res)) });
      } catch (e) {
        console.warn("Content route:", e.code || e.name);
        res.status(e.status || 400).json({
          ok: false,
          error: e.code
            ? "تعذر حفظ التغيير؛ حدّث الصفحة وحاول مجددًا."
            : text(messageText(e), 600),
        });
      }
    });
  const ownedId = (req) => {
    if (!uuid(req.params.id)) throw new Error("معرّف غير صالح.");
    return req.params.id;
  };
  route("get", "/dashboard", (r) => store.dashboard(r.contentUser));
  route("get", "/campaigns/:id", async (r) => {
    const c = (
      await db.query(
        "SELECT * FROM xpand_content_campaigns WHERE id=$1 AND user_id=$2",
        [ownedId(r), r.contentUser],
      )
    ).rows[0];
    if (!c) throw new Error("الحملة غير موجودة.");
    const [sources, calls, feedback, versions] = await Promise.all([
      db.query("SELECT * FROM xpand_content_sources WHERE campaign_id=$1", [
        c.id,
      ]),
      db.query(
        "SELECT id,provider,stage,status,usage,reserved_usd,error,created_at,completed_at FROM xpand_director_calls WHERE campaign_id=$1 ORDER BY created_at",
        [c.id],
      ),
      store.records(r.contentUser, "feedback"),
      db.query(
        "SELECT * FROM xpand_director_versions WHERE user_id=$1 AND entity_id=$2 ORDER BY created_at DESC",
        [r.contentUser, c.id],
      ),
    ]);
    return {
      campaign: campaignPresentation(c),
      sources: sources.rows,
      calls: calls.rows,
      feedback: feedback.filter((f) => f.data.campaign_id === c.id),
      versions: versions.rows,
    };
  });
  route("post", "/campaigns", async (r) => {
    const request = text(r.body.request, 3000);
    if (request.length < 8) throw new Error("اكتب الهدف أو الخدمة المطلوبة.");
    const key = text(r.get("Idempotency-Key"), 100);
    if (!key) throw new Error("مفتاح الطلب مفقود.");
    return transaction(db, async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock($1::bigint)", [
        r.contentUser,
      ]);
      const prior = (
        await tx.query(
          "SELECT id,status FROM xpand_content_campaigns WHERE user_id=$1 AND idempotency_key=$2",
          [r.contentUser, key],
        )
      ).rows[0];
      if (prior) return { campaign: prior };
      const queued = (
        await tx.query(
          "SELECT count(*)::int AS n FROM xpand_content_campaigns WHERE user_id=$1 AND status IN ('queued','running')",
          [r.contentUser],
        )
      ).rows[0].n;
      if (queued >= 3)
        throw new Error(
          "هناك ثلاث مهام قيد الانتظار أو التنفيذ. انتظر أو ألغِ مهمة.",
        );
      const campaign = (
        await tx.query(
          "INSERT INTO xpand_content_campaigns(id,user_id,request_text,status,stage,idempotency_key,checkpoint) VALUES($1,$2,$3,'queued','queued',$4,$5) RETURNING id,status",
          [
            id(),
            r.contentUser,
            request,
            key,
            JSON.stringify({
              mode: r.body.mode === "autonomous" ? "autonomous" : "brief",
            }),
          ],
        )
      ).rows[0];
      return { campaign };
    });
  });
  route("post", "/campaigns/:id/cancel", async (r) => {
    const x = await db.query(
      "UPDATE xpand_content_campaigns SET status='cancelled',stage='cancelled',lease_until=NULL,updated_at=NOW() WHERE id=$1 AND user_id=$2 AND status IN ('queued','running') RETURNING id",
      [ownedId(r), r.contentUser],
    );
    if (!x.rowCount) throw new Error("المهمة ليست قيد التنفيذ.");
    return {};
  });
  route("post", "/campaigns/:id/retry", async (r) => {
    const prior = (
      await db.query(
        "SELECT checkpoint FROM xpand_content_campaigns WHERE id=$1 AND user_id=$2",
        [ownedId(r), r.contentUser],
      )
    ).rows[0];
    if (prior?.checkpoint?.provider_issue) {
      const issue = prior.checkpoint.provider_issue;
      const provider = (await store.records(r.contentUser, "provider")).find(
        (p) => p.record_key === issue.service,
      )?.data;
      if (
        provider?.status === "blocked" &&
        Date.parse(provider.retry_at) > Date.now()
      )
        throw new Error(
          "الخدمة ما زالت متوقفة عند الحصة. عالج حصة المزود ثم اضغط «أعد التحقق» من حالة التشغيل؛ لم نستهلك محاولة جديدة.",
        );
    }
    const x = await db.query(
      "UPDATE xpand_content_campaigns SET checkpoint=(CASE WHEN status='needs_information' THEN checkpoint-'directions'-'selection'-'round'-'quality_issue' ELSE checkpoint END)-'provider_issue',limitations=NULL,status='queued',stage='queued',worker_id=NULL,lease_until=NULL,deadline_at=NULL,updated_at=NOW() WHERE id=$1 AND user_id=$2 AND status IN ('failed','blocked','needs_information','cancelled') AND attempts<3 RETURNING id",
      [ownedId(r), r.contentUser],
    );
    if (!x.rowCount)
      throw new Error(
        "لا يمكن إعادة المحاولة؛ الحد ثلاث محاولات. يمكنك إنشاء طلب جديد.",
      );
    return {};
  });
  route("post", "/providers/recheck", async (r) => {
    // Explicit operator action permits one new provider attempt, never erases usage.
    await db.query(
      "UPDATE xpand_director_records SET data=(data-'retry_at') || '{\"status\":\"unchecked\"}'::jsonb,updated_at=NOW() WHERE user_id=$1 AND kind='provider'",
      [r.contentUser],
    );
    return {};
  });
  route("put", "/profile", async (r) => {
    const data = {};
    for (const k of Object.keys(defaultProfile)) {
      if (["daily_hours", "weekly_videos"].includes(k)) {
        const n = Number(r.body[k]);
        if (!Number.isFinite(n) || n <= 0 || n > 24)
          throw new Error("قدرة الإنتاج غير صالحة.");
        data[k] = n;
      } else data[k] = text(r.body[k], 5000);
    }
    const previous = await store.records(r.contentUser, "profile");
    if (previous[0])
      await store.version(
        r.contentUser,
        previous[0].id,
        "profile",
        previous[0],
      );
    return {
      profile: await store.record(r.contentUser, "profile", "main", data),
    };
  });
  route("put", "/settings", async (r) =>
    transaction(db, async (tx) => {
      await tx.query("SELECT pg_advisory_xact_lock($1::bigint)", [
        r.contentUser,
      ]);
      const previous = (await store.config(r.contentUser, tx)).settings;
      const next = settingsInput(r.body);
      // Use the notification database's clock: even a few ms of host skew can exclude new notices.
      const databaseNow = (
        await tx.query("SELECT clock_timestamp() AS instant")
      ).rows[0].instant;
      next.telegram_since = next.telegram
        ? (previous.telegram && previous.telegram_since) ||
          new Date(databaseNow).toISOString()
        : null;
      return {
        settings: await store.record(
          r.contentUser,
          "settings",
          "main",
          next,
          tx,
        ),
      };
    }),
  );
  route("post", "/tasks", async (r) => {
    const title = text(r.body.title, 300);
    if (title.length < 3) throw new Error("اكتب اسم المهمة.");
    const local = (v) => (v ? fromLocal(v) : null);
    const row = (
      await db.query(
        `INSERT INTO xpand_content_tasks(id,user_id,title,description,status,production_at,review_at,planned_at) VALUES($1,$2,$3,$4,'planned',$5,$6,$7) RETURNING *`,
        [
          id(),
          r.contentUser,
          title,
          text(r.body.description, 5000),
          local(r.body.production_at),
          local(r.body.review_at),
          local(r.body.planned_at),
        ],
      )
    ).rows[0];
    return { task: row };
  });
  route("patch", "/tasks/:id", async (r) =>
    transaction(db, async (tx) => {
      const task = (
        await tx.query(
          "SELECT * FROM xpand_content_tasks WHERE id=$1 AND user_id=$2 FOR UPDATE",
          [ownedId(r), r.contentUser],
        )
      ).rows[0];
      if (!task) throw new Error("المهمة غير موجودة.");
      if (Number(r.body.version) !== task.version)
        throw new Error("المهمة تغيرت في جلسة أخرى؛ حدّث الصفحة.");
      const status = r.body.status || task.status;
      if (!taskStates.includes(status)) throw new Error("حالة غير صالحة.");
      if (
        status === "published" &&
        task.status !== "published" &&
        !r.body.confirm_published
      )
        throw new Error("أكد النشر الفعلي أولًا؛ الموعد المقترح ليس دليل نشر.");
      const actual =
        status === "published"
          ? task.actual_published_at || new Date()
          : task.actual_published_at;
      const dates = {};
      for (const k of ["production_at", "review_at", "planned_at"])
        dates[k] =
          k in r.body ? (r.body[k] ? fromLocal(r.body[k]) : null) : task[k];
      if (
        dates.production_at &&
        dates.review_at &&
        new Date(dates.production_at) >= new Date(dates.review_at)
      )
        throw new Error("المراجعة يجب أن تكون بعد بدء الإنتاج.");
      if (
        dates.review_at &&
        dates.planned_at &&
        new Date(dates.review_at) >= new Date(dates.planned_at)
      )
        throw new Error("النشر المقترح يجب أن يكون بعد المراجعة.");
      await store.version(r.contentUser, task.id, "task", task, tx);
      const changed = (
        await tx.query(
          "UPDATE xpand_content_tasks SET status=$3,title=$4,description=$5,production_at=$6,review_at=$7,planned_at=$8,actual_published_at=$9,locked=$10,version=version+1,updated_at=NOW() WHERE id=$1 AND user_id=$2 RETURNING *",
          [
            task.id,
            r.contentUser,
            status,
            text(r.body.title ?? task.title, 300),
            text(r.body.description ?? task.description, 5000),
            dates.production_at,
            dates.review_at,
            dates.planned_at,
            actual,
            task.locked ||
              [
                "in_production",
                "in_review",
                "ready_to_publish",
                "published",
              ].includes(status),
          ],
        )
      ).rows[0];
      return { task: changed };
    }),
  );
  route("post", "/campaigns/:id/feedback", async (r) => {
    const campaign = (
      await db.query(
        "SELECT * FROM xpand_content_campaigns WHERE id=$1 AND user_id=$2",
        [ownedId(r), r.contentUser],
      )
    ).rows[0];
    if (!campaign) throw new Error("الحملة غير موجودة.");
    if (!["accepted", "rejected", "revision", "outcome"].includes(r.body.type))
      throw new Error("نوع الملاحظة غير صالح.");
    const note = text(r.body.note, 5000);
    if (note.length < 3) throw new Error("اكتب الملاحظة أو سبب القرار.");
    if (r.body.type === "outcome" && !text(r.body.period))
      throw new Error("حدد فترة القياس عند تسجيل نتيجة فعلية.");
    return {
      feedback: await store.record(r.contentUser, "feedback", id(), {
        campaign_id: campaign.id,
        type: r.body.type,
        note,
        measurement_type:
          r.body.measurement_type === "paid" ? "paid" : "organic",
        period: text(r.body.period, 100),
        verified_by: "user",
      }),
    };
  });
  route("patch", "/campaigns/:id", async (r) =>
    transaction(db, async (tx) => {
      const c = (
        await tx.query(
          "SELECT * FROM xpand_content_campaigns WHERE id=$1 AND user_id=$2 FOR UPDATE",
          [ownedId(r), r.contentUser],
        )
      ).rows[0];
      if (!c?.result || c.status !== "completed")
        throw new Error("يمكن تعديل الحملات المكتملة فقط.");
      if (Number(r.body.revision) !== c.revision)
        throw new Error("الحملة تغيرت؛ حدّث الصفحة.");
      const result = r.body.result;
      if (
        !result ||
        typeof result !== "object" ||
        Array.isArray(result) ||
        JSON.stringify(result).length > 60000
      )
        throw new Error("تفاصيل غير صالحة.");
      await store.version(r.contentUser, c.id, "campaign", c, tx);
      await tx.query(
        "UPDATE xpand_content_campaigns SET result=$3,revision=revision+1,updated_at=NOW() WHERE id=$1 AND user_id=$2",
        [c.id, r.contentUser, JSON.stringify(result)],
      );
      await store.record(
        r.contentUser,
        "feedback",
        id(),
        {
          campaign_id: c.id,
          type: "revision",
          note: "تعديل يدوي محفوظ؛ النسخة السابقة محفوظة في السجل.",
        },
        tx,
      );
      return {};
    }),
  );
  route("post", "/occasions", async (r) => {
    const b = r.body;
    if (
      !text(b.name) ||
      !dateOnly(b.date) ||
      !safeURL(b.source) ||
      !["confirmed", "provisional", "unverified"].includes(b.status)
    )
      throw new Error("يلزم اسم وتاريخ محلي ورابط مصدر وحالة تحقق.");
    const key = text(b.key) || hash([text(b.name), text(b.geography)]);
    const old = (await store.records(r.contentUser, "occasion")).find(
      (x) => x.record_key === key,
    );
    const data = {
      name: text(b.name, 300),
      date: b.date,
      geography: text(b.geography, 300),
      source: safeURL(b.source),
      status: b.status,
      verified_at: new Date().toISOString(),
      verified_by: "user",
      preparation: text(b.preparation, 2000),
      relevance: text(b.relevance, 2000),
    };
    return transaction(db, async (tx) => {
      if (old) {
        await store.version(r.contentUser, old.id, "occasion", old, tx);
        if (old.data.date !== data.date)
          await store.notify(
            r.contentUser,
            `occasion-change:${old.id}:${data.date}`,
            `تغير موعد ${data.name}. راجع المواعيد المرتبطة؛ لم نغيّر العمل الجاري.`,
            null,
            tx,
          );
      }
      return {
        occasion: await store.record(r.contentUser, "occasion", key, data, tx),
      };
    });
  });
  route("patch", "/records/:id", async (r) => {
    const old = (
      await db.query(
        "SELECT * FROM xpand_director_records WHERE id=$1 AND user_id=$2",
        [ownedId(r), r.contentUser],
      )
    ).rows[0];
    if (!old) throw new Error("السجل غير موجود.");
    const data = { ...old.data };
    if (old.kind === "notification") data.read = true;
    else if (
      old.kind === "idea" &&
      ["reviewed", "archived"].includes(r.body.status)
    )
      data.status = r.body.status;
    else throw new Error("التعديل غير متاح.");
    return {
      record: await store.record(r.contentUser, old.kind, old.record_key, data),
    };
  });
}
