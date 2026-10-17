/** Loopback fetch from the extension service worker, with bounded streaming.
 * Browser-only development keeps the normal fetch transport. */
export const companionFetch: typeof fetch = async (input, init = {}) => {
  if (typeof chrome === "undefined" || !chrome.runtime?.id) return fetch(input, init);
  const url = String(input);
  const port = chrome.runtime.connect({ name: "tompathy-companion" });
  const signal = init.signal;
  let stream: ReadableStreamDefaultController<Uint8Array> | undefined;
  let settled = false, finished = false;
  const encoder = new TextEncoder();
  return new Promise<Response>((resolve, reject) => {
    const cleanup = () => { finished = true; signal?.removeEventListener("abort", abort); port.disconnect(); };
    const fail = (error: Error) => {
      if (finished) return;
      if (settled) stream?.error(error); else reject(error);
      cleanup();
    };
    const abort = () => fail(new DOMException("Analysis cancelled", "AbortError"));
    if (signal?.aborted) { abort(); return; }
    signal?.addEventListener("abort", abort, { once: true });
    port.onDisconnect.addListener(() => {
      if (!finished) fail(new TypeError("Local companion connection closed"));
    });
    port.onMessage.addListener(message => {
      if (finished) return;
      if (message.type === "headers" && !settled) {
        settled = true;
        resolve(new Response(new ReadableStream<Uint8Array>({
          start(controller) { stream = controller; }, cancel() { cleanup(); },
        }), { status: message.status, headers: { "Content-Type": message.contentType } }));
      } else if (message.type === "chunk" && settled) stream?.enqueue(encoder.encode(message.text));
      else if (message.type === "done" && settled) { stream?.close(); cleanup(); }
      else if (message.type === "error") fail(new TypeError("Local companion fetch failed"));
    });
    port.postMessage({ url, method: init.method ?? "GET", headers: Object.fromEntries(new Headers(init.headers).entries()), body: init.body });
  });
};
