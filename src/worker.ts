/**
 * CB6 independent-check issuer, ISOLATED CANDIDATE ONLY.
 * Authenticates limited GitHub PR webhook receipts for D1 audit.
 * Default webhook never issues Checks, authenticates approval, or returns PASS.
 * An isolated, opt-in exported helper may send negative-only Checks.
 * A signed webhook is NOT proof of current PR HEAD, prior implementation
 * approval, protected provenance, or non-revocation; all remain BLOCKED.
 * Requires a separately approved deployment and independent owner control.
 */

type SqlRun = {
  success?: boolean;
  meta?: { changes?: number };
};

type D1Binding = {
  prepare(query: string): {
    bind(...values: Array<string | number>): { run(): Promise<SqlRun> };
  };
};

interface Env {
  DB: D1Binding;
  GITHUB_WEBHOOK_SECRET: string; // Provision only by the human owner; never in source.
  EXPECTED_REPOSITORY: string;
  EXPECTED_REPOSITORY_ID: string;
  ENABLE_DECISION_CAPTURE?: string; // Explicit opt-in, NEVER authorizes Check PASS.
}

type JsonObject = Record<string, unknown>;
const MAX_PAYLOAD_BYTES = 256 * 1024;
const APPROVED_PR_ACTIONS = new Set([
  "opened", "reopened", "synchronize", "edited", "ready_for_review",
]);
const APPROVED_BASE_REFS = new Set(["main", "cb6-v2-clean"]);
const SHA40 = /^[0-9a-f]{40}$/;
const DELIVERY_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function object(value: unknown): JsonObject | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonObject) : null;
}

function positiveSafeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}

