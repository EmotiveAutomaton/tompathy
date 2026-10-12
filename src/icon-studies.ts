// Original vector studies: broad frontal arcs taper toward the back of a left-facing head.
const face =
  "M19 55L20 45Q10 44 13 36L7 33Q6 32 9 28L13 22C12 10 24 5 36 8C49 10 54 21 50 33Q47 40 41 45L43 55";
const angularFace =
  "M20 55L21 44L14 43L14 36L8 33L14 23L17 14L28 8L40 10L49 18L51 29L46 39L40 44L42 55";
const quietFace =
  "M21 55L21 44Q12 44 14 36L8 32L14 25C13 13 22 7 33 8C49 9 54 22 48 34L40 44L43 55";
const drop =
  "M7 1C-2 4-2 22 7 25C18 28 21 15 31 14Q33 13 31 12C21 11 18-2 7 1Z";
const turnedDrop =
  "M7 1C-2 4-2 22 7 25C16 27 20 18 25 16Q28 15 28 20L27 29Q28 31 30 29L32 20C33 15 30 12 26 11C20 8 18-2 7 1Z";
const path = (d: string, attrs = "") => `<path d="${d}" ${attrs}/>`;
const stroke = (d: string, width = 2.2, color = "currentColor") =>
  path(
    d,
    `fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"`,
  );
