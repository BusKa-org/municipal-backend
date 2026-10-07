// Student geofence GPS — one VU per confirmed student, POSTing their current
// coordinate for auto-checkin (app/services/viagens_service.py:
// atualizar_localizacao_aluno). Likely the single highest write-volume
// scenario at the Load tier and above: concurrent_students >> concurrent_trips,
// and every call is a synchronous UPDATE on alunos_confirmados.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, alunos } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

let lat = -7.23 + (Math.random() - 0.5) * 0.05;
let lon = -35.88 + (Math.random() - 0.5) * 0.05;

export function studentGeofenceGps() {
  const aluno = alunos[exec.vu.idInTest % alunos.length];
  const token = getToken(BASE_URL, aluno.email, aluno.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'student_geofence_gps' } };

  lat += (Math.random() - 0.5) * 0.001;
  lon += (Math.random() - 0.5) * 0.001;

  const res = http.post(
    `${BASE_URL}/v1/viagens/${aluno.viagem_id}/localizacao-aluno`,
    JSON.stringify({ latitude: lat, longitude: lon }),
    params
  );
  check(res, { 'student geofence: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 5 + 5); // 5-10s, same cadence as the driver stream
}
