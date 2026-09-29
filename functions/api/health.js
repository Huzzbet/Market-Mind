export function onRequestGet() {
  return Response.json({
    ok: true,
    app: "Market Mind",
    version: "0.2.0",
    timestamp: new Date().toISOString()
  });
}
