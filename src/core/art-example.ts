import snapshot from "./art-snapshot.json" with { type: "json" };
import { makeArtifact, type Packet, type ContextItem } from "./model";
import { createWebsiteDemo } from "./website-demo";
export const artSnapshot = snapshot;
export const artSource = snapshot.source;
export const artContext: ContextItem = {
  id: "art-public-context",
  source: artSource,
  retrievedAt: snapshot.capturedAt,
  selected: false,
  lineage: "public-url",
  provenance: {
    author: snapshot.creator,
    basis: "page-byline",
    linkedFrom: artSource,
  },
  excerpt:
    "The published essay identifies its creator and declares involvement categories. This commissioned website demonstration adds hand-authored sentence interpretations and invented confidence, attention and value trajectories. The curves are visual fixtures, not measured personality or history. No backend analysis has run.",
  facts: [
    {
      label: "Creator introduction",
      quote: snapshot.blocks[2].text,
      source: artSource,
      dateKind: "undated",
    },
    {
      label: "Published involvement markings",
      quote:
        "The page supplies Ghost Scale classes (100, 95, 60 and 0). They express declared involvement categories, not confidence percentages.",
      source: artSource,
      dateKind: "undated",
    },
  ],
};
/** Offline fixture for development. The review desk opens the actual website. */
export async function createArtExample(source = artSource): Promise<Packet> {
  const artifact = await makeArtifact(
    snapshot.blocks.map((b) => b.text),
    source,
    snapshot.title,
  );
  artifact.authors = [{ label: snapshot.creator, basis: "byline" }];
  artifact.capture = {
    method: "article",
    note: "Offline development fixture; use the review desk for the real website.",
  };
  artifact.regions.forEach((r, i) => {
    r.emphasis = snapshot.blocks[i].emphasis;
  });
  return createWebsiteDemo(artifact, true);
}
