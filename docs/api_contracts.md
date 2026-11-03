# API contracts

## Rate limit

Every route is limited by Flask-Limiter. Over the limit, the API answers `429`
with the standard error body (`code: "RATE_LIMITED"`, `details.limit` is the
limit that was hit) and a `Retry-After` header in seconds. Every limited
response also carries `X-RateLimit-Limit`, `X-RateLimit-Remaining` and
`X-RateLimit-Reset`.

Counting key depends on the route:

- Login and forgot-password count **per e-mail**, never per IP: school Wi-Fi
  and mobile carrier NAT put many students behind one IP, so a per-IP limit
  would block whole classes and let one person lock everyone out. The key is
  the `email` from the JSON body, trimmed and lowercased. A body without a
  valid e-mail (missing, not a string, no `@`, over 254 chars, not JSON)
  counts in one shared `sem-email` bucket; those requests fail validation
  anyway. Known trade-off: anyone can use up a victim's e-mail bucket and block
  that one user's login for up to a minute.
- `POST /v1/auth/reset-password`: the JSON body's `email` if it has one,
  otherwise the JSON body's `token` (never the query string or a form). No
  token: one shared `sem-token` bucket.
- `GET`/`POST /v1/alunos/guardian-consent/<token>`: the token in the URL.
- Every other route (`change-password`, real-time GPS and the default limit):
  the JWT identity when the request has a valid token, otherwise the connection
  IP (`request.remote_addr`). The app has no `ProxyFix`, so `X-Forwarded-For`
  is ignored; behind a reverse proxy every client would share the proxy's IP,
  so add `ProxyFix` before putting one in front.

E-mails, tokens and IPs only enter the counter keys as an HMAC-SHA256 keyed
with `JWT_SECRET_KEY` (LGPD: no personal data in clear text in the storage).

Each route and each HTTP method counts on its own (`GET` and `POST` on the
same path have separate counters). CORS preflight (`OPTIONS`) is never
counted, and CORS exposes `Retry-After` and `X-RateLimit-*` to the browser.

| Setting | Default | Routes |
|---|---|---|
| `RATELIMIT_SENSITIVE` | `5 per minute` | `POST /v1/auth/reset-password`, `POST /v1/users/change-password` |
| `RATELIMIT_AUTH` | `10 per minute` | `POST /v1/auth/login`, `POST /v1/auth/forgot-password`, `GET`/`POST /v1/alunos/guardian-consent/<token>` |
| `RATELIMIT_REALTIME` | `120 per minute` | `GET`/`POST /v1/viagens/<id>/localizacao`, `POST /v1/viagens/<id>/localizacao-aluno` |
| `RATELIMIT_DEFAULT` | `2000 per hour` | every other route |
| (none) | | `/health`, `/ready` (probes are never limited) |

Other settings: `RATELIMIT_ENABLED` (default `true`; the test suite and
`docker-compose.loadtest.yml` turn it off) and `RATELIMIT_STORAGE_URI`
(default `memory://`).

Storage: production has no Redis yet, so it runs on `memory://`: each gunicorn
worker keeps its own counters and the real limit is up to N times the setting
with N workers (4 today). Setting `RATELIMIT_STORAGE_URI=redis://...` shares
one counter across workers with no code change. If that Redis goes down at
request time the API keeps answering: each worker falls back to in-memory
counters (logged as a warning by `flask-limiter`) and goes back to Redis once
it answers again.
