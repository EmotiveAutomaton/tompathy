import type { Hypothesis, Packet, Session } from "./model";

const meanings: Record<string, string> = {
  "governing-purpose": "Governing purpose",
  "local-goal": "Local goal",
  "historical-event": "Possible production event",
  "reader-route": "Route a reader could follow",
  repertoire: "Possible repertoire",
  preference: "Recurring preference",
  value: "Value hypothesis",
};
export const interpretationLabel = (h: Hypothesis) =>
  meanings[h.interpretation ?? ""] ?? "Interpretation not specified";

export function contributionExplanation(
  packet: Pick<Packet, "estimates" | "documentContribution">,
  region: string,
): string {
  const estimate = packet.estimates.find((e) => e.region === region);
  const global = packet.documentContribution,
    local = estimate?.contribution;
  return [
    global
      ? `Across the document — ${global.quantity}: ${global.value ?? "unknown"}. ${global.explanation}`
      : "Document-wide contribution unknown.",
    local
      ? `This passage — ${local.quantity}: ${local.value} (${local.scale}). ${local.explanation ?? "No explanation supplied."}`
      : "Local contribution unknown; this passage is unpainted.",
    estimate
      ? `Uncertainty: ${estimate.uncertainty.level}. ${estimate.uncertainty.meaning}`
      : "Uncertainty unknown.",
  ].join("\n");
}
export function acceptRevision(
  session: Session,
  packet: Packet,
  context = session.context,
): Session {
  const history = [...(session.history ?? [])];
  if (
    session.packet &&
    (session.packet.id !== packet.id ||
      session.packet.revision !== packet.revision)
  )
    history.push({
      packet: session.packet,
      context: session.context,
      acceptedAt: new Date().toISOString(),
    });
  return {
    ...session,
    packet,
    scope: packet.scope.kind,
    context,
    history: history.slice(-5),
  };
}
export function analysisHandoff(session: Session) {
  if (!session.artifact)
    throw Error("Capture a source before exporting an analysis request.");
  return {
    requestVersion: "1.0",
    requestId: crypto.randomUUID(),
    artifact: session.artifact,
    author:
      session.authorLabel ||
      (session.artifact.authors?.length === 1
        ? session.artifact.authors[0].label
        : null),
    scope: {
      kind: session.scope,
      contextIds:
        session.scope === "context"
          ? session.context.filter((c) => c.selected).map((c) => c.id)
          : [],
    },
    context:
      session.scope === "context"
        ? session.context.filter((c) => c.selected)
        : [],
    accepts: ["1.0", "1.1", "1.2"],
  };
}
