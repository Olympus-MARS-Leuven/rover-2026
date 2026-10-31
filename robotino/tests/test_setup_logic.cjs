// Guided setup calculations and report: node --test tests/test_setup_logic.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');

require('../web/setup_logic.js');
const S = globalThis.RobotinoSetupLogic;

test('the direction seen during a wiggle names the positive-ticks direction', () => {
  assert.equal(S.positiveLabel('lower', 1, 'up'), 'up');
  assert.equal(S.positiveLabel('lower', -1, 'up'), 'down');
  assert.equal(S.positiveLabel('camera', -1, 'up'), 'down');
  assert.equal(S.positiveLabel('gripper', 1, 'unsure'), null);
});

test('channel answers detect swaps, duplicates and silent channels', () => {
  const same = S.channelMap({lower: {channel: 12, moved: 'lower'}, upper: {channel: 13, moved: 'upper'}});
  assert.deepEqual(same, {ok: true, changed: false, channels: {lower: 12, upper: 13}, problems: []});
  const swapped = S.channelMap({lower: {channel: 12, moved: 'upper'}, upper: {channel: 13, moved: 'lower'}});
  assert.equal(swapped.ok, true);
  assert.equal(swapped.changed, true);
  assert.deepEqual(swapped.channels, {upper: 12, lower: 13});
  const duplicate = S.channelMap({lower: {channel: 12, moved: 'wrist'}, wrist: {channel: 14, moved: 'wrist'}});
  assert.equal(duplicate.ok, false);
  assert.match(duplicate.problems[0], /both moved the wrist/);
  assert.match(S.channelMap({camera: {channel: 11, moved: 'nothing'}}).problems[0], /nothing moved/);
});

test('marked ends become limits with a margin, within the absolute bounds', () => {
  assert.deepEqual(S.limitsFromEnds(440, 280), {minimum: 283, maximum: 437});
  assert.deepEqual(S.limitsFromEnds(100, 520), {minimum: 103, maximum: 517});
  assert.equal(S.limitsFromEnds(300, 310), null, 'too small a range');
  assert.equal(S.limitsFromEnds(300, undefined), null);
});

test('trim lowers the faster track and never exceeds full power', () => {
  assert.deepEqual(S.trimAfter([1, 1], 'left'), [1, 0.96]);
  assert.deepEqual(S.trimAfter([1, 0.96], 'right'), [1, 1]);
  assert.deepEqual(S.trimAfter([1, 1], 'right'), [0.96, 1]);
  assert.deepEqual(S.trimAfter([0.5, 1], 'right'), [0.5, 1]);
  assert.deepEqual(S.trimAfter([1, 1], 'straight'), [1, 1]);
});

test('ramp, latency and the calibration payloads', () => {
  assert.equal(S.rampDuty(0), 0.1);
  assert.equal(S.rampDuty(4), 0.3);
  assert.equal(S.rampDuty(30), 1);
  assert.equal(S.latency(12450, 12270), 180);
  assert.equal(S.latency(100, 200), null);
  const results = {
    joints: {
      lower: {channel: 12, positive: 'up', ends: {negative: 280, positive: 440}, rest: 285},
      wrist: {ends: {negative: 300}},
      gripper: {channel: 15},
    },
    tracks: {raisedDuty: [0.25, 0.3], trim: [1, 0.96]},
  };
  assert.deepEqual(S.jointCalibration(results, 'identity'), {lower: {channel: 12, positive: 'up'}, gripper: {channel: 15}});
  assert.deepEqual(S.jointCalibration(results, 'range'), {lower: {minimum: 283, maximum: 437, rest: 285}});
  assert.deepEqual(S.trackCalibration(results), {min_duty: [0.25, 0.3], trim: [1, 0.96]});
  results.tracks.floorDuty = 0.35;
  assert.deepEqual(S.trackCalibration(results).min_duty, [0.35, 0.35], 'the floor value wins');
  results.tracks.floorDuty = 0.95;
  assert.deepEqual(S.trackCalibration(results).min_duty, [0.8, 0.8], 'capped like the Pi');
});

test('the report records modes, findings and the stored calibration', () => {
  const text = S.report({
    controller: {id: 'Wireless Controller', standard: true, seen: ['cross'], rumble: 'yes'},
    identify: {lower: {channel: 12, moved: 'upper', sign: 1, seen: 'down'}, upper: {channel: 13, moved: 'lower', sign: 1, seen: 'up'}},
    joints: {lower: {ends: {negative: 280, positive: 440}, rest: 285, restCheck: 'still', beyond: true}},
    archived: {lower: [300, 430]},
    tracks: {left: 'forward', right: 'backward', linkLoss: {after: 2.03, answer: 'stopped'}, stopping: [{speed: 50, cm: 12}]},
    video: {upright: 'upright', latency: 180, probe: '0 : ov5647 [2592x1944]'},
    notes: 'Left track squeaks',
  }, {version: 'abc123', tracks_real: true, servos_real: true, health: {max_temperature: 61.2, under_voltage_events: 1,
    flags: {under_voltage_seen: true}}, calibration: {joints: {lower: {rest: 285}}}},
  [{title: 'Joint limits', result: 'done', mode: 'real'}]);
  for (const expected of ['abc123', 'Real tracks: yes', 'under-voltage since boot: yes', '| Joint limits | done | real |',
    'Channel mapping differs', '| Lower arm | 300–430 | 280 / 440 | 283–437 | yes | 285 | still |',
    'right → backward', 'Pi stopped after 2.03 s', '50% duty: 12 cm', 'ov5647', 'Left track squeaks', '"rest": 285']) {
    assert.ok(text.includes(expected), `report should contain: ${expected}`);
  }
  assert.ok(S.report({}, {}, []).includes('SIMULATION ONLY'));
});
