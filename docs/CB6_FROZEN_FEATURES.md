# CB6 Frozen / Accepted Features

"Frozen" means real-device accepted. Do not change implementation/behavior as collateral damage. If a future requirement genuinely needs interaction with a frozen feature, prove regression safety first.

## Traffic signals — FROZEN

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
- Run #65 established accepted scale policy.
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
