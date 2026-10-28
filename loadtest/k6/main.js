// Weighted scenario mix, built from a tier's real-world sizing numbers
// (concurrent_students / concurrent_trips) rather than hardcoded VU counts,
// so the exact same orchestrator produces every tier by swapping
// -e TIER=<name>. Ramp shape (standard/spike/soak/step-climb) is expressed
// generically as a list of {duration, fraction} stages in the tier config —
// `fraction` is scaled per-scenario against that scenario's own target VU
// count, so one shape definition drives all six scenarios' ramps together.
//
// Usage:
//   k6 run loadtest/k6/main.js -e TIER=smoke
//   k6 run loadtest/k6/main.js -e TIER=load-spike -e DATA_SOURCE=load
//   k6 run loadtest/k6/main.js -e TIER=load -e EXTRA_SCENARIOS=routing_proxy,batch_trip_generation
//
// Routing proxy and batch trip generation are excluded from the default mix
// per the plan ("never mixed into the main weighted run until the stub is
// confirmed working" / "tested as a single heavy write burst separate from
// concurrent-user traffic") — opt in via -e EXTRA_SCENARIOS=....
import { TIER_CONFIG, gestores } from './lib/config.js';
import { thresholds } from './lib/thresholds.js';

import { authFlow } from './scenarios/auth.js';
import { studentBrowsing } from './scenarios/student_browsing.js';
import { driverGps } from './scenarios/driver_gps.js';
import { studentGeofenceGps } from './scenarios/student_geofence_gps.js';
import { liveTrackingPoll } from './scenarios/live_tracking_poll.js';
import { dashboardReports } from './scenarios/dashboard_reports.js';
import { routingProxy } from './scenarios/routing_proxy.js';
import { batchTripGeneration } from './scenarios/batch_trip_generation.js';

export {
  authFlow,
  studentBrowsing,
  driverGps,
  studentGeofenceGps,
  liveTrackingPoll,
  dashboardReports,
  routingProxy,
  batchTripGeneration,
};

const cfg = TIER_CONFIG;
const extraScenarios = (__ENV.EXTRA_SCENARIOS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

function stagesFor(targetVUs) {
  return cfg.stages.map((s) => ({
    duration: s.duration,
    target: Math.max(0, Math.round(targetVUs * s.fraction)),
  }));
}

// Derived VU counts. Only concurrent_students and concurrent_trips are
// sourced-or-derived per the plan's sizing methodology; the fractions below
// (5% re-auth churn, 30% actively watching the live map) are our own
// deliberate modeling assumptions for how a browsing/tracking session
// splits across sub-behaviors, not independently sourced numbers.
const authVUs = Math.max(1, Math.round(cfg.concurrent_students * 0.05));
const trackingVUs = Math.max(1, Math.round(cfg.concurrent_students * 0.3));
const gestorVUs = Math.max(1, gestores.length);

const scenarios = {
  auth: {
    executor: 'ramping-vus',
    exec: 'authFlow',
    startVUs: 0,
    stages: stagesFor(authVUs),
    gracefulRampDown: '10s',
    tags: { flow: 'auth' },
  },
  student_browsing: {
    executor: 'ramping-vus',
    exec: 'studentBrowsing',
    startVUs: 0,
    stages: stagesFor(cfg.concurrent_students),
    gracefulRampDown: '10s',
    tags: { flow: 'student_browsing' },
  },
  driver_gps: {
    executor: 'ramping-vus',
    exec: 'driverGps',
    startVUs: 0,
    stages: stagesFor(cfg.concurrent_trips),
    gracefulRampDown: '10s',
    tags: { flow: 'driver_gps' },
  },
  student_geofence_gps: {
    executor: 'ramping-vus',
    exec: 'studentGeofenceGps',
    startVUs: 0,
    stages: stagesFor(cfg.concurrent_students),
    gracefulRampDown: '10s',
    tags: { flow: 'student_geofence_gps' },
  },
  live_tracking_poll: {
    executor: 'ramping-vus',
    exec: 'liveTrackingPoll',
    startVUs: 0,
    stages: stagesFor(trackingVUs),
    gracefulRampDown: '10s',
    tags: { flow: 'live_tracking_poll' },
  },
  dashboard_reports: {
    executor: 'ramping-vus',
    exec: 'dashboardReports',
    startVUs: 0,
    stages: stagesFor(gestorVUs),
    gracefulRampDown: '10s',
    tags: { flow: 'dashboard_reports' },
  },
};

if (extraScenarios.includes('routing_proxy')) {
  scenarios.routing_proxy = {
    executor: 'ramping-vus',
    exec: 'routingProxy',
    startVUs: 0,
    stages: stagesFor(Math.min(20, cfg.concurrent_students)),
    gracefulRampDown: '10s',
    tags: { flow: 'routing_proxy' },
  };
}

if (extraScenarios.includes('batch_trip_generation')) {
  scenarios.batch_trip_generation = {
    executor: 'shared-iterations',
    exec: 'batchTripGeneration',
    vus: Math.max(1, Math.min(gestorVUs, 10)),
    iterations: gestorVUs,
    maxDuration: '5m',
    tags: { flow: 'batch_trip_generation' },
  };
}

export const options = {
  scenarios,
  thresholds,
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};
