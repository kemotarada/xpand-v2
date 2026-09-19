import test from "node:test";
import assert from "node:assert/strict";
import {
  localClock,
  fromLocal,
  dateOnly,
  daysUntil,
  webAppUser,
  settingsInput,
  defaultSettings,
  quiet,
  validatePackage,
  safeURL,
} from "./core.js";
import { signedData, TEST_TOKEN } from "./test-support.js";
test("Hebron weekday and date derive from same instant; midnight rolls over", () => {
  assert.equal(localClock("2026-09-18T20:59:59Z").localDate, "2026-09-18");
  const c = localClock("2026-09-18T21:00:00Z");
  assert.equal(c.localDate, "2026-09-19");
  assert.equal(c.weekday, "السبت");
  assert.equal(c.time, "00:00:00");
});
test("local scheduling respects winter/summer and process timezone independence", () => {
  const original = process.env.TZ;
  process.env.TZ = "America/Los_Angeles";
  assert.equal(fromLocal("2026-09-19T10:00"), "2026-09-19T07:00:00.000Z");
  assert.equal(fromLocal("2026-01-19T10:00"), "2026-01-19T08:00:00.000Z");
  process.env.TZ = original || "UTC";
});
test("date-only stays local, invalid dates and DST gaps/folds rejected", () => {
  assert.equal(dateOnly("2026-02-30"), false);
  assert.equal(daysUntil("2026-09-20", "2026-09-19T21:01:00Z"), 0);
  assert.throws(() => fromLocal("2026-09-19T25:00"));
  assert.throws(() => fromLocal("2026-03-28T02:30"));
  assert.throws(() => fromLocal("2026-10-24T01:30"));
});
test("Telegram HMAC owner check and expiry fail closed", () => {
  assert.equal(webAppUser(signedData(), TEST_TOKEN, 42)?.id, 42);
  assert.equal(webAppUser(signedData(9), TEST_TOKEN, 42), null);
  assert.equal(webAppUser(signedData(42, 86401), TEST_TOKEN, 42), null);
  assert.equal(webAppUser(signedData() + "x", TEST_TOKEN, 42), null);
  assert.equal(webAppUser(signedData(), TEST_TOKEN, ""), null);
});
test("recurring budget requires explicit confirmation and paid caps", () => {
  assert.throws(() => settingsInput({ ...defaultSettings, recurring: true }));
  assert.throws(() =>
    settingsInput({
      ...defaultSettings,
      recurring: true,
      pricing_confirmed: true,
      model_call_usd: 1,
    }),
  );
  assert.equal(
    settingsInput({
      ...defaultSettings,
      recurring: true,
      pricing_confirmed: true,
    }).recurring,
    true,
  );
  assert.throws(() => settingsInput({ rounds: 100 }));
});
test("quiet hours across midnight and safe external links", () => {
  assert.equal(quiet("2026-09-19T20:00:00Z", defaultSettings), true);
  assert.equal(quiet("2026-09-19T10:00:00Z", defaultSettings), false);
  assert.equal(safeURL("javascript:alert(1)"), null);
  assert.equal(safeURL("https://example.com"), "https://example.com/");
  assert.throws(() => validatePackage({ title: "Only a slogan" }, []));
});
