/** Only this explicitly commissioned website receives the authored demo analysis. */
export function isWebsiteDemo(source: string) {
  try {
    const url = new URL(source);
    return (
      url.protocol === "https:" &&
      ["abrahamhaskins.org", "www.abrahamhaskins.org"].includes(url.hostname)
    );
  } catch {
    return false;
  }
}
