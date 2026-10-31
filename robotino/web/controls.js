"use strict";

const token = document.querySelector('meta[name="robotino-token"]').content;
const G = globalThis.RobotinoGamepad;
const ui = Object.fromEntries(["connect", "stop", "status", "motion", "left", "right", "error", "speed", "speed-value",
  "arm-toggle", "arm-hold", "arm-park", "arm-status", "arm-speed", "arm-speed-value", "pad-status", "pad-mode",
  "pad-help", "video", "video-toggle", "video-preset", "video-status", "health", "calibration-status",
  "tab-drive", "tab-setup", "panel-drive", "panel-setup"]
  .map(id => [id, document.getElementById(id)]));
const keys = new Set();
const directions = new Map([
  ["arrowup", "forward"], ["z", "forward"], ["arrowdown", "backward"], ["s", "backward"],
  ["arrowleft", "left"], ["q", "left"], ["arrowright", "right"], ["d", "right"],
]);
const jointNames = ["camera", "lower", "upper", "wrist", "gripper"];
const jointSliders = Object.fromEntries(jointNames.map(key => [key, document.getElementById(`joint-${key}`)]));
const jointOutputs = Object.fromEntries(jointNames.map(key => [key, document.getElementById(`position-${key}`)]));
const jointScales = Object.fromEntries(jointNames.map(key => [key, [
  document.getElementById(`scale-${key}-0`), document.getElementById(`scale-${key}-1`)]]));
// Keys name a physical direction; the measured labels decide its tick sign.
const armKeys = new Map([
  ["i", ["camera", "up"]], ["k", ["camera", "down"]],
  ["r", ["lower", "up"]], ["f", ["lower", "down"]],
  ["t", ["upper", "up"]], ["g", ["upper", "down"]],
  ["j", ["wrist", "left"]], ["l", ["wrist", "right"]],
  ["o", ["gripper", "open"]], ["p", ["gripper", "close"]],
]);
const rangeInputs = new Set([ui.speed, ui["arm-speed"], ...Object.values(jointSliders)]);
let labels = {...G.DEFAULT_LABELS};
let armEnabled = false;
let armAvailable = false;
let holdArm = false;
let releaseArm = false;
let parkArm = false;
const pendingTargets = new Map();
let session = null;
let challenge = null;
let generation = 0;
let timer = null;
let connecting = false;
let override = null;        // The setup tab's test commands replace keyboard and controller.
let lastReply = null;
let lastStatus = null;
let videoOn = false;
const listeners = {reply: new Set(), status: new Set()};
const pad = {snapshot: null, device: null, mode: "drive", command: {tracks: null, jog: {}}};

