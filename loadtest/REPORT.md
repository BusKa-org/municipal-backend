# BusKá Load Test — Wrap-up Report

Status: **Smoke, Baseline, and Load (base + Spike + Soak variants) complete.**
Capacity, Stress, and Breakpoint are **deferred** — they require a second,
network-isolated OpenStack VM per the plan, which is real, billable
production-adjacent infrastructure; provisioning it was explicitly deferred
by decision, not attempted. See "What's not in this report" below.

All raw results (k6 summaries/raw JSON, `docker stats` captures, Postgres
slow-query logs, Gunicorn/app logs) are in `loadtest/results/<tier>-<UTC
timestamp>/`, gitignored but present on disk from this run. Referenced
below by directory name for traceability.

## TL;DR

- **The system is healthy at today's real single-city scale** (Baseline:
  Passagem's actual 500 students; even Load's Campina-Grande-scale 1,450
  students runs with a **0% functional error rate** under a gradual ramp).
- **The one, clear, evidence-backed bottleneck is Gunicorn's 4 sync
  workers**, capped by the container's 2-vCPU limit — confirmed by the API
  container pegging at ~100–206% CPU (of its 200% limit) while **Postgres
  sat completely idle (0.00–0.04% CPU)** at every tier, including Load.
  This is not a guess — it's exactly the plan's predicted bottleneck #1,
  now proven and with the alternatives (DB pool exhaustion, slow
  PostGIS/Postgres queries) ruled out by direct measurement.
- **A realistic "all buses depart at once" spike is the real risk**, not
  gradual growth: the same Load-scale traffic delivered as an instant
  burst (Spike variant) collapses to a **53% login failure rate** and
  up to 60-second waits, vs. 0% failures when the same load ramps in over
  2 minutes.
- No database-side issue of any kind was observed at any tier tested.

