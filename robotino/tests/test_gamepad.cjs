// PS4 controller mapping and its use by the control page: node --test tests/test_gamepad.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {harness} = require('./browser_harness.cjs');

require('../web/gamepad.js');
const G = globalThis.RobotinoGamepad;

function pad({axes = [0, 0, 0, 0], pressed = [], values = {}, mapping = 'standard', connected = true} = {}) {
  const buttons = Array.from({length: 18}, (_, index) => {
    const name = Object.keys(G.BUTTONS).find(key => G.BUTTONS[key] === index);
    const value = values[name] ?? (pressed.includes(name) ? 1 : 0);
    return {pressed: value > 0.5, value};
  });
  return {id: 'Wireless Controller (STANDARD GAMEPAD Vendor: 054c Product: 09cc)', connected, mapping, axes, buttons};
}

const snap = options => G.snapshot(pad(options));

test('sticks have a dead zone, report up as positive and respond gently near the centre', () => {
  assert.deepEqual(G.stick(0.1, 0.05), [0, 0]);
  assert.deepEqual(G.stick(0, -1), [0, 1]);
  const [, half] = G.stick(0, -(0.15 + 0.85 * 0.5));
  assert.ok(Math.abs(half - 0.25) < 1e-9);
});

test('one stick drives both tracks with the accepted turn directions', () => {
  assert.deepEqual(G.arcade(0, 1), [1, 1]);
  assert.deepEqual(G.arcade(0, -1), [-1, -1]);
  assert.deepEqual(G.arcade(1, 0), [1, -1]);     // Right turn: left track forward.
  assert.deepEqual(G.arcade(-1, 0), [-1, 1]);
  assert.deepEqual(G.arcade(0.5, 1), [1, 0.33]);
});

test('DRIVE mode: left stick gives track values; precision buttons scale them', () => {
  assert.deepEqual(G.command(snap({axes: [0, -1, 0, 0]}), 'drive').tracks, [1, 1]);
  assert.deepEqual(G.command(snap({axes: [1, 0, 0, 0]}), 'drive').tracks, [0.8, -0.8]);
  assert.deepEqual(G.command(snap({axes: [0, -1, 0, 0], pressed: ['r1']}), 'drive').tracks, [0.4, 0.4]);
  assert.equal(G.command(snap({axes: [0.05, 0.05, 0, 0]}), 'drive').tracks, null);
  assert.deepEqual(G.command(snap({axes: [0, -1, 0, 1]}), 'drive').jog, {}, 'the arm does not move in DRIVE');
});

test('ARM mode: sticks, triggers and D-pad move the right joints in the labelled directions', () => {
  const command = G.command(snap({axes: [0, -1, 0, -1], values: {r2: 1}, pressed: ['up']}), 'arm');
  assert.equal(command.tracks, null);
  assert.deepEqual(command.jog, {camera: -0.6, lower: 1, upper: -1, gripper: 1});
  assert.deepEqual(G.command(snap({axes: [0, 0, 1, 0]}), 'arm').jog, {wrist: 1});
  // A diagonal stick moves both of its joints at 71% (round dead zone).
  assert.deepEqual(G.command(snap({axes: [0, 0, 1, -1]}), 'arm').jog, {upper: -0.71, wrist: 0.71});
  assert.deepEqual(G.command(snap({values: {l2: 1}}), 'arm').jog, {gripper: -1});
  assert.deepEqual(G.command(snap({values: {l2: 1, r2: 1}}), 'arm').jog, {}, 'both triggers cancel');
});

test('measured directions flip the stick signs', () => {
  const labels = {...G.DEFAULT_LABELS, lower: ['up', 'down']};
  assert.deepEqual(G.command(snap({axes: [0, -1, 0, 0]}), 'arm', labels).jog, {lower: -1});
});

test('button edges and controller choice', () => {
  const before = snap({});
  const after = snap({pressed: ['triangle', 'circle']});
  assert.deepEqual(G.edges(before, after).sort(), ['circle', 'triangle']);
  assert.deepEqual(G.edges(after, after), []);
  const other = pad({mapping: ''});
  const standard = pad({});
  assert.equal(G.find([null, other, standard]), standard);
  assert.equal(G.find([pad({connected: false})]), null);
});

async function connected() {
  const h = harness();
  await h.connect();
  return h;
}

