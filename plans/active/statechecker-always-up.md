# Statechecker Always-Up Plan

Updated: 2026-09-27

Status: active; both outage drills delivered DOWN and UP AGAIN; final Websites
check and operator acceptance pending

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
- The initial 3.0.2 deployment passed external health checks on both hosts.
  Both hosts now run API, CHECK, and Web image version `3.1.1`. Their operator
  image-update logs and IONOS post-repair health check show API/CHECK pinned to
  `sha256:f45d935b179e217f56b821181eb3a1f3fe8915d73041c7d3dd26dd416f6a0a93`
  and Web pinned to
  `sha256:c9d30c50aed673c85fb0677a8493ed417fd0e50448e300b97ce4627bc219f327`.
- Both live check workers use a five-minute website interval and have Telegram
  enabled. The Telegram sender bot secret exists on both hosts. Error and
  information recipient-list fingerprints match across the two hosts; this
  does not prove bot-token equality or message delivery.
- On 2026-09-26, the operator ran `./quick-start.sh --health` on both hosts:
  each API, CHECK, database, and Web service was 1/1 and each public API/Web
  endpoint passed. Cross-host `/health` probes returned HTTP 200 in both
  directions. Both hosts have Telegram enabled with one configured error chat
  and email alerts disabled.
- The operator's Websites screenshots show IONOS watching
  `https://api.statechecker.fe-wi.com/health` and Ubuntu Mini watching
  `https://api.statechecker.ionos.fe-wi.com/health`, exactly one entry on each
  page and both **Up**. A fresh check is still needed after image rollout.
- In the IONOS drill on 2026-09-26, the API was scaled to zero at 14:19:00
  UTC; its public `/health` returned HTTP 502 at 14:19:11. After restoration,
  `/health` returned HTTP 200 at 14:26:28. At 14:32:28 the stack health check
  passed with API, CHECK, database, and Web all 1/1; the migration service was
  0/1 after completion. The operator observed no Telegram DOWN or UP AGAIN
  message. Alert delivery failed the drill acceptance check.
- Read-only probes of both running CHECK containers found nonempty mounted
  Telegram secrets, but neither raw value matched a bot-token shape. Telegram
  `getMe` returned HTTP 404 `Not Found` for both raw values. Ubuntu Mini's
  48-character value has literal enclosing quotes. Removing that pair in a
  read-only probe produced a valid token: Telegram `getMe` and `getChat` for its
  configured error chat both returned HTTP 200. At diagnosis, the running CHECK
  container still received the quoted secret. IONOS's value is four characters,
  has no enclosing quotes, and is not a valid token shape. Its normalized Bot API
  probes were skipped. The filtered Ubuntu Mini checker logs showed no matching
  event in the drill window, so credential repair alone will not prove that the
  worker detected the outage.
- On 2026-09-27, the operator rotated only Ubuntu Mini's CHECK service through
  a temporary valid secret, detached the malformed original, recreated the
  original external secret name with the unquoted token, and switched CHECK
  back. The token and error chat passed Telegram `getMe` and `getChat` before
  rotation. Each CHECK update converged at 1/1 and the final running worker
  read a token with valid shape. The final `./quick-start.sh --health` passed:
  API, CHECK, database, and Web were 1/1 and public API/Web endpoints were
  reachable.
- The operator repaired IONOS's malformed Telegram secret on 2026-09-27. The
  token and error chat passed Telegram preflight, API and CHECK service updates
  converged, and the final `./quick-start.sh --health` passed. The Notifications
  UI reported one test message delivered to the configured error chat on each
  host. The operator showed Telegram receipt from Ubuntu Mini and reported the
  IONOS test send worked.
- On both hosts, an ordinary stack redeploy using version `3.1.0` retained the
  expected API/CHECK and Web image digests and passed external health checks.
  The later `3.1.1` paired image updates also converged and passed health checks.
- In the IONOS retest on 2026-09-27, the operator reported that the drill worked
  perfectly. The supplied Telegram screenshot shows one **DOWN** message at
  17:20 and one **UP AGAIN** message at 17:30, both naming the IONOS API health
  URL. The observer received an HTTP `Bad Gateway` result during the outage.
  The drill command's console output was not supplied for this retest, so its
  exact scale, restore, and health-check timestamps are not recorded here.
- In the reverse drill on 2026-09-27, the operator scaled Ubuntu Mini's API to
  zero at 15:57:30 UTC. Its public health URL returned HTTP 404 at 15:57:36 UTC.
  After restoration, the URL returned HTTP 200 at 16:04:47 UTC and the local
  `./quick-start.sh --health` passed with API, CHECK, database, and Web at 1/1.
  The supplied Telegram screenshot shows a **DOWN** message at 17:58 and an
  **UP AGAIN** message at 18:07, both naming the Ubuntu Mini API health URL.
  The pasted shell output ended during the six-minute recovery wait, so its
  final `DRILL_END` line was not observed. Fresh post-rollout Websites-tab
  confirmation remains pending.

