import { logoStudies } from "./logo-studies";
for (const study of logoStudies) {
  const card = document.createElement("article");
  card.className = "prompt-card logo-study";
  const heading = document.createElement("h2");
  heading.textContent = study.name;
  const link = document.createElement("a");
  link.href = study.image;
  link.target = "_blank";
  link.rel = "noopener";
  const image = document.createElement("img");
  image.src = study.image;
  image.alt =
    study.name + ": a left-facing head with a right-facing teardrop brain";
  image.loading = "lazy";
  link.append(image);
  const sizes = document.createElement("div");
  sizes.className = "logo-sizes";
  for (const size of [24, 32, 48]) {
    const small = image.cloneNode() as HTMLImageElement;
    small.width = size;
    small.height = size;
    small.alt = `${size} pixel preview`;
    sizes.append(small);
  }
  const note = document.createElement("p");
  note.textContent = study.note;
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Generation prompt";
  const prompt = document.createElement("textarea");
  prompt.readOnly = true;
  prompt.value =
    study.prompt +
    ("refinement" in study ? "\n\nCleanup edit:\n" + study.refinement : "");
  prompt.setAttribute("aria-label", study.name + " generation prompt");
  details.append(summary, prompt);
  card.append(heading, link, sizes, note, details);
  document.querySelector("#logo-studies")!.append(card);
}
type Direction = { name: string; family: string; note: string; prompt: string };
const directions: Direction[] = [
  {
    name: "The space between people",
    family: "Swiss reduction · negative space",
    note: "Explore empathy without drawing a brain. Judge the white shape as carefully as the green one.",
    prompt:
      "Design a distinctive app icon for ToMpathy, a reading tool for exploring another creator’s perspective. Two abstract human profiles face each other; the negative space between them forms one small, open doorway. Swiss modernist graphic design, extremely economical geometry, humane proportions, asymmetrical enough to feel authored. One flat deep sage green on warm ivory. No lettering, no literal brain, no circuits, no hearts, no gradients. Deliver a single isolated vector-like mark in a square, with generous margins. It should remain recognizable at 24 pixels. Make the space between the profiles the memorable element, not a generic chat-bubble silhouette.",
  },
  {
    name: "A mind with a curved tail",
    family: "Anatomical hint · soft geometry",
    note: "Closest to the current idea, but let the image model redesign the proportions rather than trace the chart.",
    prompt:
      "Create a small logo for ToMpathy, a humane tool for reading the possible intentions behind a text. A left-facing human head, drawn as a quiet open outline. Inside the upper cranium, place two overlapping sideways teardrops: broad rounded ends behind the forehead, narrow tips toward the back of the head. Let one tip bend gently downward like a brainstem. Subdivide only one lobe into three broad areas, with no fine grid or tiny dots. The mind must feel housed inside the head, not pasted on top. Forest green linework, pale sage interior, ivory background. Rounded tips, crisp vector contours, no lettering, no medical realism. Prioritize an elegant silhouette that works at 32 pixels.",
  },
  {
    name: "Attention in one breath",
    family: "Japanese brush · gestural mark",
    note: "A deliberately expressive alternative. Keep a clean silhouette even if the large version has brush texture.",
    prompt:
      "Invent a calligraphic symbol for ToMpathy, an empathy-oriented reading tool. Use one fluid brush gesture that suggests both a listening human profile and an incomplete circle opening toward another person. The gesture begins broad and grounded, becomes fine, then ends with a small rounded turn. Inspired by the economy of Japanese ink painting, not by any existing character or religious emblem. Deep green-black ink on warm off-white. Quiet, curious, alive, slightly imperfect. No brain diagram, no text, no eyes, no heart. Show one centered standalone logo, not stationery or a product mockup. The overall gesture must survive reduction to a tiny monochrome icon.",
  },
  {
    name: "Two layers of understanding",
    family: "Mid-century paper cut · warm color",
    note: "Tests whether warmth and color communicate the project better than the current analytical styling.",
    prompt:
      "Design an editorial app icon for ToMpathy using two interlocking paper-cut shapes. One shape is a left-facing person in profile; the other is a soft coral leaf-like form inside and partly behind the head, suggesting a second perspective. Mid-century book-jacket design, bold irregular curves, limited palette of muted terracotta, deep teal and cream. Flat artwork with at most a very slight paper texture. No outlines, no detailed anatomy, no circuit motifs, no letters. Make the overlap purposeful and readable, with large areas of negative space. Return a single square logo composition; expressive at a large size, legible as two shapes at 24 pixels.",
  },
  {
    name: "Listening before interpreting",
    family: "Monoline ear · nested contour",
    note: "A listening symbol may be friendlier, although it could suggest an audio product. Compare that tradeoff.",
    prompt:
      "Create a minimal monoline logo for ToMpathy, a tool that helps readers attend to a creator’s perspective. Base the mark on an abstract ear or listening contour, enclosing a small seed-shaped space. A single continuous line subtly becomes a side profile at its outer edge. Soft geometric curves, nearly uniform stroke, rounded terminals, muted pine green on ivory. Avoid a literal hearing-aid icon, sound-wave bars, headphones, brains, eyes, hearts and lettering. The mark should express receptive curiosity rather than surveillance. One isolated square composition with generous padding. Optimize for a browser toolbar at 24 and 32 pixels; use no detail that requires zooming to understand.",
  },
  {
    name: "A ribbon taking another shape",
    family: "Continuous ribbon · spatial illusion",
    note: "Explore a more distinctive folded form. It will need a convincing flat version if chosen.",
    prompt:
      "Design a compact emblem for ToMpathy: a single broad ribbon folds once to form the outline of a human profile looking left, while its interior opening resembles a second viewpoint looking right. The two readings should emerge from the same shape. Restrained optical ambiguity, like a carefully designed folded-paper symbol. Use two tones of eucalyptus green with one clean shadow plane; no glossy rendering, no intricate knotwork, no lettering. Friendly rounded corners and a stable, balanced silhouette. Place one logo on a plain warm-white square. It must be reducible to a clear one-color mark; avoid fine overlaps and decorative loops.",
  },
  {
    name: "A small sculpted mind",
    family: "Soft clay · tactile app icon",
    note: "A strong stylistic departure. Useful for discovering a silhouette even if the final asset becomes flat.",
    prompt:
      "Create a tactile app icon for ToMpathy, a tool for thoughtful reading and perspective-taking. Sculpt one simple left-facing head from matte sage-colored clay. A shallow curved groove in the upper head suggests a gentle flow of thought, not a realistic brain. The form is compact, rounded and subtly asymmetrical, with no face details except the contour of nose and chin. Warm ivory backdrop, soft diffuse studio light, a small grounded shadow. No smiling mascot, no eyes, no text, no electronic components, no glossy plastic. One centered icon in a square. Keep the silhouette strong and the groove broad enough to survive small-scale display.",
  },
  {
    name: "A window into a perspective",
    family: "Stained glass · three broad planes",
    note: "Tests structured color and clear partitions without recreating a busy hierarchy inside a tiny icon.",
    prompt:
      "Design a graphic emblem for ToMpathy as a small arched window that also reads as a human profile. Use exactly three large stained-glass-like planes: dark pine, soft sage and warm amber, separated by restrained ivory channels. The planes converge toward a gently rounded point at the upper right, suggesting attention forming an interpretation. Modern secular design, not a cathedral illustration. Flat vector treatment, no glass shine, no fine mosaic, no lettering or literal brain. A distinctive outer contour is essential. Show one centered mark on a warm-white square, readable at 24 pixels and adaptable to monochrome.",
  },
  {
    name: "The M between two minds",
    family: "Typographic monogram · letterform",
    note: "A lettermark could be clearer in a toolbar and leave the graph to the interface. Exact lettering may need manual refinement.",
    prompt:
      "Design an original monogram for ToMpathy around a capital M. The two outer stems subtly resemble two human profiles facing inward; the central valley becomes the space where their perspectives meet. The M must remain legible before the faces are noticed. Contemporary humanist typography, rounded internal joins, confident broad strokes and generous counters. One-color dark green on ivory. No full wordmark, no additional letters, no brain, no speech bubble, no decorative border. One isolated square logo, balanced but not mechanically symmetrical. Make it work as a crisp 16- to 32-pixel browser icon and as a larger print mark.",
  },
  {
    name: "A constellation coming into focus",
    family: "Luminous abstraction · dark field",
    note: "Explore an atmospheric identity. A final toolbar version would need far fewer points and no dependence on glow.",
    prompt:
      "Explore a striking app-icon concept for ToMpathy. On a deep midnight-green field, four warm ivory points and two short curved paths imply a human head in profile without drawing its outline. One slightly brighter point represents current attention. The arrangement should feel like a sparse constellation gradually becoming a perspective, never like a network dashboard or surveillance map. Restrained soft glow, lots of darkness, no tiny stars, no text, no realistic brain. Use a compact asymmetric composition inside a square. Keep the four points and two curves large enough to read at 32 pixels, with a recognizable flat-color silhouette underneath the atmosphere.",
  },
  {
    name: "Thought as a growing seed",
    family: "Woodcut · organic emblem",
    note: "A nature-led direction with no face requirement. Check that it suggests growth and understanding rather than a gardening app.",
    prompt:
      "Make an emblem for ToMpathy, a thoughtful reading tool, using a germinating seed whose two broad leaves suggest two viewpoints. One leaf curves inward as if listening; the other opens outward. The stem forms a subtle question-like bend without becoming a literal question mark. Contemporary woodcut or linocut sensibility, bold organic silhouette, only two or three broad interior cuts. Dark moss green on warm cream. No face, no brain, no tiny veins, no text, no ornamental frame. One centered logo in a square. It should feel patient, curious and handmade while remaining clean enough for a 24-pixel browser icon.",
  },
  {
    name: "The missing piece of a portrait",
    family: "Geometric illusion · modular silhouette",
    note: "Explore recognition through absence. This should feel like incomplete understanding, not a solved puzzle or diagnostic diagram.",
    prompt:
      "Design a distinctive minimal logo for ToMpathy, a tool for exploring another person’s perspective. Construct a human side profile from three softly rounded geometric pieces, leaving a deliberate open gap through the upper head. The empty gap itself suggests a small forward-facing path. The portrait should remain incomplete and inviting, without looking broken. Bauhaus-adjacent geometry with humane proportions, charcoal green and one pale sage plane on cream. No jigsaw tabs, no brain anatomy, no eyes, no circuits, no typography. Deliver one standalone square mark with large clean shapes and generous margins. Aim for an immediately recognizable silhouette with a second visual reading discovered later.",
  },
];

