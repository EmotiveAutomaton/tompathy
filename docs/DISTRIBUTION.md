# Distribution and Chrome Web Store readiness

Checked 12 October 2026. No Chrome Web Store account was registered, payment made or item submitted as part of this release.

## Use GitHub now; consider a private Store beta next

The GitHub ZIP is immediately useful for development across machines: extract it, enable Developer mode in `chrome://extensions`, and **Load unpacked** the folder containing `manifest.json`. Keep that folder in place. Updating means replacing its files and clicking Reload. The repository's persistent Chrome review launcher is the smoother loop on a development machine; see [Development and QA](DEVELOPMENT.md).

Chrome Web Store distribution adds convenient installation and managed updates. It can be used during development; the product need not be final. However, private and unlisted items still require policy review, so the Store is not a replacement for the rapid local edit/build/reload loop.

| Distribution | Who can install | Best use |
| --- | --- | --- |
| GitHub ZIP / unpacked | Anyone with the download who enables Developer mode | Current frontend beta and rapid iteration |
| Private Store listing | Specified trusted Google accounts or configured tester groups | The owner's machines and a small review group |
| Unlisted Store listing | Anyone who has its URL | Link-based beta sharing; not access control |
| Public Store listing | Store visitors | A useful, clearly described release |

Google documents these choices and parallel testing listings in [distribution settings](https://developer.chrome.com/docs/webstore/cws-dashboard-distribution). All visibility levels have the same policy/review requirements. A separate testing listing must follow Google's beta/development naming and description conventions.

## What costs money?

The extension can be free to download. Creating a publisher currently requires a **one-time $5 developer registration fee**, even for a free extension. Google's [registration guide](https://developer.chrome.com/docs/webstore/register) explains enrollment; its [current publisher-role announcement](https://developer.chrome.com/blog/cws-role-expansion-developer-dashboard) confirms the amount. If the owner already has an eligible developer account, that enrollment may already be complete. We have not inspected their Store account.

GitHub unpacked distribution and the implemented context path require no paid search service. A future backend's hosting/inference costs are separate from Store distribution. Under the current no-spending instruction, stay with GitHub until the owner chooses otherwise.

## Does it require the full backend?

No published rule requires a backend specifically. The important requirements are useful functioning behavior, an accurate listing, a clear purpose and policy compliance. Google's [quality policies](https://developer.chrome.com/docs/webstore/program-policies/policies) prohibit broken or nonfunctional items and require basic utility.

My assessment: a working reader for imported analysis can be a legitimate product without generating analysis itself, provided that limitation is prominent and reviewers can exercise it. An empty shell that promises author inference but only displays mock data is a poor submission candidate. Store acceptance remains Google's decision.

The present GitHub beta honestly exposes its example, import/export and frontend status. Before a Store submission, make the supplied-analysis workflow easy for a new reader, remove or clearly scope unfinished controls, and provide reviewer instructions and a usable sample reading. We do not have to wait for every research feature, but ordinary users need a coherent task they can complete.

## Submission preparation

1. Register the intended publisher account, choose its contact identity carefully, and enable [two-step verification](https://developer.chrome.com/blog/policy-update-2sv).
2. Upload a tested Manifest V3 ZIP with `manifest.json` at its root. The current release package has this layout. Increment its numeric version for each new upload; `version_name` can carry a friendly beta label. See [package preparation](https://developer.chrome.com/docs/webstore/prepare) and [manifest versions](https://developer.chrome.com/docs/extensions/reference/manifest/version). If an older 0.4 build has already been uploaded to the same Store item, 0.1 cannot be its update; use a higher numeric version or a new listing.
3. Supply a clear description, category, language, support/contact information and accurate screenshots. Required imagery includes a 128×128 PNG icon, a 440×280 promotional image and at least one 1280×800 or 640×400 screenshot. The README image is repository documentation, not a complete Store asset set. See [image requirements](https://developer.chrome.com/docs/webstore/images).
4. Complete the privacy fields: single purpose, permission reasons, data handling and remote-code declaration. Publish a stable privacy-policy URL; [PRIVACY.md](../PRIVACY.md) describes this beta. Reconcile the dashboard disclosures with the exact submitted behavior, especially webpage text, linked context and any later inference service. See [privacy practices](https://developer.chrome.com/docs/webstore/cws-dashboard-privacy).
5. Select private testers, unlisted or public visibility. Submit for review and allow time for automated/manual checks and possible follow-up. Updates may also need review; do not assume instant delivery. See [review process](https://developer.chrome.com/docs/webstore/review-process).

Do not sideload a `.crx` as a promised one-click Windows/Mac distribution method. Ordinary externally installed extensions on those platforms generally need Store hosting; Developer-mode unpacked installation is the current development route. See [installation mechanisms](https://developer.chrome.com/docs/extensions/how-to/distribute/install-extensions).

## Draft permission explanations

These are starting points for the dashboard, not an assertion of approval.

| Permission | Reason in this build |
| --- | --- |
| `activeTab` | Read the active page after the user invokes ToMpathy |
| `scripting` | Attach the readable-text adapter and linked hover/selection marks |
| `sidePanel` | Display the three-part reader beside the source |
| `storage` | Retain local preferences and browser-session reading state |
| Optional HTTPS hosts | Fetch explicitly selected author context from the granted source origins |

Executable extension code is bundled locally. Retrieved text and imported readings are data, not executable extension code. The ZIP includes the MIT license and bundled dependency notices. Source maps, workstation profiles, local research inputs and QA receipts are excluded.

## Proposed reviewer walkthrough

Open ToMpathy from the toolbar, then Options → How ToMpathy works → Open the example → Open Maker Reader. Hover and hold a sentence, release its green lock, inspect a hierarchy node and expand the reels. Export the reading, import it, and confirm that the saved text and analysis reopen together. The example is fictional and hand-authored; ordinary pages do not receive generated analysis in this build.

Recommended sequence: **GitHub 0.1 beta now → private Store beta after the supplied-analysis workflow and listing assets are ready → public Store release when the advertised reading task is useful and complete.**
