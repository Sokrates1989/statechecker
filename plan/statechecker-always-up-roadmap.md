# Statechecker Always-Up Roadmap

Updated: 2026-09-26

## Goal

Run Statechecker on multiple independent servers so every instance checks a
peer through its public HTTPS endpoint and sends outage and recovery messages
to the same Telegram destination. Start with Ubuntu Mini and IONOS; add a third
observer later if the two-node operating model proves useful.

## Current status

### 1. Deployment tooling and safety — complete and accepted

- Reproducible stack generation.
- Five-minute website checks.
- Truthful, colored stack and image states.
- Safe repository update checking and operator-triggered self-update.
- Linux-only `quick-start.sh` entry point.
- Expected private environment backups do not block repository updates.
- Post-deploy readiness polling waits for Swarm convergence and HTTPS before
  printing one final verdict.

The paired image-update menu now has a local follow-up implementation awaiting
operator approval: it resolves both pulled image digests before changing any
service, updates API/CHECK/Web by digest, and checks the resulting service
specifications. Selecting the already-configured tag can repair tag-only
service references. The currently observed 3.0.2 deployments still use
tag-only service references until that follow-up is deployed and exercised.
A later stack redeploy can restore tag-based references, so this hardening does
not yet make all deployment paths immutable.

### 2. Make IONOS healthy and publicly reachable — complete and accepted

Operator evidence from IONOS confirms:

- A warm redeploy became ready on attempt 1 of 10.
- A cold deploy became ready on attempt 3 of 10.
- API and web services converged.
- `https://api.statechecker.ionos.fe-wi.com/health` responded successfully.
- `https://statechecker.ionos.fe-wi.com/` responded successfully.
- The deployment overview reported `[OK] running` only after convergence.

### 3. Configure mutual monitoring — in progress

Use one API health URL per peer for the initial rollout. This is a higher-signal
sentinel than the static web root and avoids duplicate outage messages when a
whole server becomes unavailable.

Ubuntu Mini deployment prerequisite is complete. The operator updated its
deployment checkout to `fec6d0b`, retained the existing `state_checker` database
and `/swarm/administration/statechecker/db_data` mount, regenerated the proxy-TLS
stack, and deployed it. Readiness passed on attempt 8 of 10; the API, checker,
database, and web services showed 1/1 replicas, and the public API and web
endpoints passed HTTPS checks. The live checker reports a five-minute interval,
Telegram enabled, and one running replica. Ubuntu Mini reached the IONOS peer
health URL with HTTP 200. The operator's Websites screenshots show each instance
watching the other's API health URL with an **Up** state.

Both hosts now run the 3.0.2 API, checker, and web images, with a five-minute
check interval and Telegram enabled. The operator confirmed matching fingerprints
for their error and information chat-ID lists, and neither host has a Node.js
package installed. These checks do not yet prove bot-token equality, Telegram
delivery, or down/recovery notifications.

The starter-example removal UX was included in web image 3.0.2 and is deployed
on both hosts; operator acceptance of that behavior remains outstanding. The UI
explains that a real website must be added before removing the examples, avoids
a misleading delete request in the example-only state, and refreshes the list
before reporting removal success.

#### Configuration preflight

On both deployment hosts, verify locally that:

- `CHECK_WEBSITES_EVERY_X_MINUTES=5`.
- `TELEGRAM_ENABLED=true`.
- The Telegram sender bot secret exists.
- The error and information chat-ID settings match between both deployments.
  Do not paste bot tokens or private configuration into issue reports or logs.
- The `check` service has one running replica.

#### IONOS monitors Ubuntu Mini

1. Open `https://statechecker.ionos.fe-wi.com/`.
2. Open the **Websites** tab.
3. Add the full URL `https://api.statechecker.fe-wi.com/health`.
4. Confirm its initial state is **Up**.

#### Ubuntu Mini monitors IONOS

1. Open `https://statechecker.fe-wi.com/`.
2. Open the **Websites** tab.
3. Add the full URL `https://api.statechecker.ionos.fe-wi.com/health`.
4. Confirm its initial state is **Up**.

#### Acceptance

- Each instance lists exactly one peer sentinel in the Websites tab.
- Both sentinels remain **Up** after at least one five-minute worker cycle.
- Both check workers use the intended common Telegram destination.
- The updated web UI prevents example-only removal, then allows removing the
  examples after a real peer URL has been added.
- No redeploy is required because website configuration is database-backed.

### 4. Perform failure and recovery drill — pending

Run only after step 3 is manually approved.

1. Select one peer API service as the drill target.
2. Scale that API service to zero without removing the stack or its data.
3. Wait for the observing peer's next five-minute website-check cycle.
4. Confirm one Telegram **DOWN** message identifies the peer health URL.
5. Restore the API service to one replica.
6. Wait for the next check cycle.
7. Confirm one Telegram **UP AGAIN** recovery message.
8. Confirm both deployment overviews and both Websites tabs return to healthy.

Use the actual configured stack name when scaling:

```bash
docker service scale <stack-name>_api=0
docker service scale <stack-name>_api=1
```

Do not remove stacks, volumes, databases, or secrets for this drill.

## Deferred improvements

- Add a third observer to avoid a two-node ambiguity when one observer fails.
- Consider a deeper readiness endpoint that verifies database access and worker
  freshness; the current public `/health` endpoint proves API-process and route
  availability but is intentionally shallow.
- Add separate frontend checks only if independent web availability alerts are
  worth the additional Telegram messages.
