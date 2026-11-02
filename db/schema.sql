-- CB6 independent issuer ISOLATED CANDIDATE ONLY; not deployed.
-- An audit receipt is NEVER an authenticated approval or GitHub Check PASS.
-- D1 is not a tamper-proof archive or C-05 revocation authority.
CREATE TABLE IF NOT EXISTS webhook_audit (
  delivery_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(trim(delivery_id, ' ' || char(9,10,11,12,13))) > 0),
  -- Reject a replayed signed body even if the unsigned delivery header changes.
  -- Legitimate byte-identical separate deliveries also fail closed.
  body_sha256 TEXT NOT NULL UNIQUE
    CHECK (length(body_sha256) = 64
      AND length(CAST(body_sha256 AS BLOB)) = 64
      AND body_sha256 NOT GLOB '*[^0-9a-f]*'),
  event_name TEXT NOT NULL CHECK (event_name = 'pull_request'),
  action TEXT NOT NULL CHECK (action IN (
    'opened', 'reopened', 'synchronize', 'edited', 'ready_for_review'
  )),
  repository_id INTEGER NOT NULL CHECK (repository_id > 0),
  repository_full_name TEXT NOT NULL
    CHECK (repository_full_name = 'kan1975-creator/CB6-Navi-Public-Build'),
  pr_number INTEGER NOT NULL CHECK (pr_number > 0),
  base_ref TEXT NOT NULL CHECK (base_ref IN ('main', 'cb6-v2-clean')),
  base_sha TEXT NOT NULL
    CHECK (length(base_sha) = 40
      AND length(CAST(base_sha AS BLOB)) = 40
      AND base_sha NOT GLOB '*[^0-9a-f]*'),
  head_sha TEXT NOT NULL
    CHECK (length(head_sha) = 40
      AND length(CAST(head_sha AS BLOB)) = 40
      AND head_sha NOT GLOB '*[^0-9a-f]*'),
  head_repository_full_name TEXT NOT NULL
    CHECK (length(trim(head_repository_full_name)) > 0),
  verdict TEXT NOT NULL DEFAULT 'BLOCKED_UNVERIFIED'
    CHECK (verdict = 'BLOCKED_UNVERIFIED'),
  reason TEXT NOT NULL
    CHECK (reason = 'protected_provenance_and_revocation_not_verified'),
  received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhook_audit_pr_head
  ON webhook_audit (repository_id, pr_number, head_sha, received_at);

