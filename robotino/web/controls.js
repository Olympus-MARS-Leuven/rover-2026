"use strict";

const token = document.querySelector('meta[name="robotino-token"]').content;
const ui = Object.fromEntries(["connect", "stop", "status", "motion", "left", "right", "error", "speed", "speed-value",
  "arm-toggle", "arm-hold", "arm-status", "arm-speed", "arm-speed-value"]
  .map(id => [id, document.getElementById(id)]));
const keys = new Set();
const directions = new Map([
  ["arrowup", "forward"], ["z", "forward"], ["arrowdown", "backward"], ["s", "backward"],
  ["arrowleft", "left"], ["q", "left"], ["arrowright", "right"], ["d", "right"],
]);
const jointNames = ["camera", "lower", "upper", "wrist", "gripper"];
const jointSliders = Object.fromEntries(jointNames.map(key => [key, document.getElementById(`joint-${key}`)]));
const jointOutputs = Object.fromEntries(jointNames.map(key => [key, document.getElementById(`position-${key}`)]));
const armKeys = new Map([
  ["i", ["camera", -1]], ["k", ["camera", 1]],
  ["r", ["lower", 1]], ["f", ["lower", -1]],
  ["t", ["upper", -1]], ["g", ["upper", 1]],
  ["j", ["wrist", -1]], ["l", ["wrist", 1]],
  ["o", ["gripper", -1]], ["p", ["gripper", 1]],
]);
const rangeInputs = new Set([ui.speed, ui["arm-speed"], ...Object.values(jointSliders)]);
let armEnabled = false;
let armAvailable = false;
let holdArm = false;
const pendingTargets = new Map();
let session = null;
let challenge = null;
let generation = 0;
let timer = null;
let connecting = false;

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

function disconnect(message = "Stopped — reconnect to drive") {
  const oldSession = session;
  generation += 1;
  session = challenge = null;
  connecting = false;
  clearTimeout(timer);
  keys.clear();
  armEnabled = false;
  holdArm = false;
  pendingTargets.clear();
  updateArmControls();
  ui["arm-status"].textContent = "Released";
  ui.connect.disabled = false;
  ui.status.textContent = "Disconnected";
  ui.motion.textContent = "Stop requested";
  ui.left.textContent = ui.right.textContent = "—";
  ui.error.textContent = message;
  stopRemote(oldSession);
}

function readKeys() {
  const held = [...keys].filter(key => directions.has(key));
  // Ambiguous combinations stop instead of guessing a direction.
  const deadman = keys.has("shift") && held.length === 1 && document.hasFocus() && !document.hidden;
  return {motion: deadman ? directions.get(held[0]) : "stop", deadman};
}

function updateArmControls() {
  ui["arm-toggle"].disabled = !session || !armAvailable;
  ui["arm-toggle"].textContent = armEnabled ? "Release servos" : "Enable arm + camera";
  ui["arm-hold"].disabled = ui["arm-speed"].disabled = !session || !armEnabled;
  for (const slider of Object.values(jointSliders)) slider.disabled = !session || !armEnabled;
}

function updateArm(state, sentTargets = {}) {
  if (!state) return;
  armAvailable = true;
  ui["arm-status"].textContent = state.enabled ? "Enabled — move a slider or hold Shift + joint key" : "Released";
  for (const key of jointNames) {
    const joint = state.joints[key];
    jointOutputs[key].textContent = `${Math.round(joint.percent)}%${joint.active ? "" : " · inactive"}`;
    if (document.activeElement !== jointSliders[key] && !pendingTargets.has(key) && !(key in sentTargets)) {
      jointSliders[key].value = String(Math.round(joint.target));
    }
  }
  updateArmControls();
}

function readArm() {
  const held = [...keys].filter(key => armKeys.has(key));
  const deadman = keys.has("shift") && document.hasFocus() && !document.hidden;
  const jog = armEnabled && deadman && held.length === 1 ? Object.fromEntries([armKeys.get(held[0])]) : {};
  const targets = Object.fromEntries(pendingTargets);
  pendingTargets.clear();
  const hold = holdArm;
  holdArm = false;
  return {enabled: armEnabled, speed: Number(ui["arm-speed"].value),
    targets: hold ? {} : targets, jog: hold ? {} : jog, deadman, hold};
}

async function tick(epoch) {
  if (!session || epoch !== generation) return;
  try {
    const arm = readArm();
    const result = await request("/api/drive", {
      session, challenge, ...readKeys(), speed: Number(ui.speed.value) / 100, arm,
    });
    if (epoch !== generation) return; // An old response must never reconnect us.
    challenge = result.challenge;
    ui.motion.textContent = result.motion === "stop" ? "Stopped" : result.motion;
    ui.left.textContent = `${Math.round(result.left * 100)}%`;
    ui.right.textContent = `${Math.round(result.right * 100)}%`;
    updateArm(result.arm, arm.targets);
    // Exactly one in-flight drive request: no queue of old movements.
    timer = setTimeout(() => tick(epoch), 80);
  } catch (error) {
    if (epoch === generation) disconnect(error.name === "AbortError"
      ? "Connection timed out — release keys, then reconnect" : error.message);
  }
}

ui.connect.addEventListener("click", async () => {
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
    updateArm(result.arm);
    ui.status.textContent = "Connected — hold Shift + direction";
    tick(epoch);
  } catch (error) {
    if (epoch === generation) disconnect(error.message);
  }
});

ui.stop.addEventListener("click", () => disconnect());
ui.speed.addEventListener("input", () => {
  ui["speed-value"].textContent = `${ui.speed.value}%`;
});
ui["arm-toggle"].addEventListener("click", () => {
  if (!session || !armAvailable) return;
  armEnabled = !armEnabled;
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
window.addEventListener("keydown", event => {
  const key = event.key.toLowerCase();
  if (["escape", " "].includes(key)) {
    event.preventDefault();
    disconnect();
    return;
  }
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
  if (document.hidden) disconnect("Tab hidden — reconnect to drive");
});
window.addEventListener("pagehide", () => disconnect());
updateArmControls();
