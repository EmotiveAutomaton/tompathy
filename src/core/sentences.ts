/** UTF-16 offsets into the unchanged normalized capture, never a new artifact identity. */
export function sentences(text: string) {
  return Array.from(
    new Intl.Segmenter("en", { granularity: "sentence" }).segment(text),
    (s) => {
      const leading = s.segment.length - s.segment.trimStart().length;
      return {
        text: s.segment.trim(),
        start: s.index + leading,
        end: s.index + s.segment.trimEnd().length,
      };
    },
  ).filter((s) => s.text.length);
}