const host = document.querySelector("#prompts")!;
const copyStatus = document.querySelector("#copy-status")!;
for (const [i, direction] of directions.entries()) {
  const card = document.createElement("article");
  card.className = "prompt-card";
  const number = document.createElement("span");
  number.className = "number";
  number.textContent = String(i + 1).padStart(2, "0");
  const heading = document.createElement("h2");
  heading.textContent = direction.name;
  const family = document.createElement("p");
  family.className = "prompt-family";
  family.textContent = direction.family;
  const field = document.createElement("textarea");
  field.readOnly = true;
  field.value = direction.prompt;
  field.setAttribute("aria-label", `${direction.name} prompt`);
  const note = document.createElement("p");
  note.className = "prompt-note";
  note.textContent = direction.note;
  const copy = document.createElement("button");
  copy.textContent = "Copy prompt";
  copy.setAttribute("aria-label", `Copy ${direction.name}`);
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(direction.prompt);
      copyStatus.textContent = `Copied ${direction.name}.`;
      copy.textContent = "Copied ✓";
      setTimeout(() => {
        copy.textContent = "Copy prompt";
      }, 1800);
    } catch {
      field.focus();
      field.select();
      copyStatus.textContent =
        "Prompt selected. Press Ctrl+C or Command+C to copy.";
    }
  });
  card.append(number, heading, family, field, note, copy);
  host.append(card);
}
document.querySelector("#download")!.addEventListener("click", () => {
  const text = directions
    .map(
      (d, i) =>
        `${String(i + 1).padStart(2, "0")} · ${d.name}\n${d.family}\n\n${d.prompt}\n\nConsider: ${d.note}`,
    )
    .join("\n\n———\n\n");
  const url = URL.createObjectURL(
    new Blob([text], { type: "text/plain;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "tompathy-icon-prompts.txt";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
