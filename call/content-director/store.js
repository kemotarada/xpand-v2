import crypto from "node:crypto";
import fs from "node:fs";
import { defaultProfile, defaultSettings, localClock, ZONE } from "./core.js";
import { campaignPresentation } from "./providers.js";
export const id = () => crypto.randomUUID();
export async function transaction(pool, fn) {
  const db = await pool.connect();
  try {
    await db.query("BEGIN");
    const result = await fn(db);
    await db.query("COMMIT");
    return result;
  } catch (e) {
    await db.query("ROLLBACK");
    throw e;
  } finally {
    db.release();
  }
}
export class Store {
  constructor(pool) {
    this.pool = pool;
  }
  async migrate() {
    await this.pool.query(
      fs.readFileSync(new URL("./schema.sql", import.meta.url), "utf8"),
    );
  }
  async records(user, kind, db = this.pool) {
    return (
      await db.query(
        "SELECT * FROM xpand_director_records WHERE user_id=$1 AND kind=$2 ORDER BY updated_at DESC",
        [user, kind],
      )
    ).rows;
  }
  async config(user, db = this.pool) {
    const rows = await db.query(
      "SELECT kind,data FROM xpand_director_records WHERE user_id=$1 AND kind IN ('profile','settings')",
      [user],
    );
    return {
      profile: {
        ...defaultProfile,
        ...rows.rows.find((r) => r.kind === "profile")?.data,
      },
      settings: {
        ...defaultSettings,
        ...rows.rows.find((r) => r.kind === "settings")?.data,
      },
    };
  }
  async record(user, kind, key, data, db = this.pool) {
    return (
      await db.query(
        `INSERT INTO xpand_director_records(id,user_id,kind,record_key,data) VALUES($1,$2,$3,$4,$5) ON CONFLICT(user_id,kind,record_key) DO UPDATE SET data=EXCLUDED.data,version=xpand_director_records.version+1,updated_at=NOW() RETURNING *`,
        [id(), user, kind, key, JSON.stringify(data)],
      )
    ).rows[0];
  }
  async notify(user, key, message, entityId = null, db = this.pool) {
    await db.query(
      `INSERT INTO xpand_director_records(id,user_id,kind,record_key,data) VALUES($1,$2,'notification',$3,$4) ON CONFLICT(user_id,kind,record_key) DO NOTHING`,
      [
        id(),
        user,
        key,
        JSON.stringify({
          message,
          entity_id: entityId,
          read: false,
          delivery: "pending",
        }),
      ],
    );
  }
  async assertAllowance(user, campaignId = null, db = this.pool) {
    const { settings: s } = await this.config(user, db);
    const usage = (
      await db.query(
        `SELECT count(*) FILTER(WHERE (created_at AT TIME ZONE $2)::date=(NOW() AT TIME ZONE $2)::date)::int AS day,count(*) FILTER(WHERE date_trunc('month',created_at AT TIME ZONE $2)=date_trunc('month',NOW() AT TIME ZONE $2))::int AS month,count(*) FILTER(WHERE campaign_id=$3)::int AS task FROM xpand_director_calls WHERE user_id=$1`,
        [user, ZONE, campaignId],
      )
    ).rows[0];
    if (!s.unlimited_calls && usage.day >= s.daily_calls)
      throw new Error(
        "اكتمل حد اليوم. يتجدد عند منتصف الليل بتوقيت الخليل، أو عدّل الحد المعتمد. لم نستهلك محاولة ولم ننشئ طلبًا جديدًا.",
      );
    if (!s.unlimited_calls && usage.month >= s.monthly_calls)
      throw new Error(
        "اكتمل حد الشهر. لم نستهلك محاولة جديدة؛ يلزم تجدد الحد أو تعديله.",
      );
    if (!s.unlimited_calls && campaignId && usage.task >= s.task_calls)
      throw new Error(
        "وصل هذا الطلب لحد المهمة؛ زيادة حد اليوم وحدها لا تكفي. عدّل حد المهمة المعتمد للاستكمال، دون مسح الاستهلاك السابق.",
      );
  }
  async version(user, entity, kind, snapshot, db = this.pool) {
    await db.query(
      "INSERT INTO xpand_director_versions(id,user_id,entity_id,kind,snapshot) VALUES($1,$2,$3,$4,$5)",
      [id(), user, entity, kind, JSON.stringify(snapshot)],
    );
  }
  async dashboard(user) {
    const [config, campaigns, tasks, records, usage, metrics] =
      await Promise.all([
        this.config(user),
        this.pool.query(
          "SELECT t.*,(SELECT count(*)::int FROM xpand_director_calls c WHERE c.campaign_id=t.id) AS call_count FROM (SELECT *,row_number() OVER(PARTITION BY kind ORDER BY created_at DESC) AS rn FROM xpand_content_campaigns WHERE user_id=$1) t WHERE rn<=60 ORDER BY created_at DESC",
          [user],
        ),
        this.pool.query(
          "SELECT * FROM xpand_content_tasks WHERE user_id=$1 ORDER BY CASE WHEN status IN ('published','cancelled') THEN 1 ELSE 0 END,COALESCE(planned_at,created_at) DESC LIMIT 500",
          [user],
        ),
        this.pool.query(
          "SELECT * FROM (SELECT *,row_number() OVER(PARTITION BY kind ORDER BY updated_at DESC) AS rn FROM xpand_director_records WHERE user_id=$1 AND kind IN ('idea','occasion','notification','worker','provider','day_plan')) t WHERE rn<=200 ORDER BY updated_at DESC",
          [user],
        ),
        this.pool.query(
          `SELECT count(*) FILTER(WHERE (created_at AT TIME ZONE $2)::date=(NOW() AT TIME ZONE $2)::date)::int AS daily_calls,count(*)::int AS monthly_calls,COALESCE(sum(reserved_usd),0) AS monthly_reserved_usd,COALESCE(sum(reserved_usd) FILTER(WHERE (created_at AT TIME ZONE $2)::date=(NOW() AT TIME ZONE $2)::date),0) AS daily_reserved_usd FROM xpand_director_calls WHERE user_id=$1 AND date_trunc('month',created_at AT TIME ZONE $2)=date_trunc('month',NOW() AT TIME ZONE $2)`,
          [user, ZONE],
        ),
        this.pool.query(
          `SELECT count(*) FILTER(WHERE status IN ('planned','awaiting_start'))::int AS planned,count(*) FILTER(WHERE status IN ('in_production','in_review'))::int AS production,count(*) FILTER(WHERE status NOT IN ('published','cancelled','postponed') AND planned_at<NOW())::int AS overdue,count(*) FILTER(WHERE status='published')::int AS published FROM xpand_content_tasks WHERE user_id=$1`,
          [user],
        ),
      ]);
    return {
      ok: true,
      now: localClock(),
      ...config,
      campaigns: campaigns.rows.map(campaignPresentation),
      tasks: tasks.rows,
      records: records.rows.map((r) =>
        r.kind === "provider"
          ? { ...r, data: { ...r.data, fingerprint: undefined } }
          : r,
      ),
      usage: usage.rows[0],
      metrics: metrics.rows[0],
      integrations: { analytics: false, automatic_publishing: false },
      window: { tasks_limit: 500, campaigns_limit: 60 },
    };
  }
  async reserve(job, provider, stage) {
    return transaction(this.pool, async (db) => {
      await db.query("SELECT pg_advisory_xact_lock($1::bigint)", [job.user_id]);
      const row = (
        await db.query(
          "SELECT status,worker_id,deadline_at FROM xpand_content_campaigns WHERE id=$1 FOR UPDATE",
          [job.id],
        )
      ).rows[0];
      if (row?.status !== "running" || row.worker_id !== job.worker_id)
        throw new Error("المهمة ملغاة أو انتقلت إلى عامل آخر.");
      if (new Date(row.deadline_at) < new Date())
        throw new Error("انتهت مهلة المهمة.");
      const { settings: s } = await this.config(job.user_id, db);
      const costs =
        provider === "reference"
          ? 0
          : provider === "grounding"
            ? s.search_call_usd + s.model_call_usd
            : provider === "search"
              ? s.search_call_usd
              : s.model_call_usd;
      if (costs > 0 && !s.pricing_confirmed)
        throw new Error("أسعار الخدمات لم تعتمد بعد.");
      const u = (
        await db.query(
          `SELECT count(*) FILTER(WHERE (created_at AT TIME ZONE $2)::date=(NOW() AT TIME ZONE $2)::date)::int AS daily,count(*)::int AS monthly,COALESCE(sum(reserved_usd),0)::float AS usd_month,COALESCE(sum(reserved_usd) FILTER(WHERE (created_at AT TIME ZONE $2)::date=(NOW() AT TIME ZONE $2)::date),0)::float AS usd_day FROM xpand_director_calls WHERE user_id=$1 AND date_trunc('month',created_at AT TIME ZONE $2)=date_trunc('month',NOW() AT TIME ZONE $2)`,
          [job.user_id, ZONE],
        )
      ).rows[0];
      const n = (
        await db.query(
          "SELECT count(*)::int AS n FROM xpand_director_calls WHERE campaign_id=$1",
          [job.id],
        )
      ).rows[0].n;
      if (
        (!s.unlimited_calls &&
          (u.daily >= s.daily_calls ||
            u.monthly >= s.monthly_calls ||
            n >= s.task_calls)) ||
        (costs > 0 &&
          (u.usd_day + costs > s.daily_usd ||
            u.usd_month + costs > s.monthly_usd))
      )
        throw new Error("بلغ البحث حد الاستهلاك المعتمد؛ حُفظ العمل الجزئي.");
      const call = id();
      await db.query(
        "INSERT INTO xpand_director_calls(id,user_id,campaign_id,provider,stage,reserved_usd) VALUES($1,$2,$3,$4,$5,$6)",
        [call, job.user_id, job.id, provider, stage, costs],
      );
      return call;
    });
  }
  async saveCall(call, result, usage, error) {
    await this.pool.query(
      "UPDATE xpand_director_calls SET status=$2,result=$3,usage=$4,error=$5,completed_at=NOW() WHERE id=$1",
      [
        call,
        error ? "failed" : "completed",
        result ? JSON.stringify(result) : null,
        JSON.stringify(usage || {}),
        error || null,
      ],
    );
  }
  async checkpoint(job, stage, data) {
    const r = await this.pool.query(
      "UPDATE xpand_content_campaigns SET stage=$3,checkpoint=checkpoint || $4::jsonb,updated_at=NOW(),lease_until=NOW()+INTERVAL '90 seconds' WHERE id=$1 AND worker_id=$2 AND status='running' RETURNING checkpoint",
      [job.id, job.worker_id, stage, JSON.stringify(data)],
    );
    if (!r.rows[0]) throw new Error("المهمة أُلغيت أو انتهت ملكية التنفيذ.");
    job.checkpoint = r.rows[0].checkpoint;
  }
}
