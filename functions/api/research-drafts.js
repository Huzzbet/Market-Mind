function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}

function authorised(request, env) {
  const header = request.headers.get("authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  return Boolean(env.MARKET_MIND_ENGINE_TOKEN && token && token === env.MARKET_MIND_ENGINE_TOKEN);
}

function decode(row) {
  return {
    id: row.id,
    status: row.status,
    generatedAt: row.generated_at,
    model: row.model,
    focus: row.focus,
    reviewedAt: row.reviewed_at,
    reviewerNote: row.reviewer_note,
    research: JSON.parse(row.research_json),
    sources: JSON.parse(row.sources_json)
  };
}

export async function onRequestGet({ request, env }) {
  if (!authorised(request, env)) return json({ error: "Unauthorised" }, 401);
  if (!env.DB) return json({ error: "D1 binding DB is not configured" }, 503);
  const url = new URL(request.url);
  const status = url.searchParams.get("status") || "pending";
  if (!["pending", "approved", "rejected", "all"].includes(status)) {
    return json({ error: "status must be pending, approved, rejected or all" }, 400);
  }
  const limit = Math.min(50, Math.max(1, Number(url.searchParams.get("limit")) || 20));
  const result = status === "all"
    ? await env.DB.prepare("SELECT * FROM research_drafts ORDER BY generated_at DESC LIMIT ?").bind(limit).all()
    : await env.DB.prepare("SELECT * FROM research_drafts WHERE status = ? ORDER BY generated_at DESC LIMIT ?").bind(status, limit).all();
  return json({ drafts: (result.results || []).map(decode), count: (result.results || []).length });
}

export async function onRequestPatch({ request, env }) {
  if (!authorised(request, env)) return json({ error: "Unauthorised" }, 401);
  if (!env.DB) return json({ error: "D1 binding DB is not configured" }, 503);
  let body;
  try { body = await request.json(); } catch { return json({ error: "Body must be valid JSON" }, 400); }
  if (!body || typeof body.id !== "string" || !body.id || !["approved", "rejected"].includes(body.status)) {
    return json({ error: "Provide a draft id and status of approved or rejected" }, 400);
  }
  const note = typeof body.reviewerNote === "string" ? body.reviewerNote.slice(0, 2000) : null;
  const result = await env.DB.prepare(
    "UPDATE research_drafts SET status = ?, reviewed_at = ?, reviewer_note = ? WHERE id = ? AND status = 'pending'"
  ).bind(body.status, new Date().toISOString(), note, body.id).run();
  if (!result.meta || result.meta.changes !== 1) {
    return json({ error: "Draft not found or it has already been reviewed" }, 409);
  }
  return json({ id: body.id, status: body.status, publication: "not_published" });
}
