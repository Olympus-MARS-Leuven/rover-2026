// Optional PC-side tests: node --test tests/test_keyboard.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function successful(data, challenge = 'next') {
  const homes = {camera: 100, lower: 0, upper: 53, wrist: 0, gripper: 0};
  return {ok: true, json: async () => ({session: 'session', challenge,
    motion: data.motion || 'stop', left: data.deadman ? data.speed : 0, right: data.deadman ? data.speed : 0,
    arm: {enabled: data.arm?.enabled || false, hardware: false,
      joints: Object.fromEntries(Object.entries(homes).map(([key, home]) => [key, {
        percent: home, target: data.arm?.targets?.[key] ?? home, active: false,
      }]))},
  })};
}

function harness(fetchOverride) {
  const elements = {};
  const windowEvents = {};
  const documentEvents = {};
  const calls = [];
  const timers = new Map();
  let nextId = 0;
  const document = {
    hidden: false,
    hasFocus: () => true,
    querySelector: () => ({content: 'test-token'}),
    getElementById: id => elements[id] ||= {
      textContent: '', value: id === 'speed' ? '50' : id === 'arm-speed' ? '100' : '', disabled: false, events: {},
      addEventListener(type, fn) { this.events[type] = fn; },
    },
    addEventListener: (type, fn) => { documentEvents[type] = fn; },
  };
  const context = vm.createContext({
    document,
    window: {addEventListener: (type, fn) => { windowEvents[type] = fn; }},
    AbortController,
    setTimeout: (fn, delay) => { const id = ++nextId; timers.set(id, {fn, delay}); return id; },
    clearTimeout: id => timers.delete(id),
    fetch: async (url, options) => {
      const data = JSON.parse(options.body);
      calls.push({url, data});
      if (fetchOverride) return fetchOverride(url, data, options);
      return successful(data, `challenge-${calls.length}`);
    },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/controls.js'), 'utf8'), context);
  const flush = () => new Promise(resolve => setImmediate(resolve));
  return {
    elements, calls, windowEvents, document, documentEvents, flush, timers,
    async connect() { await elements.connect.events.click(); await flush(); },
    key(type, key, extra = {}) {
      windowEvents[type]({key, shiftKey: true, repeat: false, preventDefault() {}, ...extra});
    },
    async tick() {
      const entry = [...timers].find(([, value]) => value.delay === 80);
      assert.ok(entry, 'a heartbeat should be scheduled');
      timers.delete(entry[0]);
      await entry[1].fn();
      await flush();
    },
    lastDrive() { return calls.filter(c => c.url === '/api/drive').at(-1).data; },
  };
}

test('Shift+Z drives; direction release and Shift release stop', async () => {
  const h = harness();
  await h.connect();
  assert.equal(h.lastDrive().motion, 'stop');
  h.key('keydown', 'Shift'); h.key('keydown', 'Z');
  await h.tick();
  assert.equal(h.lastDrive().motion, 'forward');
  h.key('keyup', 'Z'); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
  h.key('keydown', 'Z'); await h.tick();
  h.key('keyup', 'Shift', {shiftKey: false}); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('conflicting directions stop', async () => {
  const h = harness(); await h.connect();
  h.key('keydown', 'Shift'); h.key('keydown', 'ArrowUp'); h.key('keydown', 'ArrowDown');
  await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('focus loss sends stop and requires new presses after reconnect', async () => {
  const h = harness(); await h.connect();
  h.key('keydown', 'Shift'); h.key('keydown', 'Z'); await h.tick();
  h.windowEvents.blur(); await h.flush();
  assert.equal(h.calls.at(-1).url, '/api/stop');
  assert.equal(h.elements.status.textContent, 'Disconnected');
  await h.connect();
  h.key('keydown', 'Z', {repeat: true}); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('STOP during an unanswered connect cannot be undone by its late response', async () => {
  let resolveConnect;
  const h = harness(url => url === '/api/connect'
    ? new Promise(resolve => { resolveConnect = resolve; })
    : {ok: true, json: async () => ({motion: 'stop'})});
  const connecting = h.elements.connect.events.click();
  await h.flush();
  h.elements.stop.events.click();
  resolveConnect({ok: true, json: async () => ({session: 'late', challenge: 'late'})});
  await connecting; await h.flush();
  assert.equal(h.elements.status.textContent, 'Disconnected');
  assert.equal(h.calls.filter(c => c.url === '/api/drive').length, 0);
  assert.equal(h.calls.at(-1).url, '/api/stop');
});

test('network failure disconnects without automatic retry', async () => {
  const h = harness(url => {
    if (url === '/api/drive') throw new Error('network down');
    return {ok: true, json: async () => ({session: 'session', challenge: 'challenge'})};
  });
  await h.connect();
  assert.equal(h.elements.status.textContent, 'Disconnected');
  assert.equal(h.elements.connect.disabled, false);
  assert.equal(h.calls.filter(c => c.url === '/api/drive').length, 1);
});

test('slider starts at 50% and sends live speed changes, including zero and full duty', async () => {
  const h = harness(); await h.connect();
  assert.equal(h.lastDrive().speed, 0.5);
  h.key('keydown', 'Shift'); h.key('keydown', 'Z');
  for (const value of ['75', '0', '100']) {
    h.elements.speed.value = value;
    h.elements.speed.events.input();
    await h.tick();
    assert.equal(h.lastDrive().speed, Number(value) / 100);
    assert.equal(h.elements['speed-value'].textContent, `${value}%`);
  }
  h.key('keyup', 'Shift', {shiftKey: false}); await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
});

test('focusing the slider clears driving keys; its arrows adjust speed without driving', async () => {
  const h = harness(); await h.connect();
  h.key('keydown', 'Shift'); h.key('keydown', 'ArrowUp'); await h.tick();
  h.elements.speed.events.focus();
  await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
  h.key('keydown', 'Shift', {target: h.elements.speed});
  h.key('keydown', 'ArrowUp', {
    target: h.elements.speed, preventDefault() { assert.fail('slider arrows must stay native'); },
  });
  await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
  h.key('keydown', 'Escape', {target: h.elements.speed}); await h.flush();
  assert.equal(h.elements.status.textContent, 'Disconnected');
});

test('a delayed drive reply keeps one request in flight and uses the latest keys and speed afterward', async () => {
  let resolveDrive;
  const h = harness(url => url === '/api/drive'
    ? new Promise(resolve => { resolveDrive = resolve; })
    : {ok: true, json: async () => ({session: 'session', challenge: 'challenge'})});
  await h.connect();
  assert.equal(h.calls.filter(c => c.url === '/api/drive').length, 1);
  assert.ok([...h.timers.values()].some(t => t.delay === 1500), 'allow 1.5 seconds for a reply');
  assert.ok(![...h.timers.values()].some(t => t.delay === 80), 'do not queue drive requests');
  h.elements.speed.value = '70';
  h.key('keydown', 'Shift'); h.key('keydown', 'Z');
  resolveDrive({ok: true, json: async () => ({challenge: 'next', motion: 'stop', left: 0, right: 0})});
  await h.flush();
  const ticking = h.tick();
  await h.flush();
  assert.equal(h.lastDrive().speed, 0.7);
  assert.equal(h.lastDrive().motion, 'forward');
  assert.equal(h.lastDrive().challenge, 'next');
  resolveDrive({ok: true, json: async () => ({challenge: 'again', motion: 'forward', left: 0.7, right: 0.7})});
  await ticking;
});

test('a request timeout disconnects, sends stop, and requires manual reconnection', async () => {
  const h = harness((url, data, options) => url === '/api/drive'
    ? new Promise((resolve, reject) => {
      options.signal.addEventListener('abort', () => reject(Object.assign(new Error(), {name: 'AbortError'})));
    })
    : {ok: true, json: async () => ({session: 'session', challenge: 'challenge'})});
  await h.connect();
  const timeout = [...h.timers.values()].find(t => t.delay === 1500);
  timeout.fn(); await h.flush();
  assert.equal(h.elements.status.textContent, 'Disconnected');
  assert.match(h.elements.error.textContent, /timed out/);
  assert.equal(h.calls.at(-1).url, '/api/stop');
  assert.equal(h.calls.filter(c => c.url === '/api/connect').length, 1);
});

test('STOP cannot be undone by a late drive reply', async () => {
  let resolveDrive;
  const h = harness(url => url === '/api/drive'
    ? new Promise(resolve => { resolveDrive = resolve; })
    : {ok: true, json: async () => ({session: 'session', challenge: 'challenge'})});
  await h.connect();
  h.elements.stop.events.click(); await h.flush();
  resolveDrive({ok: true, json: async () => ({challenge: 'late', motion: 'forward', left: 1, right: 1})});
  await h.flush();
  assert.equal(h.elements.status.textContent, 'Disconnected');
  assert.equal(h.elements.motion.textContent, 'Stop requested');
  assert.ok(![...h.timers.values()].some(t => t.delay === 80));
});

test('arm starts disabled and enabling it sends no joint targets', async () => {
  const h = harness(); await h.connect();
  assert.equal(h.lastDrive().arm.enabled, false);
  assert.equal(h.elements['joint-camera'].disabled, true);
  h.elements['arm-toggle'].events.click(); await h.tick();
  assert.equal(h.lastDrive().arm.enabled, true);
  assert.deepEqual(h.lastDrive().arm.targets, {});
  assert.deepEqual(h.lastDrive().arm.jog, {});
  assert.equal(h.elements['joint-camera'].disabled, false);
});

test('all five joint key pairs jog only with Shift and key release ends jogging', async () => {
  const h = harness(); await h.connect(); h.elements['arm-toggle'].events.click();
  for (const [key, joint, direction] of [
    ['i', 'camera', -1], ['k', 'camera', 1], ['r', 'lower', 1], ['f', 'lower', -1],
    ['t', 'upper', -1], ['g', 'upper', 1], ['j', 'wrist', -1], ['l', 'wrist', 1],
    ['o', 'gripper', -1], ['p', 'gripper', 1],
  ]) {
    h.key('keydown', key); await h.tick();
    assert.deepEqual(h.lastDrive().arm.jog, {});
    h.key('keydown', 'Shift'); await h.tick();
    assert.deepEqual(h.lastDrive().arm.jog, {[joint]: direction});
    assert.equal(h.lastDrive().motion, 'stop');
    h.key('keyup', 'Shift', {shiftKey: false}); h.key('keyup', key); await h.tick();
    assert.deepEqual(h.lastDrive().arm.jog, {});
    assert.equal(h.lastDrive().arm.enabled, true);
  }
});

test('joint slider sends one latest target without Shift and arm speed is adjustable', async () => {
  const h = harness(); await h.connect(); h.elements['arm-toggle'].events.click();
  const slider = h.elements['joint-gripper']; slider.value = '75'; slider.events.input();
  h.elements['arm-speed'].value = '200'; h.elements['arm-speed'].events.input();
  await h.tick();
  assert.deepEqual(h.lastDrive().arm.targets, {gripper: 75});
  assert.equal(h.lastDrive().arm.speed, 200);
  assert.equal(h.elements['arm-speed-value'].textContent, '200%');
  await h.tick();
  assert.deepEqual(h.lastDrive().arm.targets, {});
});

test('Hold cancels pending targets and jogging; release and reconnect do not resume the arm', async () => {
  const h = harness(); await h.connect(); h.elements['arm-toggle'].events.click();
  h.key('keydown', 'Shift'); h.key('keydown', 'r');
  h.elements['arm-hold'].events.click(); await h.tick();
  assert.equal(h.lastDrive().arm.hold, true);
  assert.deepEqual(h.lastDrive().arm.jog, {});
  await h.tick(); assert.equal(h.lastDrive().arm.hold, false);
  h.elements['arm-toggle'].events.click(); await h.tick();
  assert.equal(h.lastDrive().arm.enabled, false);
  h.elements.stop.events.click(); await h.flush();
  await h.connect();
  assert.equal(h.lastDrive().arm.enabled, false);
  assert.deepEqual(h.lastDrive().arm.targets, {});
});

test('arm sliders keep native arrows without requesting track movement', async () => {
  const h = harness(); await h.connect(); h.elements['arm-toggle'].events.click();
  const slider = h.elements['joint-lower']; slider.events.focus();
  h.key('keydown', 'Shift', {target: slider});
  h.key('keydown', 'ArrowUp', {target: slider, preventDefault() { assert.fail('native range key'); }});
  await h.tick();
  assert.equal(h.lastDrive().motion, 'stop');
  assert.deepEqual(h.lastDrive().arm.jog, {});
});

test('a slider change during an in-flight request is sent on the next heartbeat', async () => {
  let defer = false, resolveDrive;
  const h = harness((url, data) => {
    if (url === '/api/drive' && defer) return new Promise(resolve => { resolveDrive = resolve; });
    return successful(data);
  });
  await h.connect(); h.elements['arm-toggle'].events.click();
  const slider = h.elements['joint-camera']; slider.value = '30'; slider.events.input();
  defer = true;
  const ticking = h.tick(); await h.flush();
  assert.deepEqual(h.lastDrive().arm.targets, {camera: 30});
  slider.value = '80'; slider.events.input();
  resolveDrive(successful(h.lastDrive())); await ticking;
  defer = false; await h.tick();
  assert.deepEqual(h.lastDrive().arm.targets, {camera: 80});
});
