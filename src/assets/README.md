# Bundled fonts and artwork

`reader-grade.woff` is a Latin subset of [Roboto Serif](https://github.com/google/fonts/tree/main/ofl/robotoserif), licensed under the accompanying SIL OFL 1.1. It was subset with fontTools 4.62.1, then instantiated at `wdth=100`, `opsz=20`, `wght=400`; the `GRAD` axis remains variable from -50 to 100. Subset coverage is U+0020–017F, U+2000–206F, U+20AC, U+2190 and U+2192. Other scripts use the platform fallback, which may not support grade. No reserved font name was declared in the supplied OFL.

The build copies the font through esbuild's file loader and includes its full license in THIRD_PARTY_NOTICES.txt. The extension exposes this font as a web-accessible resource. No external font provider is called at runtime. WOFF is used to avoid introducing an additional compression dependency into development.

`confidence-weight.woff` is a separate Latin subset of the same upstream Roboto Serif font, fixed at `wdth=100`, `opsz=16`, `GRAD=0`, with continuous `wght` from 100 to 900. It is used for attention and value labels. Canvas word packing uses the same face and reruns when the font loads. The existing reading-grade font is unchanged. This second font is about 76 KB and is not exposed to arbitrary webpages.

`essays/` contains exact copies of the owner-supplied illustrations and selected
public art-essay images. See its provenance manifest and NOTICES.txt. Essay HTML,
JavaScript, CSS and named essay images are web-accessible so the extension can
show its public authored help over a connected webpage. They contain no saved
reading or analysis data. No remote image provider is called when help opens.

`icon-small-master.png` is the optical 16/32 px variant of the supplied `icon-master.png`. The creator portrait and 48/128 px assets retain the original. `scripts/resize-icons.ps1` selects the correct source for each size. Generated with the built-in image tool on 14 October 2026, using the original as the edit target and preserving transparency.

Generation prompt: “Create an optical small-size variant of the attached ToMpathy logo for display at 16 and 32 pixels. Preserve its recognizable left-facing human head silhouette and the green hollow sideways teardrop pointing to the right at the back of the head, with a gentle downward brainstem. Convert ALL the gray filled face and thick skull arch into a very thin simple continuous cartoon outline in neutral medium gray. Greatly reduce the human outline’s visual mass. Enlarge and emphasize the inner green loop so it dominates the icon and the hollow interior is clearly open even at 16px. Simplify nose/lips/chin to very few contours. Flat solid muted forest green, no texture, no shading, no tiny details, no text, no border. Tight square framing with just 5% safety margin, transparent background. This is a single production icon, not a contact sheet or mockup. Keep green shape smoothly rounded, warm and organic; green stroke substantially thicker than gray outline. Avoid filled gray neck or face.”
