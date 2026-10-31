"use strict";
// Pure helpers for the guided setup page: turn observations into calibration
// values and a Markdown test report. No DOM and no network here.
(function (root) {
  const JOINTS = ["camera", "lower", "upper", "wrist", "gripper"];
  const NAMES = {camera: "Camera tilt", lower: "Lower arm", upper: "Upper arm", wrist: "Wrist rotation", gripper: "Gripper"};
  const PAIRS = {camera: ["up", "down"], lower: ["down", "up"], upper: ["up", "down"],
    wrist: ["left", "right"], gripper: ["open", "close"]};
  const GLOBAL = [100, 520];
  const MARGIN = 3;       // Ticks kept away from each marked end.
  const MIN_SPAN = 10;

  const other = (joint, label) => PAIRS[joint].find(item => item !== label);

  // A wiggle first moved `sign` ticks (+1/-1) and the user saw `seen`: which label is +ticks?
  function positiveLabel(joint, sign, seen) {
    if (!PAIRS[joint] || !PAIRS[joint].includes(seen)) return null;
    return sign > 0 ? seen : other(joint, seen);
  }

  // tested: {jointKey: {channel, moved}}, moved = a joint key, "nothing" or "unsure".
  function channelMap(tested) {
    const channels = {};
    const problems = [];
    for (const [key, item] of Object.entries(tested || {})) {
      if (!JOINTS.includes(item.moved)) {
        problems.push(`Channel ${item.channel} (${NAMES[key]}): ${item.moved === "nothing" ? "nothing moved" : "unclear result"}`);
        continue;
      }
      if (item.moved in channels) {
        problems.push(`Channels ${channels[item.moved]} and ${item.channel} both moved the ${NAMES[item.moved].toLowerCase()}`);
        continue;
      }
      channels[item.moved] = item.channel;
    }
    const changed = Object.entries(tested || {}).some(([key, item]) => JOINTS.includes(item.moved) && item.moved !== key);
    return {ok: problems.length === 0, changed, channels, problems};
  }

  function limitsFromEnds(a, b, margin = MARGIN) {
    if (!Number.isInteger(a) || !Number.isInteger(b)) return null;
    const minimum = Math.max(GLOBAL[0], Math.min(a, b) + margin);
    const maximum = Math.min(GLOBAL[1], Math.max(a, b) - margin);
    return maximum - minimum >= MIN_SPAN ? {minimum, maximum} : null;
  }

  // Curved left = the right track is faster: raise the left trim, or lower the right one.
  function trimAfter(trim, answer, step = 0.04) {
    let [left, right] = trim || [1, 1];
    if (answer === "left") {
      if (left < 1) left += step; else right -= step;
    } else if (answer === "right") {
      if (right < 1) right += step; else left -= step;
    }
    const fix = value => Math.round(Math.max(0.5, Math.min(1, value)) * 100) / 100;
    return [fix(left), fix(right)];
  }

  function rampDuty(step) {
    return Math.min(1, Math.round((0.1 + 0.05 * step) * 100) / 100);
  }

  function latency(screen, video) {
    const value = Number(screen) - Number(video);
    return Number.isFinite(value) && value >= 0 && value < 10000 ? value : null;
  }

  // fields: which measured joint values to send ("identity" = channel/direction, "range" = limits/rest).
  function jointCalibration(results, fields) {
    const joints = {};
    for (const key of JOINTS) {
      const r = ((results || {}).joints || {})[key] || {};
      const item = {};
      if (fields === "identity") {
        if (Number.isInteger(r.channel)) item.channel = r.channel;
        if (r.positive) item.positive = r.positive;
      } else {
        const ends = r.ends || {};
        const limits = limitsFromEnds(ends.negative, ends.positive);
        if (limits) Object.assign(item, limits);
        if (Number.isInteger(r.rest)) item.rest = r.rest;
      }
      if (Object.keys(item).length) joints[key] = item;
    }
    return joints;
  }

  function trackCalibration(results) {
    const tracks = (results || {}).tracks || {};
    const clamp = value => Math.round(Math.min(0.8, Math.max(0, value)) * 100) / 100;
    const out = {};
    if (Number.isFinite(tracks.floorDuty)) {
      out.min_duty = [clamp(tracks.floorDuty), clamp(tracks.floorDuty)];
    } else if (Array.isArray(tracks.raisedDuty) && tracks.raisedDuty.every(Number.isFinite)) {
      out.min_duty = tracks.raisedDuty.map(clamp);
    }
    if (Array.isArray(tracks.trim)) out.trim = tracks.trim.slice();
    return out;
  }

  // ---- Report -------------------------------------------------------------------------------

  const yes = value => value ? "yes" : "no";
  const cell = value => value === undefined || value === null || value === "" ? "—"
    : value === false ? "did not turn" : String(value).replace(/\|/g, "/");
  const table = (head, rows) => [`| ${head.join(" | ")} |`, `| ${head.map(() => "---").join(" | ")} |`,
    ...rows.map(row => `| ${row.map(cell).join(" | ")} |`)].join("\n");

  function report(results, status, sections) {
    const r = results || {};
    const s = status || {};
    const health = s.health || {};
    const lines = [
      "# Robotino test report", "",
      `- Generated: ${new Date().toISOString()}`,
      `- Software version: ${cell(s.version)}`,
      `- Real tracks: ${yes(s.tracks_real)} · real servos: ${yes(s.servos_real)}`
        + (s.tracks_real || s.servos_real ? "" : " · **SIMULATION ONLY — no physical result**"),
      `- Pi health: max temperature ${cell(health.max_temperature)} °C, under-voltage episodes this run: `
        + `${cell(health.under_voltage_events)}, under-voltage since boot: ${yes(health.flags && health.flags.under_voltage_seen)}`,
      "",
      "## Sections", "",
      table(["Section", "Result", "Mode"], (sections || []).map(item => [item.title, item.result, item.mode])),
      "",
    ];
    const c = r.controller || {};
    lines.push("## PS4 controller", "",
      `- Controller: ${cell(c.id)} · standard mapping: ${c.id ? yes(c.standard) : "—"}`,
      `- Buttons seen: ${(c.seen || []).length} · vibration: ${cell(c.rumble)}`, "");
    const identified = r.identify || {};
    if (Object.keys(identified).length) {
      lines.push("## Servo channels and directions", "",
        table(["Tested joint", "Channel", "What moved", "First move", "Saw", "Positive ticks mean"],
          JOINTS.filter(key => identified[key]).map(key => {
            const item = identified[key];
            return [NAMES[key], item.channel, NAMES[item.moved] || item.moved, item.sign > 0 ? "+ticks" : "−ticks",
              item.seen, JOINTS.includes(item.moved) ? positiveLabel(item.moved, item.sign, item.seen) : null];
          })), "");
      const map = channelMap(identified);
      if (map.problems.length) lines.push(...map.problems.map(text => `- Problem: ${text}`), "");
      if (map.changed) lines.push("- **Channel mapping differs from the archived one.**", "");
    }
    const joints = r.joints || {};
    if (JOINTS.some(key => joints[key] && (joints[key].ends || joints[key].rest !== undefined))) {
      lines.push("## Joint ranges and rest positions", "",
        table(["Joint", "Archived limits", "Marked ends (ticks)", "Saved limits", "Past archived?", "Rest", "Rest check"],
          JOINTS.map(key => {
            const item = joints[key] || {};
            const ends = item.ends || {};
            const limits = limitsFromEnds(ends.negative, ends.positive);
            const archived = (r.archived || {})[key];
            return [NAMES[key], archived ? `${archived[0]}–${archived[1]}` : null,
              ends.negative !== undefined || ends.positive !== undefined ? `${cell(ends.negative)} / ${cell(ends.positive)}` : null,
              limits ? `${limits.minimum}–${limits.maximum}` : null, item.beyond ? "yes" : null, item.rest, item.restCheck];
          })), "");
    }
    if (r.armStop) lines.push("## Arm behaviour after STOP", "", `- Observed: ${r.armStop}`, "");
    const t = r.tracks || {};
    if (Object.keys(t).length) {
      lines.push("## Tracks", "",
        `- Direction check: left → ${cell(t.left)}, right → ${cell(t.right)}`,
        `- Minimum duty (raised): left ${cell(t.raisedDuty && t.raisedDuty[0])}, right ${cell(t.raisedDuty && t.raisedDuty[1])}`
          + ` · on the floor: ${cell(t.floorDuty)}`,
        `- Straight-line trim: ${t.trim ? t.trim.join(" / ") : "—"} after ${cell(t.trimTries)} tries (${cell(t.straight)})`,
        `- Lost link: Pi stopped after ${cell(t.linkLoss && t.linkLoss.after)} s · observed: ${cell(t.linkLoss && t.linkLoss.answer)}`);
      for (const item of t.stopping || []) lines.push(`- Stopping distance at ${item.speed}% duty: ${item.cm} cm`);
      lines.push("");
    }
    const live = r.live || {};
    if (Object.keys(live).length) {
      lines.push("## Controller check on the robot", "",
        table(["Check", "Result", "Note"], Object.entries(live).map(([name, item]) => [name, item.answer, item.note])), "");
    }
    const v = r.video || {};
    if (Object.keys(v).length) {
      lines.push("## Video", "",
        `- Upright: ${cell(v.upright)} · latency: ${cell(v.latency)} ms`,
        `- Under load (${cell(v.perf && v.perf.preset)}): ${cell(v.perf && v.perf.fps)} fps, CPU ${cell(v.perf && v.perf.cpu)} %,`
          + ` ${cell(v.perf && v.perf.temperature)} °C · control: ${cell(v.perf && v.perf.answer)}`);
      if (v.probe) lines.push("", "Camera detection output:", "", "```text", v.probe.slice(0, 1500), "```");
      lines.push("");
    }
    if (r.notes) lines.push("## Notes", "", r.notes, "");
    const saved = s.calibration || {};
    lines.push("## Calibration stored on the Pi", "", "```json", JSON.stringify(saved, null, 2), "```", "");
    return lines.join("\n");
  }

  root.RobotinoSetupLogic = {JOINTS, NAMES, PAIRS, GLOBAL, MARGIN, positiveLabel, channelMap, limitsFromEnds,
    trimAfter, rampDuty, latency, jointCalibration, trackCalibration, report};
})(globalThis);
