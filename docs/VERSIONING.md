# Versions and public development

Updated 14 October 2026. The owner accepted 0.2 and authorized Engine v1 for 0.3 beta.

## Current baseline

| Place | Meaning |
| --- | --- |
| `main` | Reviewed 0.2 frontend, ready for the next feature specification |
| `v0.2.0` | Installable frontend milestone; npm and Chrome version 0.2.0 |
| `v0.1.0-beta.1` | Historical beta; its tag and download remain unchanged |
| `codex/<feature>` | Focused work branched from current main when a feature is defined |
| `codex/0.3-engine` | Engine v1 and opt-in providers; npm 0.3.0-beta.1, Chrome 0.3.0 |

The completed `codex/0.2-development` branch is retired after its reviewed merge.
Its commits remain in main. The October 14 engine specification starts the 0.3 cycle.

Public work in progress is normal. Commits record iterations; tags/releases mark
chosen installable snapshots. There is no need to bump a patch number after every
conversation or create a release branch for a single maintained baseline.

## Next development cycle

1. Start a focused `codex/<feature>` branch from up-to-date main.
2. Make reviewable commits and run checks appropriate to the change.
3. Open a pull request. CI builds, tests the browser and native Chrome workflows,
   then retains the verified ZIP and evidence for 14 days.
4. Merge after checks and owner review. Remove the completed feature branch.
5. Tag and publish a release only for an agreed installable milestone. Keep old
   release assets unchanged. Installed unpacked extensions update manually.

CI does not deploy or publish releases automatically. The local review profile
uses the current checkout through `npm run review`. A release tag is distinct from
an ordinary commit or CI artifact. See [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)
and [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

Repository visibility applies to every pushed branch; branch protection does not
make a branch private. The owner accepts public iterations. Separate private work
would require a separate private repository or unpushed local changes.

## Version and contract rules

Use `0.2.x` for compatible fixes to this milestone. Choose the next minor version
when the next feature's scope is understood. npm may use a prerelease suffix during
that work; Chrome's numeric version must increase for every published update.
The build fingerprint identifies exact frontend contents between version bumps.
See [Chrome version fields](https://developer.chrome.com/docs/extensions/reference/manifest/version).

The packet contract has its own version (1.7 for engine fields; 1.0–1.6 remain readable); frontend release numbers
do not imply a contract change. Pre-1.0 versions indicate initial development,
not a stable API guarantee. See [SemVer](https://semver.org/).

## What this milestone means

0.2 is the owner's accepted frontend baseline: attention, hierarchy/reels, values,
creator selection, reading treatments, optional linked context, saved readings,
and the native Chrome review loop. It does not mean that live inference exists.
Sounding Line's provider boundary remains unconnected. Website confidence and
values are demo data; broad model-driven search, word-level analysis, creator-like
models and value search remain future work. Global is an illustrative perspective.

Preserve these distinctions in release notes and future specifications. Update
privacy disclosures and contract documentation when actual backend behavior changes.
