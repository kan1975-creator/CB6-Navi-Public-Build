#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ledger=json.loads((ROOT/"v2/gates/cb6_master_progress.json").read_text())
dec=json.loads((ROOT/"v2/gates/active_decisions.json").read_text())
active={x["id"] for x in dec["decisions"] if x.get("status")=="active"}
listed={x["id"] for x in ledger.get("specifications",[])}
if active!=listed:
 print("CB6 MASTER LEDGER FAIL: active specification coverage mismatch",sorted(active-listed),sorted(listed-active)); raise SystemExit(1)
required={"ROOT","METHOD","FEATURES","APK","DEVICE","FINAL"}
stages={x["id"] for x in ledger.get("progress_pipeline",[])}
if stages!=required:
 print("CB6 MASTER LEDGER FAIL: progress pipeline incomplete"); raise SystemExit(1)
for x in ledger["specifications"]:
 if not x.get("spec_key") or not x.get("requirement") or not x.get("evidence"):
  print("CB6 MASTER LEDGER FAIL: specification basis incomplete",x.get("id")); raise SystemExit(1)
for p in ledger.get("reconstruction",[]):
 if not (ROOT/p).exists():
  print("CB6 MASTER LEDGER FAIL: reconstruction path missing",p); raise SystemExit(1)
print("CB6 MASTER DEVELOPMENT LEDGER PASS:",len(active),"active specifications covered")

# Preserve partial/deferred history and prevent accidental restart semantics.
overrides=ledger.get("progress_overrides",{})
for req_id,state in overrides.items():
    if req_id not in active:
        print("CB6 MASTER LEDGER FAIL: progress override is not active",req_id); raise SystemExit(1)
    if state.get("restart_from_zero") is not False:
        print("CB6 MASTER LEDGER FAIL: restart semantics not explicit",req_id); raise SystemExit(1)
    if not state.get("achieved") or not state.get("unresolved") or not state.get("resume_from"):
        print("CB6 MASTER LEDGER FAIL: partial/deferred history incomplete",req_id); raise SystemExit(1)
    if state.get("implementation_state")=="DEFERRED_WITH_EVIDENCE" and not state.get("deferred_reason"):
        print("CB6 MASTER LEDGER FAIL: deferred reason missing",req_id); raise SystemExit(1)
print("CB6 MASTER RESUME STATE PASS:",len(overrides),"tracked partial/deferred requirements")

# Master source-inventory closure: no required authority/evidence source may silently disappear.
inventory=ledger.get("source_inventory",[])
for item in inventory:
    p=item.get("path","")
    if not p:
        print("CB6 MASTER LEDGER FAIL: empty source inventory path"); raise SystemExit(1)
    if p.endswith(("features","research_records","impact_records")):
        if not (ROOT/p).is_dir():
            print("CB6 MASTER LEDGER FAIL: source directory missing",p); raise SystemExit(1)
    elif not (ROOT/p).exists():
        print("CB6 MASTER LEDGER FAIL: source inventory file missing",p); raise SystemExit(1)
required_failure_ids={"STALE_VALIDATOR","ESCAPED_NEWLINE","LATER_PATCH_RESTORE","USERMARK_GROUP_MISMATCH","GROUP_REPLACEMENT","BUILD_NOT_FEATURE_SUCCESS","MWM_DUPLICATED_BY_NETWORK","CONTEXT_CONTINUITY","REPEATED_STALE_AUDIT"}
actual_failure_ids={x.get("id") for x in ledger.get("known_failure_classes",[])}
if required_failure_ids-actual_failure_ids:
    print("CB6 MASTER LEDGER FAIL: known failure coverage missing",sorted(required_failure_ids-actual_failure_ids)); raise SystemExit(1)
if not ledger.get("completeness",{}).get("zero_omission_required"):
    print("CB6 MASTER LEDGER FAIL: zero-omission rule missing"); raise SystemExit(1)
print("CB6 MASTER SOURCE/HISTORY COVERAGE PASS")

# Explicit development-order coverage: prohibit ambiguous catch-all buckets.
order_rows=ledger.get("development_order",[])
if len(order_rows)!=22 or [x.get("order") for x in order_rows] != list(range(22)):
    print("CB6 MASTER LEDGER FAIL: development order must be explicit contiguous 0..21"); raise SystemExit(1)
