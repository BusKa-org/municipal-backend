// Routing proxy — GET /v1/routing/route. Per the plan: "only ever against
// the OSRM stub, kept as an isolated scenario, never mixed into the main
// weighted run until the stub is confirmed working." main.js only includes
// this scenario when explicitly requested via -e EXTRA_SCENARIOS=routing_proxy.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, alunos } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

export function routingProxy() {
  const aluno = alunos[exec.vu.idInTest % alunos.length];
  const token = getToken(BASE_URL, aluno.email, aluno.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'routing_proxy' } };

  const originLat = -7.23 + (Math.random() - 0.5) * 0.05;
  const originLng = -35.88 + (Math.random() - 0.5) * 0.05;
  const destLat = -7.23 + (Math.random() - 0.5) * 0.05;
  const destLng = -35.88 + (Math.random() - 0.5) * 0.05;

  const res = http.get(
    `${BASE_URL}/v1/routing/route?origin_lat=${originLat}&origin_lng=${originLng}&dest_lat=${destLat}&dest_lng=${destLng}`,
    params
  );
  check(res, { 'routing: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 10 + 5);
}
