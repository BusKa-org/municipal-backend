// Shared thresholds, applied identically at every tier (per the plan: "may
// be intentionally allowed to fail at Stress/Breakpoint since those are
// exploratory" — that's a human read-the-report decision at those tiers,
// not a different threshold definition; keeping one definition avoids
// silently moving the goalposts between tiers).
//
// Filtered by the `flow` tag every http call in this project sets, e.g.
// `tags: { flow: 'student_browsing' }`, per Grafana k6 scenario tagging
// conventions.
export const thresholds = {
  // Reads: browsing, polling — p95 < 300ms, error rate < 1%
  'http_req_duration{flow:auth}': ['p(95)<300'],
  'http_req_duration{flow:student_browsing}': ['p(95)<300'],
  'http_req_duration{flow:live_tracking_poll}': ['p(95)<300'],
  'http_req_failed{flow:auth}': ['rate<0.01'],
  'http_req_failed{flow:student_browsing}': ['rate<0.01'],
  'http_req_failed{flow:live_tracking_poll}': ['rate<0.01'],

  // GPS writes — p95 < 500ms, error rate < 1%
  'http_req_duration{flow:driver_gps}': ['p(95)<500'],
  'http_req_duration{flow:student_geofence_gps}': ['p(95)<500'],
  'http_req_failed{flow:driver_gps}': ['rate<0.01'],
  'http_req_failed{flow:student_geofence_gps}': ['rate<0.01'],

  // Dashboard/reports — heaviest PostGIS queries, explicitly given more room
  'http_req_duration{flow:dashboard_reports}': ['p(95)<1500'],
  'http_req_failed{flow:dashboard_reports}': ['rate<0.01'],

  // Routing proxy — only ever hits the local OSRM stub, isolated scenario
  'http_req_duration{flow:routing_proxy}': ['p(95)<300'],
  'http_req_failed{flow:routing_proxy}': ['rate<0.01'],

  // Batch trip generation — single heavy write burst, latency less
  // meaningful than "did it complete without error"
  'http_req_failed{flow:batch_trip_generation}': ['rate<0.01'],
};
