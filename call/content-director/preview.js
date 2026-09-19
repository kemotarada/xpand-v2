// Local-only UI acceptance fixture; never imported by production server.
import fs from "node:fs";
import express from "express";
import { fixture, signedData, enqueue, workerFor } from "./test-support.js";
const f = await fixture();
const worker = workerFor(f);
await enqueue(f);
await worker.run(await worker.claim());
const root = new URL("../content-command/", import.meta.url);
f.app.get("/content-command", (req, res) => {
  const html = fs
    .readFileSync(new URL("index.html", root), "utf8")
    .replace(
      '<script src="https://telegram.org/js/telegram-web-app.js"></script>',
      `<script>window.Telegram={WebApp:{initData:${JSON.stringify(signedData())},ready(){},expand(){},setHeaderColor(){},setBackgroundColor(){}}}</script>`,
    )
    .replace(
      "<body>",
      '<body><div class="error">بيئة اختبار محلية منفصلة — المراجع والذكاء الاصطناعي محاكاة؛ لا اتصال بالإنتاج</div>',
    );
  res.type("html").send(html);
});
f.app.use(
  "/content-command",
  express.static(root.pathname.replace(/^\/([A-Za-z]:)/, "$1")),
);
worker.start();
console.log("ISOLATED_PREVIEW " + f.url + "/content-command");
process.on("SIGINT", async () => {
  worker.stop();
  await f.close();
  process.exit(0);
});
