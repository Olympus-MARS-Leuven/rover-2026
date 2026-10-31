"use strict";
// Guided setup and test tab. Every movement is small, slow and started by the
// user; each answer is stored in this browser, turned into calibration that is
// saved on the Pi, and summarised in a downloadable report.
(function () {
  const C = globalThis.RobotinoControl;
  const L = globalThis.RobotinoSetupLogic;
  const G = globalThis.RobotinoGamepad;
  const root = document.getElementById("setup-root");
  const STORAGE = "robotino-setup-v1";
  const TEST_SPEED = 30;  // Ticks per second; the Pi caps calibration moves at 40.
  const LIMIT_ORDER = ["camera", "gripper", "wrist", "upper", "lower"];
  const REST_ORDER = ["lower", "upper"];
  const HINTS = {
    camera: "Tilt it fully both ways, stopping just before the mechanical end.",
    gripper: "Open end: fully open without straining. Close end: close it on a 3 cm block until it holds firmly, not until it buzzes.",
    wrist: "Turn it both ways until just before the end of travel, or until a cable starts to pull.",
    upper: "Support the arm. Move both ways until just before it touches the body, the lower arm or the floor.",
    lower: "Support the arm. Find the lowest and the highest safe position.",
  };
  const PAD_NAMES = {cross: "✕ Cross", circle: "○ Circle", square: "□ Square", triangle: "△ Triangle", l1: "L1", r1: "R1",
    l2: "L2", r2: "R2", share: "Share", options: "Options", l3: "L3 (press stick)", r3: "R3 (press stick)",
    up: "D-pad ↑", down: "D-pad ↓", left: "D-pad ←", right: "D-pad →"};
  const LIVE_CHECKS = [
    ["stick", "DRIVE: left stick drives forward/backward and turns; letting go stops"],
    ["mode", "△ switches DRIVE ↔ ARM, with 1 / 2 vibrations"],
    ["lower", "ARM: left stick ↕ moves the lower arm the right way"],
    ["upper", "ARM: right stick ↕ moves the upper arm the right way"],
    ["wrist", "ARM: right stick ↔ turns the wrist the right way"],
    ["gripper", "ARM: R2 closes, L2 opens the gripper"],
    ["camera", "D-pad ↑ / ↓ tilts the camera up / down"],
    ["precision", "Holding L1 or R1 makes movement slower"],
    ["stop", "○ stops everything; Options connects again"],
    ["unplug", "Unplugging the USB cable while driving stops the tracks"],
  ];

  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const cap = text => text ? text[0].toUpperCase() + text.slice(1) : "";

  let results = load();
  let visible = false;
  let liveControl = false;
  let measuring = false;   // Video load test: normal controls for a while.
  let busy = false;        // A scripted movement is running.
  let flash = null;        // One-time message on the card.
  let jogging = null;      // {key, direction} while a hold button is pressed.
  let blocked = null;      // {key, side}: paused at an archived limit.
  let ramp = null;         // Minimum-duty ramp in progress.
  let preview = false;
  let wasConnected = false;
  const cmd = {drive: {motion: "stop", deadman: false}, arm: {enabled: false}, once: {}};
  const updaters = new Set();
  const tickers = new Set();

  // ---- State ------------------------------------------------------------------------------

  function fresh() {
    return {section: "prepare", done: {}, practice: {}, progress: {}, joints: {}, identify: {}, archived: {},
      tracks: {}, live: {}, video: {}, controller: {}, notes: ""};
  }

  function load() {
    try {
      return {...fresh(), ...(JSON.parse(localStorage.getItem(STORAGE)) || {})};
    } catch (_) {
      return fresh();
    }
  }

  function save() {
    try { localStorage.setItem(STORAGE, JSON.stringify(results)); } catch (_) { /* Answers stay in memory. */ }
  }

  function store() {
    save();
    render();
  }

  const prog = id => (results.progress[id] ||= {});
  const status = () => C.lastStatus() || {};
  const armState = () => (C.connected() && C.lastReply() && C.lastReply().arm) || (status().controller || {}).arm || null;
  const joint = key => ((armState() || {}).joints || {})[key];

  // ---- Commands sent by controls.js while this tab is visible -------------------------------

  function armOn(extra = {}) {
    cmd.arm = {enabled: true, calibrate: true, speed: TEST_SPEED, ...extra};
  }

  function stopDrive() {
    cmd.drive = {motion: "stop", deadman: false};
  }

  const override = {
    drive: () => cmd.drive,
    arm: () => {
      const value = {...cmd.arm, ...cmd.once};
      cmd.once = {};
      return value;
    },
  };

  function applyOverride() {
    C.setOverride(visible && !liveControl && !measuring ? override : null);
  }

  function resetCommands() {
    stopDrive();
    cmd.arm = {enabled: false};
    cmd.once = {};
    jogging = null;
    if (ramp) ramp.running = false;
  }

  async function until(predicate, timeout = 4000) {
    const end = Date.now() + timeout;
    while (Date.now() < end) {
      if (!C.connected()) return false;
      if (predicate()) return true;
      await sleep(60);
    }
    return false;
  }

  // Power an inactive joint where the Pi thinks it is, then ramp slowly to the target.
  async function moveTo(key, target) {
    const current = joint(key);
    if (!current || !C.connected()) throw new Error("Connect first");
    if (!current.active) {
      armOn({ticks: {[key]: current.ticks}});
      await until(() => (joint(key) || {}).active, 2000);
    }
    armOn({ticks: {[key]: target}});
    await until(() => Math.abs((joint(key) || {}).ticks - target) <= 1, 5000);
    armOn();
  }

  async function wiggle(key, amount) {
    const current = joint(key);
    if (!current || !C.connected()) throw new Error("Connect first");
    const base = current.ticks;
    const sign = base + amount <= Math.max(current.default_maximum, current.maximum) ? 1 : -1;
    const target = Math.max(L.GLOBAL[0], Math.min(L.GLOBAL[1], base + sign * amount));
    await moveTo(key, target);
    await sleep(600);
    await moveTo(key, base);
    return sign;
  }

  async function scripted(action) {
    if (busy) return;
    busy = true;
    flash = null;
    render();
    try {
      await action();
    } catch (error) {
      flash = {kind: "bad", text: error.message};
    } finally {
      busy = false;
      stopDrive();
      store();
    }
  }

  async function runTracks(tracks, speed, ms) {
    cmd.drive = {motion: "analog", tracks, raw: true, speed, deadman: true};
    await sleep(ms);
    stopDrive();
  }

  function startJog(key, direction) {
    if (blocked && blocked.key === key && blocked.side === (direction < 0 ? "negative" : "positive")) return;
    jogging = {key, direction};
    armOn({jog: {[key]: direction}, deadman: true});
  }

  function stopJog() {
    jogging = null;
    if (cmd.arm.jog) armOn();
  }

  // ---- DOM helpers --------------------------------------------------------------------------

  function h(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (key === "on") for (const [type, fn] of Object.entries(value)) node.addEventListener(type, fn);
      else if (key === "class") node.className = value;
      else if (value !== undefined && value !== null && value !== false) node[key] = value;
    }
    for (const child of children.flat(Infinity)) {
      if (child !== null && child !== undefined && child !== false) node.append(child instanceof Node ? child : String(child));
    }
    return node;
  }

  const p = (...children) => h("p", {}, ...children);
  const muted = (...children) => h("p", {class: "muted"}, ...children);
  const box = (kind, ...children) => h("div", {class: kind}, ...children);
  const row = (...children) => h("div", {class: "row"}, ...children);

  function button(label, onClick, kind = "secondary", disabled = false) {
    return h("button", {class: kind, disabled: Boolean(disabled), on: {click: onClick}}, label);
  }

  function choice(question, options, picked, onPick) {
    return h("div", {}, p(h("b", {}, question)), h("div", {class: "choices"}, options.map(([value, label]) =>
      h("button", {class: value === picked ? "picked" : "", on: {click: () => onPick(value)}}, label))));
  }

  function holdButton(label, start, stop, disabled = false) {
    const node = h("button", {class: "hold", disabled: Boolean(disabled)}, label);
    let active = false;
    const end = () => {
      if (!active) return;
      active = false;
      node.classList.remove("active");
      stop();
    };
    node.addEventListener("pointerdown", event => {
      event.preventDefault();
      if (!C.connected() || node.disabled) return;
      active = true;
      node.classList.add("active");
      try { node.setPointerCapture(event.pointerId); } catch (_) { /* Older browsers. */ }
      start();
    });
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) node.addEventListener(type, end);
    return node;
  }

  function live(read, className = "live") {
    const node = h("span", {class: className});
    const update = () => { node.textContent = read(); };
    update();
    updaters.add(update);
    return node;
  }

  function connection() {
    return C.connected() ? null : box("warn", "Not connected. ", button("Connect", () => C.connect(), "primary"));
  }

  function missingFor(section) {
    const s = status();
    const missing = [];
    if ((section.needs === "servos" || section.needs === "both") && !s.servos_real) missing.push("real servos (--servos)");
    if ((section.needs === "tracks" || section.needs === "both") && !s.tracks_real) missing.push("real tracks (--hardware)");
    if (section.needs === "camera" && !(s.camera && s.camera.available)) missing.push("the Pi camera");
    return missing;
  }

  function requirement(section) {
    const missing = missingFor(section);
    if (!missing.length) return null;
    return box("warn", `Practice mode: this step needs ${missing.join(" and ")}. It still runs in simulation so you `
      + "can learn it; results are marked as practice and no calibration is saved. For the real test stop the app "
      + "(Ctrl+C) and start: python3 robotino_app.py --hardware --servos");
  }

  function finish(id, result = "done") {
    const index = SECTIONS.findIndex(section => section.id === id);
    results.done[id] = result;
    results.practice[id] = missingFor(SECTIONS[index]).length > 0;
    results.section = (SECTIONS[index + 1] || SECTIONS[index]).id;
    flash = null;
    store();
  }

  async function saveCalibration(payload) {
    try {
      await C.post("/api/calibration", payload);
      flash = {kind: "good", text: "Saved on the robot. It is used from now on, also after a restart."};
      return true;
    } catch (error) {
      flash = {kind: "bad", text: `Not saved: ${error.message}`};
      return false;
    } finally {
      render();
    }
  }

  const ticks = key => {
    const current = joint(key);
    return current ? `${current.ticks} ticks${current.active ? "" : " (not powered)"}` : "—";
  };

  // ---- Sections -----------------------------------------------------------------------------

  const SECTIONS = [
    {id: "prepare", title: "Before you start", render: renderPrepare},
    {id: "controller", title: "PS4 controller", render: renderController},
    {id: "identify", title: "Servo channels & directions", needs: "servos", render: renderIdentify},
    {id: "limits", title: "Joint limits", needs: "servos", render: renderLimits},
    {id: "rest", title: "Arm rest positions", needs: "servos", render: renderRest},
    {id: "armstop", title: "Arm after STOP", needs: "servos", render: renderArmStop},
    {id: "trackdir", title: "Track directions", needs: "tracks", render: renderTrackDirections},
    {id: "minduty", title: "Minimum track power", needs: "tracks", render: renderMinDuty},
    {id: "straight", title: "Driving straight", needs: "tracks", render: renderStraight},
    {id: "linkloss", title: "Lost-link stop", needs: "tracks", render: renderLinkLoss},
    {id: "stopping", title: "Stopping distance", needs: "tracks", render: renderStopping},
    {id: "savetracks", title: "Save track calibration", needs: "tracks", render: renderSaveTracks},
    {id: "live", title: "Controller on the robot", needs: "both", render: renderLive},
    {id: "video", title: "Video", needs: "camera", render: renderVideo},
    {id: "report", title: "Report", render: renderReport},
  ];

  function renderPrepare() {
    const s = status();
    const checks = [
      ["charged", "Batteries freshly charged. The bar at the top warns about under-voltage (weak batteries)."],
      ["raised", "Robot on a stand: both tracks off the ground and free to turn."],
      ["clear", "Arm area clear of hands, cables and objects; one hand free to support the arm."],
      ["power", "Power switch within reach: the software STOP is not an emergency stop."],
      ["pad", "PS4 controller plugged into this PC with the USB cable (for the controller steps)."],
    ];
    const pr = prog("prepare");
    return [
      p("This tab moves one thing at a time, slowly, and asks what you saw. Your answers become the robot's "
        + "calibration (saved on the Pi, used automatically from then on) and a report you can download and send."),
      p("Start on the Pi with: ", h("code", {}, "python3 robotino_app.py --hardware --servos")),
      p(`This app: tracks ${s.tracks_real ? "REAL" : "simulated"} · servos ${s.servos_real ? "REAL" : "simulated"} · `
        + `camera ${s.camera ? (s.camera.available ? "found" : "test card") : "off"} · version ${s.version || "?"}`),
      checks.map(([key, text]) => h("label", {class: "check"}, h("input", {type: "checkbox", checked: Boolean(pr[key]),
        on: {change: event => { pr[key] = event.target.checked; save(); }}}), text)),
      muted("The red STOP at the top (or Esc, or ○ on the controller) stops everything at any moment. "
        + "Steps can be done in any order and repeated; click a step on the left."),
      button("Start the tests", () => finish("prepare"), "primary"),
    ];
  }

  function renderController() {
    const record = results.controller;
    record.seen ||= [];
    const names = Object.keys(PAD_NAMES);
    const cells = Object.fromEntries(names.map(name => [name, h("span", {}, PAD_NAMES[name])]));
    tickers.add(() => {
      const snap = C.pad();
      if (snap) {
        record.id = snap.id;
        record.standard = snap.standard;
        for (const name of names) {
          if (snap.pressed[name] && !record.seen.includes(name)) { record.seen.push(name); save(); }
        }
      }
      for (const name of names) {
        cells[name].className = `${snap && snap.pressed[name] ? "on" : ""} ${record.seen.includes(name) ? "seen" : ""}`;
      }
    });
    const missing = () => names.filter(name => !record.seen.includes(name));
    return [
      p("This works without the robot. Plug the controller into this PC with the USB cable and press any button, "
        + "so the browser sees it. Then press every button once and move both sticks. ○ is STOP; pressing it here is harmless."),
      p(live(() => {
        const snap = C.pad();
        if (!snap) return "No controller seen yet";
        return `${snap.standard ? "Standard layout" : "UNKNOWN layout — buttons may be wrong"}: ${snap.id}`;
      }, "muted")),
      h("div", {class: "pad-grid"}, Object.values(cells)),
      p(live(() => {
        const snap = C.pad();
        if (!snap) return "";
        const [lx, ly, rx, ry] = snap.axes.map(value => value.toFixed(2));
        return `Left stick ${lx}, ${ly} · right stick ${rx}, ${ry} · L2 ${snap.values.l2.toFixed(2)} · R2 ${snap.values.r2.toFixed(2)}`;
      }, "muted")),
      p(live(() => missing().length ? `Still to press: ${missing().map(name => PAD_NAMES[name]).join(", ")}` : "All buttons seen ✓", "muted")),
      row(button("Test vibration", () => { record.rumbleTried = C.rumble(2) ? "sent" : "unsupported"; store(); })),
      record.rumbleTried === "unsupported" ? box("warn", "This browser cannot vibrate the controller. That is only feedback; driving still works.") : null,
      record.rumbleTried === "sent" ? choice("Did it vibrate twice?", [["yes", "Yes"], ["no", "No"]], record.rumble, value => {
        record.rumble = value; store();
      }) : null,
      button("Done", () => finish("controller", missing().length || record.standard === false ? "issue" : "done"), "primary"),
    ];
  }

  function applyIdentity() {
    for (const item of Object.values(results.identify)) {
      if (!L.JOINTS.includes(item.moved)) continue;
      const target = results.joints[item.moved] ||= {};
      target.channel = item.channel;
      const positive = L.positiveLabel(item.moved, item.sign, item.seen);
      if (positive) target.positive = positive; else delete target.positive;
    }
  }

  function renderIdentify() {
    const pr = prog("identify");
    const index = pr.index || 0;
    if (index >= L.JOINTS.length) return renderIdentifySummary();
    const key = L.JOINTS[index];
    const current = joint(key);
    const item = results.identify[key] || {};
    const doWiggle = amount => scripted(async () => {
      const sign = await wiggle(key, amount);
      results.identify[key] = {channel: joint(key).channel, sign, amount};
    });
    return [
      connection(),
      p(h("b", {}, `Joint ${index + 1} of 5: channel ${current ? current.channel : "?"}`), ` — expected: ${L.NAMES[key]}.`),
      p("Support the arm with one hand. Wiggle moves this channel slowly by 20 ticks and back. If its position is "
        + "unknown, the moment it is powered it can jump to the start value: that is normal here."),
      p("Position: ", live(() => ticks(key))),
      row(button(busy ? "Moving…" : "Wiggle", () => doWiggle(20), "primary", busy || !C.connected()),
        button("Wiggle bigger (40)", () => doWiggle(40), "secondary", busy || !C.connected())),
      item.sign ? choice("What moved?", [...L.JOINTS.map(name => [name, L.NAMES[name]]), ["nothing", "Nothing"],
        ["unsure", "Several / not sure"]], item.moved, value => { item.moved = value; item.seen = undefined; store(); }) : null,
      item.moved === "nothing" ? box("warn", "Nothing moved: check the battery switch and that this servo's cable is "
        + "plugged into the board. Try the bigger wiggle once. If still nothing, go on and the report will show it.") : null,
      L.JOINTS.includes(item.moved) ? choice(`Which way did the ${L.NAMES[item.moved].toLowerCase()} move FIRST?`,
        [...L.PAIRS[item.moved].map(label => [label, cap(label)]), ["unsure", "Couldn't tell"]], item.seen,
        value => { item.seen = value; store(); }) : null,
      row(button("Next joint", () => { pr.index = index + 1; store(); }, "primary", !item.moved || (L.JOINTS.includes(item.moved) && !item.seen)),
        button("Skip this joint", () => { pr.index = index + 1; store(); })),
    ];
  }

  function renderIdentifySummary() {
    const map = L.channelMap(results.identify);
    const canSave = status().can_save && status().can_save.joints;
    return [
      p("Results:"),
      h("table", {}, h("tr", {}, ["Tested", "Channel", "What moved", "Saw"].map(text => h("th", {}, text))),
        L.JOINTS.map(key => {
          const item = results.identify[key] || {};
          return h("tr", {}, [L.NAMES[key], item.channel, L.NAMES[item.moved] || item.moved || "—", item.seen || "—"]
            .map(text => h("td", {}, text === undefined ? "—" : String(text))));
        })),
      map.problems.length ? box("bad", map.problems.join(" · ")) : null,
      map.changed ? box("warn", "The channel mapping differs from the archived one. Saving releases all servos first: support the arm.") : null,
      !canSave ? box("warn", "Practice mode: nothing is saved.") : null,
      row(button("Save channels and directions", () => scripted(async () => {
        applyIdentity();
        if (map.changed) {
          cmd.once.release = true;
          cmd.arm = {enabled: false};
          await sleep(400);
        }
        if (await saveCalibration({joints: L.jointCalibration(results, "identity")})) finish("identify");
      }), "primary", !map.ok || !canSave || busy || !C.connected()),
        button("Continue without saving", () => { applyIdentity(); finish("identify", map.ok ? "skipped" : "issue"); }),
        button("Redo from joint 1", () => { prog("identify").index = 0; store(); })),
    ];
  }

  function renderLimits() {
    const pr = prog("limits");
    const index = pr.index || 0;
    if (index >= LIMIT_ORDER.length) return renderRangeSummary("limits");
    const key = LIMIT_ORDER[index];
    const current = joint(key);
    const record = results.joints[key] ||= {};
    record.ends ||= {};
    if (current) results.archived[key] = [current.default_minimum, current.default_maximum];
    const [negative, positive] = current ? current.labels : L.PAIRS[key];
    const mark = side => { record.ends[side] = joint(key).ticks; store(); };
    const isBlocked = blocked && blocked.key === key;
    return [
      connection(),
      p(h("b", {}, `${index + 1} of 5: ${L.NAMES[key]}. `), HINTS[key]),
      p("Hold a yellow button to move slowly (30 ticks per second); let go to stop. Stop before anything touches or "
        + "strains. Buzzing means straining: move back a little before marking."),
      p("Now: ", live(() => ticks(key)), current ? h("span", {class: "muted"},
        ` · archived range ${current.default_minimum}–${current.default_maximum} · absolute limit 100–520`) : null),
      row(holdButton(`◀ Hold: move ${negative}`, () => startJog(key, -1), stopJog, busy),
        holdButton(`Hold: move ${positive} ▶`, () => startJog(key, 1), stopJog, busy)),
      isBlocked ? box("warn", `Paused at the archived ${blocked.side === "negative" ? negative : positive} limit. `
        + "The real joint may go further. Continue only while watching closely. ",
      button("Continue past it", () => {
        (record.allowBeyond ||= {})[blocked.side] = true;
        record.beyond = true;
        blocked = null;
        store();
      }, "primary")) : null,
      row(button(`Mark this as the ${negative} end`, () => mark("negative"), "secondary", !current),
        button(`Mark this as the ${positive} end`, () => mark("positive"), "secondary", !current)),
      p(live(() => {
        const limits = L.limitsFromEnds(record.ends.negative, record.ends.positive);
        const ends = `${cap(negative)} end: ${record.ends.negative ?? "—"} · ${positive} end: ${record.ends.positive ?? "—"}`;
        return limits ? `${ends} → limits ${limits.minimum}–${limits.maximum} (${L.MARGIN}-tick margin)` : `${ends} → mark both ends`;
      }, "muted")),
      row(button("Next joint", () => { pr.index = index + 1; blocked = null; store(); }, "primary",
        !L.limitsFromEnds(record.ends.negative, record.ends.positive)),
      button("Keep the archived limits", () => { record.ends = {}; pr.index = index + 1; blocked = null; store(); })),
    ];
  }

  function renderRangeSummary(id) {
    const canSave = status().can_save && status().can_save.joints;
    const joints = L.jointCalibration(results, "range");
    return [
      p("Measured values to save (other joints keep their current values):"),
      h("pre", {}, JSON.stringify(joints, null, 2)),
      !canSave ? box("warn", "Practice mode: nothing is saved.") : null,
      row(button(id === "rest" ? "Save limits and rest positions" : "Save limits now", async () => {
        if (await saveCalibration({joints})) finish(id);
      }, "primary", !canSave || !Object.keys(joints).length || !C.connected()),
      button("Continue without saving", () => finish(id, "skipped")),
      button("Redo", () => { prog(id).index = 0; store(); })),
    ];
  }

  function restEstimate(key) {
    const record = results.joints[key] || {};
    if (Number.isInteger(record.rest)) return record.rest;
    const current = joint(key);
    const ends = record.ends || {};
    const downSide = current && current.labels[0] === "down" ? "negative" : "positive";
    if (Number.isInteger(ends[downSide])) return ends[downSide];
    return current ? current.ticks : 300;
  }

  function renderRest() {
    const pr = prog("rest");
    const index = pr.index || 0;
    if (index >= REST_ORDER.length) return renderRangeSummary("rest");
    const key = REST_ORDER[index];
    const record = results.joints[key] ||= {};
    const phase = pr.phase || "release";
    const name = L.NAMES[key].toLowerCase();
    const steps = {
      release: [
        p("Gravity pulls this joint to the same resting pose whenever it is unpowered. Measuring that pose lets the "
          + "robot power the arm later without a jump."),
        p("1. Hold the arm. Press Release, then let the whole arm down gently until it rests by itself. Take your hand away."),
        button("Release all servos", () => {
          cmd.once.release = true;
          cmd.arm = {enabled: false};
          pr.phase = "power";
          store();
        }, "primary", !C.connected()),
      ],
      power: [
        p(`2. Power the ${name} at ${restEstimate(key)} ticks (your marked down end, if any). If it jumps, that value `
          + "was not where it rests. Keep a hand near."),
        button("Power here", () => {
          armOn({ticks: {[key]: restEstimate(key)}});
          pr.phase = "adjust";
          store();
        }, "primary", !C.connected()),
      ],
      adjust: [
        p("3. Hold the buttons to bring it back to exactly where it rested: touching its support, not lifted, not pressing down."),
        p("Now: ", live(() => ticks(key))),
        row(holdButton(`◀ ${(joint(key) || {labels: ["", ""]}).labels[0]}`, () => startJog(key, -1), stopJog),
          holdButton(`${(joint(key) || {labels: ["", ""]}).labels[1]} ▶`, () => startJog(key, 1), stopJog)),
        button("Mark rest here", () => { record.rest = joint(key).ticks; pr.phase = "verify"; store(); }, "primary", !joint(key)),
      ],
      verify: [
        p(`4. Check: release, wait 2 seconds, then power again at the rest value ${record.rest}.`),
        button(busy ? "Running…" : "Release and re-power", () => scripted(async () => {
          cmd.once.release = true;
          cmd.arm = {enabled: false};
          await sleep(2000);
          armOn({ticks: {[key]: record.rest}});
        }), "primary", busy || !C.connected()),
        choice("Did it stay still when powered?", [["still", "Stayed still (a tiny twitch is fine)"], ["jumped", "Jumped noticeably"]],
          record.restCheck, value => {
            record.restCheck = value;
            if (value === "jumped") pr.phase = "adjust";
            store();
          }),
        button("Next joint", () => { pr.index = index + 1; pr.phase = "release"; store(); }, "primary", record.restCheck !== "still"),
      ],
    };
    return [connection(), p(h("b", {}, `${index + 1} of 2: ${L.NAMES[key]}`)), steps[phase],
      muted("You can go back to step 1 at any time: ", button("Restart this joint", () => { pr.phase = "release"; store(); }))];
  }

  function renderArmStop() {
    const lift = () => scripted(async () => {
      const current = joint("lower");
      if (!current) throw new Error("Connect first");
      await moveTo("lower", Math.min(current.maximum, current.ticks + 20));
    });
    return [
      connection(),
      p("STOP is designed to freeze the arm: it keeps holding for 10 seconds, so a block is not dropped, then releases."),
      p("1. Lift the lower arm a little."),
      button(busy ? "Moving…" : "Lift the lower arm", lift, "primary", busy || !C.connected()),
      p("2. Now press the red STOP at the top (or Esc, or ○). Support the arm and watch for about 15 seconds."),
      p(live(() => {
        const arm = (status().controller || {}).arm;
        if (C.connected()) return "Connected";
        if (!arm) return "";
        if (arm.release_in !== null && arm.release_in !== undefined) return `Holding — releases in ${Math.ceil(arm.release_in)} s`;
        return Object.values(arm.joints).some(item => item.active) ? "Holding" : "Released";
      }, "live")),
      choice("3. What did the arm do after STOP?", [["held", "Held still, then went limp after about 10 s"],
        ["dropped", "Went limp at once"], ["kept", "Still holding after 15 s"], ["moved", "Something moved"]],
        results.armStop, value => { results.armStop = value; store(); }),
      button("Done", () => finish("armstop", results.armStop === "held" ? "done" : "issue"), "primary", !results.armStop),
    ];
  }

  function renderTrackDirections() {
    const t = results.tracks;
    const side = (name, tracks) => [
      button(busy ? "Running…" : `Run the ${name} track forward for 1 s`, () => scripted(() => runTracks(tracks, 0.5, 1000)),
        "primary", busy || !C.connected()),
      choice(`What did the ${name} track do?`, [["forward", "Turned forward (would push the robot forward)"],
        ["backward", "Turned backward"], ["other", "The other track moved"], ["nothing", "Nothing moved"]],
        t[name], value => { t[name] = value; store(); }),
    ];
    const wrong = ["left", "right"].some(name => t[name] && t[name] !== "forward");
    return [
      connection(),
      p("Tracks off the ground. Each button runs one track at 50% duty for 1 second."),
      side("left", [1, 0]), side("right", [0, 1]),
      wrong ? box("bad", "Please do not change wiring or code to fix this: the track mapping was accepted after two "
        + "corrections and is protected. Finish the report and send it, so the cause can be checked first.") : null,
      button("Done", () => finish("trackdir", wrong ? "issue" : "done"), "primary", !t.left || !t.right),
    ];
  }

  // Records the duty at "It turns now", false when 100% passed without movement,
  // and nothing when stopped or disconnected.
  async function runRamp(name, tracks, field) {
    ramp = {name, step: 0, duty: L.rampDuty(0), running: true, found: false, aborted: false};
    render();
    while (ramp.running && ramp.step <= 18 && C.connected()) {
      ramp.duty = L.rampDuty(ramp.step);
      cmd.drive = {motion: "analog", tracks, raw: true, speed: ramp.duty, deadman: true};
      for (const update of updaters) update();
      await sleep(800);
      ramp.step += 1;
    }
    stopDrive();
    if (!ramp.aborted && C.connected()) {
      const t = results.tracks;
      if (field === "floor") t.floorDuty = ramp.found;
      else {
        t.raisedDuty ||= [null, null];
        t.raisedDuty[name === "left" ? 0 : 1] = ramp.found;
      }
    }
    ramp = null;
    store();
  }

  function renderMinDuty() {
    const t = results.tracks;
    const turns = () => { if (ramp) { ramp.found = ramp.duty; ramp.running = false; } };
    const abort = () => { if (ramp) { ramp.aborted = true; ramp.running = false; } };
    const start = (name, tracks, field) => button(`Start ${name} ramp`, () => runRamp(name, tracks, field),
      "primary", Boolean(ramp) || !C.connected());
    const show = value => Number.isFinite(value) ? `${Math.round(value * 100)}%` : value === false ? "did not turn" : "—";
    return [
      connection(),
      p("Find the smallest power that turns each track. Small stick movements then start at that power instead of "
        + "buzzing without moving. The duty rises by 5% every 0.8 s from 10%."),
      p(h("b", {}, "Raised (tracks off the ground):")),
      row(start("left", [1, 0], "raised"), start("right", [0, 1], "raised")),
      ramp ? box("good", "Ramping ", ramp.name, ": ", live(() => ramp ? `${Math.round(ramp.duty * 100)}%` : ""),
        " ", button("It turns now!", turns, "primary"), " ", button("Stop", abort, "danger")) : null,
      p(`Left: ${show((t.raisedDuty || [])[0])} · right: ${show((t.raisedDuty || [])[1])}`),
      p(h("b", {}, "Optional, on the floor with 1 m free in front:"), " both tracks ramp; press when the robot starts moving."),
      start("floor", [1, 1], "floor"),
      p(`Floor: ${show(t.floorDuty)}`),
      button("Done", () => finish("minduty"), "primary", !(t.raisedDuty || []).some(Number.isFinite) && !Number.isFinite(t.floorDuty)),
    ];
  }

  function renderStraight() {
    const t = results.tracks;
    const trim = t.trim || [1, 1];
    return [
      connection(),
      p("On the floor with 1.5 m free in front. The robot drives forward for 2 seconds at 60% with the current trim."),
      p(h("b", {}, `Current trim: left ${trim[0]} · right ${trim[1]}`), " (1 = full power for that track)"),
      button(busy ? "Driving…" : "Drive straight for 2 s", () => scripted(() => runTracks(trim, 0.6, 2000)),
        "primary", busy || !C.connected()),
      choice("How did it drive?", [["straight", "Straight"], ["left", "Curved to the left"], ["right", "Curved to the right"]],
        t.straight, value => {
          t.trimTries = (t.trimTries || 0) + 1;
          t.straight = value;
          if (value !== "straight") t.trim = L.trimAfter(trim, value);
          else t.trim = trim;
          store();
        }),
      t.straight && t.straight !== "straight" ? muted("Trim adjusted. Put the robot back and drive again.") : null,
      button("Done", () => finish("straight", t.straight === "straight" ? "done" : "issue"), "primary", !t.straight),
    ];
  }

  function renderLinkLoss() {
    const t = results.tracks;
    const run = () => scripted(async () => {
      const before = JSON.stringify((status().controller || {}).last_expiry);
      cmd.drive = {motion: "analog", tracks: [1, 1], raw: true, speed: 0.4, deadman: true};
      await sleep(1000);
      C.simulateLinkLoss();
      stopDrive();
      const end = Date.now() + 7000;
      while (Date.now() < end) {
        const fresh = await C.request("/api/status", {}).catch(() => null);
        const expiry = fresh && fresh.controller && fresh.controller.last_expiry;
        if (expiry && JSON.stringify(expiry) !== before) {
          t.linkLoss = {...(t.linkLoss || {}), after: expiry.after, moving: expiry.moving};
          break;
        }
        await sleep(400);
      }
    });
    return [
      connection(),
      p("Tracks off the ground. Both tracks run at 40%. After 1 second this page stops talking to the robot, exactly "
        + "as if Wi-Fi dropped. The Pi's watchdog must then stop the motors by itself, about 2 seconds later. "
        + "Keep a hand near the power switch."),
      button(busy ? "Running…" : "Start lost-link test", run, "danger", busy || !C.connected()),
      t.linkLoss && t.linkLoss.after ? box("good", `The Pi stopped the motors ${t.linkLoss.after} s after the last command.`) : null,
      choice("What did you see?", [["stopped", "They stopped by themselves about 2 s later"],
        ["kept", "They kept running (I switched off)"], ["immediate", "They stopped at once"]],
        t.linkLoss && t.linkLoss.answer, value => { t.linkLoss = {...(t.linkLoss || {}), answer: value}; store(); }),
      button("Done", () => finish("linkloss", t.linkLoss && t.linkLoss.answer === "stopped" ? "done" : "issue"),
        "primary", !(t.linkLoss && t.linkLoss.answer)),
    ];
  }

  function renderStopping() {
    const t = results.tracks;
    const pr = prog("stopping");
    pr.speed ||= 0.5;
    const input = h("input", {type: "number", min: "0", max: "500", step: "1", placeholder: "cm"});
    return [
      connection(),
      p("Optional, on the floor. Put a tape mark 1 m in front of the robot. Hold the button to drive forward and let "
        + "go when the front passes the mark. Then measure how far past the mark the front stopped."),
      choice("Speed:", [[0.5, "50%"], [0.75, "75%"], [1, "100%"]], pr.speed, value => { pr.speed = value; store(); }),
      holdButton("Hold to drive forward", () => { cmd.drive = {motion: "forward", deadman: true, speed: pr.speed}; },
        stopDrive, !C.connected()),
      row("Distance past the mark: ", input, button("Add result", () => {
        const cm = Number(input.value);
        if (!Number.isFinite(cm) || input.value === "") return;
        (t.stopping ||= []).push({speed: Math.round(pr.speed * 100), cm});
        store();
      })),
      (t.stopping || []).length ? p((t.stopping || []).map(item => `${item.speed}%: ${item.cm} cm`).join(" · ")) : null,
      row(button("Done", () => finish("stopping"), "primary", !(t.stopping || []).length),
        button("Skip", () => finish("stopping", "skipped"))),
    ];
  }

  function renderSaveTracks() {
    const tracks = L.trackCalibration(results);
    const canSave = status().can_save && status().can_save.tracks;
    return [
      p("Values to save. The minimum power makes small stick movements start moving; the trim balances the tracks. "
        + "Track directions are never changed by calibration."),
      h("pre", {}, JSON.stringify(tracks, null, 2)),
      !canSave ? box("warn", "Practice mode: nothing is saved.") : null,
      row(button("Save track calibration", async () => {
        if (await saveCalibration({tracks})) finish("savetracks");
      }, "primary", !canSave || !Object.keys(tracks).length || !C.connected()),
      button("Continue without saving", () => finish("savetracks", "skipped"))),
    ];
  }

  function renderLive() {
    const note = h("textarea", {value: results.liveNote || "", placeholder: "Notes about anything odd",
      on: {input: event => { results.liveNote = event.target.value; save(); }}});
    return [
      connection(),
      box("good", "Normal controls are active in this step (controller and keyboard), exactly as on the Drive tab. "
        + "Keep the tracks raised at first. Press △ to switch to ARM mode."),
      LIVE_CHECKS.map(([key, text]) => choice(text, [["works", "Works"], ["problem", "Problem"]],
        (results.live[text] || {}).answer, value => { results.live[text] = {answer: value}; store(); })),
      note,
      button("Done", () => {
        const answers = LIVE_CHECKS.map(([, text]) => (results.live[text] || {}).answer);
        if (results.liveNote) results.notes = `${results.notes || ""}\nController check: ${results.liveNote}`.trim();
        finish("live", answers.every(answer => answer === "works") ? "done" : "issue");
      }, "primary"),
    ];
  }

  function renderVideo() {
    const v = results.video;
    const camera = status().camera;
    const clock = h("div", {class: "clock"}, "0");
    tickers.add(() => { clock.textContent = String(Date.now() % 100000).padStart(5, "0"); });
    const screen = h("input", {type: "number", placeholder: "screen"});
    const video = h("input", {type: "number", placeholder: "video"});
    const measure = () => scripted(async () => {
      const samples = [];
      measuring = true;
      applyOverride();
      try {
        for (let i = 0; i < 10; i++) {
          await sleep(2000);
          const s = await C.request("/api/status", {}).catch(() => null);
          if (s) samples.push(s);
        }
      } finally {
        measuring = false;
        applyOverride();
      }
      const values = (read) => samples.map(read).filter(Number.isFinite);
      const fps = values(s => s.camera && s.camera.fps);
      const cpu = values(s => s.health && s.health.cpu_percent);
      const temperature = values(s => s.health && s.health.temperature);
      v.perf = {...(v.perf || {}), preset: camera && camera.preset, fps: fps.length ? Math.min(...fps) : null,
        cpu: cpu.length ? Math.max(...cpu) : null, temperature: temperature.length ? Math.max(...temperature) : null};
    });
    return [
      p(h("b", {}, "1. Detect the camera."), " Lists what the Pi's camera software sees (sensor model)."),
      button(busy ? "Detecting…" : "Detect camera", () => scripted(async () => {
        v.probe = (await C.request("/api/camera", {probe: true})).probe;
      }), "secondary", busy || !camera),
      v.probe ? h("pre", {}, v.probe) : null,
      p(h("b", {}, "2. Look at the picture.")),
      row(button(preview ? "Stop preview" : "Start preview", () => { preview = !preview; render(); }, "secondary", !camera),
        camera ? h("span", {class: "muted"}, live(() => {
          const c = status().camera || {};
          return c.running ? `${c.fps} fps · ${c.width}×${c.height}${c.simulated ? " · test card" : ""}` : c.error || "Off";
        }, "muted")) : null),
      preview ? h("div", {class: "video-frame"}, h("img", {src: C.videoUrl(), alt: "Camera preview"})) : null,
      choice("Is the picture the right way up?", [["upright", "Yes"], ["upside", "Upside down"]], v.upright, async value => {
        v.upright = value;
        save();
        if (value === "upside" && status().can_save && status().can_save.camera) {
          const rotation = (camera && camera.rotation) === 180 ? 0 : 180;
          if (await saveCalibration({camera: {rotation}})) v.upright = undefined;
        }
        render();
      }),
      p(h("b", {}, "3. Delay (latency)."), " Point the camera at this clock so the screen shows the clock and the video "
        + "of the clock. Take a phone photo of the screen and type both numbers. The difference is the delay in ms."),
      clock,
      row(screen, video, button("Calculate", () => {
        const value = L.latency(screen.value, video.value);
        v.latency = value;
        flash = value === null ? {kind: "bad", text: "Check the two numbers: screen must be larger than video."} : null;
        store();
      })),
      v.latency ? p(`Delay: ${v.latency} ms`) : null,
      p(h("b", {}, "4. Video while driving."), " Start the preview, then press Measure and drive with the controller "
        + "(tracks raised) for 20 seconds. Frame rate, CPU and temperature are recorded."),
      button(busy ? "Measuring… drive now" : "Measure for 20 s", measure, "primary", busy || !camera),
      v.perf ? p(`Lowest ${v.perf.fps ?? "—"} fps · highest CPU ${v.perf.cpu ?? "—"}% · ${v.perf.temperature ?? "—"} °C`) : null,
      v.perf ? choice("Did the controls stay responsive while video ran?", [["responsive", "Yes"],
        ["laggy", "Noticeably slower"], ["unusable", "Unusable"]], v.perf.answer, value => { v.perf.answer = value; store(); }) : null,
      button("Done", () => finish("video", v.upright === "upright" && (!v.perf || v.perf.answer === "responsive") ? "done" : "issue"),
        "primary", !v.upright),
    ];
  }

  function sectionRows() {
    return SECTIONS.filter(section => section.id !== "report").map(section => ({
      title: section.title,
      result: results.done[section.id] || "not run",
      mode: results.done[section.id] ? (results.practice[section.id] ? "practice (simulation)" : "real") : "",
    }));
  }

  function renderReport() {
    const notes = h("textarea", {value: results.notes || "", placeholder: "Anything else you noticed",
      on: {input: event => { results.notes = event.target.value; save(); }}});
    const text = () => L.report(results, status(), sectionRows());
    return [
      h("table", {}, h("tr", {}, ["Step", "Result", "Mode"].map(item => h("th", {}, item))),
        sectionRows().map(item => h("tr", {}, [item.title, item.result, item.mode].map(value => h("td", {}, value))))),
      p("Notes for the report:"), notes,
      row(button("Download report (.md)", () => {
        const url = URL.createObjectURL(new Blob([text()], {type: "text/markdown"}));
        const link = h("a", {href: url, download: `robotino-report-${new Date().toISOString().slice(0, 10)}.md`});
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 2000);
      }, "primary"),
      button("Save a copy on the Pi", async () => {
        try {
          const result = await C.post("/api/report", {text: text()});
          flash = {kind: "good", text: result.saved ? `Saved on the Pi: ${result.saved}` : "Simulation: not kept on the Pi (download it instead)."};
        } catch (error) {
          flash = {kind: "bad", text: error.message};
        }
        render();
      }, "secondary", !C.connected()),
      button("Clear all answers", () => {
        if (window.confirm("Clear every answer in this browser? Calibration already saved on the Pi stays.")) {
          results = fresh();
          store();
        }
      }, "danger")),
      muted("Send the downloaded report (it lands in your Downloads folder) so the results can be added to the repository."),
    ];
  }

  // ---- Rendering ----------------------------------------------------------------------------

  function chip(id) {
    const result = results.done[id];
    if (!result) return null;
    const kind = result === "issue" ? "issue" : results.practice[id] ? "practice" : "done";
    const text = result === "issue" ? "issue" : result === "skipped" ? "skipped" : results.practice[id] ? "practice" : "✓";
    return h("span", {class: `chip ${kind}`}, text);
  }

  function render() {
    if (!visible) return;
    updaters.clear();
    tickers.clear();
    const current = SECTIONS.find(section => section.id === results.section) || SECTIONS[0];
    const nowLive = current.id === "live";
    if (nowLive !== liveControl) {
      liveControl = nowLive;
      if (!nowLive) resetCommands();
      applyOverride();
    }
    if (current.id !== "video") preview = false;
    const nav = h("ul", {class: "steps"}, SECTIONS.map((section, index) => h("li", {}, h("button", {
      class: section === current ? "current" : "",
      on: {click: () => { if (!busy) { stopJog(); blocked = null; results.section = section.id; flash = null; store(); } }},
    }, chip(section.id), `${index + 1}. ${section.title}`))));
    const card = h("section", {class: "panel card"}, h("h2", {}, current.title), requirement(current),
      flash ? box(flash.kind, flash.text) : null, current.render());
    root.replaceChildren(h("div", {class: "setup"}, h("nav", {}, nav), card));
  }

  C.onReply(() => {
    guardLimitsSafely();
    for (const update of updaters) update();
  });
  C.onStatus(() => {
    for (const update of updaters) update();
  });

  // Pause once at the archived limit; the user decides whether to go further.
  function guardLimitsSafely() {
    if (!jogging) return;
    const current = joint(jogging.key);
    if (!current) return;
    const record = results.joints[jogging.key] ||= {};
    const side = jogging.direction < 0 ? "negative" : "positive";
    if ((record.allowBeyond || {})[side]) return;
    const [low, high] = [current.default_minimum, current.default_maximum];
    // Already past the archived limit when the hold began: the user chose that earlier.
    if (jogging.startedOutside === undefined) {
      jogging.startedOutside = side === "negative" ? current.ticks < low : current.ticks > high;
    }
    const atLimit = side === "negative" ? current.ticks <= low : current.ticks >= high;
    if (atLimit && !jogging.startedOutside) {
      const key = jogging.key;
      stopJog();
      blocked = {key, side};
      render();
    }
  }

  // Leaving the window must never leave a hold button "pressed".
  window.addEventListener("blur", () => {
    stopJog();
    stopDrive();
  });

  setInterval(() => {
    const connected = C.connected();
    if (connected !== wasConnected) {
      wasConnected = connected;
      if (!connected) resetCommands();
      if (!jogging) render();
    }
    for (const ticker of tickers) ticker();
  }, 60);

  globalThis.RobotinoSetup = {
    show() { visible = true; applyOverride(); render(); },
    hide() {
      visible = false;
      liveControl = false;
      resetCommands();
      applyOverride();
    },
  };
})();
