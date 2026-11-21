#!/usr/bin/env python3
"""Turn the Onshape export of the Olympus rover into a URDF that Gazebo can load and drive.

What it does (all printed at the end):
  1. deletes the empty 'loop_closure' placeholder links/joints
  2. renames links that share a name with a joint (Gazebo does not allow that)
  3. locks every joint except the 4 wheel joints  -> the rover is one rigid body on 4 driven wheels
  4. adds a cylinder collision shape to each wheel (size read from Tyre.stl)
  5. sets realistic masses (the CAD has almost none)
  6. adds a new root frame so the rover drives forward along +x (what Gazebo's drive plugin expects)
  7. adds Gazebo's DiffDrive plugin (left/right wheels, wheel radius, track width)

Usage:
  python3 make_rover_sim_urdf.py
  python3 make_rover_sim_urdf.py --src PATH.urdf --meshes DIR --out OUT.urdf --mass 8.0
"""
import argparse
import collections
import copy
import json
import math
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

HOME = os.path.expanduser("~")
DEFAULT_SRC = os.path.join(HOME, "olympus_ws/cad_exports/Full Rover Assembly/full_rover_assembly/urdf/full_rover_assembly.urdf")
DEFAULT_MESHES = os.path.join(HOME, "olympus_ws/sim_models/rover_sim/meshes")
DEFAULT_OUT = os.path.join(HOME, "olympus_ws/sim_models/rover_sim/urdf/rover_sim.urdf")
PKG = "rover_sim"


# ---------- small 3x3 maths (no numpy needed) ----------
def rpy_to_R(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mv(A, v):
    return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]


