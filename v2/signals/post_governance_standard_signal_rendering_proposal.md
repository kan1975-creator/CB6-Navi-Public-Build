# Post-Governance Signal Rendering Proposal

Status: PROPOSAL_ONLY — NOT IMPLEMENTATION AUTHORITY

## Start condition

This proposal is the first item to evaluate when Signal development resumes **after the
Governance / cross-cutting rule foundation work is complete** and a separate implementation
instruction/approval is given.

During Governance work, keep the existing Signal read-only constraint. This document does
not authorize changes to Signal code, styles, patches, rendering behavior, acquisition, or
workflows.

## Proposed direction

Stop treating the CB6-specific `CB6_SIGNAL` UserMark path as the primary signal display.
Instead, investigate extending CoMaps' stock `traffic_signals` rendering as the primary
display path.

Priority order:

1. Preserve the stock CoMaps traffic-signal position accuracy and visual appearance.
2. Extend visibility to approximately the CB6 200 m / 500 m use cases instead of relying
   on the current stock z19+ normal-map visibility.
3. When the map is panned away from the vehicle, display signals according to the visible
   map/viewport rather than only vehicle-location/forward criteria.
4. Use Overpass or another supplemental source only for signals absent from the MWM, with
   supplemental rendering made as close as practical to the stock CoMaps appearance.

## Existing evidence / context to preserve

- CoMaps MWM data contains `highway=traffic_signals` features and stock rendering.
- CB6 has an independent `CB6_SIGNAL` UserMark path and Overpass acquisition path.
- Device observations showed the stock CoMaps signal presentation was easier to read and
  had preferable positioning compared with the CB6-added presentation.
- Existing MWM diagnostic work may be used for comparison, but it does not itself authorize
  this proposed architecture change.
- Existing Signal 0-count / acquisition / JNI / rendering diagnostics remain evidence and
  must not be discarded merely because this proposal exists.

## Required restart procedure

When Governance is complete and Signal work is explicitly resumed:

1. Re-fetch the then-current canonical HEAD and active Governance authority.
2. Re-inspect the then-current stock CoMaps signal style/rendering and CB6 Signal paths.
3. Compare MWM presence, stock rendering, CB6/Overpass acquisition, and known missing
   locations before replacing any active display path.
4. Produce an impact/rollback/test plan under the active approval rules.
5. Obtain a new explicit implementation approval. Do not treat this proposal document or
   its commit as that approval.