if any(x.get("id") in {"OTHER_POI_AND_CONTROLS","OTHER_FEATURES","MISC"} for x in order_rows):
    print("CB6 MASTER LEDGER FAIL: catch-all development bucket forbidden"); raise SystemExit(1)
mapped=set()
for row in order_rows:
    mapped.update(row.get("requirements",[]))
# PROC requirements govern the pipeline rather than one feature row.
required_order_ids={x["id"] for x in ledger.get("specifications",[]) if not x["id"].startswith("PROC-")}
missing_order=required_order_ids-mapped
if missing_order:
    print("CB6 MASTER LEDGER FAIL: active product requirements missing from development order",sorted(missing_order)); raise SystemExit(1)
print("CB6 MASTER DEVELOPMENT ORDER PASS:",len(order_rows),"explicit stages")

# Atomic specification registry is mandatory; broad parent requirements are not sufficient.
atomic_path=ROOT/"v2/gates/atomic_requirements.json"
atomic=json.loads(atomic_path.read_text())
items=atomic.get("requirements",[])
ids=[x.get("id") for x in items]
if len(ids)!=len(set(ids)) or any(not x for x in ids):
    print("CB6 MASTER LEDGER FAIL: atomic requirement IDs invalid/duplicated"); raise SystemExit(1)
if len(items)<367:
    print("CB6 MASTER LEDGER FAIL: atomic specification registry unexpectedly incomplete",len(items)); raise SystemExit(1)
required_groups={"PROCESS","SIGNAL","CONVENIENCE","MAP_LOCATION_UI","LABEL_POI","STOP_SEARCH_LIFECYCLE","ROUTING_FAVORITES_PRODUCT"}
actual_groups={x.get("group") for x in items}
if required_groups-actual_groups:
    print("CB6 MASTER LEDGER FAIL: atomic requirement groups missing",sorted(required_groups-actual_groups)); raise SystemExit(1)
if ledger.get("atomic_requirement_registry",{}).get("path")!="v2/gates/atomic_requirements.json":
    print("CB6 MASTER LEDGER FAIL: atomic registry not bound to Master"); raise SystemExit(1)
if atomic.get("status")!="RECONSTRUCTION_IN_PROGRESS" and atomic.get("status")!="VERIFIED_COMPLETE":
    print("CB6 MASTER LEDGER FAIL: invalid atomic reconstruction state"); raise SystemExit(1)
print("CB6 MASTER ATOMIC SPEC COVERAGE PASS:",len(items),"atomic requirements registered")

# Atomic traceability closure: each detailed requirement must have explicit order + active parent + evidence + acceptance.
active_ids={x["id"] for x in active_decisions.get("decisions",[]) if x.get("status")=="active"}
for x in items:
    if not isinstance(x.get("development_order"),int) or not x.get("development_stage"):
        print("CB6 MASTER LEDGER FAIL: atomic development order missing",x.get("id")); raise SystemExit(1)
    parents=set(x.get("parent_active_decisions",[]))
    if not parents or not parents.issubset(active_ids):
        print("CB6 MASTER LEDGER FAIL: atomic authority mapping invalid",x.get("id"),sorted(parents-active_ids)); raise SystemExit(1)
    if not x.get("evidence") or not x.get("acceptance"):
        print("CB6 MASTER LEDGER FAIL: atomic evidence/acceptance missing",x.get("id")); raise SystemExit(1)
    if x.get("restart_from_zero") is not False or not x.get("resume_from"):
        print("CB6 MASTER LEDGER FAIL: atomic resume semantics missing",x.get("id")); raise SystemExit(1)
print("CB6 MASTER ATOMIC TRACEABILITY PASS:",len(items),"requirements mapped")

