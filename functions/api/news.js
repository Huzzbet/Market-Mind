export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const q = url.searchParams.get("q") || "ASX Australia markets OR US stocks OR RBA";
  const rss = "https://news.google.com/rss/search?q=" + encodeURIComponent(q) + "&hl=en-AU&gl=AU&ceid=AU:en";
  const response = await fetch(rss, { headers: { "User-Agent": "MarketMind/1.0" } });
  if (!response.ok) return new Response("News upstream unavailable", { status: 502 });
  const xml = await response.text();

  const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, 12).map(m => {
    const block = m[1];
    const get = tag => {
      const x = block.match(new RegExp("<" + tag + ">([\\s\\S]*?)<\/" + tag + ">"));
      return x ? x[1].replace(/<!\[CDATA\[|\]\]>/g, "").trim() : "";
    };
    return { title: get("title"), link: get("link"), pubDate: get("pubDate"), source: get("source") };
  });

  return Response.json({ updatedAt: new Date().toISOString(), query: q, items },
    { headers: { "Cache-Control": "public, max-age=120" }});
}