def tr(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


def floats(s, default):
    return [float(x) for x in s.split()] if s else list(default)


def origin_T(el):
    o = el.find("origin")
    if o is None:
        return rpy_to_R(0, 0, 0), [0.0, 0.0, 0.0]
    return rpy_to_R(*floats(o.get("rpy"), [0, 0, 0])), floats(o.get("xyz"), [0, 0, 0])


def fmt(v):
    return " ".join(repr(round(x, 9)) if abs(x) > 1e-12 else "0" for x in v)


# ---------- STL bounding box (binary or ASCII) ----------
def stl_bbox(path):
    with open(path, "rb") as f:
        data = f.read()
    mn, mx = [1e30] * 3, [-1e30] * 3

    def add(x, y, z):
        for i, v in enumerate((x, y, z)):
            mn[i] = min(mn[i], v)
            mx[i] = max(mx[i], v)

    if len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        if 84 + 50 * n == len(data):
            for rec in struct.iter_unpack("<12fH", data[84:]):
                for k in (3, 6, 9):
                    add(rec[k], rec[k + 1], rec[k + 2])
            return mn, mx
    for line in data.decode("utf-8", "ignore").splitlines():
        p = line.split()
        if len(p) == 4 and p[0] == "vertex":
            add(float(p[1]), float(p[2]), float(p[3]))
    if mn[0] > mx[0]:
        sys.exit(f"ERROR: could not read any vertices from {path}")
    return mn, mx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--meshes", default=DEFAULT_MESHES)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--mass", type=float, default=8.0, help="total rover mass in kg (PLACEHOLDER, set the real one)")
    ap.add_argument("--wheel-mass", type=float, default=0.3, help="mass of one wheel in kg (placeholder)")
    ap.add_argument("--mu", type=float, default=1.0, help="tyre friction (placeholder)")
    ap.add_argument("--flip", choices=["none", "left", "right", "all"], default="none",
                    help="reverse the spin direction of these wheels (use only if the rover drives the wrong way in Gazebo)")
    ap.add_argument("--drive", choices=["diff", "kinematic"], default="kinematic",
                    help="kinematic = Gazebo moves the whole rover directly (turns on the spot, no wheel friction needed); "
                         "diff = real wheel-ground friction (4-wheel rovers often will not turn)")
    ap.add_argument("--steer", action="store_true",
                    help="also unlock the 4 steering joints (one vertical-axis joint above each wheel) so the wheels can steer; "
                         "writes rover_steer.json next to the URDF")
    a = ap.parse_args()

    tree = ET.parse(a.src)
    robot = tree.getroot()
    jname = lambda j: j.get("name")
    par = lambda j: j.find("parent").get("link")
    chd = lambda j: j.find("child").get("link")

    # ---- 1. delete loop-closure placeholders ----
    bad_links = {l.get("name") for l in robot.findall("link") if "loop_closure" in l.get("name")}
    dropped_j = 0
    for j in list(robot.findall("joint")):
        if "loop_closure" in jname(j) or par(j) in bad_links or chd(j) in bad_links:
            robot.remove(j)
            dropped_j += 1
    for l in list(robot.findall("link")):
        if l.get("name") in bad_links:
            robot.remove(l)
    print(f"[1] removed {len(bad_links)} loop-closure links and {dropped_j} joints")

    # ---- 2. rename links that clash with joint names ----
    joint_names = {jname(j) for j in robot.findall("joint")}
    renamed = {}
    for l in robot.findall("link"):
        if l.get("name") in joint_names:
            renamed[l.get("name")] = l.get("name") + "_lnk"
            l.set("name", renamed[l.get("name")])
    for j in robot.findall("joint"):
        if par(j) in renamed:
            j.find("parent").set("link", renamed[par(j)])
        if chd(j) in renamed:
            j.find("child").set("link", renamed[chd(j)])
    print(f"[2] renamed {len(renamed)} links that clashed with joint names: {sorted(renamed.values())}")

    links = {l.get("name"): l for l in robot.findall("link")}
    joints = robot.findall("joint")
    kids = collections.defaultdict(list)
    for j in joints:
        kids[par(j)].append(j)
    child_set = {chd(j) for j in joints}
    roots = [n for n in links if n not in child_set]
    if len(roots) != 1:
        sys.exit(f"ERROR: expected one root link, found {roots}")
    old_root = roots[0]

    def subtree(name):
        out, st = [name], [name]
        while st:
            for jj in kids[st.pop()]:
                out.append(chd(jj))
                st.append(chd(jj))
        return out

    def fk():
        pose = {old_root: (rpy_to_R(0, 0, 0), [0.0, 0.0, 0.0])}
        st = [old_root]
        while st:
            p = st.pop()
            Rp, tp = pose[p]
            for jj in kids[p]:
                Rj, tj = origin_T(jj)
                pose[chd(jj)] = (mm(Rp, Rj), [tp[i] + mv(Rp, tj)[i] for i in range(3)])
                st.append(chd(jj))
        return pose

    def mesh_names(link):
        return [os.path.basename(m.get("filename")) for m in link.findall(".//mesh")]

    # ---- find the 4 wheel joints: deepest moving joints that carry a Tyre.stl ----
    moving = [j for j in joints if j.get("type") != "fixed"]
    wheel_joints = []
    for j in moving:
        sub = subtree(chd(j))
        has_tyre = any("Tyre.stl" in mesh_names(links[n]) for n in sub)
        has_moving_below = any(jj.get("type") != "fixed" for n in sub for jj in kids[n])
        if has_tyre and not has_moving_below:
            wheel_joints.append(j)
    if len(wheel_joints) != 4:
        sys.exit(f"ERROR: expected 4 wheel joints, found {[jname(j) for j in wheel_joints]}")
    wheel_info = {}
    for j in wheel_joints:
        tyre = [n for n in subtree(chd(j)) if "Tyre.stl" in mesh_names(links[n])]
        if len(tyre) != 1:
            sys.exit(f"ERROR: wheel {jname(j)} has {len(tyre)} tyre links")
        wheel_info[jname(j)] = {"joint": j, "link": chd(j), "tyre": tyre[0]}

    # ---- wheel size from Tyre.stl ----
    tyre_stl = os.path.join(a.meshes, "Tyre.stl")
    if not os.path.isfile(tyre_stl):
        sys.exit(f"ERROR: {tyre_stl} not found (use --meshes)")
    mn, mx = stl_bbox(tyre_stl)
    ext = [mx[i] - mn[i] for i in range(3)]
    ctr_mesh = [(mx[i] + mn[i]) / 2 for i in range(3)]
    ax_i = ext.index(min(ext))
    other = [ext[i] for i in range(3) if i != ax_i]
    radius, width = max(other) / 2.0, ext[ax_i]
    print(f"[4] Tyre.stl size (m): x={ext[0]:.4f} y={ext[1]:.4f} z={ext[2]:.4f}  -> radius {radius:.4f}, width {width:.4f}")
    if abs(other[0] - other[1]) > 0.1 * max(other):
        print("    WARNING: tyre is not round (the two diameters differ by more than 10%)")

    # ---- forward direction and wheel levelling ----
    pose = fk()
    centers = {}
    for n, w in wheel_info.items():
        Rw, tw = pose[w["link"]]
        Rt, tt = pose[w["tyre"]]
        vis = links[w["tyre"]].find("visual")
        Rv, tv = origin_T(vis)
        c_link = [tv[i] + mv(Rv, ctr_mesh)[i] for i in range(3)]          # mesh centre in tyre-link frame
        c_world = [tt[i] + mv(Rt, c_link)[i] for i in range(3)]
        Rrel = mm(tr(Rw), mm(Rt, Rv))                                      # mesh frame -> wheel-link frame
        axis_mesh = [1.0 if i == ax_i else 0.0 for i in range(3)]
        axis_w = mv(Rrel, axis_mesh)
        if abs(axis_w[2]) < 0.99:
            sys.exit(f"ERROR: tyre axis of {n} is not the wheel joint axis (axis in wheel frame = {axis_w})")
        c_wheel = mv(tr(Rw), [c_world[i] - tw[i] for i in range(3)])      # tyre centre in wheel-link frame
        wheel_info[n].update(c_world=c_world, c_wheel=c_wheel, Rw=Rw)
        ax_loc = floats(w["joint"].find("axis").get("xyz"), [0, 0, 1])
        ax_world = mv(Rw, ax_loc)
        wheel_info[n]["ax_world"] = ax_world
        centers[n] = c_world

    lat_i = max(range(2), key=lambda i: sum(abs(w["ax_world"][i]) for w in wheel_info.values()))
    fwd_i = 1 - lat_i
    yaw = -math.pi / 2 if lat_i == 0 else 0.0            # old +y (or +x) becomes the new +x
    R_NO = rpy_to_R(0, 0, yaw)
    print(f"[6] wheels spin about the CAD {'xy'[lat_i]}-axis, so the rover drives along CAD +{'xy'[fwd_i]}; "
          f"new root rotated by {math.degrees(yaw):.0f} deg about z")

    # level each axle: both wheels of one axle get the same centre height
    order = sorted(wheel_info, key=lambda n: centers[n][fwd_i])
    for grp in (order[:2], order[2:]):
        zmean = sum(centers[n][2] for n in grp) / 2.0
        for n in grp:
            dz = zmean - centers[n][2]
            j = wheel_info[n]["joint"]
            Rp = pose[par(j)][0]
            off = [Rp[2][0] * dz, Rp[2][1] * dz, Rp[2][2] * dz]       # world-z shift expressed in parent frame
            o = j.find("origin")
            xyz = floats(o.get("xyz"), [0, 0, 0])
            o.set("xyz", fmt([xyz[i] + off[i] for i in range(3)]))
    pose = fk()

    # recompute centres in the new root frame, left/right, track
    N = {}
    for n, w in wheel_info.items():
        Rw, tw = pose[w["link"]]
        c_world = [tw[i] + mv(Rw, w["c_wheel"])[i] for i in range(3)]
        N[n] = mv(R_NO, c_world)
    ymean = sum(p[1] for p in N.values()) / 4.0
    left = sorted(n for n in N if N[n][1] > ymean)
    right = sorted(n for n in N if N[n][1] <= ymean)
    if len(left) != 2 or len(right) != 2:
        sys.exit("ERROR: could not split wheels into 2 left + 2 right")
    separation = sum(N[n][1] for n in left) / 2 - sum(N[n][1] for n in right) / 2
    cx = sum(p[0] for p in N.values()) / 4.0      # middle of the 4 wheels (new frame)
    cy = sum(p[1] for p in N.values()) / 4.0
    print(f"    wheel-centre offset from CAD origin: x={cx:.4f} y={cy:.4f} m -> base_footprint is moved there so turns pivot on the rover's middle")
    by_x = sorted(N, key=lambda n: N[n][0])
    rear, front = by_x[:2], by_x[2:]
    wheelbase = sum(N[n][0] for n in front) / 2 - sum(N[n][0] for n in rear) / 2
    dz_axles = sum(N[n][2] for n in front) / 2 - sum(N[n][2] for n in rear) / 2
    pitch = math.degrees(math.atan2(dz_axles, wheelbase))
    print(f"[7] left wheels {left}, right wheels {right}")
    print(f"    track width (tyre centre to tyre centre) {separation:.4f} m, wheelbase {wheelbase:.4f} m")
    print(f"    at rest the rigid rover is pitched about {abs(pitch):.1f} deg because the CAD pose has the two axles at different heights")

    # ---- steering joints: closest vertical-axis moving ancestor of each wheel joint ----
    jmap = {jname(j): j for j in joints}
    steer = {}
    if a.steer:
        parent_joint = {chd(j): j for j in joints}
        for n, w in wheel_info.items():
            cur = par(w["joint"])
            while cur in parent_joint:
                pj = parent_joint[cur]
                axe = pj.find("axis")
                if pj.get("type") in ("continuous", "revolute") and axe is not None and not jname(pj).startswith("ball"):
                    axw = mv(R_NO, mv(pose[chd(pj)][0], floats(axe.get("xyz"), [0, 0, 1])))
                    if abs(axw[2]) > 0.99:
                        steer[n] = (jname(pj), 1.0 if axw[2] > 0 else -1.0, chd(pj))
                        break
                cur = par(pj)
        if len(steer) != 4:
            sys.exit(f"ERROR: --steer could not find a vertical steering joint for every wheel (found {steer})")
        print("[6b] steering joint above each wheel: " + ", ".join(f"{steer[n][0]} -> {n}" for n in sorted(steer)))
    steer_names = {v[0] for v in steer.values()}

    # ---- 3. lock everything except the wheel joints; fix wheel axis sign ----
    wheel_names = set(wheel_info)
    locked = 0
    for j in joints:
        if jname(j) in wheel_names or jname(j) in steer_names:
            continue
        j.set("type", "fixed")
        for tag in ("axis", "limit", "dynamics", "mimic", "calibration", "safety_controller"):
            for e in j.findall(tag):
                j.remove(e)
        locked += 1
    flipped = []
    for n, w in wheel_info.items():
        j = w["joint"]
        j.set("type", "continuous")
        ax_loc = floats(j.find("axis").get("xyz"), [0, 0, 1])
        ax_n = mv(R_NO, mv(w["Rw"], ax_loc))
        if abs(ax_n[1]) < 0.99:
            sys.exit(f"ERROR: wheel axis of {n} is not along the new y axis: {ax_n}")
        if ax_n[1] < 0:                       # positive spin must roll the rover forward (+x)
            ax_loc = [-v for v in ax_loc]
            flipped.append(n)
        j.find("axis").set("xyz", fmt(ax_loc))
    print(f"[3] locked {locked} joints; wheel axes flipped so positive spin drives forward: {sorted(flipped)}")
    extra = {"none": [], "left": left, "right": right, "all": left + right}[a.flip]
    for n in extra:
        ax_el = wheel_info[n]["joint"].find("axis")
        ax_el.set("xyz", fmt([-v for v in floats(ax_el.get("xyz"), [0, 0, 1])]))
    if extra:
        print(f"    --flip {a.flip}: additionally reversed {sorted(extra)}")

    # ---- 4/5. collisions, masses ----
    wheel_links = {w["link"] for w in wheel_info.values()}
    wheel_sub = set()
    for wl in wheel_links:
        wheel_sub.update(subtree(wl))
    m_w = a.wheel_mass
    izz = 0.5 * m_w * radius ** 2
    ixx = m_w * (3 * radius ** 2 + width ** 2) / 12.0
    for n, w in wheel_info.items():
        link = links[w["link"]]
        for old in link.findall("inertial"):
            link.remove(old)
        zc = w["c_wheel"][2]
        off_axis = math.hypot(w["c_wheel"][0], w["c_wheel"][1])
        if off_axis > 0.003:
            print(f"    WARNING: tyre centre of {n} is {off_axis * 1000:.1f} mm off the joint axis (collision centred on the axis)")
        inert = ET.SubElement(link, "inertial")
        ET.SubElement(inert, "origin", xyz=fmt([0, 0, zc]), rpy="0 0 0")
        ET.SubElement(inert, "mass", value=repr(m_w))
        ET.SubElement(inert, "inertia", ixx=repr(ixx), ixy="0", ixz="0", iyy=repr(ixx), iyz="0", izz=repr(izz))
        col = ET.SubElement(link, "collision", name=f"{w['link']}_collision")
        ET.SubElement(col, "origin", xyz=fmt([0, 0, zc]), rpy="0 0 0")
        g = ET.SubElement(col, "geometry")
        ET.SubElement(g, "cylinder", radius=repr(round(radius, 6)), length=repr(round(width, 6)))
    body = [n for n in links if n not in wheel_sub]
    cad_total = sum(float(links[n].find("inertial/mass").get("value")) for n in body if links[n].find("inertial") is not None)
    target = a.mass - 4 * m_w
    k = target / cad_total
    for n in body:
        ine = links[n].find("inertial")
        if ine is None:
            continue
        m = ine.find("mass")
        m.set("value", repr(float(m.get("value")) * k))
        i = ine.find("inertia")
        for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz"):
            i.set(key, repr(float(i.get(key)) * k))
    # drop physically invalid mass blocks (zero inertia, or breaking the triangle rule); they weigh ~nothing
    dropped = 0
    for n in body:
        ine = links[n].find("inertial")
        if ine is None:
            continue
        q = ine.find("inertia")
        ixx, iyy, izz = (float(q.get(key)) for key in ("ixx", "iyy", "izz"))
        tol = 1e-9 * max(ixx, iyy, izz, 1e-30)
        if min(ixx, iyy, izz) <= 0 or ixx > iyy + izz + tol or iyy > ixx + izz + tol or izz > ixx + iyy + tol:
            links[n].remove(ine)
            dropped += 1
    print(f"[5] masses: CAD body mass {cad_total:.3f} kg scaled x{k:.1f} to {target:.2f} kg, + 4 wheels x {m_w} kg = {a.mass:.2f} kg total (PLACEHOLDERS)")
    print(f"    dropped {dropped} invalid mass blocks (zero or impossible inertia in the CAD, ~0 kg each)")

    # steering links must not be featherweight: a position controller on a ~0 inertia joint blows up the physics
    for n, (sj, sg, sl) in steer.items():
        ine = links[sl].find("inertial")
        if ine is None:
            ine = ET.SubElement(links[sl], "inertial")
            ET.SubElement(ine, "origin", xyz="0 0 0", rpy="0 0 0")
            ET.SubElement(ine, "mass", value="0.3")
            ET.SubElement(ine, "inertia", ixx="1", ixy="0", ixz="0", iyy="1", iyz="0", izz="1")
        m = ine.find("mass")
        m.set("value", repr(max(float(m.get("value")), 0.3)))
        q = ine.find("inertia")
        for key in ("ixx", "iyy", "izz"):
            q.set(key, repr(3e-3))
        for key in ("ixy", "ixz", "iyz"):
            q.set(key, "0")
        jx = jmap[sj]
        for e in jx.findall("dynamics"):
            jx.remove(e)
        ET.SubElement(jx, "dynamics", damping="0.3", friction="0")
    if steer:
        print("    steering links: mass >= 0.3 kg, inertia 3e-3, joint damping 0.3 (keeps the steering stable)")

    # ---- mesh paths ----
    n_mesh = 0
    for m in robot.iter("mesh"):
        m.set("filename", f"package://{PKG}/meshes/" + os.path.basename(m.get("filename")))
        n_mesh += 1

    # ---- friction + plugin ----
    for wl in sorted(wheel_links):
        gz = ET.SubElement(robot, "gazebo", reference=wl)
        ET.SubElement(gz, "mu1").text = repr(a.mu)
        ET.SubElement(gz, "mu2").text = repr(a.mu)
    gz = ET.SubElement(robot, "gazebo")
    if a.drive == "diff":
        pl = ET.SubElement(gz, "plugin", filename="gz-sim-diff-drive-system", name="gz::sim::systems::DiffDrive")
        for n in left:
            ET.SubElement(pl, "left_joint").text = n
        for n in right:
            ET.SubElement(pl, "right_joint").text = n
        ET.SubElement(pl, "wheel_separation").text = repr(round(separation, 6))
        ET.SubElement(pl, "wheel_radius").text = repr(round(radius, 6))
        ET.SubElement(pl, "odom_publish_frequency").text = "50"
        ET.SubElement(pl, "frame_id").text = "odom"
        ET.SubElement(pl, "child_frame_id").text = "base_footprint"
    else:
        # Gazebo sets the whole rover's velocity from /model/rover/cmd_vel (wheels just spin along for show)
        vc = ET.SubElement(gz, "plugin", filename="gz-sim-velocity-control-system",
                           name="gz::sim::systems::VelocityControl")
        ET.SubElement(vc, "topic").text = "/model/rover/cmd_vel"
        op = ET.SubElement(gz, "plugin", filename="gz-sim-odometry-publisher-system",
                           name="gz::sim::systems::OdometryPublisher")
        ET.SubElement(op, "odom_frame").text = "odom"
        ET.SubElement(op, "robot_base_frame").text = "base_footprint"
        ET.SubElement(op, "odom_publish_frequency").text = "50"
        ET.SubElement(op, "dimensions").text = "2"
        ET.SubElement(op, "odom_topic").text = "/model/rover/odometry"
    for n, (sj, sg, sl) in sorted(steer.items()):
        sp = ET.SubElement(gz, "plugin", filename="gz-sim-joint-position-controller-system",
                           name="gz::sim::systems::JointPositionController")
        ET.SubElement(sp, "joint_name").text = sj
        ET.SubElement(sp, "topic").text = f"/model/rover/steer/{sj}"
        ET.SubElement(sp, "p_gain").text = "5"
        ET.SubElement(sp, "i_gain").text = "0"
        ET.SubElement(sp, "d_gain").text = "0"
    # publishes every wheel joint's position and speed, so we can see what the wheels really do
    ET.SubElement(gz, "plugin", filename="gz-sim-joint-state-publisher-system",
                  name="gz::sim::systems::JointStatePublisher")

    # ---- 6. new root so the rover drives along +x ----
    foot = ET.Element("link", name="base_footprint")
    robot.insert(0, foot)
    fj = ET.Element("joint", name="base_footprint_joint", type="fixed")
    ET.SubElement(fj, "origin", xyz=f"{-cx!r} {-cy!r} 0", rpy=f"0 0 {yaw!r}")
    ET.SubElement(fj, "parent", link="base_footprint")
    ET.SubElement(fj, "child", link=old_root)
    robot.insert(1, fj)

    # ---- final sanity checks ----
    all_links = [l.get("name") for l in robot.findall("link")]
    all_joints = [j.get("name") for j in robot.findall("joint")]
    assert len(set(all_links)) == len(all_links), "duplicate link names"
    assert len(set(all_joints)) == len(all_joints), "duplicate joint names"
    assert not (set(all_links) & set(all_joints)), "link/joint name clash"
    assert len(all_links) == len(all_joints) + 1, "not a tree"
    ET.indent(tree)
    if os.path.dirname(a.out):
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
    tree.write(a.out, xml_declaration=True, encoding="utf-8")
    print(f"\nDONE. {len(all_links)} links, {len(all_joints)} joints ({sum(1 for j in robot.findall('joint') if j.get('type') != 'fixed')} moving), {n_mesh} mesh paths.")
    print(f"Wrote {a.out}")
    jp = os.path.join(os.path.dirname(a.out) or ".", "rover_steer.json")
    if steer:
        info = {"wheels": [{"wheel_joint": n, "steer_joint": steer[n][0], "sign": steer[n][1],
                            "x": N[n][0] - cx, "y": N[n][1] - cy} for n in sorted(steer)]}
        with open(jp, "w") as f:
            json.dump(info, f, indent=2)
        print(f"Wrote {jp}")
    elif os.path.exists(jp):
        os.remove(jp)                                    # stale file from an earlier --steer run


if __name__ == "__main__":
    main()