## Milestones

### 1. Confirm mutual monitoring — health and peer UI passed; fresh post-rollout UI check pending

On both Websites tabs, confirm that exactly one peer API sentinel remains and
is **Up** after at least one five-minute worker cycle. Confirm the intended
Telegram error destination without exposing bot tokens or private `.env` data.
The API sentinel is deliberately used instead of a duplicate Web check during
the initial rollout.

Acceptance: both peers remain visible and **Up**, and the checker services
remain at 1/1. This is the preflight for the outage drill.

### 2. Controlled failure and recovery drill — both alert pairs and recovery observed

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

### 3. Make Telegram delivery acknowledgement reliable — deployed; both directions validated

The earlier 3.0.2 checker stored a website's down-message-sent flag before
calling Telegram and ignored the sender's Boolean result. Version `3.1.1` now
acknowledges DOWN and UP AGAIN after at least one Telegram error chat accepts
the message. A total failure stays pending for the next worker cycle. Partial
success is logged and acknowledged to avoid repeats to chats that succeeded;
the existing one-flag schema cannot track each recipient separately. Website
Up/Down state is saved independently of alert acknowledgement. The two live
hosts each use one Telegram error chat and have email alerts disabled. With
Telegram enabled, email sends occur only after Telegram acknowledgement so
failed Telegram retries do not duplicate email.

Affected repository: Statechecker application. Local focused tests for
successful send, failed send, recovery, partial-recipient behavior, and
email-only compatibility pass. The operator built and deployed version `3.1.1`
on both hosts. Ubuntu Mini's live worker delivered the IONOS DOWN and UP AGAIN
messages; IONOS's live worker delivered the reverse pair. No database schema
migration was required.

### 4. Preserve image identity through normal redeploys — validated at 3.1.0

The paired-update menu already pinned running service specs, but version
`3.0.2` rendered tag-based image references from `.env` during ordinary stack
deploys. The updated deployment code now pulls both configured versioned tags,
resolves unambiguous repository digests, renders those references for API,
CHECK, and Web, and verifies the rendered images before stack deploy. The
human-readable version tags remain in `.env`. Pull, digest, or render failure
stops before service changes; no second rollout should be needed to re-pin.

Affected repository: Swarm Statechecker deployment. Local Bash syntax,
mocked failure paths, and stack rendering pass. The operator's normal `3.1.0`
stack redeploy on each host retained the expected digests and passed external
health checks. The subsequent `3.1.1` image updates also pinned both image
digests. Preserve existing rollback targets and secret handling.

### 5. Final operator acceptance and runbook — draft complete; acceptance pending

Confirm that each post-rollout Websites tab contains only its peer URL and is
**Up** after the reverse drill. Document the minimal operating procedure:
deployment, health checks, peer URL ownership, Telegram destination checks,
image update/redeploy, emergency API restoration, and response to missing
alerts. The draft operating procedure is in the deployment repository at
`docs/always-up-operations.md`. Close this plan after fresh peer UI checks and
final operator acceptance.

## Decisions and authorization

- The operator approved the drill batch with IONOS as the first target. The
  IONOS retest delivered the expected DOWN and UP AGAIN alert pair, and the
  operator reported that it worked perfectly. Both hosts' Telegram secrets
  have been repaired and their UI test sends succeeded. The reverse drill on
  Ubuntu Mini also delivered the alert pair and passed local health checks.
  Final Websites-tab confirmation and operator acceptance remain pending.
- The operator controls image build/publication, deployment, and final batch
  approval. The Telegram acknowledgement and redeploy-pinning changes are live
  in version `3.1.1`; their remaining checks are listed in the milestones.
- The live one-recipient, email-disabled configuration permits one-success
  acknowledgement without a per-recipient schema. Partial success in a
  future multi-recipient configuration is acknowledged and logged; retrying
  only failed recipients would require a durable per-recipient delivery record.
- The Notifications tab and admin-only Telegram test endpoint are deployed and
  delivered test messages on both hosts. Recipient editing in Statechecker
  remains deployment-managed because API and checker use separate config mounts.

## Deferred, not required for two-server acceptance

- Add a third independent observer to reduce two-node ambiguity.
- Consider a deeper health endpoint covering database access and checker
  freshness; today's public `/health` is an API-and-route sentinel.
- Add separate frontend checks only if independent Web alerts are useful.
- Consider failure debounce if transient network errors cause false alerts;
  changing the current five-minute detection behavior requires a conscious
  latency trade-off.