> ## UPDATE — Gunicorn tuning tested & infrastructure re-modeled
>
> A follow-up investigation **tested recommendation #1 below (switch to
> `gthread`) and rejected it** — it made things dramatically worse — and
> corrected the infrastructure model. The findings in this box **supersede
> the original "tune Gunicorn" recommendation**; the tier tables further
> down are kept as-is for the audit trail.
>
> ### 1. Worker/thread tuning does not help — the app is CPU-bound
>
> Eight worker configurations were A/B-tested at the Campina Grande (Load)
> scale (short 3-min probe, same profile for all). Higher is worse:
>
> | Config (2 vCPU) | req/s | fail % | p95 | auth p95 |
> |---|---|---|---|---|
> | **sync ×3** | **287.6** | 6.5% | **24.2s** | 40.2s |
> | sync ×2 | 265.7 | 6.5% | 26.3s | 42.0s |
> | sync ×4 (original) | 276.9 | 7.0% | 25.5s | 43.9s |
> | sync ×6 | 189.6 | 22.2% | 44.0s | 58.8s |
> | sync ×8 | 248.9 | 11.6% | 31.6s | 53.3s |
> | sync ×12 | 107.6 | 68.5% | 60s | 60s |
> | gthread 3×3 | 71.8 | 80.5% | 60s | 60s |
> | **gthread 5×4** (the recommended "fix") | 91.8 | **93.2%** | 60s | 60s |
>
> The app is **CPU-bound** (JSON serialization + bcrypt on login), so adding
> workers/threads only intensifies contention over the two cores and removes
> the sync worker's implicit admission control. `gthread` was the worst.
> **Kept `sync`/4** (`Dockerfile` reverted, now env-tunable via
> `GUNICORN_WORKERS`/`_THREADS`/`_WORKER_CLASS`).
>
> ### 2. The real lever is CPU cores, and the prod model was too pessimistic
>
> Prod is a single `general.large` VM (**4 vCPU / 8 GB**) with API **and**
> Postgres **co-located, uncapped**. The original runs capped the API at 2
> vCPU, which understates reality: Postgres is nearly idle, so the API
> effectively gets ~3 of the 4 cores. Re-modeled two ways and re-ran the
> full-profile (gradual-ramp) suite:
>
> - **Today (co-located, API≈3 / DB≈1, sync 4):**
>   - Baseline (Passagem): ~171 req/s, **0% fail**, p95 ~10 ms.
>   - Load (Campina Grande, gradual): ~490 req/s, **0% fail**, p95 ~200 ms —
>     the *only* miss was login p95 458 ms vs a 300 ms target.
>   - Spike: ~348 req/s, **5.1% fail**, p95 19.7s (auth fail 38%).
>   - Soak (2h30 sustained at Load scale): ~545 req/s, **0% fail**,
>     overall p95 ~177 ms, auth p95 368 ms (same login-only miss pattern
>     as short Load — not a time-decay effect). API RSS stable
>     (~288→303 MiB); DB grew ~61→219 MiB (normal cache warmup).
>     `results/load-soak-20260724T184831Z`.
> - **DB separated (API 4 vCPU dedicated, sync 8):**
>   - Load: ~491 req/s, **0% fail**, p95 ~10 ms, login ~90 ms — **full pass**.
>   - Spike: ~370 req/s, **4.1% fail**, p95 18.9s (auth fail 31%).
>
> **Conclusion:** today's 4-vCPU VM already handles both a small town and a
> medium city (Campina Grande) under **normal gradual load** with 0%
> failures, and holds that performance for **2.5 hours of continuous
> load** with no memory leak or rising error rate. The only real gap is
> the **simultaneous spike**, which is a CPU concentration problem:
> separating the DB (cheap, validated) helps but doesn't fully solve it —
> the durable fix is client-side jittered retry/backoff plus additional
> CPU capacity.
>
> ### 3. Endurance (soak) — completed
>
> Single 2.5h soak on the **today (co-located)** model, with the fixed
> harness (`K6_RAW` off — earlier attempt starved k6 on a 12 GB JSONL
> stream and was discarded). Wall-clock ≈ k6 clock (2h33m). JWT client
> refresh kept auth healthy past the 2h token TTL.
>
> | Metric | Value |
> |---|---|
> | Duration | 2h33m (full profile) |
> | Requests | 5,012,913 |
> | Throughput | **545.5 req/s** |
> | HTTP failures | **0.00%** |
> | Overall p95 / p99 | **177 ms / 567 ms** |
> | auth p95 | 368 ms (threshold 300 ms — only miss) |
> | student_browsing p95 | 170 ms |
> | live_tracking_poll p95 | 176 ms |
> | driver_gps p95 | 184 ms |
> | student_geofence_gps p95 | 179 ms |
> | dashboard_reports p95 | 303 ms |
> | API memory | 288 → 303 MiB (stable) |
> | DB memory | 61 → 219 MiB (cache warmup, then flat) |
>
> Gate: **pass for endurance** (no degradation). Login p95 above target is
> the same CPU-bound bcrypt pattern seen on the short Load run, not soak
> drift.
>
> _Raw data: `results/load-quick-*` (config A/B), `results/{baseline,load,load-spike}-20260724T12*` (official two-model suite), `results/load-soak-20260724T184831Z` (endurance)._

## Results by tier

Thresholds per `loadtest/k6/lib/thresholds.js`: reads/polling p95<300ms,
GPS writes p95<500ms, dashboard/reports p95<1500ms, error rate <1% (all
flows except dashboard/reports, which is allowed higher latency by design).

### 1. Smoke — "Pilot Run" (`results/smoke-20260724T034506Z`)

1 município (own seed-data scale: 4 buses, 20 students), 52 max VUs, ~70s.

| Flow | p95 | p99 | max | error rate |
|---|---|---|---|---|
| auth | 86.7ms | 175.2ms | 176.8ms | 0.00% |
| dashboard_reports | 5.2ms | 5.2ms | 5.2ms | 0.00% |
| driver_gps | 18.5ms | 34.0ms | 39.3ms | 0.00% |
| live_tracking_poll | 11.0ms | 11.9ms | 12.6ms | 0.00% |
| student_browsing | 13.7ms | 14.9ms | 57.0ms | 0.00% |
| student_geofence_gps | 13.2ms | 13.8ms | 14.2ms | 0.00% |

