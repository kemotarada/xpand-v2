# XPAND Content Director

Production entry point: `server.js` mounts authenticated `/api/content` routes and starts the PostgreSQL-backed worker. `/api/content/health` is a non-sensitive public deployment readiness endpoint. The UI is `/content-command`; open through Telegram to authenticate. No public authentication bypass exists.

## Operating model

- UTC instants + IANA `Asia/Hebron`; occasions are local date-only strings. Ambiguous/gap DST wall times are rejected. Browser clock is anchored to server time.
- Existing campaigns/tasks remain untouched. Migrations are additive and idempotent. The legacy result format remains readable.
- Jobs use a 90-second owner lease, five-second heartbeat, transactional claims (`SKIP LOCKED` + advisory lock), persisted stage checkpoints, a 3-attempt ceiling and bounded absolute deadline. A redeploy resumes after lease expiry. Final campaign/task/notification commit is atomic and ownership-fenced.
- External calls are **at least once**: a crash between provider response and checkpoint can repeat a billed call. Every attempt reserves quota before calling, so retries cannot reset consumption. Final task creation is transactionally fenced, not advertised as provider exactly-once execution.
- Campaign pipeline: public-topic web queries (or explicitly disclosed direct reading of general creative references) → three concepts → selection → production package → independent quality review → bounded improvement. No usable sources means no completed campaign. Sources describe inspected text, not unviewed videos/images. The full supplied director instructions are `director.md`.
- Sources are not date authorities. Automatically discovered occasions are unverified until a person checks their source; confirmed dates alone receive countdowns. Changes alert without replacing production work.
- Model JSON is validated before saving. Local production slots respect aggregate daily capacity and weekly original-video capacity; platform adaptation is part of the same content task. Times are test hypotheses, not proven optimal times.
- Recurring research defaults OFF pending approved limits/pricing. Once enabled, it creates deduplicated interval jobs, caches searches for six hours, saves useful ideas separately, and deepens a new idea only if the active production plan has room. No-change runs don't send filler notifications.
- In-app notifications default ON. Telegram is opt-in per owner, respects Hebron quiet hours and a daily cap. Sending is reserved before contacting Telegram. Unknown outcomes are not automatically resent to prevent duplicate messages; dashboard labels delivery uncertainty.
- No auto-publishing, image/video generation, account analytics, ad spend or client messages. Feedback enters future context; it does not retrain a model.

## Configuration

Required existing service env: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_ID`, `GEMINI_API_KEY`, `TAVILY_API_KEY`. Optional `XPAND_CONTENT_MODEL` overrides the service's configured tool model. No additional API keys are required. Secrets never enter the client.

### Provider availability and quota recovery

- `search_provider` is `auto` (Tavily then Gemini Google Search, then direct references for campaigns only), `tavily`, `gemini`, or `direct`. `XPAND_SEARCH_MODEL` optionally selects the grounding model; otherwise it follows the content model. Google Search has its own model/project quota: working text generation does not prove grounding is available. Models are never silently rotated to evade provider limits.
- `references.js` reads two reviewed public Google/Adobe articles with no search API subscription. Only these exact HTTPS URLs are accepted; redirects, cookies, scripts, non-HTML, challenge pages and bodies above 3 MiB are rejected. A 25-second timeout and cancellation apply. Per-owner results are cached 24 hours with original access timestamps. Every uncached attempt still counts toward local request caps; API cost reservation is zero for the GET only (hosting traffic and Gemini text are separate).
- Automatic reference fallback applies only to provider errors, never local budget exhaustion. It yields an evergreen campaign with `research_mode=direct_references` and explicit limitations in both the model context and saved package. It must not imply a current-market, trend, competitor, social-account or occasion scan. Current-event scans remain paused until real search is available and budget/pricing are approved. Explicit Tavily/Gemini-only choices remain strict. Text generation still needs available Gemini quota.
- Grounding is accepted only with actual `webSearchQueries`, source chunks and supported citation segments. Model-written URLs are insufficient. Search Suggestions from Google are preserved and rendered in an isolated, script-free iframe. The UI identifies synthesized grounded excerpts, not directly inspected pages or videos.
- Each fallback attempt is reserved against the existing call caps. A grounding request reserves the configured search **plus** model maximum cost. Pricing must cover both; no new paid subscription or billing setting is enabled. Failed calls still count toward local limits.
- Provider health/cooldowns persist across deploys. HTTP 432/433 means Tavily plan/spend limit, 429 quota/rate limit, and 404 unavailable model. Repeating a request cannot repair these. Periodic scans pause when all configured research routes, or the selected text model, are blocked. The authenticated recheck action permits a fresh attempt after the operator has repaired quota/configuration, without resetting usage.
- Old `[object Object]` limitations are displayed honestly as incomplete legacy research. Original records and results are preserved, not rewritten or deleted. Successful new retries clear obsolete limitations.
- Enabling Telegram records an activation cutoff. Pre-activation pending notices remain in-app and are not sent as a historical backlog. Quiet hours and daily delivery caps still apply independently of research availability.

Official API references: [Tavily status codes](https://help.tavily.com/articles/8645538886-understanding-http-errors), [Tavily usage](https://docs.tavily.com/documentation/api-reference/endpoint/usage), [Gemini search grounding](https://ai.google.dev/gemini-api/docs/generate-content/google-search). An API key being configured is not proof of service readiness.

Settings in the UI store daily/monthly call limits, per-task calls, rounds, concurrency (1–2), job timeout, quiet hours, and conservative **per-request maximum cost reservations**. These are not provider billing data. The operator must supply verified upper-bound prices (including tokens/search depth) or confirm free quota with paid billing disabled. Provider-level caps remain recommended. Zero price is never proof of a free plan. No recurring work is enabled by this release automatically.

Railway: service root `/call`, continuous web process, Serverless must remain OFF. This was verified in the existing deployment's settings on 2026-09-19. Healthcheck endpoint should be `/api/content/health`. Multiple worker instances coordinate through PostgreSQL. Do not set a cron schedule on the web service.

## Validation

`npm install` then `npm test` and `npm run build`.

Tests use PostgreSQL 18 through PGlite (real SQL semantics in one isolated connection), mocked outbound services and a dummy signed Telegram identity. They do not access production or assert real provider availability. A real multi-connection PostgreSQL race/kill test remains appropriate for load testing. `node content-director/preview.js` serves an explicitly labelled localhost-only fixture for mobile/desktop UI checks. It is never imported by production.

Rollback: revert the release commit and redeploy; additive tables/columns may remain. Do not drop tables or delete user records. Never run preview/test fixtures on a production bind address.
