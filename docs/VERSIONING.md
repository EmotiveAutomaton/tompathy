# Versions and public development

Decision recorded 11 October 2026 (Pacific time).

Public work in progress is normal. A commit records an iteration; a release is a deliberately chosen, named snapshot for people to install. Do not publish a release or increment the patch number after every design conversation. Clear status, reproducible checks and honest release notes matter more than a tidy-looking sequence of numbers.

## Our workflow toward 0.2

| Place | Meaning |
| --- | --- |
| `main` | The reviewed public 0.1 frontend baseline |
| `codex/0.2-development` | Public work toward the complete 0.2 frontend; expect changes |
| `v0.1.0-beta.1` | The existing downloadable beta snapshot; keep its assets unchanged |
| A future `v0.2.0-beta.N` | Optional review milestone when a downloadable preview is useful |
| A future `v0.2.0` | The agreed frontend completion milestone after review and checks |

Commit and push useful iterations to the development branch. CI runs on each push and retains a tested ZIP and verification evidence for 14 days. It does **not** publish a release or update installed extensions. The local persistent Chrome review profile uses the current checkout through `npm run review`.

Use focused topic branches off the development branch if parallel or risky work warrants isolation. When the 0.2 milestone is ready, review the accumulated changes in a pull request, pass CI, merge to main, and create a new tag/release. A draft pull request can be opened earlier for feedback. The milestone branch is intentionally longer lived than the short branches in ordinary GitHub flow; this keeps the user's first public preview separate while the design develops.

There is no need for a separate `release/0.1` branch now. If a published 0.1 defect needs an independent fix, branch from main or the release tag, fix and test it, publish a new patch snapshot, then bring that fix into 0.2. Do not rewrite an already downloaded release.

## Privacy and common methods

Repository visibility applies to its branches: a branch pushed to a public repository is public. Branch protection controls changes, not visibility. Truly private development needs a separate private repository or unpushed local work. That extra arrangement is unnecessary here because the owner explicitly accepts public iterations. [GitHub repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories).

- **GitHub flow:** a focused branch, commits, a pull request, checks/review, merge. A good small-project default. [Official workflow](https://docs.github.com/en/get-started/using-github/github-flow).
- **Trunk-based development:** small changes reach main frequently, often with unfinished features behind switches. Useful when main can remain usable throughout development.
- **GitFlow-style release branches:** separate development, release preparation and hotfix branches. Useful when maintaining several shipping versions, but more coordination than this project presently needs.

These are choices, not social obligations. Release branches are not a prerequisite for publishing responsibly. GitHub releases are tag-backed snapshots, distinct from the full development history. [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## Version labels in this checkout

The development package is **`0.2.0-dev.1`**. Chrome's numeric field is **`0.1.1`**, honoring the requested first iteration, with a human-readable **`0.2 development 1`** label. No public 0.1.1 release was created. Chrome cannot put `-dev.1` in its numeric field; later installable previews can use `0.1.2`, `0.1.3`, and so on, all preceding `0.2.0`. Individual commits need no bump: the build fingerprint identifies their exact contents. [Chrome version fields](https://developer.chrome.com/docs/extensions/reference/manifest/version).

Semantic versioning uses major/minor/patch to communicate compatibility. `0.y.z` explicitly means initial development, where the interface is not yet stable. After 1.0, incompatible API changes increment major, compatible features minor, and fixes patch. Our packet contract has its own version because frontend releases and data compatibility are separate concerns. [SemVer 2.0](https://semver.org/).

## Proposed 0.2 completion criteria

The owner's target is a complete frontend that can accept the backend when ready, not a claim that inference already exists. Use this as the review checklist:

- Final attention, hierarchy, reel, values and Options interactions, including deep/ambiguous graphs and keyboard/reduced-motion behavior.
- Consistent empty, loading, cancellation, unavailable-source, stale-result and invalid-packet states.
- Stable capture, author selection, context timeline, saved readings and revision handling across page changes and browser restarts.
- A documented provider boundary exercised with deterministic success, error and delayed-response fixtures; no invented estimates when fields are absent.
- A repeatable native Chrome review loop, green CI, current privacy/contract documentation, and an installable verified package.
- Owner review of the interface and explicit decisions about features that remain marked future, such as Global, value search, word-level analysis and author-like models.

The current iteration advances these criteria; it does not declare 0.2 complete.
