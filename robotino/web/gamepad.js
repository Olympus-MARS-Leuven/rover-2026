"use strict";
// PS4 (DualShock 4) helpers for the browser Gamepad API "standard" mapping.
// Pure functions only: controls.js reads the controller and sends commands.
(function (root) {
  const BUTTONS = {
    cross: 0, circle: 1, square: 2, triangle: 3, l1: 4, r1: 5, l2: 6, r2: 7,
    share: 8, options: 9, l3: 10, r3: 11, up: 12, down: 13, left: 14, right: 15, ps: 16, touchpad: 17,
  };
  // [negative ticks, positive ticks], as in calibration.py until the page receives measured labels.
  const DEFAULT_LABELS = {
    camera: ["up", "down"], lower: ["down", "up"], upper: ["up", "down"],
    wrist: ["left", "right"], gripper: ["open", "close"],
  };
  const DEADZONE = 0.15;  // Worn sticks rarely rest exactly at zero.
  const PRECISION = 0.4;  // L1/R1 held: slower, finer movement.
  const TURN = 0.8;       // Turning is less sensitive than driving straight.
  const CAMERA_RATE = 0.6;

  const round = value => Math.round(Math.max(-1, Math.min(1, value)) * 100) / 100;

  function find(pads) {
    const list = [...(pads || [])].filter(pad => pad && pad.connected);
    return list.find(pad => pad.mapping === "standard") || list[0] || null;
  }

  function snapshot(pad) {
    if (!pad) return null;
    const pressed = {};
    const values = {};
    for (const [name, index] of Object.entries(BUTTONS)) {
      const button = pad.buttons[index];
      values[name] = button ? Number(button.value) || (button.pressed ? 1 : 0) : 0;
      pressed[name] = Boolean(button && (button.pressed || values[name] > 0.5));
    }
    const axes = [0, 1, 2, 3].map(index => Number(pad.axes[index]) || 0);
    return {id: String(pad.id || "controller"), standard: pad.mapping === "standard", pressed, values, axes};
  }

  function edges(previous, current) {
    if (!current) return [];
    return Object.keys(BUTTONS).filter(name => current.pressed[name] && !(previous && previous.pressed[name]));
  }

  // Radial dead zone, rescaled, squared for fine control near the centre. Returns [x, y] with up positive.
  function stick(x, y) {
    const magnitude = Math.hypot(x, y);
    if (magnitude < DEADZONE) return [0, 0];
    const curved = Math.min(1, (magnitude - DEADZONE) / (1 - DEADZONE)) ** 2;
    return [x / magnitude * curved, -y / magnitude * curved];
  }

  // One stick drives both tracks: up = forward, right = turn right (left track forward).
  function arcade(x, y) {
    const left = y + x;
    const right = y - x;
    const peak = Math.max(1, Math.abs(left), Math.abs(right));
    return [round(left / peak), round(right / peak)];
  }

  function trigger(value) {
    return value < 0.1 ? 0 : Math.min(1, (value - 0.1) / 0.9);
  }

  // +1 when the label is the positive-ticks direction of that joint.
  function sign(labels, label) {
    return (labels || [])[0] === label ? -1 : 1;
  }

  // Map one snapshot to {tracks: [left, right] | null, jog: {joint: -1..1}}. mode: "drive" | "arm".
  function command(snap, mode, labels = DEFAULT_LABELS) {
    const result = {tracks: null, jog: {}};
    if (!snap) return result;
    const scale = snap.pressed.l1 || snap.pressed.r1 ? PRECISION : 1;
    const add = (joint, label, amount) => {
      const value = round(sign(labels[joint] || DEFAULT_LABELS[joint], label) * amount * scale);
      if (value) result.jog[joint] = value;
    };
    if (snap.pressed.up !== snap.pressed.down) add("camera", snap.pressed.up ? "up" : "down", CAMERA_RATE);
    const [lx, ly] = stick(snap.axes[0], snap.axes[1]);
    const [rx, ry] = stick(snap.axes[2], snap.axes[3]);
    if (mode === "arm") {
      add("lower", "up", ly);
      add("upper", "up", ry);
      add("wrist", "right", rx);
      add("gripper", "close", trigger(snap.values.r2) - trigger(snap.values.l2));
    } else if (lx || ly) {
      const tracks = arcade(lx * TURN * scale, ly * scale);
      if (tracks[0] || tracks[1]) result.tracks = tracks;
    }
    return result;
  }

  root.RobotinoGamepad = {BUTTONS, DEFAULT_LABELS, DEADZONE, PRECISION, find, snapshot, edges, stick, arcade,
    trigger, sign, command};
})(globalThis);
