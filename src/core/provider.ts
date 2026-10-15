import {
  matchPacket,
  parsePacket,
  type Artifact,
  type ContextItem,
  type Packet,
  type Scope,
} from "./model";
export interface AnalysisRequest {
  requestId: string;
  artifact: Artifact;
  scope: Scope;
  context: ContextItem[];
  signal: AbortSignal;
  history?: "wikipedia";
}
export interface InferenceProvider {
  id: string;
  analyze(request: AnalysisRequest): Promise<Packet>;
}
export type ProviderSettings =
  | { kind: "none" }
  | { kind: "registry"; url: string }
  | { kind: "local"; url: string; token: string };

export function providerOrigin(settings: ProviderSettings): string | null {
  if (settings.kind === "none") return null;
  const url = new URL(settings.url);
  if (url.username || url.password || url.search || url.hash)
    throw Error("Use a source URL without credentials, query or fragment.");
  if (settings.kind === "registry" && url.protocol !== "https:")
    throw Error("A registry must use HTTPS.");
  if (
    settings.kind === "local" &&
    (url.protocol !== "http:" ||
      url.hostname !== "127.0.0.1" ||
      url.pathname !== "/")
  )
    throw Error("The local companion must use http://127.0.0.1 with its port.");
  if (settings.kind === "local" && !/^[0-9a-f]{64}$/i.test(settings.token))
    throw Error("Paste the companion's 64-character session token.");
  return url.origin;
}

async function boundedText(
  response: Response,
  signal: AbortSignal,
  limit = 2_000_000,
) {
  signal.throwIfAborted();
  if (!response.ok) {
    if (response.status === 401)
      throw Error("The companion token was not accepted.");
    if (response.status === 404)
      throw Error("No analysis is available for this page.");
    if (response.status === 409)
      throw Error("The companion is busy or this request was cancelled.");
    throw Error(`Analysis source returned HTTP ${response.status}.`);
  }
  const reader = response.body?.getReader();
  if (!reader) throw Error("Analysis source returned an empty response.");
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      signal.throwIfAborted();
      if (done) break;
      total += value.byteLength;
      if (total > limit)
        throw Error("Analysis response exceeds its size limit.");
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}

function matching(packet: Packet, request: AnalysisRequest) {
  request.signal.throwIfAborted();
  const mismatch = matchPacket(
    packet,
    request.artifact,
    request.scope,
    request.context,
  );
  if (mismatch) throw Error(mismatch);
  return packet;
}

export function registryProvider(
  url: string,
  fetcher: typeof fetch = fetch,
): InferenceProvider {
  providerOrigin({ kind: "registry", url });
  const base = new URL(url.endsWith("/") ? url : url + "/");
  return {
    id: "registry",
    async analyze(request) {
      if (request.history)
        throw Error("History analysis requires the local companion.");
      if (request.scope !== "artifact")
        throw Error(
          "Registry readings cover the work only. Select artifact scope to use one.",
        );
      request.signal.throwIfAborted();
      const hash = Array.from(
        new Uint8Array(
          await crypto.subtle.digest(
            "SHA-256",
            new TextEncoder().encode(request.artifact.id),
          ),
        ),
        (byte) => byte.toString(16).padStart(2, "0"),
      ).join("");
      const options: RequestInit = {
        signal: request.signal,
        credentials: "omit",
        redirect: "error",
        referrerPolicy: "no-referrer",
      };
      const index = JSON.parse(
        await boundedText(
          await fetcher(
            new URL(`index/${hash.slice(0, 4)}.json`, base),
            options,
          ),
          request.signal,
          1_000_000,
        ),
      ) as unknown;
      if (!Array.isArray(index) || index.length > 5000)
        throw Error("Invalid registry index.");
      const entries = index.filter(
        (item) =>
          item && typeof item === "object" && item.artifact_id_hash === hash,
      );
      if (!entries.length)
        throw Error("No analysis is available for this page.");
      if (entries.length !== 1) throw Error("Ambiguous registry entry.");
      const entry = entries[0];
      if (
        !Array.isArray(entry.revisions) ||
        !entry.revisions.includes(request.artifact.revision)
      )
        throw Error("This page changed since it was analyzed.");
      const relative = entry.packet_paths?.[request.artifact.revision];
      if (
        relative !== `packets/${hash}/${request.artifact.revision}.json` ||
        !/^[0-9a-f]{64}$/.test(request.artifact.revision)
      )
        throw Error("Invalid registry packet path.");
      const packet = parsePacket(
        await boundedText(
          await fetcher(new URL(relative, base), options),
          request.signal,
        ),
      );
      return matching(packet, request);
    },
  };
}

export function localProvider(
  url: string,
  token: string,
  fetcher: typeof fetch = fetch,
): InferenceProvider {
  const origin = providerOrigin({ kind: "local", url, token })!;
  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
  return {
    id: "local",
    async analyze(request) {
      request.signal.throwIfAborted();
      const cancel = () => {
        void fetcher(
          `${origin}/v1/analyze/${encodeURIComponent(request.requestId)}`,
          {
            method: "DELETE",
            headers,
            signal: AbortSignal.timeout(5000),
            credentials: "omit",
            redirect: "error",
          },
        ).catch(() => {});
      };
      request.signal.addEventListener("abort", cancel, { once: true });
      try {
        const response = await fetcher(`${origin}/v1/analyze`, {
          method: "POST",
          headers,
          signal: request.signal,
          credentials: "omit",
          redirect: "error",
          body: JSON.stringify({
            requestId: request.requestId,
            artifact: request.artifact,
            scope: request.scope,
            context:
              request.scope === "context"
                ? request.context.filter((c) => c.selected)
                : [],
            ...(request.history ? { history: request.history } : {}),
          }),
        });
        return matching(
          parsePacket(await boundedText(response, request.signal)),
          request,
        );
      } finally {
        request.signal.removeEventListener("abort", cancel);
      }
    },
  };
}

export function makeProvider(
  settings: ProviderSettings,
): InferenceProvider | null {
  return settings.kind === "registry"
    ? registryProvider(settings.url)
    : settings.kind === "local"
      ? localProvider(settings.url, settings.token)
      : null;
}

// Selection is explicitly opt-in through Options. Merely capturing a page sends nothing.
export const configuredProvider: InferenceProvider | null = null;
