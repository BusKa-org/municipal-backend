# ADR-0001 — Tiered load-testing harness (k6 + isolated Compose stack + OSRM stub)

- **Status:** Proposed — open for comment
- **Date:** 2026-08-05
- **Introduced by:** [PR #35](https://github.com/BusKa-org/municipal-backend/pull/35)
- **Evidence:** [`loadtest/REPORT.md`](https://github.com/BusKa-org/municipal-backend/blob/main/loadtest/REPORT.md)
  (results),
  [`loadtest/README.md`](https://github.com/BusKa-org/municipal-backend/blob/main/loadtest/README.md)
  (how to run)

> Every path in this document is written in full, from the root of the
> `buska-backend` repository, and every link is absolute, so both stay
> resolvable when this document is read outside of GitHub. The one exception is
> the diagram in §3.1, whose image link must stay repository-relative to render
> on GitHub; its full path is given in the caption beneath it.

**The chain of logic:** we had a question we could not answer (§1), so we built
something to answer it (§2), which works like this (§3), for these reasons
(§4), and it told us this (§5), at this cost (§6), leaving this to do (§7) and
this still undecided (§8).

## 1. Context — the question we could not answer

BusKá is deployed on a single OpenStack `general.large` VM (4 vCPU / 8 GB) with
the Flask API and Postgres/PostGIS **co-located on that one host**. Before this
work, nobody could answer three questions with evidence:

1. Does the current VM actually hold a real municipality's morning rush?
2. When it eventually breaks, *what* breaks first — Gunicorn, the connection
   pool, or PostGIS?
3. How much room is left before a second município can be onboarded?

School transport has an unusually brutal traffic shape: essentially the entire
user base logs in within the same few minutes before the 5:30–6:00 AM
departure, then GPS pings and live-tracking polls run continuously for about an
hour. Averages are meaningless here; only a burst-shaped test tells the truth.

The constraint that shaped nearly every decision below: **the only real
infrastructure that exists is production.** There is no staging VM, and
provisioning a second one costs real money, so the harness had to produce
useful answers from a laptop or a CI runner while remaining honest about where
that stops being representative.

## 2. Decision — what we built

Build a **tiered** harness — Smoke → Baseline → Load → Capacity → Stress →
Breakpoint — where a tier is a JSON file describing real-world sizing (how many
students, how many buses, in which municipality) plus a ramp shape, and a
single k6 orchestrator turns that into a weighted mix of user scenarios. The
system under test runs in a dedicated Docker Compose stack that never touches
production, with every external dependency neutralized.

## 3. How the harness works

### 3.1 Architecture

![Load-testing harness architecture: run_tier.sh drives generate_data.py, k6
and observe.sh against an isolated Compose stack of api, db and osrm-stub,
collecting everything into a timestamped results directory.](images/0001-load-test-architecture.png)

*Diagram file: `docs/adr/images/0001-load-test-architecture.png`, generated
from the editable source `docs/adr/images/0001-load-test-architecture.svg`.
When exporting this document to a format that cannot follow repository paths,
insert that PNG here.*

| Component | Responsibility |
|---|---|
| `loadtest/tiers/*.json` | The only place sizing lives. Each município entry carries a `source_note` recording whether its numbers are a sourced fact or a derived assumption. |
| `loadtest/generate_data.py` | Builds the dataset for a tier directly in the DB. Bulk Core inserts (not per-object ORM adds) so the Breakpoint tier's ~99k students is minutes, not hours. Idempotent per tier: re-running wipes and regenerates only the municípios named in that config. |
| `loadtest/k6/main.js` | Derives per-scenario VU counts from the tier's sizing and applies one ramp shape (`{duration, fraction}` stages) across all scenarios at once. |
| `loadtest/k6/scenarios/*.js` | One file per user action: auth, student browsing, driver GPS, student geofence GPS, live tracking poll, dashboard reports (default mix) + routing proxy and batch trip generation (opt-in). |
| `loadtest/k6/lib/thresholds.js` | Pass/fail criteria as code, identical at every tier. See §3.4. |
| `loadtest/osrm-stub/` | ~150-line stdlib-only OSRM-compatible server returning synthetic straight-line geometry with configurable latency/jitter/error rate. |
| `loadtest/run_tier.sh` | One command per tier: health check → generate data → start observability → run k6 → collect everything into `loadtest/results/<tier>-<timestamp>/`. |
| `loadtest/observe.sh` | Captures the evidence needed to attribute a failure: `docker stats`, Postgres slow-query log, Gunicorn logs. |
| `docker-compose.loadtest.yml` | The isolated stack itself: resource limits, slow-query logging, neutralized external services. |

### 3.2 The tiers — how much load

Each tier is one JSON file in `loadtest/tiers/`. `concurrent_students` and
`concurrent_trips` are the only inputs the scenario mix reads; everything else
in the file describes the dataset to generate.

| Tier | Question it answers | Scale | Ramp shape | Status |
|---|---|---|---|---|
| `smoke` — *Pilot Run* | Does the harness itself work end to end? | 1 município, 20 students / 4 buses | 10s up, 40s hold | ✅ passed |
| `baseline` — *Morning Rush, One Small Town* | Does today's real deployment hold a real small town? | Passagem, PB: 500 students / 14 buses | 1m up, 5m hold | ✅ passed, 0% errors |
| `load` — *Full City Capacity* | Can one VM serve a medium city? | Campina Grande, PB: 1,450 students / 39 buses | 2m up, 10m hold | ⚠️ latency thresholds fail (queueing, not errors) |
| `load-spike` — *Dawn Departure* | What happens when everyone logs in at once? | same dataset as `load` | **10s** up, 3m hold | ❌ 53% login failures — the key finding |
| `load-soak` — *School-Term Soak* | Does it degrade over hours? | same dataset as `load` | 2m up, **2h30m** hold | ✅ 0% errors, no memory drift |
| `load-quick` | A/B probe for worker-config tuning | same dataset as `load` | 30s up, 3m hold | ✅ used for the 8-config comparison |
| `capacity` — *Regional Rollout* | Can we onboard several municípios? | 5 municípios, 6,950 students / 96 buses | 2m up, 10m hold | ⏸ deferred — needs a 2nd VM |
| `stress` — *Statewide Expansion* | Where does it start failing? | 20 municípios, 29,450 students / 361 buses | 3m up, 10m hold | ⏸ deferred — needs a 2nd VM |
| `breakpoint` — *Ceiling Discovery* | Where is the hard ceiling? | 99,225 students / 2,682 buses | 6-step climb to 100% | ⏸ deferred — needs a 2nd VM |

The three deferred tiers are fully written and runnable; what they lack is
honest infrastructure, not code (§7, item 4).

### 3.3 The scenarios — what kind of load

Eight scenarios in `loadtest/k6/scenarios/`, six in the default mix and two
opt-in. Each models one real user behaviour, and each tags every HTTP call with
a `flow` label so thresholds and results are attributable per behaviour rather
than as one undifferentiated average.

| Scenario file | Models | Endpoints | Cadence | VUs derived from |
|---|---|---|---|---|
| `loadtest/k6/scenarios/auth.js` | Login storms | `POST /v1/auth/login` | 5–15s think time | 5% of `concurrent_students` |
| `loadtest/k6/scenarios/student_browsing.js` | Students checking routes/schedule/notices | `GET /v1/rotas/`, `/v1/viagens/aluno/agenda`, `/v1/notificacoes/` | 1–4s between calls, 5–15s between cycles | `concurrent_students` (highest count) |
| `loadtest/k6/scenarios/driver_gps.js` | The bus streaming its position | `POST /v1/viagens/{id}/localizacao` | every 5–10s | `concurrent_trips` |
| `loadtest/k6/scenarios/student_geofence_gps.js` | Student phones reporting position for auto check-in | `POST /v1/viagens/{id}/localizacao-aluno` | every 5–10s | `concurrent_students` |
| `loadtest/k6/scenarios/live_tracking_poll.js` | Students watching the live map | `GET /v1/viagens/{id}/localizacao` | every 5–10s | 30% of `concurrent_students` |
| `loadtest/k6/scenarios/dashboard_reports.js` | Gestor opening reports | `GET /v1/dashboard/relatorios/periodo` (7-day range) | every 30–60s | one per município |
| `loadtest/k6/scenarios/routing_proxy.js` *(opt-in)* | Route preview via OSRM | `GET /v1/routing/route` | 5–15s | min(20, students) |
| `loadtest/k6/scenarios/batch_trip_generation.js` *(opt-in)* | The Sunday 02:00 scheduler job | `POST /v1/viagens/gerar-lote` | one pass per gestor | `shared-iterations` |

Why each one is a separate scenario rather than folded into another:

- **`auth.js`** is the only scenario that deliberately *bypasses* the shared
  token cache in `loadtest/k6/lib/auth.js`. Every other scenario logs in once
  and reuses the JWT, which is what real clients do; `auth.js` re-logs in
  continuously because `POST /v1/auth/login` is the one endpoint with no
  effective rate limiting (`AUTH_RATE_LIMIT` in `app/utils/security.py` is a
  constant — flask-limiter is not actually wired up), and it runs bcrypt on
  every call. It turned out to be the most expensive endpoint in the system,
  and the first to collapse.
- **`student_browsing.js`** deviates from the obvious endpoint list on purpose.
  `GET /v1/viagens/` is gestor-only (`list_viagens_gestor` in
  `app/services/viagens_service.py` rejects non-`GESTOR` roles), so pointing a
  student session at it would generate a wall of 403s — cheap responses that
  look like traffic but exercise nothing. The student-facing equivalent,
  `/v1/viagens/aluno/agenda`, is used instead.
- **`driver_gps.js`** exists separately from the student GPS stream because it
  is a different write path: `atualizar_localizacao` in
  `app/services/viagens_service.py` does a synchronous `TelemetriaViagem`
  insert *plus* a geofence distance check on every call. Each VU walks its
  coordinate slightly between pings so "distance moved" is never trivially
  zero.
- **`student_geofence_gps.js`** is the highest write volume in the system at
  Load scale and above, simply because students vastly outnumber trips and
  every call is a synchronous `UPDATE` on `alunos_confirmados`. Separating it
  from `driver_gps.js` is what makes it possible to tell those two write paths
  apart in the results.
- **`live_tracking_poll.js`** reads exactly the rows `driver_gps.js` is
  concurrently writing. It is deliberately not folded into
  `student_browsing.js` so that read-contention against hot, actively-written
  rows shows up under its own tag.
- **`dashboard_reports.js`** is low-frequency by design — gestores do not
  refresh dashboards every few seconds — but it issues the heaviest aggregate
  queries in the app, so it gets its own far looser budget rather than dragging
  the shared one down.
- **`routing_proxy.js`** is opt-in because it only ever exercises the stub in
  `loadtest/osrm-stub/`. It measures our proxy layer, not a real routing
  engine, so including it in the default mix would inflate the numbers with
  synthetic latency we chose ourselves.
- **`batch_trip_generation.js`** is opt-in and uses a `shared-iterations`
  executor rather than a sustained loop, because it models a burst job
  (`job_gerar_viagens_semanais` in `app/utils/scheduler_setup.py`) that runs
  once a week at 02:00 — mixing it into steady-state user traffic would
  describe a situation that never happens.

The mix weights come from the tier's sizing, with two exceptions flagged in
`loadtest/k6/main.js` as our own modelling assumptions rather than sourced
facts: 5% of students re-authenticating and 30% actively watching the map at
any moment. Both materially change the generated load (§8, question 3).

### 3.4 The metrics — what counts as passing, and why

A run produces two kinds of number: the ones that decide pass/fail, and the
ones that explain *why* it failed. Only the first kind is a threshold.

**Gated — `loadtest/k6/lib/thresholds.js`**

| Metric | Applies to | Budget | Why this number |
|---|---|---|---|
| `http_req_duration` p95 | `auth`, `student_browsing`, `live_tracking_poll` | **< 300 ms** | A person is waiting on these. 300 ms is roughly where a mobile screen stops feeling instant, and these are simple indexed reads — if they exceed it, the cause is queueing, not work. |
| `http_req_duration` p95 | `driver_gps`, `student_geofence_gps` | **< 500 ms** | Nobody is waiting on a GPS ping, but every device sends one every 5–10 s. The budget is set an order of magnitude under that interval so writes cannot start overlapping their own cadence and compounding. |
| `http_req_duration` p95 | `dashboard_reports` | **< 1500 ms** | A gestor deliberately asked for a report over a date range and will tolerate a beat. Given its own budget so the heaviest aggregate query in the app does not consume everyone else's. |
| `http_req_failed` rate | every flow | **< 1%** | Not a comfortable number — at Load scale 1% is still hundreds of failed requests a minute. It is the line above which something is structurally wrong, not a tolerance we are happy to spend. |
| `http_req_failed` rate | `batch_trip_generation` | **< 1%** | The only budget it gets. For a weekly batch job, latency is close to meaningless; "did it complete without error" is the whole question. |

Three deliberate choices behind that table:

- **p95, not the average.** The traffic shape is a burst, and an average is
  exactly the statistic that hides a burst. p90, p99 and max are recorded in
  every summary for diagnosis but are not gated, because at low request counts
  p99 is one unlucky request rather than a signal.
- **Per behaviour, not one global budget.** Every HTTP call carries a `flow`
  tag, so a failure names the behaviour that broke instead of reporting that
  "the API" is slow. That is what makes the report able to say *logins*
  collapsed while GPS writes stayed clean.
- **The same numbers at every tier.** A threshold that relaxes as load grows
  can never fail, which makes it decoration. At Stress and Breakpoint,
  threshold failure is the *expected* outcome and is interpreted by a human
  reading the report — the goalposts do not move to make the run look good.

**Observed but not gated — `loadtest/observe.sh`**

These do not decide pass/fail; they are what makes a failure attributable to a
component instead of leaving "it got slow" as the conclusion.

| Capture | What it settles |
|---|---|
| Container CPU and memory (`docker stats`) | Which container is the constraint. This is how we established the API, not Postgres, is the bottleneck — and how the soak run showed no memory drift. |
| Postgres slow-query log (anything over 200 ms, configured in `docker-compose.loadtest.yml`) | Whether a slow request means a slow *query* or a request that spent its time queued before reaching the database. |
| Gunicorn logs | Worker timeouts and restarts — the difference between "slow" and "the worker died and took its requests with it". |

One honest caveat: these budgets are defensible engineering defaults, not a
product SLO, because no SLO exists yet (§8, question 2).

## 4. Why it is built this way

**A tiered plan rather than one big test.** Each tier answers a different
question and has a go/no-go gate into the next. It also means a failure is
already bracketed: Baseline passing and Load failing localizes the problem to a
known range instead of producing "it broke somewhere."

**Sizing in JSON, not in the k6 scripts.** The scenarios are about *behaviour*;
the tier files are about *scale*. Separating them means the same scenario files
serve every tier, and re-sizing a tier is a data edit reviewable by someone who
does not read JavaScript. It also forced the `source_note` discipline — every
number is marked as sourced or assumed, so nobody later mistakes a modelling
guess for a researched fact.

**k6 as the generator.** Scenarios are plain JS modules, thresholds are
declarative and live in version control, `ramping-vus` expresses the burst
shapes this domain needs, and it ships as a single binary with a first-party
GitHub Action. Locust and JMeter were not formally benchmarked against it (§8,
question 1).

**A dedicated Compose stack, never `docker-compose.prod.yml`.** A load test
that can reach production is one typo away from an outage. The separate
`docker-compose.loadtest.yml` also lets the stack differ where it must:
resource limits, slow-query logging, and neutralized external services. Limits
are set to 2 vCPU / 4 GB per container — half the prod VM each — to model API
and Postgres sharing the one real host.

**A local OSRM stub instead of the public demo server.** Load-test volumes
against `router.project-osrm.org` would be both rate-limited and a ToS
violation. Self-hosting real OSRM needs a multi-GB regional extract and a long
preprocessing step for no benefit here: `app/services/routing_service.py`
consumes only distance, duration, and a coordinate list, and never checks that
the geometry follows real roads. Reaching the stub required one production code
change — `OSRM_BASE_URL` as an environment override, defaulting to exactly the
previous hardcoded URL, so prod behaviour is unchanged unless the variable is
set.

**Fake Firebase credentials as a mounted fixture, not a code change.** Firebase
initialization in `app/__init__.py` (`create_app()`) is unconditional and kills
Gunicorn's worker boot under `FLASK_ENV=production` if credentials are absent.
The alternative — making initialization conditional — is a real behaviour
change to production startup, made to satisfy a test harness. Mounting a
syntactically valid but functionally dead service account at
`loadtest/fixtures/firebase-credentials.fake.json` keeps the change entirely
outside the application. No exercised endpoint reaches
`firebase_admin.messaging.send`, which is gated behind a per-user `fcm_token`
the generated users never set.

**Gunicorn settings became environment-tunable.** Concurrency had to be A/B
tested against one image, which is impossible with values baked into the
`Dockerfile`'s `CMD`. `GUNICORN_WORKERS` / `_THREADS` / `_WORKER_CLASS` /
`_TIMEOUT` default to exactly the previous `sync`/4/120s, so this is a no-op in
production until someone deliberately overrides it.

**CI runs Smoke and Baseline only, and only on demand.**
`.github/workflows/loadtest-regression.yml` is `workflow_dispatch`. A shared
GitHub-hosted runner has neither stable CPU allocation nor enough of it to
produce trustworthy latency numbers at Load scale and above, and a 10–15 minute
job on every PR would be a bad trade. Smoke and Baseline are cheap enough to be
worth having as a manual regression check that the harness itself still works.

**A minimal `loadtest/db-init/extensions.sql` instead of the repo's
`database/init.sql`.** Mounting the real one fails: its first statement
(`CREATE ROLE buska_user`) errors because `POSTGRES_USER` already created that
role, and `docker-entrypoint.sh` aborts the *entire* init sequence on that
failure — so `uuid-ossp` and `postgis` never get created. This is a latent
production bug, not a load-test-only quirk (§6, item 4).

## 5. What it told us

Recorded here because it is the justification for the harness existing at all;
full numbers and raw-data references are in
[`loadtest/REPORT.md`](https://github.com/BusKa-org/municipal-backend/blob/main/loadtest/REPORT.md).

- The bottleneck is **CPU on the API container**, confirmed by elimination, not
  guessed: Postgres sat at 0.00–0.04% CPU at every tier while the API pegged
  its limit, with only a handful of slow queries and zero worker timeouts.
- The obvious fix was **tested and rejected**. Eight worker configurations were
  A/B tested; `gthread` was the worst of them (93% failure rate). The workload
  is CPU-bound on JSON serialization and bcrypt, so more workers only add
  contention. Without the harness this would have shipped as a plausible-
  sounding "tune Gunicorn" change that made production worse.
- The real risk is the **burst, not growth**: the same load that runs at 0%
  errors when ramped over two minutes fails ~53% of logins when it arrives in
  ten seconds. That reframes the fix as client-side jittered retry plus CPU
  headroom, rather than anything in the query layer.

## 6. Consequences

**Accepted costs**

1. **The harness is a maintained surface.** New endpoints do not appear in the
   scenario mix by themselves; the mix will drift from reality unless someone
   updates it. `loadtest/generate_data.py` is also coupled to the models and
   will break on schema changes.
2. **Three production files changed for testability**: `Dockerfile`,
   `app/services/routing_service.py`, `.gitignore`. Each is a defaults-
   preserving no-op, but they are still production files carrying test-driven
   changes.
3. **`loadtest/fixtures/firebase-credentials.fake.json` contains a real
   RSA-shaped private key.** It is synthetic and worthless, but secret scanners
   cannot know that — it is already the top hit when running gitleaks over this
   repo. Whatever secret scanning gets adopted will need this path allowlisted,
   and every future reader will have to be told it is fake.
4. **A production landmine is documented but not fixed.** The
   `database/init.sql` role-creation bug means a from-scratch deploy (new VM,
   disaster recovery) fails at first migration with
   `function uuid_generate_v4() does not exist`. This ADR's stack routes around
   it; production still has it.
5. **Results are not portable across machines.** Absolute latencies depend on
   the host. Comparisons are only valid within a run set on one machine, which
   is why the report always cites the
   `loadtest/results/<tier>-<timestamp>/` directory a number came from.

**Deliberately out of scope**

6. **Capacity, Stress, and Breakpoint were not run.** Their tier configs are
   written and ready, but a single host running both the load generator and the
   system under test stops being representative at multi-município scale — k6
   would be stealing CPU from the thing it is measuring. These need a second VM
   and a third host for k6. Deferred by decision, not by oversight.
7. **The multi-município tiers model synthetic clones** of one real sourced
   município, using `codigo_ibge` prefixes (`9500xxxx`/`9600xxxx`) that no
   Brazilian state uses. This is a modelling choice, recorded in each tier's
   `source_note`, not a claim that N distinct towns were independently
   researched.

## 7. Next steps

Ordered by what the evidence says matters, not by effort. Items 1–3 are the
ones with a user-visible consequence today.

**Act on what the harness found**

1. **Fix the dawn login collapse.** ~53% of logins fail when the whole user base
   arrives inside ten seconds, and that is the actual production traffic shape.
   Two complementary directions, neither yet decided: jittered retry with
   backoff on the client so arrivals spread themselves out, and enough API CPU
   headroom to absorb what remains. A third option worth costing: wiring up real
   rate limiting on `POST /v1/auth/login` so a storm degrades predictably
   instead of taking the whole API's CPU with it.
2. **Fix `database/init.sql`.** The role-creation statement aborts the entire
   Postgres init sequence, so a from-scratch deploy fails at first migration.
   Unrelated to load testing except that load testing is how we found it; it
   costs a first-VM rebuild or a disaster recovery to find it otherwise.
3. **Decide whether to keep the Firebase fixture** (§8, question 5) and, either
   way, allowlist `loadtest/fixtures/firebase-credentials.fake.json` in whatever
   secret scanning gets adopted. It is currently the top gitleaks hit in the
   repo, and a scanner that always reports a known false positive stops being
   read.

**Unblock the deferred tiers**

4. **Provision honest infrastructure for Capacity, Stress, and Breakpoint.**
   The tier configs are written; what is missing is a second VM for the system
   under test and a separate host for k6, so the generator is not competing for
   CPU with the thing it measures. Until that exists, any number those tiers
   produce would be a measurement of the laptop.
5. **Re-check the co-location assumption at multi-município scale.** Postgres
   idled at 0.00–0.04% CPU at every tier we ran, so splitting the database onto
   its own host buys nothing *today*. That conclusion is only valid up to Load
   scale, and should be revisited the first time Capacity runs for real.

**Make it stay true**

6. **Turn the thresholds into an actual SLO.** The numbers in §3.4 are
   defensible defaults chosen by the harness author. Once product commits to
   real targets, `loadtest/k6/lib/thresholds.js` becomes the executable form of
   that commitment rather than one engineer's opinion.
7. **Keep the scenario mix in sync with the API.** New endpoints do not add
   themselves. The cheapest enforcement is a line in the PR checklist asking
   whether a new endpoint belongs in the mix; the alternative is discovering in
   six months that the harness tests a version of the product that no longer
   exists.
8. **Agree on a re-run trigger.** Before onboarding a second município is the
   obvious one. Worth also considering: any change to the auth path or to the
   GPS write paths, since those are where the measured headroom is thinnest.
9. **Extend the soak once there is somewhere to run it.** 2h30m at Load scale
   showed no memory drift, which is good evidence but shorter than a school
   term's daily cycle. A full-day run is only meaningful on dedicated
   infrastructure, so this is gated on item 4.

## 8. Open questions / call for comments

Genuine uncertainty — pushback on any of these is wanted, ideally as inline
comments on [PR #35](https://github.com/BusKa-org/municipal-backend/pull/35).

1. **Was k6 the right generator?** It was chosen on properties, not on a
   bake-off against Locust or JMeter. If anyone on the team has operational
   experience with an alternative, that experience probably outweighs the
   comparison done here.
2. **Are the thresholds in §3.4 the right ones?** p95 < 300 ms for reads,
   < 500 ms for GPS writes, < 1500 ms for dashboards, < 1% errors. These are
   defensible defaults, not numbers derived from a product SLO — no SLO exists
   yet. If the product view differs, the thresholds should move, and this is
   the cheapest moment to move them.
3. **Should the modelling fractions be defended better?** The mix assumes 5% of
   students are re-authenticating and 30% are actively watching the live map at
   any moment. Both are our assumptions, flagged as such in
   `loadtest/k6/main.js`, and both materially change the generated load.
4. **Is a manual-only CI check enough?** The alternative — Smoke on every PR —
   costs ~10 minutes per PR and produces latency numbers too noisy to gate on,
   so it would only ever catch "the harness broke," and would do it slowly.
5. **Should the Firebase fixture exist at all?** Making `create_app()` in
   `app/__init__.py` skip Firebase initialization when credentials are absent
   is arguably the more honest fix, would delete a fake private key from the
   repo, and would remove a real crash-on-misconfiguration footgun from
   production startup. It was rejected here only to keep the harness from
   changing app behaviour.
6. **Who owns re-running this, and when?** A load test that runs once is a
   snapshot, not a safety net. Before onboarding a second município is the
   obvious trigger; whether anything else should trigger it is undecided.