test('the left stick drives through the existing session and releasing it stops', async () => {
  const h = await connected();
  h.pads.push(pad({axes: [0, -1, 0, 0]}));
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().motion, 'analog');
  assert.deepEqual(h.lastDrive().tracks, [1, 1]);
  assert.equal(h.lastDrive().deadman, true);
  h.pads[0] = pad({});
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('the keyboard has priority over the stick', async () => {
  const h = await connected();
  h.pads.push(pad({axes: [0, -1, 0, 0]}));
  h.pollPad();
  h.key('keydown', 'Shift'); h.key('keydown', 'ArrowDown');
  await h.tick();
  assert.equal(h.lastDrive().motion, 'backward');
});

test('unplugging the controller or losing focus stops controller movement', async () => {
  const h = await connected();
  h.pads.push(pad({axes: [0, -1, 0, 0]}));
  h.pollPad(); await h.tick();
  h.pads.length = 0;
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
  assert.match(h.elements.error.textContent, /Controller disconnected/);
  h.pads.push(pad({axes: [0, -1, 0, 0]}));
  h.document.hasFocus = () => false;
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('triangle switches to ARM, enables the arm and the sticks then jog joints', async () => {
  const h = await connected();
  h.pads.push(pad({pressed: ['triangle']}));
  h.pollPad();
  assert.equal(h.elements['pad-mode'].textContent, 'ARM');
  h.pads[0] = pad({axes: [0, -1, 0, 0]});
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().arm.enabled, true);
  assert.deepEqual(h.lastDrive().arm.jog, {lower: 1});
  assert.equal(h.lastDrive().arm.deadman, true);
  assert.equal(h.lastDrive().motion, 'stop', 'tracks do not move in ARM mode');
  h.pads[0] = pad({pressed: ['triangle']});
  h.pollPad();
  assert.equal(h.elements['pad-mode'].textContent, 'DRIVE');
});

test('circle is STOP and Options connects again, never automatically', async () => {
  const h = await connected();
  h.pads.push(pad({pressed: ['circle']}));
  h.pollPad(); await h.flush();
  assert.equal(h.calls.at(-1).url, '/api/stop');
  assert.equal(h.elements.status.textContent, 'Disconnected');
  h.pads[0] = pad({});
  h.pollPad(); await h.flush();
  assert.equal(h.calls.filter(c => c.url === '/api/connect').length, 1);
  h.pads[0] = pad({pressed: ['options']});
  h.pollPad(); await h.flush();
  assert.equal(h.calls.filter(c => c.url === '/api/connect').length, 2);
});

test('D-pad left/right changes the speed; Share releases the servos', async () => {
  const h = await connected();
  h.pads.push(pad({pressed: ['right']}));
  h.pollPad();
  assert.equal(h.elements.speed.value, '60');
  h.pads[0] = pad({pressed: ['triangle']});
  h.pollPad(); await h.tick();
  h.pads[0] = pad({pressed: ['share']});
  h.pollPad(); await h.tick();
  assert.equal(h.lastDrive().arm.enabled, false);
  assert.equal(h.lastDrive().arm.release, true);
  await h.tick();
  assert.equal(h.lastDrive().arm.release, undefined, 'release is sent once');
});

test('during setup tests only the override moves the robot, but circle still stops', async () => {
  const h = await connected();
  h.context.RobotinoControl.setOverride({
    drive: () => ({motion: 'analog', tracks: [0.5, 0], raw: true, speed: 0.3, deadman: true}),
    arm: () => ({enabled: true, calibrate: true}),
  });
  h.pads.push(pad({axes: [0, -1, 0, 0], pressed: ['triangle']}));
  h.pollPad(); await h.tick();
  assert.deepEqual(h.lastDrive().tracks, [0.5, 0]);
  assert.equal(h.lastDrive().speed, 0.3);
  assert.equal(h.lastDrive().raw, true);
  assert.equal(h.elements['pad-mode'].textContent, 'DRIVE');
  h.pads[0] = pad({pressed: ['circle']});
  h.pollPad(); await h.flush();
  assert.equal(h.calls.at(-1).url, '/api/stop');
});

test('a simulated link loss forgets the session without telling the Pi', async () => {
  const h = await connected();
  h.context.RobotinoControl.simulateLinkLoss();
  assert.equal(h.context.RobotinoControl.connected(), false);
  assert.notEqual(h.calls.at(-1).url, '/api/stop');
  assert.ok(![...h.timers.values()].some(t => t.delay === 80), 'no more heartbeats');
});