const cut = "var(--cut, var(--paper, #fcfdf9))";
let shapeId = 0;
function graph(
  x: number,
  y: number,
  scale: number,
  mode: "bricks" | "outline" | "simple" | "cut" = "bricks",
  bend = false,
  angle = 0,
) {
  const id = `lobe-${shapeId++}-__INSTANCE__`,
    d = bend ? turnedDrop : drop;
  const partitions =
    "M10 0V26M19 4V22M25 9V17M0 7H10M0 13H19M0 19H10M10 7H19M10 19H19";
  const simple = "M11 0V26M21 7V20M0 13H21";
  return `<g transform="translate(${x} ${y}) rotate(${angle} 16 13) scale(${scale})"><defs><clipPath id="${id}">${path(d)}</clipPath></defs>${path(d, `fill="${mode === "cut" ? cut : "currentColor"}" ${mode === "outline" ? 'fill-opacity=".07"' : ""}`)}<g clip-path="url(#${id})">${mode === "outline" ? stroke(partitions, 1.25) : stroke(mode === "simple" ? simple : partitions, 1.15, mode === "cut" ? "currentColor" : cut)}</g>${mode === "outline" ? stroke(d, 1.7) : ""}</g>`;
}
const studies = [
  {
    name: "The literal map",
    family: "A graph inside a head",
    note: "The full lateral teardrop sits high in the cranium, with its broad arc behind the brow and its tip at the back. Most faithful to the reader; fine divisions soften at 16 px.",
    body: stroke(face) + graph(18, 11, 0.9),
  },
  {
    name: "Overlapping hemispheres",
    family: "Two offset lobes",
    note: "Two translucent teardrops overlap behind the forehead; their tips step down at the rear. More brain-like volume, with a softer boundary between the two graphs.",
    body:
      stroke(quietFace) +
      `<g opacity=".42">${graph(18, 18, 0.86, "outline", false, 6)}</g>` +
      graph(17, 10, 0.88, "bricks", false, -4),
  },
  {
    name: "The turning stem",
    family: "A continuous curved tail",
    note: "One tapered graph curls down at the back into a short stem. A direct link between hierarchy and anatomy without adding a separate brain symbol.",
    body: stroke(face) + graph(18, 10, 0.86, "simple", true),
  },
  {
    name: "Open cranial frame",
    family: "The graph completes the head",
    note: "An open outline lets the teardrop become the crown, rather than enclosing another icon. Airier and more distinctive; less immediately a conventional head.",
    body:
      stroke(
        "M19 55L20 44Q10 43 13 36L7 33L13 24L14 20M48 28Q48 39 40 44L43 55",
        2.5,
      ) + graph(15, 8, 1.08, "outline", true),
  },
  {
    name: "Cut from a silhouette",
    family: "Solid head / light graph",
    note: "The teardrop is cut out of a solid profile, with dark divisions crossing it. Strong at tiny sizes and on a toolbar; heavier than the current interface.",
    body: path(face + "Z", 'fill="currentColor"') + graph(18, 12, 0.84, "cut"),
  },
  {
    name: "A pair of sails",
    family: "Stacked compact graphs",
    note: "Two narrow teardrops share a rear stem. The separated lobes are easy to read; their almost wing-like shape makes this the most emblematic option.",
    body:
      stroke(quietFace, 1.9) +
      `<g transform="translate(18 11) scale(.88 .49)">${graph(0, 0, 1, "simple")}</g><g transform="translate(18 23) scale(.78 .45)">${graph(0, 0, 1, "simple")}</g>` +
      stroke("M45 18Q49 23 45 29L43 36", 2.5),
  },
  {
    name: "Three divisions",
    family: "Small-size shorthand",
    note: "One bold teardrop, split into only three tiers, sits inside a generous round head. The cleanest graph shorthand; deliberately gives up the finer sentence rows.",
    body: stroke(face, 2.8) + graph(18, 12, 0.9, "simple"),
  },
  {
    name: "Interleaved contours",
    family: "Two open, interlocking maps",
    note: "Two outlined lobes interlock diagonally and share a low exit. Keeps the layered idea light, though the crossings are better at 32 px than at 16 px.",
    body:
      stroke(face, 1.7) +
      graph(17, 9, 0.8, "outline", false, -8) +
      graph(20, 18, 0.77, "outline", true, 5),
  },
  {
    name: "Faceted memory",
    family: "Angular shell / organic interior",
    note: "A geometric profile contrasts with one soft, bent teardrop. A different silhouette from the round studies, while the interior retains the familiar hierarchy.",
    body: stroke(angularFace, 2.4) + graph(19, 11, 0.83, "bricks", true),
  },
  {
    name: "A shared back",
    family: "Two lobes, one stem",
    note: "A large upper graph and a smaller lower graph end along one bowed rear contour. Reads as one brain rather than two separate badges; has the richest structure.",
    body:
      stroke(face, 1.9) +
      graph(18, 10, 0.88, "bricks", false, -3) +
      `<g opacity=".65">${graph(21, 25, 0.58, "simple", false, -12)}</g>` +
      stroke("M47 21Q50 29 43 36L41 40", 2.5),
  },
  {
    name: "The graph is the crown",
    family: "Profile and lobe share a silhouette",
    note: "The enlarged teardrop supplies the whole crown and rear of the mind. A face and the product’s shape become one mark; this is the most abstract outline study.",
    body:
      stroke(
        "M18 55L19 44Q9 43 12 35L6 32L12 24L13 20M47 28L39 43L42 55",
        2.4,
      ) +
      graph(13, 7, 1.22, "outline", true) +
      path(
        "M20 14Q17 18 19 24",
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"',
      ),
  },
  {
    name: "The quiet imprint",
    family: "Bold contour / two unbroken lobes",
    note: "A broad, closed profile carries two simple teardrop cutouts and a curved stem. The strongest tiny icon; the paired shapes imply the graph instead of drawing its grid.",
    body:
      path(quietFace + "Z", 'fill="currentColor"') +
      `<g fill="${cut}">${path("M21 14C15 18 17 26 23 26C31 26 34 19 44 20Q45 19 43 18C34 18 29 9 21 14Z")}${path("M23 28C19 30 21 36 26 36C33 36 37 29 43 30Q44 29 42 28C34 28 29 24 23 28Z")}</g>` +
      stroke("M44 23Q48 30 40 37", 2.3, cut),
  },
];
let instance = 0;
function svg(body: string, size: number, cut?: string) {
  body = body.replaceAll("__INSTANCE__", String(instance++));
  return `<svg width="${size}" height="${size}" viewBox="0 0 64 64" aria-hidden="true" ${cut ? `style="--cut:${cut}"` : ""}>${body}</svg>`;
}
const grid = document.querySelector<HTMLDivElement>("#studies")!;
const dialog = document.querySelector<HTMLDialogElement>("#detail")!;
let current = 0;
function show(index: number) {
  current = (index + studies.length) % studies.length;
  const study = studies[current];
  document.querySelector("#study-number")!.textContent =
    `${String(current + 1).padStart(2, "0")} / 12`;
  document.querySelector("#study-title")!.textContent = study.name;
  document.querySelector("#study-note")!.textContent = study.note;
  document.querySelector("#large-icons")!.innerHTML =
    `<div>${svg(study.body, 144, "#f3f6ed")}</div><div>${svg(study.body, 144, "#243c32")}</div>`;
  if (!dialog.open) dialog.showModal();
}
studies.forEach((study, i) => {
  const button = document.createElement("button");
  button.className = "study-card";
  button.setAttribute("aria-label", `Explore ${study.name}`);
  button.innerHTML = `<span class="number">${String(i + 1).padStart(2, "0")}</span><div class="hero-mark">${svg(study.body, 96)}</div><h2>${study.name}</h2><span class="study-family">${study.family}</span><p>${study.note}</p><div class="size-samples">${[16, 24, 32, 48].map((size) => `<span>${svg(study.body, size)}<small>${size}px</small></span>`).join("")}</div>`;
  button.addEventListener("click", () => show(i));
  grid.append(button);
});
document
  .querySelector("#close")!
  .addEventListener("click", () => dialog.close());
document
  .querySelector("#previous")!
  .addEventListener("click", () => show(current - 1));
document
  .querySelector("#next")!
  .addEventListener("click", () => show(current + 1));
dialog.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
    e.preventDefault();
    show(current + (e.key === "ArrowLeft" ? -1 : 1));
  }
});