function reply(status: number, reason: string): Response {
  return new Response(JSON.stringify({
    receipt: reason,
    gate_verdict: "BLOCKED_UNVERIFIED",
    check_run_created: false,
  }), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

async function authenticGitHubSignature(
  body: Uint8Array, supplied: string | null, secret: string,
): Promise<boolean> {
  if (!supplied || !/^sha256=[0-9a-f]{64}$/.test(supplied) || !secret) {
    return false;
  }
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["verify"],
  );
  const hex = supplied.slice("sha256=".length);
  const tag = new Uint8Array(32);
  for (let i = 0; i < tag.length; i++) {
    tag[i] = Number.parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return crypto.subtle.verify("HMAC", key, tag, body);
}

// Never buffer an unbounded request body: stop reading once the fixed cap is hit.
async function boundedRequestBytes(request: Request): Promise<Uint8Array> {
  if (!request.body) throw new Error("unreadable_body");
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value) throw new Error("unreadable_body");
      if (value.byteLength > MAX_PAYLOAD_BYTES - total) {
        await reader.cancel().catch(() => undefined);
        throw new RangeError("payload_limit");
      }
      total += value.byteLength;
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  if (total === 0) throw new RangeError("payload_limit");
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return bytes;
}

function prReceipt(payload: JsonObject, env: Env) {
  const repo = object(payload.repository);
  const pr = object(payload.pull_request);
  const base = object(pr?.base);
  const head = object(pr?.head);
  const baseRepo = object(base?.repo);
  const headRepo = object(head?.repo);
  const expectedId = Number(env.EXPECTED_REPOSITORY_ID);
  const repoId = repo?.id;
  const prNumber = payload.number;
  const baseSha = base?.sha;
  const headSha = head?.sha;
  const baseRef = base?.ref;
  const action = payload.action;

  if (
    env.EXPECTED_REPOSITORY !== "kan1975-creator/CB6-Navi-Public-Build" ||
    !positiveSafeInteger(expectedId) ||
    !positiveSafeInteger(repoId) || repoId !== expectedId ||
    repo?.full_name !== env.EXPECTED_REPOSITORY ||
    !positiveSafeInteger(baseRepo?.id) || baseRepo.id !== expectedId ||
    !positiveSafeInteger(prNumber) || pr?.number !== prNumber ||
    typeof action !== "string" || !APPROVED_PR_ACTIONS.has(action) ||
    typeof baseRef !== "string" || !APPROVED_BASE_REFS.has(baseRef) ||
    typeof baseSha !== "string" || !SHA40.test(baseSha) ||
    typeof headSha !== "string" || !SHA40.test(headSha) ||
    typeof headRepo?.full_name !== "string" || !headRepo.full_name
  ) {
    return null;
  }
  return {
    repoId, repoFullName: env.EXPECTED_REPOSITORY, prNumber,
    baseRef, baseSha, headSha,
    headRepoFullName: headRepo.full_name, action,
  };
}

// ISOLATED CANDIDATE: read-only observations for a future independently
// protected issuer. This function is NOT an approval gate and is NOT wired
// to the webhook handler until external provenance and revocation authority
// exist. Never infer "not revoked" from a GitHub comment search.
type ReadOnlyObservation = {
  observedHeadSha: string;
  headState: "MATCH" | "CHANGED";
  approvalSignal: "UNVERIFIED" | "UNTRUSTED_COMMENT_PRESENT";
  revocationSignal: "UNVERIFIED" | "POSSIBLE_REVOCATION";
  gateVerdict: "BLOCKED_UNVERIFIED";
};

type CandidatePrIdentity = {
  repoId: number;
  repoFullName: string;
  prNumber: number;
  baseRef: string;
  baseSha: string;
  headSha: string;
  headRepoFullName: string;
};

const GITHUB_API =
  "https://api.github.com/repos/kan1975-creator/CB6-Navi-Public-Build";
// This ID comes from the existing approval contract. It is an identity filter,
// NOT an independent trust anchor or evidence of revocation authority.
const CANDIDATE_APPROVER_ID = 313684924;
const APPROVAL_COMMENT = /^CB6-APPROVE [A-Za-z0-9_.-]+ [0-9a-f]{64} [0-9a-f]{40}$/;
const MAX_COMMENT_PAGES = 5;

type ReadOnlyFetch = typeof fetch;

async function githubPublicRead(
  endpoint: string, read: ReadOnlyFetch,
): Promise<unknown> {
  // Every endpoint is constructed from fixed literal paths and validated
  // integer PR numbers. No URL or host is taken from a webhook payload.
  const response = await read(GITHUB_API + endpoint, {
    method: "GET",
    headers: { accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28" },
    redirect: "error",
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error("github_api_unavailable");
  return response.json();
}

/**
 * Observe the current PR HEAD and *signals* from GitHub, independently of
 * webhook body fields. Public API observations are NOT protected provenance.
 * No candidate result can authorize approval or establish non-revocation.
 * Absence of a revocation signal MUST remain UNVERIFIED.
 * Call only on an isolated candidate after separate authorization; the
 * currently deployed/legacy webhook audit path is deliberately unchanged.
 */
export async function observeGitHubStateCandidate(
  identity: CandidatePrIdentity, read: ReadOnlyFetch = fetch,
): Promise<ReadOnlyObservation> {
  if (!identity || !positiveSafeInteger(identity.repoId) ||
      identity.repoFullName !== "kan1975-creator/CB6-Navi-Public-Build" ||
      !positiveSafeInteger(identity.prNumber) ||
      !APPROVED_BASE_REFS.has(identity.baseRef) ||
      !SHA40.test(identity.baseSha) || !SHA40.test(identity.headSha) ||
      typeof identity.headRepoFullName !== "string" ||
      !identity.headRepoFullName.trim()) {
    throw new Error("invalid_candidate_identity");
  }
  const raw = await githubPublicRead("/pulls/" + identity.prNumber, read);
  const pr = object(raw);
  const base = object(pr?.base);
  const head = object(pr?.head);
  const baseRepo = object(base?.repo);
  const headRepo = object(head?.repo);
  const observedHead = head?.sha;
  if (!pr || pr.number !== identity.prNumber || pr.state !== "open" ||
      !SHA40.test(String(observedHead ?? "")) ||
      base?.ref !== identity.baseRef || base?.sha !== identity.baseSha ||
      baseRepo?.full_name !== identity.repoFullName ||
      baseRepo?.id !== identity.repoId ||
      headRepo?.full_name !== identity.headRepoFullName) {
    throw new Error("github_pr_identity_mismatch");
  }
  const headState = observedHead === identity.headSha ? "MATCH" : "CHANGED";
  // Candidate signals are deliberately unauthenticated and cannot bypass a
  // canceled approval, even if every publicly visible comment appears valid.
  let approvalSignal: ReadOnlyObservation["approvalSignal"] = "UNVERIFIED";
  let revocationSignal: ReadOnlyObservation["revocationSignal"] = "UNVERIFIED";
  let complete = false;
  for (let page = 1; page <= MAX_COMMENT_PAGES; page++) {
    const rawComments = await githubPublicRead(
      "/issues/" + identity.prNumber + "/comments?per_page=100&page=" + page, read,
    );
    if (!Array.isArray(rawComments) || rawComments.length > 100) {
      throw new Error("github_comments_unavailable");
    }
    for (const entry of rawComments) {
      const comment = object(entry);
      const actor = object(comment?.user);
      if (!comment || typeof comment.body !== "string" ||
          !positiveSafeInteger(comment.id) || !actor ||
          !positiveSafeInteger(actor.id) ||
          typeof comment.created_at !== "string" ||
          typeof comment.updated_at !== "string") {
        throw new Error("github_comment_malformed");
      }
      if (actor.id !== CANDIDATE_APPROVER_ID) continue;
      if (APPROVAL_COMMENT.test(comment.body.trim()) &&
          comment.created_at === comment.updated_at) {
        approvalSignal = "UNTRUSTED_COMMENT_PRESENT";
      }
      // This is only a hint to BLOCK; the existing contract does not define
      // an authoritative CB6-REVOKE syntax or guarantee that all cancellations
      // are represented by surviving GitHub comments.
      if (comment.body.trim().startsWith("CB6-REVOKE ")) {
        revocationSignal = "POSSIBLE_REVOCATION";
      }
    }
    if (rawComments.length < 100) { complete = true; break; }
  }
  if (!complete) throw new Error("github_comments_incomplete");
  // A second current HEAD read detects PR changes during comment enumeration.
  const latestRaw = await githubPublicRead("/pulls/" + identity.prNumber, read);
  const latest = object(latestRaw);
  if (!latest || object(latest.head)?.sha !== observedHead ||
      object(latest.base)?.sha !== identity.baseSha ||
      latest.state !== "open") {
    throw new Error("github_pr_changed_during_observation");
  }
  return {
    observedHeadSha: observedHead as string, headState,
    approvalSignal, revocationSignal, gateVerdict: "BLOCKED_UNVERIFIED",
  };
}

// C-07 isolated App connector candidate. This is NOT an authorization source.
// It authenticates an independently configured GitHub App and obtains fresh
// repository state, but cannot prove a complete, fresh revocation decision.
// In particular, no successful or even failure Check is emitted here until
// the external protected C-05 provenance/revocation authority is established.
interface IndependentAppEnv extends Env {
  GITHUB_APP_ID?: string;
  GITHUB_APP_INSTALLATION_ID?: string;
  GITHUB_APP_PRIVATE_KEY_PEM?: string;
  ENABLE_BLOCKED_CHECK_CANDIDATE?: string; // Never set in production without separately approved deployment.
}

type AuthenticatedIssuerObservation = ReadOnlyObservation & {
  appIdentity: "VERIFIED_GITHUB_API_RESPONSE";
  gateVerdict: "BLOCKED_UNVERIFIED";
  checkRunCreated: false;
};

function asn1Length(n: number): number[] {
  if (!Number.isSafeInteger(n) || n < 0 || n > 16384) {
    throw new Error("invalid_private_key_length");
  }
  if (n < 128) return [n];
  if (n <= 255) return [0x81, n];
  return [0x82, n >>> 8, n & 255];
}

function asn1Node(tag: number, contents: Uint8Array): Uint8Array {
  return new Uint8Array([tag, ...asn1Length(contents.byteLength), ...contents]);
}

function parseAppPrivateKey(pem: string): Uint8Array {
  // GitHub downloads PKCS#1 RSA keys; WebCrypto expects PKCS#8.
  const match = pem.match(/^-----BEGIN (RSA )?PRIVATE KEY-----\s+([A-Za-z0-9+/=\s]+?)\s+-----END (RSA )?PRIVATE KEY-----\s*$/);
  if (!match || match[1] !== match[3]) throw new Error("invalid_app_private_key_pem");
  const raw64 = match[2].replace(/\s/g, "");
  if (raw64.length < 64 || raw64.length > 12000 || raw64.length % 4 !== 0) {
    throw new Error("invalid_app_private_key_encoding");
  }
  let binary: string;
  try { binary = atob(raw64); } catch { throw new Error("invalid_app_private_key_encoding"); }
  const key = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  if (key.byteLength < 64 || key.byteLength > 8192) throw new Error("invalid_app_key_size");
  if (!match[1]) return key; // Already PKCS#8.
  // PKCS#8 = SEQUENCE { version INTEGER 0, rsaEncryption AlgorithmIdentifier,
  //                     privateKey OCTET STRING containing PKCS#1 }.
  const header = new Uint8Array([
    0x02, 0x01, 0x00, 0x30, 0x0d, 0x06, 0x09,
    0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00,
  ]);
  return asn1Node(0x30, new Uint8Array([
    ...header, ...asn1Node(0x04, key),
  ]));
}

function b64url(bytes: Uint8Array): string {
  let s = "";
  for (const byte of bytes) s += String.fromCharCode(byte);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function appJwt(env: IndependentAppEnv): Promise<string> {
  const appId = Number(env.GITHUB_APP_ID);
  if (!positiveSafeInteger(appId) || String(appId) !== env.GITHUB_APP_ID ||
      typeof env.GITHUB_APP_PRIVATE_KEY_PEM !== "string" ||
      !env.GITHUB_APP_PRIVATE_KEY_PEM) {
    throw new Error("protected_app_configuration_missing");
  }
  const pkcs8 = parseAppPrivateKey(env.GITHUB_APP_PRIVATE_KEY_PEM);
  const key = await crypto.subtle.importKey(
    "pkcs8", pkcs8.buffer as ArrayBuffer,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false, ["sign"],
  );
  const now = Math.floor(Date.now() / 1000);
  const data = b64url(new TextEncoder().encode(JSON.stringify({ alg: "RS256", typ: "JWT" }))) +
    "." + b64url(new TextEncoder().encode(JSON.stringify({
      iat: now - 60, exp: now + 480, iss: String(appId),
    })));
  const sig = new Uint8Array(await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(data),
  ));
  return data + "." + b64url(sig);
}

async function authenticatedGitHubJson(
  url: string, token: string, read: ReadOnlyFetch,
  method: "GET" | "POST" = "GET", body?: unknown,
): Promise<unknown> {
  if (!url.startsWith("https://api.github.com/") ||
      !/^https:\/\/api\.github\.com\/[A-Za-z0-9_/?=&.\-]+$/.test(url) ||
      !token || typeof token !== "string") {
    throw new Error("invalid_github_app_request");
  }
  const response = await read(url, {
    method,
    headers: {
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
      authorization: "Bearer " + token,
      ...(body === undefined ? {} : { "content-type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    redirect: "error", cache: "no-store", signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error("authenticated_github_api_rejected:" + response.status);
  return response.json();
}

async function appInstallationToken(
  env: IndependentAppEnv, read: ReadOnlyFetch,
): Promise<string> {
  if (env.EXPECTED_REPOSITORY !== "kan1975-creator/CB6-Navi-Public-Build" ||
      !positiveSafeInteger(Number(env.EXPECTED_REPOSITORY_ID)) ||
      String(Number(env.EXPECTED_REPOSITORY_ID)) !== env.EXPECTED_REPOSITORY_ID) {
    throw new Error("repository_binding_invalid");
  }
  const installationId = Number(env.GITHUB_APP_INSTALLATION_ID);
  if (!positiveSafeInteger(installationId) ||
      String(installationId) !== env.GITHUB_APP_INSTALLATION_ID) {
    throw new Error("installation_id_invalid");
  }
  const jwt = await appJwt(env);
  const app = object(await authenticatedGitHubJson("https://api.github.com/app", jwt, read));
  if (!app || app.id !== Number(env.GITHUB_APP_ID)) {
    throw new Error("github_app_id_unverified");
  }
  const installation = object(await authenticatedGitHubJson(
    "https://api.github.com/app/installations/" + installationId, jwt, read,
  ));
  if (!installation || installation.id !== installationId ||
      installation.app_id !== Number(env.GITHUB_APP_ID) ||
      installation.suspended_at != null) {
    throw new Error("github_installation_unverified");
  }
  const issued = object(await authenticatedGitHubJson(
    "https://api.github.com/app/installations/" + installationId + "/access_tokens",
    jwt, read, "POST", {
      repositories: ["CB6-Navi-Public-Build"],
      permissions: { checks: "write", issues: "read", pull_requests: "read", contents: "read" },
    },
  ));
  const permissions = object(issued?.permissions);
  const token = issued?.token;
  const expires = typeof issued?.expires_at === "string"
    ? Date.parse(issued.expires_at) : NaN;
  if (typeof token !== "string" || token.length < 20 ||
      !Number.isFinite(expires) || expires - Date.now() < 60000 ||
      permissions?.checks !== "write" || permissions?.issues !== "read" ||
      permissions?.pull_requests !== "read" || permissions?.contents !== "read") {
    throw new Error("github_installation_token_unverified");
  }
  // Do not trust token response's repository selection alone. Re-read the
  // repository with the actual installation token and bind its immutable ID.
  const repo = object(await authenticatedGitHubJson(GITHUB_API, token, read));
  if (!repo || repo.id !== Number(env.EXPECTED_REPOSITORY_ID) ||
      repo.full_name !== env.EXPECTED_REPOSITORY) {
    throw new Error("authenticated_repository_identity_mismatch");
  }
  return token;
}

/** Read-only App connector. No PASS or Check write can originate here. */
export async function inspectIndependentIssuerCandidate(
  identity: CandidatePrIdentity, env: IndependentAppEnv,
  read: ReadOnlyFetch = fetch,
): Promise<AuthenticatedIssuerObservation> {
  if (!env || !identity || identity.repoId !== Number(env.EXPECTED_REPOSITORY_ID)) {
    throw new Error("independent_issuer_configuration_mismatch");
  }
  const token = await appInstallationToken(env, read);
  // The downstream candidate only permits GET under the fixed repository URL.
  // A signed App JWT establishes App authentication, NOT independent control
  // over the private key or a complete, fresh revocation decision.
  const authenticatedRead: ReadOnlyFetch = (input, init) => {
    if (typeof input !== "string" || !input.startsWith(GITHUB_API + "/") ||
        init?.method !== "GET") {
      throw new Error("unsafe_issuer_candidate_read");
    }
    return read(input, {
      ...init,
      headers: {
        accept: "application/vnd.github+json",
        "x-github-api-version": "2022-11-28",
        authorization: "Bearer " + token,
      }, redirect: "error", cache: "no-store",
    });
  };
  const observed = await observeGitHubStateCandidate(identity, authenticatedRead);
  if (observed.headState !== "MATCH" ||
      observed.revocationSignal === "POSSIBLE_REVOCATION") {
    throw new Error("approval_or_head_unverified");
  }
  // GitHub issue comments are not an authoritative revocation ledger: an
  // absent comment cannot rule out a removed or externally stored revocation.
  // Protected C-05 provenance, pre-implementation authorization and merge-time
  // cancellation validation remain unavailable. Thus no Check POST occurs.
  return { ...observed, appIdentity: "VERIFIED_GITHUB_API_RESPONSE",
    gateVerdict: "BLOCKED_UNVERIFIED", checkRunCreated: false };
}

/** Optional, isolated D1 diagnostic for an independently authenticated App.
 * This does NOT establish protected approval or authoritative non-revocation.
 * Do not wire into the legacy webhook until separately authorized.
 */
export async function auditIndependentIssuerCandidate(
  deliveryId: string, identity: CandidatePrIdentity, env: IndependentAppEnv,
  read: ReadOnlyFetch = fetch,
): Promise<AuthenticatedIssuerObservation> {
  if (typeof deliveryId !== "string" || !DELIVERY_UUID.test(deliveryId) ||
      !env?.DB || typeof env.DB.prepare !== "function") {
    throw new Error("issuer_candidate_audit_configuration_invalid");
  }
  const observation = await inspectIndependentIssuerCandidate(identity, env, read);
  const saved = await env.DB.prepare(`
    INSERT INTO issuer_app_candidate_audit
      (delivery_id, repository_id, pr_number, head_sha, app_identity,
       revocation_status, gate_verdict, check_run_created)
    VALUES (?, ?, ?, ?, 'VERIFIED_GITHUB_API_RESPONSE', 'UNVERIFIED',
            'BLOCKED_UNVERIFIED', 0)
    ON CONFLICT DO NOTHING
  `).bind(deliveryId.toLowerCase(), identity.repoId,
          identity.prNumber, observation.observedHeadSha).run();
  if (!saved.success || saved.meta?.changes !== 1) {
    throw new Error("issuer_candidate_audit_not_confirmed");
  }
  return observation;
}

// ISOLATED CANDIDATE: authenticated record intake for explicit owner comments.
// This function is intentionally NOT routed from the active webhook fetch():
// protected start evidence, complete revocation authority, private-key custody,
// external deployment, and Check enforcement remain unproven.
// Captured START is only a witnessed GitHub comment, not independent proof
// that implementation work began at that moment.
const OWNER_DECISION = /^CB6-(APPROVE|REVOKE|START) ([A-Za-z0-9_.-]{1,128}) ([0-9a-f]{64}) ([0-9a-f]{40})$/;
type DecisionCandidateRecord = {
  decision: "APPROVE" | "REVOKE" | "START";
  changeId: string; planSha256: string; planCommitSha: string;
  headSha: string; basisHead: string;
  gateVerdict: "BLOCKED_UNVERIFIED";
};

export async function recordAuthenticatedDecisionCandidate(
  request: Request, env: IndependentAppEnv, read: ReadOnlyFetch = fetch,
): Promise<DecisionCandidateRecord> {
  if (request.method !== "POST" ||
      request.headers.get("x-github-event") !== "issue_comment" ||
      !env?.DB || !env.GITHUB_WEBHOOK_SECRET ||
      env.EXPECTED_REPOSITORY !== "kan1975-creator/CB6-Navi-Public-Build" ||
      !positiveSafeInteger(Number(env.EXPECTED_REPOSITORY_ID))) {
    throw new Error("decision_candidate_configuration_invalid");
  }
  const delivery = request.headers.get("x-github-delivery");
  if (!delivery || !DELIVERY_UUID.test(delivery) ||
      !/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") ?? "")) {
    throw new Error("decision_candidate_envelope_invalid");
  }
  const bytes = await boundedRequestBytes(request);
  if (!await authenticGitHubSignature(bytes,
      request.headers.get("x-hub-signature-256"), env.GITHUB_WEBHOOK_SECRET)) {
    throw new Error("decision_candidate_signature_invalid");
  }
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const bodySha = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0")).join("");
  const event = object(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)));
  const repo = object(event?.repository);
  const issue = object(event?.issue);
  const comment = object(event?.comment);
  const actor = object(comment?.user);
  const prNo = issue?.number;
  const commentId = comment?.id;
  if (event?.action !== "created" || !positiveSafeInteger(prNo) ||
      !object(issue?.pull_request) || !positiveSafeInteger(commentId) ||
      repo?.id !== Number(env.EXPECTED_REPOSITORY_ID) ||
      repo?.full_name !== env.EXPECTED_REPOSITORY ||
      actor?.id !== CANDIDATE_APPROVER_ID ||
      typeof comment?.body !== "string" ||
      typeof comment?.created_at !== "string" ||
      comment?.created_at !== comment.updated_at ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(comment.created_at)) {
    throw new Error("decision_candidate_untrusted_event");
  }
  const match = OWNER_DECISION.exec(comment.body);
  if (!match) throw new Error("decision_candidate_invalid_content");
  // Independently read both immutable comment identity and live PR using an
  // installation token. A signed delivery or submitted PR JSON alone is NOT
  // authoritative for live HEAD or comment edit/deletion.
  const token = await appInstallationToken(env, read);
  const [liveCommentRaw, livePrRaw] = await Promise.all([
    authenticatedGitHubJson(GITHUB_API + "/issues/comments/" + commentId, token, read),
    authenticatedGitHubJson(GITHUB_API + "/pulls/" + prNo, token, read),
  ]);
  const liveComment = object(liveCommentRaw);
  const livePr = object(livePrRaw);
  const liveBase = object(livePr?.base);
  const liveHead = object(livePr?.head);
  if (liveComment?.id !== commentId ||
      object(liveComment?.user)?.id !== CANDIDATE_APPROVER_ID ||
      liveComment?.body !== comment.body ||
      liveComment?.created_at !== comment.created_at ||
      liveComment?.updated_at !== comment.created_at ||
      liveComment?.issue_url !== GITHUB_API + "/issues/" + prNo ||
      livePr?.number !== prNo || livePr?.state !== "open" ||
      object(liveBase?.repo)?.id !== Number(env.EXPECTED_REPOSITORY_ID) ||
      !APPROVED_BASE_REFS.has(String(liveBase?.ref)) ||
      !SHA40.test(String(liveBase?.sha ?? "")) ||
      !SHA40.test(String(liveHead?.sha ?? ""))) {
    throw new Error("decision_candidate_live_reconciliation_failed");
  }
  // Historical comment capture is never proof of pre-implementation intent,
  // and missing REVOKE rows are not proof of authoritative non-revocation.
  const record: DecisionCandidateRecord = {
    decision: match[1] as "APPROVE" | "REVOKE" | "START", changeId: match[2],
    planSha256: match[3], planCommitSha: match[4],
    headSha: String(liveHead?.sha), basisHead: String(liveBase?.sha),
    gateVerdict: "BLOCKED_UNVERIFIED",
  };
  // START is deliberately isolated from approval/cancellation history.
  // Both tables reject replay; SQL triggers reject observed late approvals
  // regardless of whether the START or APPROVE webhook arrives first.
  if (record.decision === "START") {
    const started = await env.DB.prepare(`
      INSERT INTO issuer_start_observation_candidate
        (delivery_id, body_sha256, repository_id, pr_number, pr_head_sha,
         basis_head, change_id, plan_sha256, plan_commit_sha,
         github_comment_id, github_actor_id, github_created_at, gate_verdict)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BLOCKED_UNVERIFIED')
    `).bind(delivery.toLowerCase(), bodySha, Number(env.EXPECTED_REPOSITORY_ID),
        prNo, record.headSha, record.basisHead, record.changeId,
        record.planSha256, record.planCommitSha, commentId,
        CANDIDATE_APPROVER_ID, comment.created_at).run();
    if (!started.success || started.meta?.changes !== 1) {
      throw new Error("start_candidate_observation_unconfirmed");
    }
    return record;
  }
  const saved = await env.DB.prepare(`
    INSERT INTO issuer_decision_event_candidate
      (delivery_id, body_sha256, repository_id, pr_number, pr_head_sha,
       basis_head, change_id, plan_sha256, plan_commit_sha, decision,
       github_comment_id, github_actor_id, github_created_at, gate_verdict)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BLOCKED_UNVERIFIED')
  `).bind(delivery.toLowerCase(), bodySha, Number(env.EXPECTED_REPOSITORY_ID),
      prNo, record.headSha, record.basisHead, record.changeId,
      record.planSha256, record.planCommitSha, record.decision,
      commentId, CANDIDATE_APPROVER_ID, comment.created_at).run();
  if (!saved.success || saved.meta?.changes !== 1) {
    throw new Error("decision_candidate_audit_unconfirmed");
  }
  return record;
}

// The fixed existing Required Check name is reserved for a future independent
// issuer. Construct only the BLOCKED/failure request here. It is never sent by
// this candidate: issuing ANY Check needs an approved protected revocation
// authority and separate deployment authorization. No success/neutral/skipped
// conclusion exists anywhere in this Check payload.
export function blockedCheckRequestCandidate(headSha: string): {
  method: "POST"; url: string; body: {
    name: string; head_sha: string; status: "completed"; conclusion: "failure";
    output: { title: string; summary: string };
  };
} {
  if (typeof headSha !== "string" || !SHA40.test(headSha)) {
    throw new Error("invalid_check_head_sha");
  }
  return { method: "POST", url: GITHUB_API + "/check-runs", body: {
    name: "CB6 Approval Enforcement", head_sha: headSha,
    status: "completed", conclusion: "failure",
    output: { title: "CB6 approval blocked",
      summary: "Protected approval, revocation and required-check authority not verified" },
  } };
}

// C-05/C-07 candidate Check payload identity handshake, BLOCKED only.
// No successful verdict exists. An isolated, deliberately gated function below
// may emit this negative-only Check; the public webhook never calls it.
export function blockedBoundCheckCandidate(
  headSha: string, changeId: string, planSha256: string,
): ReturnType<typeof blockedCheckRequestCandidate> & { body: {
    external_id: string;
  } } {
  if (!/^[A-Za-z0-9_.-]{1,128}$/.test(changeId) ||
      !/^[0-9a-f]{64}$/.test(planSha256)) {
    throw new Error("invalid_bound_check_identity");
  }
  const original = blockedCheckRequestCandidate(headSha);
  return { ...original, body: { ...original.body,
    external_id: "CB6-BLOCKED:" + changeId + ":" + planSha256 + ":" + headSha,
  } };
}


/** Isolated negative-only GitHub Check connector; NOT reachable from fetch().
 * A failed Check reports a block, NEVER protected consent or complete revocation.
 * A separate, explicit configuration flag prevents accidental deployment use.
 */
export async function emitBlockedBoundCheckCandidate(
  identity: CandidatePrIdentity, changeId: string, planSha256: string,
  env: IndependentAppEnv, read: ReadOnlyFetch = fetch,
): Promise<{
  gateVerdict: "BLOCKED_UNVERIFIED";
  checkRunCreated: true;
  checkRunId: number;
  issuerAppId: number;
  headSha: string;
  externalId: string;
}> {
  if (env?.ENABLE_BLOCKED_CHECK_CANDIDATE !== "isolated_candidate_only" ||
      !identity || identity.repoId !== Number(env.EXPECTED_REPOSITORY_ID) ||
      identity.repoFullName !== "kan1975-creator/CB6-Navi-Public-Build" ||
      !positiveSafeInteger(identity.prNumber) ||
      !APPROVED_BASE_REFS.has(identity.baseRef) ||
      !SHA40.test(identity.baseSha) || !SHA40.test(identity.headSha) ||
      identity.headRepoFullName !== identity.repoFullName) {
    throw new Error("blocked_check_candidate_not_authorized");
  }
  // Constructing the payload first rejects invalid change and plan identifiers
  // before requesting a token or performing any GitHub side effect.
  const bounded = blockedBoundCheckCandidate(identity.headSha, changeId, planSha256);
  const token = await appInstallationToken(env, read);
  const validatePr = async () => {
    const pr = object(await authenticatedGitHubJson(
      GITHUB_API + "/pulls/" + identity.prNumber, token, read,
    ));
    const base = object(pr?.base);
    const head = object(pr?.head);
    const baseRepo = object(base?.repo);
    const headRepo = object(head?.repo);
    if (!pr || pr.number !== identity.prNumber || pr.state !== "open" ||
        base?.sha !== identity.baseSha || base?.ref !== identity.baseRef ||
        baseRepo?.id !== identity.repoId ||
        baseRepo?.full_name !== identity.repoFullName ||
        head?.sha !== identity.headSha ||
        headRepo?.full_name !== identity.headRepoFullName) {
      throw new Error("blocked_check_stale_or_foreign_pr");
    }
  };
  await validatePr();
  // Only a completed failure may be submitted. URL and body are fixed/local
  // constructions, never controlled by webhook input.
  const created = object(await authenticatedGitHubJson(
    bounded.url, token, read, bounded.method, bounded.body,
  ));
  if (!created || !positiveSafeInteger(created.id) ||
      created.name !== "CB6 Approval Enforcement" ||
      created.head_sha !== identity.headSha ||
      created.external_id !== bounded.body.external_id ||
      created.status !== "completed" || created.conclusion !== "failure" ||
      object(created.app)?.id !== Number(env.GITHUB_APP_ID)) {
    throw new Error("blocked_check_issuer_receipt_unverified");
  }
  // On a race, the Check only marks the *old* SHA as failed; never grant PASS.
  await validatePr();
  return { gateVerdict: "BLOCKED_UNVERIFIED", checkRunCreated: true,
    checkRunId: created.id, issuerAppId: Number(env.GITHUB_APP_ID),
    headSha: identity.headSha, externalId: bounded.body.external_id };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") return reply(405, "post_only");
    if (
      !env || !env.DB || typeof env.DB.prepare !== "function" ||
      !env.GITHUB_WEBHOOK_SECRET || !env.EXPECTED_REPOSITORY ||
      !env.EXPECTED_REPOSITORY_ID
    ) return reply(503, "trusted_configuration_missing");

    // Strictly optional candidate intake: the deployed legacy PR behavior is
    // unchanged with the flag unset; no authorization/check result is possible.
    if (request.headers.get("x-github-event") === "issue_comment" &&
        env.ENABLE_DECISION_CAPTURE === "isolated_candidate") {
      try {
        await recordAuthenticatedDecisionCandidate(request, env as IndependentAppEnv);
        return reply(202, "decision_candidate_recorded_without_authorization");
      } catch {
        return reply(503, "decision_candidate_authentication_or_audit_failed");
      }
    }
    if (request.headers.get("x-github-event") !== "pull_request") {
      return reply(403, "unsupported_webhook_event");
    }
    const delivery = request.headers.get("x-github-delivery");
    if (!delivery || !DELIVERY_UUID.test(delivery)) {
      return reply(400, "invalid_delivery_id");
    }
    if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") ?? "")) {
      return reply(415, "json_required");
    }
    const declaredLength = request.headers.get("content-length");
    if (declaredLength !== null &&
        (!/^\d+$/.test(declaredLength) || Number(declaredLength) > MAX_PAYLOAD_BYTES)) {
      return reply(413, "payload_limit");
    }

    let bytes: Uint8Array;
    try {
      bytes = await boundedRequestBytes(request);
    } catch (error) {
      if (error instanceof RangeError && error.message === "payload_limit") {
        return reply(413, "payload_limit");
      }
      return reply(400, "unreadable_body");
    }

    let bodySha256: string;
    try {
      if (!await authenticGitHubSignature(
        bytes, request.headers.get("x-hub-signature-256"),
        env.GITHUB_WEBHOOK_SECRET,
      )) return reply(401, "signature_invalid");
      // Hash the raw signed bytes: GitHub's delivery ID header is not HMAC-bound.
      const digest = await crypto.subtle.digest("SHA-256", bytes);
      bodySha256 = Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, "0")).join("");
    } catch {
      return reply(503, "signature_verification_unavailable");
    }

    let payload: JsonObject | null;
    try {
      payload = object(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)));
    } catch {
      return reply(400, "invalid_json");
    }
    if (!payload) return reply(400, "invalid_json");
    const receipt = prReceipt(payload, env);
    if (!receipt) return reply(422, "pr_binding_unverified");

    // Audit only: webhook content has not been independently reconciled with
    // fresh GitHub API HEAD, protected approval, revocation state, or start event.
    // Check issuance and all success paths are intentionally absent.
    try {
      const saved = await env.DB.prepare(`
        INSERT INTO webhook_audit
          (delivery_id, body_sha256, event_name, action, repository_id, repository_full_name,
           pr_number, base_ref, base_sha, head_sha, head_repository_full_name,
           verdict, reason)
        VALUES (?, ?, 'pull_request', ?, ?, ?, ?, ?, ?, ?, ?, 'BLOCKED_UNVERIFIED',
                'protected_provenance_and_revocation_not_verified')
        ON CONFLICT DO NOTHING
      `).bind(
        delivery.toLowerCase(), bodySha256, receipt.action, receipt.repoId,
        receipt.repoFullName, receipt.prNumber, receipt.baseRef,
        receipt.baseSha, receipt.headSha, receipt.headRepoFullName,
      ).run();
      if (!saved.success) return reply(503, "audit_write_failed");
      if (saved.meta?.changes !== 1) return reply(409, "duplicate_or_unconfirmed_receipt");
    } catch {
      return reply(503, "audit_unavailable");
    }
    return reply(202, "webhook_audited_without_authorization");
  },
};
