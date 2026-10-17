// Only our extension pages may use this bounded, loopback-only transport.
export function companionRelay(port: chrome.runtime.Port) {
  if (port.name !== "tompathy-companion") return false;
  if (port.sender?.id !== chrome.runtime.id || !port.sender.url?.startsWith(chrome.runtime.getURL(""))) {
    port.disconnect(); return true;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180_000);
  let used = false;
  port.onDisconnect.addListener(() => { controller.abort(); clearTimeout(timeout); });
  port.onMessage.addListener(async message => {
    if (used) return;
    used = true;
    try {
      const url = new URL(message.url);
      if (url.protocol !== "http:" || url.hostname !== "127.0.0.1" || url.username || url.password || url.search || url.hash) throw Error("Invalid companion origin");
      const method = message.method;
      if (!(method === "GET" && url.pathname === "/v1/health" || method === "POST" && url.pathname === "/v1/analyze" || method === "DELETE" && /^\/v1\/analyze\/[A-Za-z0-9_-]{1,200}$/.test(url.pathname))) throw Error("Invalid companion operation");
      const headers = new Headers(message.headers);
      if (!/^Bearer [a-f0-9]{64}$/.test(headers.get("authorization") ?? "")) throw Error("Invalid companion token");
      if ([...headers.keys()].some(key => !["authorization", "content-type", "accept"].includes(key))) throw Error("Invalid headers");
      if (message.body !== undefined && (typeof message.body !== "string" || new TextEncoder().encode(message.body).length > 2_000_000)) throw Error("Oversized body");
      const response = await fetch(url, { method, headers, body: message.body, signal: controller.signal, credentials: "omit", redirect: "error", cache: "no-store" });
      port.postMessage({ type: "headers", status: response.status, contentType: response.headers.get("content-type") ?? "application/json" });
      const reader = response.body?.getReader(), decoder = new TextDecoder("utf-8", { fatal: true });
      let total = 0;
      if (reader) while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        total += value.byteLength;
        if (total > 64_000_000) throw Error("Oversized stream");
        port.postMessage({ type: "chunk", text: decoder.decode(value, { stream: true }) });
      }
      port.postMessage({ type: "chunk", text: decoder.decode() });
      port.postMessage({ type: "done" });
    } catch {
      try { port.postMessage({ type: "error" }); } catch { /* Client already left. */ }
    } finally { controller.abort(); clearTimeout(timeout); }
  });
  return true;
}