-- ISOLATED CANDIDATE ONLY. This is an OPTIONAL FUTURE AUDIT TABLE, NOT
-- an approval database, a tamper-proof ledger, or a revocation authority.
-- It does not change the existing webhook_audit schema or its 38-case trial.
-- A missing revocation hint is NEVER proof that consent remains valid.
CREATE TABLE IF NOT EXISTS github_state_observation_audit (
  delivery_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(trim(delivery_id, ' ' || char(9,10,11,12,13))) > 0),
  repository_id INTEGER NOT NULL CHECK (repository_id > 0),
  pr_number INTEGER NOT NULL CHECK (pr_number > 0),
  event_head_sha TEXT NOT NULL
    CHECK (length(event_head_sha) = 40
      AND length(CAST(event_head_sha AS BLOB)) = 40
      AND event_head_sha NOT GLOB '*[^0-9a-f]*'),
  observed_head_sha TEXT NOT NULL
    CHECK (length(observed_head_sha) = 40
      AND length(CAST(observed_head_sha AS BLOB)) = 40
      AND observed_head_sha NOT GLOB '*[^0-9a-f]*'),
  head_state TEXT NOT NULL CHECK (head_state IN ('MATCH', 'CHANGED')),
  approval_signal TEXT NOT NULL
    CHECK (approval_signal IN ('UNVERIFIED', 'UNTRUSTED_COMMENT_PRESENT')),
  revocation_signal TEXT NOT NULL
    CHECK (revocation_signal IN ('UNVERIFIED', 'POSSIBLE_REVOCATION')),
  gate_verdict TEXT NOT NULL DEFAULT 'BLOCKED_UNVERIFIED'
    CHECK (gate_verdict = 'BLOCKED_UNVERIFIED'),
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- C-07 isolated App diagnostic history ONLY; never an approval or cancellation
-- authority. Existing audit tables and tested D1 constraints are unchanged.
-- No Check may be authorized from rows in this table.
CREATE TABLE IF NOT EXISTS issuer_app_candidate_audit (
  delivery_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(trim(delivery_id, ' ' || char(9,10,11,12,13))) > 0),
  repository_id INTEGER NOT NULL CHECK (repository_id > 0),
  pr_number INTEGER NOT NULL CHECK (pr_number > 0),
  head_sha TEXT NOT NULL
    CHECK (length(head_sha) = 40 AND length(CAST(head_sha AS BLOB)) = 40
      AND head_sha NOT GLOB '*[^0-9a-f]*'),
  app_identity TEXT NOT NULL CHECK (app_identity = 'VERIFIED_GITHUB_API_RESPONSE'),
  revocation_status TEXT NOT NULL CHECK (revocation_status = 'UNVERIFIED'),
  gate_verdict TEXT NOT NULL DEFAULT 'BLOCKED_UNVERIFIED'
    CHECK (gate_verdict = 'BLOCKED_UNVERIFIED'),
  check_run_created INTEGER NOT NULL DEFAULT 0 CHECK (check_run_created = 0),
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Unadopted C-05/C-07 candidate: authenticated GitHub comment events only.
-- Not a protected implementation-start record, a complete cancellation ledger,
-- or proof that an approval is currently valid. Never authorizes PASS.
CREATE TABLE IF NOT EXISTS issuer_decision_event_candidate (
  delivery_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(trim(delivery_id, ' ' || char(9,10,11,12,13))) > 0),
  body_sha256 TEXT NOT NULL UNIQUE
    CHECK (length(body_sha256) = 64 AND body_sha256 NOT GLOB '*[^0-9a-f]*'),
  repository_id INTEGER NOT NULL CHECK (repository_id > 0),
  pr_number INTEGER NOT NULL CHECK (pr_number > 0),
  pr_head_sha TEXT NOT NULL
    CHECK (length(pr_head_sha) = 40 AND pr_head_sha NOT GLOB '*[^0-9a-f]*'),
  basis_head TEXT NOT NULL
    CHECK (length(basis_head) = 40 AND basis_head NOT GLOB '*[^0-9a-f]*'),
  change_id TEXT NOT NULL CHECK (length(change_id) BETWEEN 1 AND 128
    AND change_id NOT GLOB '*[^A-Za-z0-9_.-]*'),
  plan_sha256 TEXT NOT NULL
    CHECK (length(plan_sha256) = 64 AND plan_sha256 NOT GLOB '*[^0-9a-f]*'),
  plan_commit_sha TEXT NOT NULL
    CHECK (length(plan_commit_sha) = 40 AND plan_commit_sha NOT GLOB '*[^0-9a-f]*'),
  decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'REVOKE')),
  github_comment_id INTEGER NOT NULL UNIQUE CHECK (github_comment_id > 0),
  github_actor_id INTEGER NOT NULL CHECK (github_actor_id = 313684924),
  github_created_at TEXT NOT NULL CHECK (length(github_created_at) BETWEEN 20 AND 35),
  gate_verdict TEXT NOT NULL DEFAULT 'BLOCKED_UNVERIFIED'
    CHECK (gate_verdict = 'BLOCKED_UNVERIFIED'),
  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_issuer_decision_candidate_lookup
  ON issuer_decision_event_candidate
  (repository_id, pr_number, change_id, pr_head_sha, captured_at);
-- Fail-closed protection from accidental edits; D1 administrator can remove
-- triggers, so this is NOT tamper-proof custody or independent human authority.
CREATE TRIGGER IF NOT EXISTS issuer_decision_candidate_no_update
BEFORE UPDATE ON issuer_decision_event_candidate
BEGIN SELECT RAISE(ABORT, 'decision_event_immutable'); END;
CREATE TRIGGER IF NOT EXISTS issuer_decision_candidate_no_delete
BEFORE DELETE ON issuer_decision_event_candidate
BEGIN SELECT RAISE(ABORT, 'decision_event_immutable'); END;

