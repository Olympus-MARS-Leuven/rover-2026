"use strict";
// Arm panel, "Edit joint limits": view and change each joint's travel limits
// at any time. Saved on the Pi like the Setup & tests calibration.
(function () {
  const C = globalThis.RobotinoControl;
  const L = globalThis.RobotinoSetupLogic;
  const root = document.getElementById("limits-root");
  const inputs = {};
  const live = {};
  let message = null;
  let built = false;

  const arm = () => (C.connected() && C.lastReply() && C.lastReply().arm) || ((C.lastStatus() || {}).controller || {}).arm;
  const joint = key => ((arm() || {}).joints || {})[key];

  function h(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (key === "on") for (const [type, fn] of Object.entries(value)) node.addEventListener(type, fn);
      else if (key === "class") node.className = value;
      else if (value !== undefined && value !== null && value !== false) node[key] = value;
    }
    for (const child of children.flat()) {
      if (child !== null && child !== undefined && child !== false) node.append(child instanceof Node ? child : String(child));
    }
    return node;
  }

  function canSave() {
    const status = C.lastStatus() || {};
    if (!status.can_save || !status.can_save.joints) return "Limits can only be saved with real servos (start with --servos).";
    if (!C.connected()) return "Connect first.";
    return null;
  }

  async function save(key, minimum, maximum) {
    const current = joint(key);
    if (!current) return;
    const check = L.checkLimits(minimum, maximum, [current.default_minimum, current.default_maximum]);
    if (!check.ok) {
      message = {kind: "bad", text: `${L.NAMES[key]}: ${check.error}.`};
    } else if (!check.warning || window.confirm(`${L.NAMES[key]}: ${check.warning}. Save anyway?`)) {
      try {
        await C.post("/api/calibration", {joints: {[key]: {minimum: check.minimum, maximum: check.maximum}}});
        message = {kind: "good", text: `Saved: ${L.NAMES[key]} ${check.minimum}–${check.maximum} ticks. Used now and after restarts.`};
      } catch (error) {
        message = {kind: "bad", text: `Not saved: ${error.message}`};
      }
    }
    render();
  }

  function row(key) {
    const current = joint(key);
    const minimum = h("input", {type: "number", min: "100", max: "520", step: "1", value: String(current.minimum)});
    const maximum = h("input", {type: "number", min: "100", max: "520", step: "1", value: String(current.maximum)});
    inputs[key] = {minimum, maximum};
    live[key] = {now: h("span", {}), limits: h("span", {})};
    const useCurrent = input => h("button", {class: "secondary small", title: "Copy the joint's present position",
      on: {click: () => { const value = joint(key); if (value) input.value = String(value.ticks); }}}, "Use current");
    const blocked = canSave();
    return h("tr", {},
      h("td", {}, h("b", {}, L.NAMES[key]), h("br"), h("span", {class: "muted"}, "now: "), live[key].now),
      h("td", {}, live[key].limits, h("br"),
        h("span", {class: "muted"}, `archived ${current.default_minimum}–${current.default_maximum}`)),
      h("td", {}, minimum, " ", useCurrent(minimum)),
      h("td", {}, maximum, " ", useCurrent(maximum)),
      h("td", {},
        h("button", {class: "primary small", disabled: Boolean(blocked), on: {click: () => save(key, minimum.value, maximum.value)}}, "Save"),
        " ",
        h("button", {class: "secondary small", disabled: Boolean(blocked), title: "Back to the original software's values",
          on: {click: () => save(key, current.default_minimum, current.default_maximum)}}, "Archived")));
  }

  function update() {
    for (const [key, spans] of Object.entries(live)) {
      const current = joint(key);
      if (!current) continue;
      spans.now.textContent = `${current.ticks}${current.active ? "" : " (off)"}`;
      spans.limits.textContent = `${current.minimum}–${current.maximum}`;
    }
  }

  function render() {
    if (!arm()) return;
    built = true;
    const blocked = canSave();
    root.replaceChildren(...[
      h("p", {class: "muted"}, "Limits are in PWM ticks (absolute range 100–520). Move a joint to a safe end with a slider, "
        + "keys or the controller, press Use current, then Save. Change limits a few ticks at a time and test slowly."),
      blocked ? h("div", {class: "warn"}, blocked) : null,
      message ? h("div", {class: message.kind}, message.text) : null,
      h("table", {class: "limits-table"},
        h("tr", {}, ["Joint", "Limits now", "Minimum", "Maximum", ""].map(text => h("th", {}, text))),
        L.JOINTS.filter(joint).map(row)),
    ].filter(Boolean));
    update();
  }

  let lastBlocked = null;
  function refresh() {
    // Rebuild only when saving becomes possible or impossible; otherwise keep typed values.
    const blocked = canSave();
    if (!built || blocked !== lastBlocked) {
      lastBlocked = blocked;
      render();
    } else {
      update();
    }
  }

  C.onStatus(refresh);
  C.onReply(update);
})();
