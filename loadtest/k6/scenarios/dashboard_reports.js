// Dashboard/reports — gestor-only, the heaviest PostGIS-adjacent queries in
// the app (relatorio_periodo_gestor aggregates across viagens/alunos for a
// date range). Low VU count by design (one gestor per prefeitura), tested
// in isolation from the write-heavy GPS scenarios' data first per the plan,
// then folded into the main mix once its own latency profile is understood.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, gestores } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

export function dashboardReports() {
  const gestor = gestores[exec.vu.idInTest % gestores.length];
  const token = getToken(BASE_URL, gestor.email, gestor.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'dashboard_reports' } };

  const hoje = new Date();
  const seteDiasAtras = new Date(hoje.getTime() - 7 * 24 * 60 * 60 * 1000);

  const res = http.get(
    `${BASE_URL}/v1/dashboard/relatorios/periodo?data_inicio=${isoDate(seteDiasAtras)}&data_fim=${isoDate(hoje)}`,
    params
  );
  check(res, { 'relatorio periodo: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 30 + 30); // low frequency: gestores don't refresh dashboards every few seconds
}