# Every atomic requirement exposes the complete development pipeline; evidence-bearing states require evidence.
pipeline_names=["research","impact","implementation","audit","positive_test","destructive_test","feature_gate","apk","device"]
for x in items:
    p=x.get("pipeline",{})
    if list(p.keys())!=pipeline_names:
        print("CB6 MASTER LEDGER FAIL: atomic pipeline incomplete/order mismatch",x.get("id")); raise SystemExit(1)
    for name in pipeline_names:
        st=p[name].get("state")
        ev=p[name].get("evidence",[])
        if not st:
            print("CB6 MASTER LEDGER FAIL: empty pipeline state",x.get("id"),name); raise SystemExit(1)
        if st in {"RECORDED","EXISTS_REQUIRES_RECERTIFICATION","IN_PROGRESS_REQUIRES_RECERTIFICATION"} and not ev:
            print("CB6 MASTER LEDGER FAIL: evidence-bearing pipeline state lacks evidence",x.get("id"),name); raise SystemExit(1)
print("CB6 MASTER PIPELINE COVERAGE PASS:",len(items),"atomic requirements x",len(pipeline_names),"stages")

# Zero-omission audit anchors from canonical/historical sources.
required_atomic_ids={"SIG-REFRESH-45","SIG-RETRY-12","SIG-MOVE-250","SIG-RADIUS-3000","SIG-RETENTION","CV-ZOOM-1KM","CV-ZOOM-500M","CV-ZOOM-200M","CV-GROUP","PROC-RENDER-CROSSCUT","PROC-JNI-CROSSCUT","PROC-PATCH-ORDER","PROC-DATASOURCE-CROSSCUT","CV-METADATA-DIAGNOSTIC","MAP-RAW-SEPARATE","MAP-LOW-SPEED-HYSTERESIS","BASE-STOCK-SEARCH","BASE-STOCK-HISTORY","BASE-STOCK-BOOKMARKS","BASE-STOCK-DOWNLOADS","BASE-STOCK-POI"}
missing_atomic=required_atomic_ids-set(ids)
if missing_atomic:
    print("CB6 MASTER LEDGER FAIL: audited detailed specifications disappeared",sorted(missing_atomic)); raise SystemExit(1)
print("CB6 MASTER ZERO-OMISSION AUDIT ANCHORS PASS:",len(required_atomic_ids))

# Current-spec and process-policy anchors found by zero-omission audit must remain atomic.
required_policy_atomic={"PROC-NO-LINE-FIX","PROC-OBSOLETE-SWEEP","PROC-FROZEN-REGRESSION","PROC-FINAL-GENERATED","PROC-MINIMIZE-BUILDS","PROC-NATIVE-FIRST","PROC-RESPONSIBILITY-OWNERSHIP","PROC-NO-STALE-VALIDATOR-FIX","PROC-AUTOMATION-NOT-PROGRESS","PROC-DURABLE-CHECKPOINT","PROC-FAILURE-LOOP","PROC-DOC-MAINT","PROC-SINGLE-SOURCE","PROC-BEHAVIORAL-FREEZE","PROC-APK-MINIMAL"}
required_signal_spec_atomic={"SIG-MAX-1400","SIG-FORWARD-450","SIG-CONE-45","SIG-CLUSTER-30","SIG-DEDUP-12","SIG-CACHE-24H","SIG-OSM-HIGHWAY","SIG-OSM-CROSSING","SIG-OSM-SET","SIG-OSM-NODE","SIG-OSM-WAY","SIG-OSM-RELATION","SIG-SUPPLEMENT","SIG-SVG-XS","SIG-SVG-S","SIG-SVG-M","SIG-SVG-L","SIG-Z14-XS","SIG-Z15-XS","SIG-FWD-Z17-M","SIG-FWD-Z19-L"}
for required_set,label in [(required_policy_atomic,"process policy"),(required_signal_spec_atomic,"current signal spec")]:
    missing=required_set-set(ids)
    if missing:
        print("CB6 MASTER LEDGER FAIL:",label,"atomic specifications disappeared",sorted(missing)); raise SystemExit(1)
print("CB6 MASTER POLICY/CURRENT-SPEC ATOMIC PASS:",len(required_policy_atomic)+len(required_signal_spec_atomic))

