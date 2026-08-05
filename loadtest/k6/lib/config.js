// Shared config/data loading for all BusKá load test scenarios.
//
// Selected via -e TIER=<name>, matching a file in loadtest/tiers/<name>.json
// and a generated loadtest/exports/<name>_export.json (see generate_data.py).
//
// Spike/Soak variants reuse the Load tier's generated data (they model the
// same "Full City Capacity" dataset under a different traffic shape) via
// -e DATA_SOURCE=load, so we don't need to regenerate ~1,450 students twice.
import { SharedArray } from 'k6/data';

export const TIER = __ENV.TIER || 'smoke';
const DATA_SOURCE = __ENV.DATA_SOURCE || TIER;

export const TIER_CONFIG = JSON.parse(open(`../../tiers/${TIER}.json`));

// SharedArray keeps one copy of the (potentially large, e.g. ~99k students at
// Breakpoint) dataset in memory shared across all VUs, instead of each VU
// process holding its own copy.
const exportData = new SharedArray('export-root', function () {
  return [JSON.parse(open(`../../exports/${DATA_SOURCE}_export.json`))];
})[0];

export const BASE_URL = __ENV.BASE_URL || exportData.base_url || 'http://localhost:5000';

export const alunos = new SharedArray('alunos', function () {
  const out = [];
  for (const pref of exportData.prefeituras) {
    for (const a of pref.alunos) out.push(a);
  }
  return out;
});

export const motoristas = new SharedArray('motoristas', function () {
  const out = [];
  for (const pref of exportData.prefeituras) {
    for (const m of pref.motoristas) out.push(m);
  }
  return out;
});

export const gestores = new SharedArray('gestores', function () {
  const out = [];
  for (const pref of exportData.prefeituras) out.push(pref.gestor);
  return out;
});

export const rotas = new SharedArray('rotas', function () {
  const out = [];
  for (const pref of exportData.prefeituras) {
    for (const r of pref.rotas) out.push(r);
  }
  return out;
});

export const viagensEmAndamento = new SharedArray('viagens', function () {
  const out = [];
  for (const pref of exportData.prefeituras) {
    for (const v of pref.viagens_em_andamento) out.push(v);
  }
  return out;
});

// Deterministic-ish per-VU picker: spreads VUs evenly across the available
// pool instead of every VU hammering the same row (exec.vu.idInTest is
// stable for the lifetime of a VU).
export function pick(array, vuId) {
  return array[vuId % array.length];
}
