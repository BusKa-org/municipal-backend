// Student browsing — the highest-VU-count scenario in every tier.
//
// Deviates slightly from the plan's literal endpoint list ("GET /v1/rotas,
// GET /v1/viagens, GET /v1/notificacoes"): GET /v1/viagens/ is gestor-only
// (list_viagens_gestor rejects non-GESTOR roles — see
// app/services/viagens_service.py:426), so a student session would just get
// a wall of 403s that don't reflect real usage or real DB load. The
// student-facing equivalent is GET /v1/viagens/aluno/agenda, used here
// instead.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { BASE_URL, alunos } from '../lib/config.js';
import { getToken, authHeaders } from '../lib/auth.js';

export function studentBrowsing() {
  const aluno = alunos[exec.vu.idInTest % alunos.length];
  const token = getToken(BASE_URL, aluno.email, aluno.password);
  if (!token) {
    sleep(5);
    return;
  }
  const params = { ...authHeaders(token), tags: { flow: 'student_browsing' } };

  const rRotas = http.get(`${BASE_URL}/v1/rotas/`, params);
  check(rRotas, { 'rotas: status 200': (r) => r.status === 200 });
  sleep(Math.random() * 3 + 1);

  const rAgenda = http.get(`${BASE_URL}/v1/viagens/aluno/agenda`, params);
  check(rAgenda, { 'agenda: status 200': (r) => r.status === 200 });
  sleep(Math.random() * 3 + 1);

  const rNotif = http.get(`${BASE_URL}/v1/notificacoes/`, params);
  check(rNotif, { 'notificacoes: status 200': (r) => r.status === 200 });

  sleep(Math.random() * 10 + 5); // 5-15s think time between polling cycles
}
