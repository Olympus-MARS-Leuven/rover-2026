// Fake page for the browser-logic tests: no real DOM, timers or network.
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
  const intervals = [];
  const pads = [];
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
    navigator: {getGamepads: () => pads},
    AbortController,
    setTimeout: (fn, delay) => { const id = ++nextId; timers.set(id, {fn, delay}); return id; },
    clearTimeout: id => timers.delete(id),
    setInterval: (fn, delay) => { intervals.push({fn, delay}); return intervals.length; },
    fetch: async (url, options) => {
      const data = JSON.parse(options.body);
      calls.push({url, data});
      if (fetchOverride) return fetchOverride(url, data, options);
      return successful(data, `challenge-${calls.length}`);
    },
  });
  context.globalThis = context;
  for (const file of ['gamepad.js', 'controls.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../web', file), 'utf8'), context);
  }
  const flush = () => new Promise(resolve => setImmediate(resolve));
  return {
    elements, calls, windowEvents, document, documentEvents, flush, timers, pads, context,
    pollPad() { intervals.find(item => item.delay === 30).fn(); },
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

module.exports = {harness, successful};
