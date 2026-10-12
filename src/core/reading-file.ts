import {
  SessionSchema,
  matchPacket,
  makeArtifact,
  type Session,
} from "./model";

const escapeHTML = (s: string) =>
  s.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
/** A readable, inert page copy and its exact analysis travel in one file. */
export function readingFile(session: Session): string {
  if (!session.artifact) throw Error("Open a page before exporting a reading.");
  const a = session.artifact;
  // A context change can leave the last account awaiting replacement. Preserve
  // it as history, rather than exporting an active account that cannot reimport.
  let portable = session;
  if (
    session.packet &&
    matchPacket(session.packet, a, session.scope, session.context)
  ) {
    const p = session.packet;
    const artifactMismatch = matchPacket(
      { ...p, scope: { kind: "artifact", contextIds: [] } },
      a,
      "artifact",
      [],
    );
    if (artifactMismatch) throw Error(artifactMismatch);
    portable = {
      ...session,
      packet: null,
      history: [
        ...(session.history ?? []),
        {
          packet: p,
          context: session.context.map((c) => ({
            ...c,
            selected: p.scope.contextIds.includes(c.id),
          })),
          acceptedAt: new Date().toISOString(),
        },
      ].slice(-5),
    };
  }
  const payload = JSON.stringify({
    format: "tompathy-reading",
    version: 1,
    session: { ...portable, savedPageId: undefined },
  }).replace(/</g, "\\u003c");
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>${escapeHTML(a.title)}</title><style>body{max-width:740px;margin:60px auto;padding:0 24px;font:19px/1.75 Georgia,serif;color:#24382e;background:#fbfcf8}header{font:13px/1.6 system-ui;color:#64726a}p{white-space:pre-wrap}</style><header>ToMpathy saved reading · ${escapeHTML(a.source)}<br>Readable text snapshot${a.truncated ? " · capture was truncated" : ""}. Import this file in ToMpathy to explore its analysis.</header><article>${a.regions.map((r) => `<p>${escapeHTML(r.anchor.exact)}</p>`).join("\n")}</article><script type="application/json" id="tompathy-reading">${payload}</script></html>`;
}
export async function parseReadingFile(text: string): Promise<Session> {
  const payload = text.trimStart().startsWith("<")
    ? text.match(
        /<script type="application\/json" id="tompathy-reading">([\s\S]*?)<\/script>/,
      )?.[1]
    : text;
  if (!payload) throw Error("This is not a ToMpathy reading file.");
  const data = JSON.parse(payload);
  if (data.format !== "tompathy-reading" || data.version !== 1)
    throw Error("Unsupported reading file version.");
  const session = SessionSchema.parse(data.session),
    a = session.artifact;
  if (!a) throw Error("The reading file has no saved page.");
  const rebuilt = await makeArtifact(
    a.regions.map((r) => r.anchor.exact),
    a.source,
    a.title,
  );
  if (
    a.id !== rebuilt.id ||
    a.revision !== rebuilt.revision ||
    new Set(a.regions.map((r) => r.id)).size !== a.regions.length ||
    a.regions.some((r, i) =>
      Object.entries(r.anchor).some(
        ([key, value]) =>
          value !== rebuilt.regions[i].anchor[key as keyof typeof r.anchor],
      ),
    )
  )
    throw Error("The saved page no longer matches its text anchors.");
  if (session.packet) {
    const mismatch = matchPacket(
      session.packet,
      a,
      session.scope,
      session.context,
    );
    if (mismatch) throw Error(mismatch);
  }
  return { ...session, savedPageId: undefined };
}
