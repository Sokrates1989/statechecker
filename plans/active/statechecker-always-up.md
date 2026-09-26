# Statechecker Always-Up Plan

Updated: 2026-09-26

Status: active; outage drill approved, not yet run

## Outcome and scope

Run independent Statechecker instances on IONOS and Ubuntu Mini. Each watches
the other's public API `/health` URL every five minutes and sends outage and
recovery alerts to the same Telegram error channel. Keep the existing checker
worker inside Statechecker; no separate watchdog repository or feature-parity
project is needed for this rollout.

This is the single active plan for the Statechecker application and its Swarm
deployment repository. Implementation, operator testing, and approval are
separate states. The operator manually tests and approves each batch before the
next production-affecting batch.

## Verified starting point

- The initial deployment-tooling and IONOS reachability milestones were
  accepted. IONOS readiness passed on a warm redeploy at attempt 1/10 and a
  cold deploy at attempt 3/10. Ubuntu Mini's preserved `state_checker` database
  and `/swarm/administration/statechecker/db_data` mount survived its upgrade;
  initial readiness passed on attempt 8/10.
- Both deployments run API, CHECK, and Web image version `3.0.2`; API/Web
  endpoints returned HTTP 200 and all three services converged to 1/1.
- The paired-update menu pinned the application services on both hosts to the
  same API/CHECK digest (`sha256:4aa057a3e0fb385de3bec46d1ddddc8b41ec4d90be0b4b721e0e60b7c0570e70`)
  and Web digest (`sha256:57eb50edc33bb80b6d3847670763d2d6ef80c25ed8987055bcbe9acb57867bca`).
- Both live check workers use a five-minute website interval and have Telegram
  enabled. The Telegram sender bot secret exists on both hosts. Error and
  information recipient-list fingerprints match across the two hosts; this
  does not prove bot-token equality or message delivery.
- The Websites UI previously showed IONOS watching
  `https://api.statechecker.fe-wi.com/health` and Ubuntu Mini watching
  `https://api.statechecker.ionos.fe-wi.com/health`, both **Up**. A fresh
  post-rollout check after a worker cycle is still needed.
- The 3.0.2 Web image includes guidance for removing starter examples, but the
  operator has not yet accepted that UI behavior.

## Milestones

### 1. Confirm mutual monitoring — configured; final check pending

On both Websites tabs, confirm that exactly one peer API sentinel remains and
is **Up** after at least one five-minute worker cycle. Confirm the intended
Telegram error destination without exposing bot tokens or private `.env` data.
The API sentinel is deliberately used instead of a duplicate Web check during
the initial rollout.

Acceptance: both peers remain visible and **Up**, and the checker services
remain at 1/1. This is the preflight for the outage drill.

### 2. Controlled failure and recovery drill — approved; pending execution

Test IONOS API first, with Ubuntu Mini observing. After the operator reviews
that result, reverse the direction. For each direction, preflight the healthy
endpoint and service replica count, temporarily scale only the target API to
zero, verify that its public health URL fails, and restore it automatically
after a bounded observation window. Keep an emergency restore command visible
to the operator. Do not remove a stack, volume, database, or secret.

Acceptance for each direction: the surviving checker sends one Telegram
**DOWN** alert naming the peer URL to the intended error channel; after API
restoration, it sends an **UP AGAIN** alert; the API returns HTTP 200, service
replicas return to 1/1, and both Websites tabs return to **Up**. Record actual
timing and any duplicate or missing messages. If an alert is missing, restore
the API first and investigate rather than extending the outage indefinitely.

Rollback: restore the target API to one replica immediately, then verify its
public health URL and Swarm convergence. The drill changes no persisted data.

### 3. Make Telegram delivery acknowledgement reliable — planned after drill

The current checker stores a website's down-message-sent flag before calling
Telegram and ignores the sender's Boolean result. A temporary Telegram failure
can therefore suppress retry. Change the worker so delivery failure does not
falsely acknowledge an alert. Review the configured error recipients and any
email behavior before choosing the smallest safe policy for partial delivery;
avoid unbounded duplicate messages to recipients that did succeed.

Affected repository: Statechecker application. Validate with focused tests for
successful send, failed send, recovery, and partial-recipient behavior, plus
the relevant local test suite. The operator controls image build/publication
and tests the new image on each host before accepting this batch. No database
schema migration is planned. If rollout fails, restore the prior working image
and preserve the database.

### 4. Preserve image identity through normal redeploys — planned

The paired-update menu pins running service specs, but ordinary stack deploys
still render tag-based image references from `.env`. Prefer resolving both
versioned tags to unambiguous repository digests before changing services and
using those references in the normal deploy path. Keep the human-readable
version tags in `.env`; fail closed if either digest cannot be established.
Avoid a second rollout solely to re-pin after deployment.

Affected repository: Swarm Statechecker deployment. Validate Bash syntax,
mocked failure paths, stack rendering, and a manual redeploy that retains the
expected digests and passes external health checks. Preserve existing rollback
targets and do not change database or secret handling. The operator reviews
this as a separate batch before production use.

### 5. Final operator acceptance and runbook — pending

Confirm the 3.0.2 starter-example removal guidance and successful removal
after adding a real peer URL. Document the minimal operating procedure:
deployment, health checks, peer URL ownership, Telegram destination checks,
image update/redeploy, emergency API restoration, and response to missing
alerts. Close this plan only after both drill directions and the two reliability
fixes have passed their separate operator checks.

## Decisions and authorization

- The operator approved the drill batch, with IONOS as the first target and a
  manual review before reversing direction. Fresh peer **Up** states remain a
  required preflight, not an assumed result.
- The Telegram acknowledgement and redeploy-pinning changes are proposed
  separate batches; their production rollout is not authorized by this plan.
  The operator retains image publication, deployment, and batch approval.
- If the current recipient/email configuration makes partial-delivery semantics
  materially ambiguous, resolve that choice before implementing milestone 3.

## Deferred, not required for two-server acceptance

- Add a third independent observer to reduce two-node ambiguity.
- Consider a deeper health endpoint covering database access and checker
  freshness; today's public `/health` is an API-and-route sentinel.
- Add separate frontend checks only if independent Web alerts are useful.
- Consider failure debounce if transient network errors cause false alerts;
  changing the current five-minute detection behavior requires a conscious
  latency trade-off.
