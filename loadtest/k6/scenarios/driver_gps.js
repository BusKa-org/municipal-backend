// Driver GPS stream — one VU per active trip, POSTing its current
// coordinate on a fixed ~5-10s interval for the scenario's duration, mirroring
// how the mobile app behaves during a real route (see
// app/services/viagens_service.py:atualizar_localizacao, which also does a
// synchronous TelemetriaViagem insert + a geofence-distance check on every
// call — one of the heavier write paths in the system).
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, motoristas } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

// Seed a plausible starting point once per VU; small deterministic-ish walk
// after that so consecutive points aren't identical (avoids "0 distance
// moved" being trivially true every call).
let lat = -7.23 + (Math.random() - 0.5) * 0.05;
let lon = -35.88 + (Math.random() - 0.5) * 0.05;

export function driverGps() {
  const motorista = motoristas[exec.vu.idInTest % motoristas.length];
  const token = getToken(BASE_URL, motorista.email, motorista.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'driver_gps' } };

  lat += (Math.random() - 0.5) * 0.001;
  lon += (Math.random() - 0.5) * 0.001;

  const res = http.post(
    `${BASE_URL}/v1/viagens/${motorista.viagem_id}/localizacao`,
    JSON.stringify({ latitude: lat, longitude: lon }),
    params
  );
  check(res, { 'driver gps: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 5 + 5); // 5-10s interval, matches real GPS ping cadence
}
