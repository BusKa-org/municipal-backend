// Auth helpers shared by every scenario.
//
// Per the plan: "Each VU logs in once, caches the JWT (2h expiry per
// JWT_EXPIRES_HOURS) for the run." Module-level `let` variables in k6 are
// per-VU (each VU runs its own JS VM instance), so a simple in-memory cache
// here is sufficient — no need for k6/execution VU-scoped storage.
import http from 'k6/http';
import { check } from 'k6';

const cache = {};

// Server tokens expire after JWT_EXPIRES_HOURS (2h in the load-test env). Re-login
// a bit before that so long-running tiers (e.g. the multi-hour soak) don't start
// getting 401s at the 2h mark — which would be a pure test artifact, not a real
// regression. Short tiers finish well inside this window and are unaffected.
const TOKEN_TTL_MS = 100 * 60 * 1000; // refresh at ~100 min, safely under the 120 min expiry

/**
 * Logs in once per VU per credential and reuses the token until it nears
 * expiry, then transparently re-logs in. Use this from every scenario except
 * scenarios/auth.js, which intentionally bypasses the cache to load-test the
 * login endpoint itself.
 */
export function getToken(baseUrl, email, password) {
  const entry = cache[email];
  if (entry && Date.now() - entry.ts < TOKEN_TTL_MS) return entry.token;
  const token = loginRaw(baseUrl, email, password);
  if (token) cache[email] = { token, ts: Date.now() };
  return token ? token : entry ? entry.token : token;
}

/** Always calls POST /v1/auth/login, no caching. Returns the token or null. */
export function loginRaw(baseUrl, email, password) {
  const res = http.post(
    `${baseUrl}/v1/auth/login`,
    JSON.stringify({ email, password }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { flow: 'auth' },
    }
  );
  const ok = check(res, {
    'login: status 200': (r) => r.status === 200,
    'login: has token': (r) => !!(r.json && r.json('token')),
  });
  return ok ? res.json('token') : null;
}

export function authHeaders(token) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
}
