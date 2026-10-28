// Auth scenario — deliberately bypasses lib/auth.js's cache to repeatedly
// hit POST /v1/auth/login, since AUTH_RATE_LIMIT in app/utils/security.py is
// a documented constant only (flask-limiter isn't actually wired up — see
// the plan's "known bottlenecks"). This scenario is the one place we
// actually measure that unprotected endpoint under concurrency; every other
// scenario logs in once and reuses the token.
import { sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, alunos, motoristas, gestores } from '../lib/config.js';
import { loginRaw } from '../lib/auth.js';

const allCredentials = [...alunos, ...motoristas, ...gestores];

export function authFlow() {
  const cred = allCredentials[exec.vu.idInTest % allCredentials.length];
  loginRaw(BASE_URL, cred.email, cred.password);
  sleep(Math.random() * 10 + 5); // 5-15s think time between re-auths
}