# Root authority/reconstruction invariants discovered by zero-omission audit are mandatory.
required_root_atomic={"PROC-EVIDENCE-STATUS","PROC-CROSS-PROJECT-REVALIDATE","PROC-AUTHORITY-ONLY","PROC-FORBIDDEN-HISTORICAL","PROC-ROOT-RECONSTRUCT","PROC-UNKNOWN-BLOCK","PROC-NO-SELF-COMPLETE","PROC-NO-BYPASS","PROC-METHOD-INVALIDATE","PROC-CLAIM-EVIDENCE","PROC-CLOSED-TRACE","PROC-ROOT-BLOCK-LOWER","PROC-ROOT-NO-SELF-CERT","PROC-CONTEXT-NEWCHAT","PROC-CONTEXT-TIME","PROC-CONTEXT-FEATURESWITCH","PROC-CONTEXT-HANDOFF","PROC-CONTEXT-OPERATOR","PROC-CONTEXT-PARTIAL","PROC-CONTEXT-NOCONV","PROC-RECON-AUTH","PROC-RECON-REQ","PROC-RECON-METHOD","PROC-RECON-FEATURE","PROC-RECON-PENDING","PROC-RECON-FAILURES","PROC-RECON-RESEARCH","PROC-RECON-IMPACT","PROC-RECON-VERIFY","PROC-RECON-APK","PROC-RECON-DEVICE"}
missing_root_atomic=required_root_atomic-set(ids)
if missing_root_atomic:
    print("CB6 MASTER LEDGER FAIL: root/reconstruction atomic specifications disappeared",sorted(missing_root_atomic)); raise SystemExit(1)
if ledger.get("atomic_requirement_registry",{}).get("current_count") != len(items):
    print("CB6 MASTER LEDGER FAIL: Master atomic count stale",ledger.get("atomic_requirement_registry",{}).get("current_count"),len(items)); raise SystemExit(1)
print("CB6 MASTER ROOT/RECONSTRUCTION ATOMIC PASS:",len(required_root_atomic))

# Execution-gate and pinned-architecture zero-omission anchors.
required_exec_arch={"PROC-EVIDENCE-CONSUME","PROC-UNKNOWN-OPEN","PROC-STATE-MACHINE","PROC-FAIL-EARLIEST","PROC-CHANGE-PROPAGATION","PROC-WORKFLOW-GATE-FIRST","PROC-FEATURE-IDENTITY","PROC-LEGACY-NOT-V2","PROC-RETIRED-CROSSCHECK","PROC-EXTERNAL-REFRESH","PROC-OBJECTIVE-PROGRESS","PROC-GENERATED-HASH","PROC-ALL-V2-WORKFLOWS-SCAN","ARCH-POI-PIPELINE","ARCH-POI-NOTVISIBLE","ARCH-STOCK-VS-USERMARK","ARCH-SYMBOL-PIPELINE","ARCH-FRAMEWORK-ROOT","ARCH-CONVENIENCE-TYPE","ARCH-BRAND-META","ARCH-VEHICLE-CV-TEXT","ARCH-EXISTING-MWM-COMPAT","ARCH-SEARCH-STOCK","ARCH-ROUTING-NATIVE","ARCH-BOOKMARK-NATIVE","ARCH-LOCATION-SHARED","ARCH-CONVENIENCE-DIAGNOSTIC","ARCH-CONVENIENCE-REPRESENTATIVE","ARCH-CONVENIENCE-DECISION","ARCH-NO-WHOLESALE-GENERATOR"}
missing_exec_arch=required_exec_arch-set(ids)
if missing_exec_arch:
    print("CB6 MASTER LEDGER FAIL: execution/architecture atomic specifications disappeared",sorted(missing_exec_arch)); raise SystemExit(1)
print("CB6 MASTER EXECUTION/ARCHITECTURE ATOMIC PASS:",len(required_exec_arch))

# Development-method/domain/traceability zero-omission anchors.
required_method_atomic={"PROC-METHOD-GATES","PROC-METHOD-REGRESSIONS","PROC-AUDIT-SPECIFIC-PROOF","PROC-IMPACT-COVERS-AUDIT","PROC-INTERNAL-ANALYSIS","PROC-WEB-WHEN-MATERIAL","PROC-WEB-NOT-AUTH","PROC-PINNED-REVALIDATE","PROC-RESEARCH-BEFORE-IMPL","PROC-NO-UNRECORDED-SPEC","PROC-CHANGE-REASON","PROC-NO-UNRELATED-CHANGE","PROC-PINNED-EVERY-FEATURE","PROC-PINNED-PATHS","PROC-PINNED-FINDINGS","PROC-DOMAIN-COVERAGE","PROC-COMPLETION-METHOD","PROC-COMPLETION-BUILD","PROC-COMPLETION-BEHAVIOR","PROC-DOMAIN-AUDITS","PROC-DOMAIN-TESTS","PROC-DOMAIN-WORKFLOW","PROC-DOMAIN-RENDERER","PROC-DOMAIN-SYMBOLS","PROC-DOMAIN-CACHE","PROC-DOMAIN-DATASOURCE","PROC-DOMAIN-LIFECYCLE","PROC-DOMAIN-REALDEVICE","PROC-DOMAIN-GATES","PROC-DOMAIN-DESIGN","PROC-TRACE-CONSUMED"}
missing_method_atomic=required_method_atomic-set(ids)
if missing_method_atomic:
    print("CB6 MASTER LEDGER FAIL: method/domain atomic specifications disappeared",sorted(missing_method_atomic)); raise SystemExit(1)