async function request(path, data) {
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 1500);
  try {
    const response = await fetch(path, {
      method: "POST", headers: {"Content-Type": "application/json", "X-Robotino-Token": token},
      body: JSON.stringify(data), signal: abort.signal, cache: "no-store",
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Connection failed");
    return result;
  } finally {
    clearTimeout(timeout);
  }
}

function stopRemote(oldSession) {
  if (oldSession) request("/api/stop", {session: oldSession}).catch(() => {});
}

function windowActive() {
  return document.hasFocus() && !document.hidden;
}

function disconnect(message = "Stopped — reconnect to drive") {
  const oldSession = session;
  generation += 1;
  session = challenge = null;
  connecting = false;
  clearTimeout(timer);
  keys.clear();
  armEnabled = false;
  holdArm = releaseArm = parkArm = false;
  pendingTargets.clear();
  updateArmControls();
  ui["arm-status"].textContent = "Stopped — the arm holds for 10 s, then releases";
  ui.connect.disabled = false;
  ui.status.textContent = "Disconnected";
  ui.motion.textContent = "Stop requested";
  ui.left.textContent = ui.right.textContent = "—";
  ui.error.textContent = message;
  stopRemote(oldSession);
}

// Setup test: forget the session WITHOUT telling the Pi, as if Wi-Fi dropped.
function simulateLinkLoss() {
  generation += 1;
  session = challenge = null;
  connecting = false;
  clearTimeout(timer);
  keys.clear();
  armEnabled = false;
  updateArmControls();
  ui.connect.disabled = false;
  ui.status.textContent = "Link loss simulated — the Pi must stop by itself";
}

function readKeys() {
  const held = [...keys].filter(key => directions.has(key));
  // Ambiguous combinations stop instead of guessing a direction.
  const deadman = keys.has("shift") && held.length === 1 && windowActive();
  return {motion: deadman ? directions.get(held[0]) : "stop", deadman};
}

function readDrive() {
  if (override) return override.drive();
  const keyboard = readKeys();
  if (keyboard.motion !== "stop") return keyboard;  // Keyboard first; the controller otherwise.
  if (pad.command.tracks && windowActive()) return {motion: "analog", tracks: pad.command.tracks, deadman: true};
  return keyboard;
}

function signFor(joint, label) {
  return G.sign(labels[joint], label);
}

function updateArmControls() {
  ui["arm-toggle"].disabled = !session || !armAvailable;
  ui["arm-toggle"].textContent = armEnabled ? "Release servos" : "Enable arm + camera";
  ui["arm-hold"].disabled = ui["arm-speed"].disabled = ui["arm-park"].disabled = !session || !armEnabled;
  for (const slider of Object.values(jointSliders)) slider.disabled = !session || !armEnabled;
}

function updateArm(state, sentTargets = {}) {
  if (!state) return;
  armAvailable = true;
  if (state.enabled) {
    ui["arm-status"].textContent = "Enabled — move a slider, hold Shift + joint key, or use ARM mode";
  } else if (state.release_in !== null && state.release_in !== undefined) {
    ui["arm-status"].textContent = `Holding after STOP — releases in ${Math.ceil(state.release_in)} s unless enabled`;
  } else {
    ui["arm-status"].textContent = "Released";
  }
  let hasRest = false;
  for (const key of jointNames) {
    const joint = state.joints[key];
    if (joint.labels) labels[key] = joint.labels;
    if (joint.rest !== null && joint.rest !== undefined) hasRest = true;
    const ticks = joint.ticks === undefined ? "" : ` · ${joint.ticks}`;
    jointOutputs[key].textContent = `${Math.round(joint.percent)}%${ticks}${joint.active ? "" : " · off"}`;
    if (document.activeElement !== jointSliders[key] && !pendingTargets.has(key) && !(key in sentTargets)) {
      jointSliders[key].value = String(Math.round(Math.max(0, Math.min(100, joint.target))));
    }
    labels[key].forEach((label, index) => {
      const key2 = [...armKeys].find(([, value]) => value[0] === key && value[1] === label);
      if (jointScales[key][index]) {
        jointScales[key][index].textContent = `${label[0].toUpperCase()}${label.slice(1)}${key2 ? ` · Shift+${key2[0].toUpperCase()}` : ""}`;
      }
    });
  }
  ui["arm-park"].hidden = !hasRest;
  updateArmControls();
}

function readArm() {
  if (override) return override.arm();
  const held = [...keys].filter(key => armKeys.has(key));
  const keyboardDeadman = keys.has("shift") && windowActive();
  let jog = {};
  if (armEnabled && keyboardDeadman && held.length === 1) {
    const [joint, label] = armKeys.get(held[0]);
    jog = {[joint]: signFor(joint, label)};
  } else if (armEnabled && windowActive() && Object.keys(pad.command.jog).length) {
    jog = pad.command.jog;  // A stick springs back to centre: that is its stop.
  }
  const deadman = keyboardDeadman || Object.keys(jog).length > 0;
  const targets = Object.fromEntries(pendingTargets);
  pendingTargets.clear();
  const hold = holdArm;
  const extra = {};
  if (releaseArm) extra.release = true;
  if (parkArm && !hold) extra.park = true;
  holdArm = releaseArm = parkArm = false;
  return {enabled: armEnabled, speed: Number(ui["arm-speed"].value),
    targets: hold ? {} : targets, jog: hold ? {} : jog, deadman, hold, ...extra};
}

async function tick(epoch) {
  if (!session || epoch !== generation) return;
  try {
    const drive = readDrive();
    const arm = readArm();
    const result = await request("/api/drive", {
      session, challenge, speed: Number(ui.speed.value) / 100, ...drive, arm,
    });
    if (epoch !== generation) return; // An old response must never reconnect us.
    challenge = result.challenge;
    lastReply = result;
    ui.motion.textContent = result.motion === "stop" ? "Stopped" : result.motion;
    ui.left.textContent = `${Math.round(result.left * 100)}%`;
    ui.right.textContent = `${Math.round(result.right * 100)}%`;
    updateArm(result.arm, arm.targets);
    for (const listener of listeners.reply) listener(result);
    // Exactly one in-flight drive request: no queue of old movements.
    timer = setTimeout(() => tick(epoch), 80);
  } catch (error) {
    if (epoch === generation) disconnect(error.name === "AbortError"
      ? "Connection timed out — release keys, then reconnect" : error.message);
  }
}

async function connectControls() {
  if (connecting || session) return;
  connecting = true;
  keys.clear(); // Require a NEW key press after connecting.
  const epoch = ++generation;
  ui.connect.disabled = true;
  ui.error.textContent = "";
  try {
    const result = await request("/api/connect", {});
    if (epoch !== generation) { stopRemote(result.session); return; }
    session = result.session;
    challenge = result.challenge;
    connecting = false;
    armEnabled = false;
    pendingTargets.clear();
    lastReply = result;
    updateArm(result.arm);
    ui.status.textContent = "Connected — hold Shift + direction, or use the controller";
    tick(epoch);
  } catch (error) {
    if (epoch === generation) disconnect(error.message);
  }
}

// ---- PS4 controller ------------------------------------------------------------------------

function rumble(pulses) {
  const actuator = pad.device && pad.device.vibrationActuator;
  if (!actuator || typeof actuator.playEffect !== "function") return false;
  for (let i = 0; i < pulses; i++) {
    setTimeout(() => {
      try {
        actuator.playEffect("dual-rumble", {duration: 120, strongMagnitude: 0.7, weakMagnitude: 0.7});
      } catch (_) { /* Vibration is only feedback. */ }
    }, i * 220);
  }
  return true;
}

function setMode(mode) {
  pad.mode = mode;
  if (mode === "arm" && session && armAvailable && !armEnabled) {
    armEnabled = true;  // ARM mode means the operator wants arm control.
    keys.clear();
    pendingTargets.clear();
  }
  rumble(mode === "arm" ? 2 : 1);
  updateArmControls();
  renderPad();
}

function stepSpeed(direction) {
  if (pad.mode === "arm") {
    const value = Math.max(25, Math.min(200, Number(ui["arm-speed"].value) + 25 * direction));
    ui["arm-speed"].value = String(value);
    ui["arm-speed-value"].textContent = `${value}%`;
  } else {
    const value = Math.max(0, Math.min(Number(ui.speed.max) || 100, Number(ui.speed.value) + 10 * direction));
    ui.speed.value = String(value);
    ui["speed-value"].textContent = `${value}%`;
  }
}

function padButton(name) {
  if (name === "circle") {  // STOP works everywhere, also during setup tests.
    if (session || connecting) disconnect("Controller STOP (○) — reconnect to drive");
    return;
  }
  if (override) return;     // Setup tests own the other buttons.
  if (name === "options") connectControls();
  else if (name === "triangle") setMode(pad.mode === "drive" ? "arm" : "drive");
  else if (name === "share" && armEnabled) { armEnabled = false; releaseArm = true; updateArmControls(); }
  else if (name === "square" && armEnabled) parkArm = true;
  else if (name === "left" || name === "right") stepSpeed(name === "right" ? 1 : -1);
}

function renderPad() {
  const snap = pad.snapshot;
  ui["pad-status"].textContent = snap
    ? `${snap.standard ? "Connected" : "Connected, unknown button layout"}: ${snap.id}`
    : "No controller — plug it in (USB) and press any button";
  ui["pad-mode"].textContent = pad.mode === "arm" ? "ARM" : "DRIVE";
  ui["pad-mode"].className = `pad-mode ${pad.mode}`;
}

function pollPad() {
  let pads = [];
  try {
    if (typeof navigator !== "undefined" && navigator.getGamepads) pads = navigator.getGamepads();
  } catch (_) { pads = []; }
  const device = G.find(pads);
  const snap = G.snapshot(device);
  const pressed = G.edges(pad.snapshot, snap);
  const lost = pad.snapshot && !snap;
  pad.snapshot = snap;
  pad.device = device;
  pad.command = snap && windowActive() ? G.command(snap, pad.mode, labels) : {tracks: null, jog: {}};
  if (lost) ui.error.textContent = "Controller disconnected — controller movement stopped";
  for (const name of pressed) padButton(name);
  renderPad();
}

// ---- Status, health and video --------------------------------------------------------------

function renderHealth(health) {
  if (!health || !health.available) {
    ui.health.textContent = "Pi health: not available here (simulation on a PC)";
    ui.health.className = "health";
    return;
  }
  const flags = health.flags || {};
  const parts = [];
  let level = "ok";
  if (flags.under_voltage_now) { parts.push("⚡ UNDER-VOLTAGE NOW — batteries too weak"); level = "bad"; }
  else if (flags.under_voltage_seen) { parts.push("⚠ Under-voltage happened since boot"); level = "warn"; }
  else parts.push("Supply OK");
  if (flags.throttled_now) { parts.push("CPU throttled"); if (level === "ok") level = "warn"; }
  if (health.temperature !== null) parts.push(`${health.temperature} °C`);
  if (health.cpu_percent !== null) parts.push(`CPU ${health.cpu_percent}%`);
  ui.health.textContent = parts.join(" · ");
  ui.health.className = `health ${level}`;
}

function renderVideo(camera) {
  if (!camera) {
    ui["video-status"].textContent = "Video is switched off (--no-camera)";
    ui["video-toggle"].disabled = true;
    return;
  }
  ui["video-toggle"].disabled = false;
  if (camera.running) {
    ui["video-status"].textContent = `${camera.simulated ? "Test card · " : ""}${camera.fps} fps · ${camera.width}×${camera.height}`;
  } else {
    ui["video-status"].textContent = camera.error || (camera.simulated ? "Off · this computer has no camera (test card)" : "Off");
  }
  if (document.activeElement !== ui["video-preset"]) ui["video-preset"].value = camera.preset;
}

function applyStatus(status) {
  if (!status || typeof status !== "object") return;
  lastStatus = status;
  renderHealth(status.health);
  renderVideo(status.camera);
  const saved = status.calibration && status.calibration.saved_at;
  ui["calibration-status"].textContent = saved ? `Calibration saved ${saved}` : "No calibration yet (archived limits)";
  const controller = status.controller || {};
  if (!session && controller.arm) updateArm(controller.arm);
  for (const listener of listeners.status) listener(status);
}

async function pollStatus() {
  try {
    applyStatus(await request("/api/status", {}));
  } catch (_) { /* The next poll retries; driving does not depend on it. */ }
}

function startVideo() {
  ui.video.src = `/video.mjpg?token=${encodeURIComponent(token)}&t=${Date.now()}`;
  videoOn = true;
  ui["video-toggle"].textContent = "Stop video";
}

function stopVideo() {
  ui.video.removeAttribute("src");
  videoOn = false;
  ui["video-toggle"].textContent = "Start video";
}

function showTab(name) {
  ui["panel-drive"].hidden = name !== "drive";
  ui["panel-setup"].hidden = name !== "setup";
  ui["tab-drive"].className = name === "drive" ? "tab active" : "tab";
  ui["tab-setup"].className = name === "setup" ? "tab active" : "tab";
  keys.clear();
  const setup = globalThis.RobotinoSetup;
  if (setup) name === "setup" ? setup.show() : setup.hide();
}

// ---- Page events ---------------------------------------------------------------------------

ui.connect.addEventListener("click", connectControls);
ui.stop.addEventListener("click", () => disconnect());
ui.speed.addEventListener("input", () => {
  ui["speed-value"].textContent = `${ui.speed.value}%`;
});
ui["arm-toggle"].addEventListener("click", () => {
  if (!session || !armAvailable) return;
  armEnabled = !armEnabled;
  releaseArm = !armEnabled;  // "Release servos" removes holding force at once.
  keys.clear();
  pendingTargets.clear();
  holdArm = false;
  updateArmControls();
});
ui["arm-hold"].addEventListener("click", () => {
  keys.clear();
  pendingTargets.clear();
  holdArm = true;
});
ui["arm-park"].addEventListener("click", () => {
  if (armEnabled) parkArm = true;
});
ui["arm-speed"].addEventListener("input", () => {
  ui["arm-speed-value"].textContent = `${ui["arm-speed"].value}%`;
});
for (const [key, slider] of Object.entries(jointSliders)) {
  slider.addEventListener("input", () => {
    if (!session || !armEnabled) return;
    keys.clear();
    pendingTargets.set(key, Number(slider.value));
  });
}
for (const slider of rangeInputs) slider.addEventListener("focus", () => keys.clear());
ui["video-toggle"].addEventListener("click", () => (videoOn ? stopVideo() : startVideo()));
ui["video-preset"].addEventListener("change", () => {
  request("/api/camera", {preset: ui["video-preset"].value}).then(renderVideo).catch(error => {
    ui.error.textContent = error.message;
  });
});
ui["tab-drive"].addEventListener("click", () => showTab("drive"));
ui["tab-setup"].addEventListener("click", () => showTab("setup"));
window.addEventListener("keydown", event => {
  const key = event.key.toLowerCase();
  const target = event.target || {};
  const typing = target.tagName === "TEXTAREA" || (target.tagName === "INPUT" && /^(text|number)$/.test(target.type));
  if (key === "escape" || (key === " " && !typing)) {
    event.preventDefault();
    disconnect();
    return;
  }
  if (typing) return;
  // Leave the range input's native arrow-key adjustment available without driving.
  if (rangeInputs.has(event.target) && key.startsWith("arrow")) return;
  if (directions.has(key) || armKeys.has(key) || key === "shift") {
    event.preventDefault();
    if (session && !event.repeat) keys.add(key);
  }
});
window.addEventListener("keyup", event => {
  const key = event.key.toLowerCase();
  keys.delete(key);
  if (!event.shiftKey) keys.delete("shift");
});
window.addEventListener("blur", () => disconnect("Window lost focus — reconnect to drive"));
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    disconnect("Tab hidden — reconnect to drive");
    if (videoOn) stopVideo();
  }
});
window.addEventListener("pagehide", () => disconnect());

// The setup tab (setup.js) drives tests through this small interface.
globalThis.RobotinoControl = {
  connect: connectControls,
  disconnect,
  simulateLinkLoss,
  connected: () => Boolean(session),
  setOverride(value) { override = value; keys.clear(); },
  lastReply: () => lastReply,
  lastStatus: () => lastStatus,
  pad: () => pad.snapshot,
  rumble,
  request,
  post: (path, data) => request(path, {session, ...data}),
  onReply: listener => listeners.reply.add(listener),
  onStatus: listener => listeners.status.add(listener),
  videoUrl: () => `/video.mjpg?token=${encodeURIComponent(token)}&t=${Date.now()}`,
};

updateArmControls();
renderPad();
setInterval(pollPad, 30);
setTimeout(pollStatus, 50);
setInterval(pollStatus, 2000);
