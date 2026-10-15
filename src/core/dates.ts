/** Preserve supplied precision; reject impossible dates instead of normalizing them. */
export function calendarDate(value: string): string | undefined {
  const match = value
    .trim()
    .match(
      /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?$/,
    );
  if (!match) return;
  if (match[4] && (!match[3] || !Number.isFinite(Date.parse(value)))) return;
  const year = Number(match[1]),
    month = Number(match[2] ?? 1),
    day = Number(match[3] ?? 1);
  if (
    year < 1000 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > new Date(Date.UTC(year, month, 0)).getUTCDate()
  )
    return;
  return (
    match[1] +
    (match[2] ? `-${match[2]}` : "") +
    (match[3] ? `-${match[3]}` : "")
  );
}
