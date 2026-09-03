// Batch trip generation — POST /v1/viagens/gerar-lote, one call per gestor.
// Mirrors the Sunday 02:00 APScheduler job (job_gerar_viagens_semanais in
// app/utils/scheduler_setup.py) that generates the coming week's trips for
// every horario in one pass. Per the plan: "tested as a single heavy write
// burst separate from concurrent-user traffic" — main.js runs this with a
// `shared-iterations` executor (one pass per gestor, not a sustained loop),
// and only when explicitly requested via -e EXTRA_SCENARIOS=batch_trip_generation.
import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, gestores } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

export function batchTripGeneration() {
  const gestor = gestores[exec.vu.idInTest % gestores.length];
  const token = getToken(BASE_URL, gestor.email, gestor.password);
  if (!token) return;
  const params = { ...authHeaders(token), tags: { flow: 'batch_trip_generation' } };

  const targetDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

  const res = http.post(
    `${BASE_URL}/v1/viagens/gerar-lote`,
    JSON.stringify({ data: targetDate }),
    params
  );
  check(res, { 'gerar-lote: status 201': (r) => r.status === 201 });
}
