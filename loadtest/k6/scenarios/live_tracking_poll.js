// Live tracking poll — students watching the map, reading the same
// viagem.motorista_lat/lon rows the driver_gps scenario writes. Deliberately
// a separate scenario (not folded into student_browsing) so its read
// contention against actively-written rows shows up under its own `flow`
// tag in results.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, alunos } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

export function liveTrackingPoll() {
  const aluno = alunos[exec.vu.idInTest % alunos.length];
  const token = getToken(BASE_URL, aluno.email, aluno.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'live_tracking_poll' } };

  const res = http.get(`${BASE_URL}/v1/viagens/${aluno.viagem_id}/localizacao`, params);
  check(res, { 'live tracking: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 5 + 5); // 5-10s poll interval, matches map refresh rate
}
