// A small, reviewed reading list, not a substitute for current-event web search.
// Never fetch user/model URLs, follow redirects, send credentials or execute HTML.
import { load } from "cheerio";
export const REFERENCES = Object.freeze([
  {
    url: "https://support.google.com/google-ads/answer/14783551?hl=en",
    marker: "ABCDs",
    title: "Google Ads · مبادئ بناء إعلان فيديو",
  },
  {
    url: "https://business.adobe.com/uk/blog/basics/how-to-build-a-brand",
    marker: "brand",
    title: "Adobe · بناء الهوية واتساق العلامة",
  },
  {
    url: "https://www.pentagram.com/work/mastercard",
    marker: "Mastercard",
    title: "Pentagram · دراسة بناء نظام هوية Mastercard",
  },
]);
export function selectReferences(request) {
  return [
    /شعار|هوي|logo|brand/i.test(request) ? REFERENCES[1] : REFERENCES[0],
    REFERENCES[2],
  ];
}
export const REFERENCE_LIMITATION =
  "تمت قراءة مراجع إبداعية عامة مباشرة؛ هذا ليس مسحًا للترندات أو السوق الفلسطيني أو المناسبات الحالية. الفكرة أصلية مبنية على طلبك وملف XPAND، وليست دليلًا على نتائج تجارية مضمونة.";

export function referenceExcerpt(html, marker) {
  const $ = load(html);
  // Article headers may contain the real project H1; navigation is removed separately.
  $("script,style,noscript,svg,nav,footer,form,iframe").remove();
  const heading = $("h1,h2")
    .filter((_, e) => $(e).text().toLowerCase().includes(marker.toLowerCase()))
    .first();
  if (!heading.length)
    throw new Error("الصفحة لم تحتوِ المقال المتوقع؛ لم نستخدمها كمرجع.");
  const article = heading.closest("article");
  const main = heading.closest("main");
  const root = article.length ? article : main.length ? main : $("body");
  const paragraphs = root
    .find("h1,h2,h3,p,li,blockquote")
    .map((_, e) => $(e).text().replace(/\s+/g, " ").trim())
    .get()
    .filter((x) => x.length >= 15);
  const content = [...new Set(paragraphs)].join("\n");
  if (content.length < 400) throw new Error("النص المسترجع لا يكفي كمرجع.");
  return content.slice(0, 12000);
}

export async function readReference(ref, fetcher = fetch, signal) {
  if (!REFERENCES.some((r) => r.url === ref.url && r.marker === ref.marker))
    throw new Error("رابط خارج قائمة المراجع المسموح بها.");
  const response = await fetcher(ref.url, {
    method: "GET",
    redirect: "error",
    credentials: "omit",
    headers: {
      Accept: "text/html",
      "User-Agent": "XPAND-Content-ReferenceReader/1.0",
    },
    signal: signal
      ? AbortSignal.any([signal, AbortSignal.timeout(25000)])
      : AbortSignal.timeout(25000),
  });
  if (!response.ok)
    throw new Error(`تعذرت قراءة المرجع العام: HTTP ${response.status}`);
  if (!/text\/html/i.test(response.headers.get("content-type") || ""))
    throw new Error("نوع صفحة المرجع غير مدعوم.");
  const reader = response.body.getReader(),
    chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 3 * 1024 * 1024)
        throw new Error("تجاوزت صفحة المرجع حد الحجم.");
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  return {
    title: ref.title,
    url: ref.url,
    content: referenceExcerpt(
      Buffer.concat(chunks).toString("utf8"),
      ref.marker,
    ),
  };
}