print("CB6 MASTER METHOD/DOMAIN ATOMIC PASS:",len(required_method_atomic))

# Project-state, method-proof and feature/research-contract zero-omission anchors.
required_contract_atomic={"PROC-PROJECT-BRANCH","PROC-PROJECT-DESIGN-STATE","PROC-CANONICAL-DESIGN","PROC-RETIRED-DESIGN-PATH","PROC-METHOD-CURRENT-INVALID","PROC-METHOD-SAMEHEAD","PROC-METHOD-SEMANTIC-CLOSURE","PROC-METHOD-HISTORICAL-REPLAY","PROC-METHOD-INDEPENDENT","PROC-METHOD-EXTENSIBILITY","PROC-METHOD-ARTIFACT-CHAIN","PROC-METHOD-DEVICE-CHAIN","PROC-ROOT-PROOF-EXEC","PROC-ROOT-CONTEXT-PROOF","PROC-ROOT-MISSING-PROOF","PROC-ROOT-PERMISSION-PROOF","PROC-ROOT-HISTORY-PROOF","PROC-ROOT-UNKNOWN-PROOF","PROC-ROOT-INDEPENDENT-PROOF","PROC-ROOT-EXTENSIBILITY-PROOF","PROC-ROOT-ARTIFACT-PROOF","PROC-ROOT-DEVICE-PROOF","PROC-FEATURE-CONTRACT","PROC-FEATURE-REPO-SWEEP","PROC-FEATURE-DOMAIN-VERIFY","PROC-FEATURE-DEVICE-PENDING","PROC-RESEARCH-STATUS","PROC-RESEARCH-INTERNAL-PATHS","PROC-RESEARCH-APPLICABILITY","PROC-RESEARCH-SOURCES-FINDINGS","PROC-RESEARCH-AUTH-CLASS","PROC-RESEARCH-TEMPORAL","PROC-RESEARCH-DOMAIN-MAP"}
missing_contract_atomic=required_contract_atomic-set(ids)
if missing_contract_atomic:
    print("CB6 MASTER LEDGER FAIL: project/method/template atomic specifications disappeared",sorted(missing_contract_atomic)); raise SystemExit(1)
print("CB6 MASTER PROJECT/METHOD/TEMPLATE ATOMIC PASS:",len(required_contract_atomic))

# Active-decision acceptance and current feature-contract zero-omission anchors.
required_feature_atomic={"PROC-ACTIVE-NO-DISAPPEAR","PROC-SUPERSEDED-NO-AUTH","PROC-BUILD-GATE-DESIGN","SIG-UPDATE-INSTALL","BASE-UPSTREAM-OWNERSHIP","MAP-NORTH-LOCK","HUD-ORIENTATION","STOP-INDEPENDENT","VOICE-SAFE-FALLBACK","ROUTE-PROVE-TOLL","TOLL-SOURCE-VERSION","FAV-TRANSPORT-BOUNDARY","LIFE-STATE-TRANSITIONS","UI-CURRENT-TOUCH","MAJOR-POI-CATEGORIES","TOLL-PASSENGER","TOLL-ZERO","SEARCH-SHOWMAP-NORMALIZE","ORIENT-AUTO","ORIENT-PORTRAIT","ORIENT-LANDSCAPE","SEARCH-HISTORY-DELETE","SCOPE-NO-SILENT-CHANGE","SIG-APK-ARM64","SIG-APK-IDENTITY","SIG-APK-SIGNATURE","CV-DIAG-NO-NETWORK-FAB","CV-DEVICE-DETECTION","CV-DEVICE-BRANDS","CV-DEVICE-NO-TEXT","CV-DEVICE-OFFLINE","CV-RENDERER-OPEN","CV-SYMBOLS-OPEN","CV-OFFLINE-OPEN"}
missing_feature_atomic=required_feature_atomic-set(ids)
if missing_feature_atomic:
    print("CB6 MASTER LEDGER FAIL: active-decision/feature atomic specifications disappeared",sorted(missing_feature_atomic)); raise SystemExit(1)
