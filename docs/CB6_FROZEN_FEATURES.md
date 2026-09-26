# CB6 Frozen / Accepted Features

"Frozen" means real-device accepted. Do not change implementation/behavior as collateral damage. If a future requirement genuinely needs interaction with a frozen feature, prove regression safety first.

## Traffic signals — HISTORICAL ACCEPTANCE EVIDENCE; LATER REQUIREMENTS MAY SUPERSEDE

User accepted: "信号機はこれでok".

Behavior baseline:
- visible at ~200 m with established standard size;
- ~500 m uses smaller/thinner XS presentation;
- no need at 1 km;
- forward/near scaling retained;
- acquisition policy: 45 s refresh, 12 s retry, 250 m movement, 3000 m near radius;
- broad retention cap and near-first policy retained;
- renderer behavior proven on CB6 real device.

Historical reference:
- Run #65 established the historical accepted scale policy. It is evidence, not current authority where the active Requirement Registry or `v2/gates/current_spec.json` records a later user-approved change. In particular, `SIG-200M-001` supersedes the old 200m size expectation.
- Later real-device checks continued to show signals correctly.

Regression rule:
- Convenience/POI work must not rewrite signal query, scheduler, signal symbol mapping or accepted zoom sizes.
- If a final patch touches signal-related source unexpectedly, stop before build and inspect.

## CoMaps standard functionality — PRESERVE

CB6 is an extension, not a replacement. Preserve standard:
- route options unless explicitly extended;
- search result selection and routing;
- search history;
- favorites/bookmarks;
- map downloads/offline maps;
- stock POIs unless a CB6 specification intentionally changes their presentation.

## Current convenience status — NOT FROZEN

Specification:
- brand icon only; no convenience-store text;
- 1 km very small, 500 m small, 200 m standard;
- 7-Eleven=1, FamilyMart=2, Lawson=3, Seicomart=4, MyBasket=5, generic=6, Ministop=8, Daily Yamazaki=9.

Run #91 built successfully but real-device test showed no CB6 convenience icon, including diagnostic probe. Stock CoMaps "セブン-イレブン" text remained visible. This proves build success was not feature success.

Current root-cause correction under test: dedicated convenience UserMark must belong to `CB6_DRIVING`, not default `DEBUG_MARK`.

## V2 Gate 1 migration — NOT YET FROZEN

The Run #65 feature above remains historical real-device evidence, not current behavioral authority for clauses superseded by active requirements. `active_decisions.json` plus `current_spec.json` own the current signal expectation. `v2/signals` ports its constants/resources into isolated signal ownership. No V2 real-device acceptance has been claimed. Build evidence must come from `CB6 V2 Gate 1 Signals`, then the physical CB6 checklist in `v2/signals/README.md` must pass before changing this status.