-- Protected-start CANDIDATE OBSERVATION. A GitHub comment is not proof of
-- actual implementation start, and D1 is not independent tamper-proof custody.
-- All rows are non-authorizing. Missing rows never imply consent.
CREATE TABLE IF NOT EXISTS issuer_start_observation_candidate (
  delivery_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(trim(delivery_id, ' ' || char(9,10,11,12,13))) > 0),
  body_sha256 TEXT NOT NULL UNIQUE
    CHECK (length(body_sha256) = 64 AND body_sha256 NOT GLOB '*[^0-9a-f]*'),
  repository_id INTEGER NOT NULL CHECK (repository_id > 0),
  pr_number INTEGER NOT NULL CHECK (pr_number > 0),
  pr_head_sha TEXT NOT NULL
    CHECK (length(pr_head_sha) = 40 AND pr_head_sha NOT GLOB '*[^0-9a-f]*'),
  basis_head TEXT NOT NULL
    CHECK (length(basis_head) = 40 AND basis_head NOT GLOB '*[^0-9a-f]*'),
  change_id TEXT NOT NULL CHECK (length(change_id) BETWEEN 1 AND 128
    AND change_id NOT GLOB '*[^A-Za-z0-9_.-]*'),
  plan_sha256 TEXT NOT NULL
    CHECK (length(plan_sha256) = 64 AND plan_sha256 NOT GLOB '*[^0-9a-f]*'),
  plan_commit_sha TEXT NOT NULL
    CHECK (length(plan_commit_sha) = 40 AND plan_commit_sha NOT GLOB '*[^0-9a-f]*'),
  github_comment_id INTEGER NOT NULL UNIQUE CHECK (github_comment_id > 0),
  github_actor_id INTEGER NOT NULL CHECK (github_actor_id = 313684924),
  github_created_at TEXT NOT NULL CHECK (length(github_created_at) BETWEEN 20 AND 35),
  gate_verdict TEXT NOT NULL DEFAULT 'BLOCKED_UNVERIFIED'
    CHECK (gate_verdict = 'BLOCKED_UNVERIFIED'),
  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_issuer_start_candidate_lookup
  ON issuer_start_observation_candidate
  (repository_id, pr_number, change_id, plan_sha256, captured_at);
CREATE TRIGGER IF NOT EXISTS issuer_start_candidate_no_update
BEFORE UPDATE ON issuer_start_observation_candidate
BEGIN SELECT RAISE(ABORT, 'start_observation_immutable'); END;
CREATE TRIGGER IF NOT EXISTS issuer_start_candidate_no_delete
BEFORE DELETE ON issuer_start_observation_candidate
BEGIN SELECT RAISE(ABORT, 'start_observation_immutable'); END;

-- Atomic, conservative contradiction checks. Prevent event arrival order from
-- allowing a late owner approval or a renewed approval after any recorded
-- cancellation for the same plan, including after a PR HEAD change. These
-- triggers do NOT prove completeness of cancellation history.
CREATE TRIGGER IF NOT EXISTS issuer_decision_candidate_revoke_dominates
BEFORE INSERT ON issuer_decision_event_candidate
WHEN NEW.decision = 'APPROVE' AND EXISTS (
  SELECT 1 FROM issuer_decision_event_candidate AS old
   WHERE old.repository_id = NEW.repository_id
     AND old.pr_number = NEW.pr_number
     AND old.change_id = NEW.change_id
     AND old.plan_sha256 = NEW.plan_sha256
     AND old.plan_commit_sha = NEW.plan_commit_sha
     AND old.decision = 'REVOKE'
)
BEGIN SELECT RAISE(ABORT, 'prior_revocation_blocks_reapproval'); END;
CREATE TRIGGER IF NOT EXISTS issuer_decision_candidate_start_precedes_late_approval
BEFORE INSERT ON issuer_decision_event_candidate
WHEN NEW.decision = 'APPROVE' AND EXISTS (
  SELECT 1 FROM issuer_start_observation_candidate AS started
   WHERE started.repository_id = NEW.repository_id
     AND started.pr_number = NEW.pr_number
     AND started.change_id = NEW.change_id
     AND started.plan_sha256 = NEW.plan_sha256
     AND started.plan_commit_sha = NEW.plan_commit_sha
     AND started.github_created_at <= NEW.github_created_at
)
BEGIN SELECT RAISE(ABORT, 'approval_not_before_captured_start'); END;
CREATE TRIGGER IF NOT EXISTS issuer_start_candidate_reject_existing_posthoc_approval
BEFORE INSERT ON issuer_start_observation_candidate
WHEN EXISTS (
  SELECT 1 FROM issuer_decision_event_candidate AS approved
   WHERE approved.repository_id = NEW.repository_id
     AND approved.pr_number = NEW.pr_number
     AND approved.change_id = NEW.change_id
     AND approved.plan_sha256 = NEW.plan_sha256
     AND approved.plan_commit_sha = NEW.plan_commit_sha
     AND approved.decision = 'APPROVE'
     AND approved.github_created_at >= NEW.github_created_at
)
BEGIN SELECT RAISE(ABORT, 'observed_start_not_after_approval'); END;