**All thresholds passed.** Harness validated end-to-end. Gate to Baseline: clear.

### 2. Baseline — "Morning Rush, One Small Town" (`results/baseline-20260724T040214Z`)

1 município (Passagem, PB scale: 14 buses, **500 students** — sourced
fact), 1,190 max VUs, ~6.7 min.

| Flow | p95 | p99 | max | error rate |
|---|---|---|---|---|
| auth | 63.8ms | 76.7ms | 154.6ms | 0.00% |
| dashboard_reports | 17.0ms | 21.9ms | 23.2ms | 0.00% |
| driver_gps | 5.6ms | 9.5ms | 37.2ms | 0.00% |
| live_tracking_poll | 3.2ms | 5.2ms | 59.4ms | 0.00% |
| student_browsing | 4.7ms | 6.8ms | 66.0ms | 0.00% |
| student_geofence_gps | 4.0ms | 6.0ms | 68.6ms | 0.00% |

**All thresholds passed, 0% errors, 68,148 requests.** API container CPU
peaked around 60% of its 2-vCPU limit (~1.2 cores); Postgres CPU was
negligible throughout. **No Gunicorn tuning triggered** — per the plan's
"measure before optimizing" principle, since no degradation was observed,
the unmodified config was carried forward into Load rather than tuning
speculatively.

### 3. Load — "Full City Capacity" (`results/load-20260724T040940Z`)

1 município (Campina Grande, PB's actual fleet: **39 buses** — sourced
fact — and a derived ~1,450 concurrent students), 3,448 max VUs, gradual
2 min ramp + 10 min sustain + 1 min ramp-down.

| Flow | p95 | p99 | max | error rate |
|---|---|---|---|---|
| auth | 9.85s | 15.0s | 48.3s | 0.50% |
| dashboard_reports | 3.98s | 7.92s | 8.91s | 0.00% |
| driver_gps | 3.22s | 11.7s | 19.7s | 0.09% |
| live_tracking_poll | 3.40s | 11.3s | 31.3s | 0.13% |
| student_browsing | 2.23s | 10.4s | 21.6s | 0.08% |
| student_geofence_gps | 3.39s | 11.2s | 23.9s | 0.11% |

**All latency thresholds failed** (overall error rate still low, 0.107% of
351,272 requests — this is a latency/queueing failure, not a functional
one). k6 exit code 99 (thresholds crossed).

**Root-cause evidence** (this is the deliverable the plan asked for — "understand and document the failure mode"):
- API container CPU: **pegged at 116–206% of its 200% (2-vCPU) limit**
  continuously through the 10-minute sustain window.
- Postgres/DB container CPU: **0.00–0.04%** — completely idle.
- Postgres slow-query log (200ms threshold): only **2 queries** over 200ms
  in the entire 13-minute run (265ms, 276ms) — noise, not a pattern.
- Gunicorn logs: 4 workers booted once at startup, **zero worker
  timeouts, zero restarts** — ruling out crash-looping as a cause.
- Latency distribution is bimodal (e.g. auth: med=131ms but p95=9.85s,
  max=48.3s) — the signature of **queueing**, not per-request slowness:
  most requests get a free worker quickly, a growing tail waits behind
  many others.

**Conclusion: this is Gunicorn's 4-sync-worker ceiling, confirmed by
elimination of the other two candidates in the plan (DB pool exhaustion,
CPU-bound Postgres/PostGIS queries) — not a guess.** The container's
2-vCPU allocation (matching the actual prod VM split) is saturated by only
4 synchronous workers well before 3,448 concurrent VUs, while the database
underneath has essentially unlimited remaining headroom.

#### 3a. Spike variant — "Dawn Departure" (`results/load-spike-20260724T042453Z`)

Same Load dataset/VU target (3,448), but ramped to full concurrency in
**10 seconds** instead of 2 minutes — simulating every route's 5:30–6:00 AM
departure happening at once.

