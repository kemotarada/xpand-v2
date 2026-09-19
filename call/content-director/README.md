# XPAND Content Director

Production entry point: `server.js` mounts authenticated `/api/content` routes and starts the PostgreSQL-backed worker. `/api/content/health` is a non-sensitive public deployment readiness endpoint. The UI is `/content-command`; open through Telegram to authenticate. No public authentication bypass exists.

## Operating model

- UTC instants + IANA `Asia/Hebron`; occasions are local date-only strings. Ambiguous/gap DST wall times are rejected. Browser clock is anchored to server time.
- Existing campaigns/tasks remain untouched. Migrations are additive and idempotent. The legacy result format remains readable.
- Jobs use a 90-second owner lease, five-second heartbeat, transactional claims (`SKIP LOCKED` + advisory lock), persisted stage checkpoints, a 3-attempt ceiling and bounded absolute deadline. A redeploy resumes after lease expiry. Final campaign/task/notification commit is atomic and ownership-fenced.
- External calls are **at least once**: a crash between provider response and checkpoint can repeat a billed call. Every attempt reserves quota before calling, so retries cannot reset consumption. Final task creation is transactionally fenced, not advertised as provider exactly-once execution.
- Campaign pipeline: public-topic web queries → three concepts → selection → production package → independent quality review → bounded improvement. Failed research never produces a completed campaign. Sources describe inspected snippets, not unviewed videos/images. The full supplied director instructions are `director.md`.
- Sources are not date authorities. Automatically discovered occasions are unverified until a person checks their source; confirmed dates alone receive countdowns. Changes alert without replacing production work.
- Model JSON is validated before saving. Local production slots respect aggregate daily capacity and weekly original-video capacity; platform adaptation is part of the same content task. Times are test hypotheses, not proven optimal times.
- Recurring research defaults OFF pending approved limits/pricing. Once enabled, it creates deduplicated interval jobs, caches searches for six hours, saves useful ideas separately, and deepens a new idea only if the active production plan has room. No-change runs don't send filler notifications.
- In-app notifications default ON. Telegram is opt-in per owner, respects Hebron quiet hours and a daily cap. Sending is reserved before contacting Telegram. Unknown outcomes are not automatically resent to prevent duplicate messages; dashboard labels delivery uncertainty.
- No auto-publishing, image/video generation, account analytics, ad spend or client messages. Feedback enters future context; it does not retrain a model.

## Configuration

Required existing service env: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_ID`, `GEMINI_API_KEY`, `TAVILY_API_KEY`. Optional `XPAND_CONTENT_MODEL` overrides the service's configured tool model. No additional API keys are required. Secrets never enter the client.

Settings in the UI store daily/monthly call limits, per-task calls, rounds, concurrency (1–2), job timeout, quiet hours, and conservative **per-request maximum cost reservations**. These are not provider billing data. The operator must supply verified upper-bound prices (including tokens/search depth) or confirm free quota with paid billing disabled. Provider-level caps remain recommended. Zero price is never proof of a free plan. No recurring work is enabled by this release automatically.

Railway: service root `/call`, continuous web process, Serverless must remain OFF. This was verified in the existing deployment's settings on 2026-09-19. Healthcheck endpoint should be `/api/content/health`. Multiple worker instances coordinate through PostgreSQL. Do not set a cron schedule on the web service.

## Validation

`npm install` then `npm test` and `npm run build`.

Tests use PostgreSQL 18 through PGlite (real SQL semantics in one isolated connection), mocked outbound services and a dummy signed Telegram identity. They do not access production or assert real provider availability. A real multi-connection PostgreSQL race/kill test remains appropriate for load testing. `node content-director/preview.js` serves an explicitly labelled localhost-only fixture for mobile/desktop UI checks. It is never imported by production.

Rollback: revert the release commit and redeploy; additive tables/columns may remain. Do not drop tables or delete user records. Never run preview/test fixtures on a production bind address.