print("CB6 MASTER ACTIVE-DECISION/FEATURE ATOMIC PASS:",len(required_feature_atomic))

required_research_atomic={"SIG-RESEARCH-FRAMEWORK","SIG-RESEARCH-USERMARK","SIG-RESEARCH-JNI","SIG-EXTERNAL-SEPARATE","SIG-CACHE-OUTSIDE-UPSTREAM","CV-DATASOURCE-PUBLIC","CV-FEATURE-METADATA","CV-CLASSIFY-PRIORITY","CV-CLASSIFY-DETERMINISTIC","CV-DIAG-POSTRENDER","CV-DIAG-NOT-RENDERER","CV-NO-PERIODIC-OVERPASS","CV-NO-FABRICATED-MARKS","CV-PRESERVE-SIGNALS","CV-HISTORICAL-SCRIPTS-REVIEW","CV-MWM-PRIMARY","CV-BRAND-UPSTREAM-DATA","PROC-IMPACT-REVIEWED-PATHS","PROC-IMPACT-DECISION","PROC-RESEARCH-PINNED-SHA","PROC-RESEARCH-FINDINGS-CONCRETE","PROC-RESEARCH-DOMAIN-FINDINGS","PROC-RESEARCH-WEB-PROVENANCE","PROC-RESEARCH-TIME-PROOF"}
missing_research_atomic=required_research_atomic-set(ids)
if missing_research_atomic:
    print("CB6 MASTER LEDGER FAIL: research/impact atomic specifications disappeared",sorted(missing_research_atomic)); raise SystemExit(1)
print("CB6 MASTER RESEARCH/IMPACT ATOMIC PASS:",len(required_research_atomic))

required_authority_atomic={"PROC-EVIDENCE-CROSSPROJECT","PROC-EVIDENCE-FROZEN-LINK","PROC-EVIDENCE-BASELINE-HIST","PROC-EVIDENCE-OLD-DESIGN-RETIRED","PROC-EVIDENCE-OLD-MODULES-RETIRED","PROC-EVIDENCE-OLD-POI-RETIRED","PROC-EVIDENCE-OLD-SIGNAL-HIST","PROC-EVIDENCE-HANDOVER-HIST","PROC-AUTH-ALLOWLIST","PROC-AUTH-FORBIDDEN-PHRASES","PROC-RECON-AUTHORITY","PROC-RECON-REQUIREMENTS","PROC-RECON-METHOD","PROC-RECON-FEATURES","PROC-RECON-PENDING","PROC-RECON-FAILURES","PROC-RECON-RESEARCH","PROC-RECON-IMPACT","PROC-RECON-VERIFY","PROC-RECON-APK","PROC-RECON-DEVICE","PROC-INC-RETIRED-REPROMOTION","PROC-INC-AUDIT-NOPROOF","PROC-INC-STALE-CONVENIENCE","PROC-INC-STALE-SIGNAL","PROC-INC-PREFLIGHT","PROC-INC-RESEARCH-SCOPE","PROC-INC-SYNTAX","PROC-INC-APK-ASSUMPTION","PROC-INC-CONTEXT-LOSS","PROC-STAGE-CONSISTENCY","PROC-CERT-HEAD-FRESHNESS"}
missing_authority_atomic=required_authority_atomic-set(ids)
if missing_authority_atomic:
    print("CB6 MASTER LEDGER FAIL: authority/reconstruction/incident atomic specifications disappeared",sorted(missing_authority_atomic)); raise SystemExit(1)
print("CB6 MASTER AUTHORITY/RECONSTRUCTION/INCIDENT ATOMIC PASS:",len(required_authority_atomic))