| Flow | p95 | p99 | max | error rate |
|---|---|---|---|---|
| auth | 52.3s | 60.0s (timeout) | 60.0s | **53.14%** |
| dashboard_reports | 6.2s | 6.8s | 6.9s | 0.00% |
| driver_gps | 26.8s | 50.1s | 59.9s | 3.82% |
| live_tracking_poll | 26.0s | 48.2s | 60.0s (timeout) | 5.75% |
| student_browsing | 23.8s | 44.3s | 60.0s (timeout) | 3.14% |
| student_geofence_gps | 25.9s | 47.9s | 60.0s (timeout) | 5.07% |

**Overall error rate 12.2%** of 52,580 requests — a dramatic step up from
Load's 0.1%, despite the exact same eventual VU count. The `max` values
sitting exactly at 60.0s across every flow are client-side request
timeouts (k6's default), not server 5xx responses — requests were still
queued in Gunicorn's backlog when the client gave up.

**This is the single most actionable finding in this report.** The
"everyone logs in for the 5:30 AM run" pattern is not a hypothetical edge
case for a school-transport app — it is the expected daily traffic shape.
The same infrastructure that handles a *gradual* ramp to this scale with
0% functional errors **fails on over half of all login attempts** when
that same demand arrives as a burst.

#### 3b. Soak variant — "School-Term Soak" (`results/load-soak-20260724T042953Z`)

**Deviation from the plan, disclosed:** the plan specifies a 4–8 hour
sustain to catch slow-burn issues. Run here for **20 minutes** sustain
(23 min total) instead, to fit a single interactive session — long enough
to observe ~10 cycles of the 2-minute `job_10min` APScheduler job
(`app/utils/scheduler_setup.py`), but **not a substitute for the full
4–8h run**, which is recommended before treating soak stability as fully
validated. `loadtest/tiers/load-soak.json` documents this and how to
restore the full duration.

| Flow | p95 | p99 | max | error rate |
|---|---|---|---|---|
| auth | 6.95s | 12.2s | 16.5s | 0.13% |
| dashboard_reports | 2.25s | 5.9s | 7.3s | 0.00% |
| driver_gps | 2.29s | 7.2s | 16.1s | 0.06% |
| live_tracking_poll | 2.30s | 7.3s | 21.2s | 0.06% |
| student_browsing | 2.20s | 6.7s | 21.2s | 0.04% |
| student_geofence_gps | 2.30s | 7.3s | 21.2s | 0.05% |

Same latency-threshold failure pattern as base Load (same root cause,
same VU count), but notably **no upward drift**: API memory stayed flat
(~310–340MB) for the full 20 minutes, CPU fluctuated in the same
116–206% band with no trend, and the Postgres slow-query log had only 5
entries in 23 minutes with no connection errors (`FATAL`/`PANIC`/"too many
connections" all absent from the logs). **No sign of connection-pool
drift or scheduler-job interference within the window actually tested** —
but again, this is a 20-minute window standing in for a 4–8 hour
requirement, so absence of drift here is encouraging, not conclusive.

## Bugs found and fixed along the way

None of these change the load-test conclusions above, but are worth
tracking as real findings from this exercise:

1. **Production landmine (not yet fixed in prod code):** `database/init.sql`'s
   first statement (`CREATE ROLE buska_user ...`) fails on a **truly fresh**
   Postgres container where `POSTGRES_USER` env var has already pre-created
   that role — and `docker-entrypoint.sh` aborts its *entire* init sequence
   on that failure, meaning the `uuid-ossp`/`postgis` extension statements
   later in the same file **never run**. Any future from-scratch prod
   deploy (new VM, disaster recovery) would fail at first migration with
   `function uuid_generate_v4() does not exist`. Worked around here with a
   minimal, idempotent `loadtest/db-init/extensions.sql`, but the real fix
   belongs in `database/init.sql` itself (make role creation idempotent, or
   drop it entirely since `POSTGRES_USER` already handles it).
2. **`generate_data.py` CPF collision across tiers (fixed):** a single
   global `random.seed(42)` meant two different tiers' first município
   drew the *same* "random" CPF, since `wipe_prefeitura_data()` only clears
   the current tier's município, not previously-generated ones still in
   the DB. Fixed by salting the seed per-município
   (`random.seed(f"{tier_seed}:{codigo_ibge}")`), keeping reproducibility
   while eliminating collisions.
3. **OSRM stub path-parsing bug (fixed):** `urllib.parse.urlparse` splits
   off a leading `;`-delimited segment into a legacy `params` field (RFC
   2396), which corrupts OSRM's `{lng1},{lat1};{lng2},{lat2}` coordinate
   syntax. Fixed with plain string partitioning instead.
4. **`routing_service.py` hardcoded OSRM URL (fixed, safe no-op in prod):**
   added an `OSRM_BASE_URL` environment override so the load-test stub
   could be targeted without touching the default behavior (still
   `https://router.project-osrm.org` unless the env var is set).

## Infra recommendations (evidence-backed, not speculative)

1. **~~Tune Gunicorn~~ — SUPERSEDED (see UPDATE box at top).** This was
   tested and **rejected**: switching to `gthread` (and every other
   worker/thread increase) regressed performance because the app is
   CPU-bound, not I/O-blocked. Kept `sync`/4. Do **not** raise worker/thread
   counts on the current 2-vCPU-per-API allocation.
2. **The capacity lever is CPU cores, not worker config.** Under gradual
   load the current 4-vCPU VM already serves Campina Grande at 0% failures;
   for extra headroom (and to clear the login-latency near-miss), **separate
   Postgres onto its own host** so the API gets a full 4 vCPU — validated to
   bring Load to a full pass (login ~90 ms). This is cheaper than upsizing
   the VM and the DB is idle enough to run comfortably on a small host.
3. **Treat the Spike/"Dawn Departure" finding as the priority.** It is the
   only scenario that still fails (~4–5% overall, ~31–38% of logins) even
   with the DB separated. Address it in the **client**: jittered
   retry/backoff on login to spread the thundering herd over a few seconds,
   plus additional CPU capacity for the burst.
4. **Fix the `database/init.sql` role-creation bug** (finding #1 above)
   before it causes a real incident on the next from-scratch deploy.
5. **Re-run Load, Spike, and Soak (full 4–8h) after the Gunicorn change**,
   then revisit Capacity/Stress/Breakpoint on a second VM — those still
   need the explicitly-deferred second OpenStack host to produce
   meaningful (non-single-host) numbers.

## What's not in this report

- **Capacity ("Regional Rollout"), Stress ("Statewide Expansion"), and
  Breakpoint ("Ceiling Discovery")** — deferred by explicit decision. They
  require a second OpenStack VM (`general.large`, matching prod) per the
  plan's "Isolated test environment" section, since local Docker Compose
  on one machine stops being representative once modeling multiple
  concurrent municípios and real network latency between k6 and the
  system under test. Provisioning that VM means spinning up real,
  billable infrastructure via `infra/terraform/`, which was not undertaken
  this session. `loadtest/tiers/capacity.json`, `stress.json`, and
  `breakpoint.json` are already written and ready to run once that VM
  exists — see `loadtest/README.md` §4.
- **Load-Soak's full 4–8 hour duration** — run at 20 minutes instead (see
  §3b above); no drift observed in that window, but not a substitute for
  the full-length run.

## CI

`loadtest/run_tier.sh smoke` and `loadtest/run_tier.sh baseline` are now
promoted into a manual CI check:
[`.github/workflows/loadtest-regression.yml`](../.github/workflows/loadtest-regression.yml)
(`workflow_dispatch`, ~10–15 min, runs on a standard GitHub-hosted
runner against `docker-compose.loadtest.yml`). Load's Spike/Soak variants
and Capacity/Stress/Breakpoint remain manual/exploratory
(`loadtest/run_tier.sh <tier>` on real infra), per the plan, given their
cost and infrastructure requirements.
