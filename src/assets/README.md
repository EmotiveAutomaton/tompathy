# Reader font

`reader-grade.woff` is a Latin subset of [Roboto Serif](https://github.com/google/fonts/tree/main/ofl/robotoserif), licensed under the accompanying SIL OFL 1.1. It was subset with fontTools 4.62.1, then instantiated at `wdth=100`, `opsz=20`, `wght=400`; the `GRAD` axis remains variable from -50 to 100. Subset coverage is U+0020–017F, U+2000–206F, U+20AC, U+2190 and U+2192. Other scripts use the platform fallback, which may not support grade. No reserved font name was declared in the supplied OFL.

The build copies the font through esbuild's file loader and includes its full license in THIRD_PARTY_NOTICES.txt. The extension exposes only this font as a web-accessible resource. No external font provider is called at runtime. WOFF is used to avoid introducing an additional compression dependency into development.
