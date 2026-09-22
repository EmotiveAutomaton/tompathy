import type { Artifact, ContextItem, Packet, Scope } from "./model";
export interface AnalysisRequest {
  requestId: string;
  artifact: Artifact;
  scope: Scope;
  context: ContextItem[];
  signal: AbortSignal;
}
export interface InferenceProvider {
  id: string;
  analyze(request: AnalysisRequest): Promise<Packet>;
}
// Sounding Line does not yet expose a callable frontend service contract.
export const configuredProvider: InferenceProvider | null = null;
