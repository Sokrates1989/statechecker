# Statechecker Always-Up Roadmap

Updated: 2026-08-26

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
