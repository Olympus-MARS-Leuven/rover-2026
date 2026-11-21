"""Go-to-point controller. No ROS in this file, so it can be tested on its own.

Idea: the rover is either TURNING in place (until it faces the target) or
DRIVING straight (until it is close to the target). Never both at once.
This matches the bridge from week 2, which cannot do turn + drive together.
"""
import math


def wrap_angle(a):
    """Wrap an angle to the range (-pi, pi]."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a <= -math.pi:
        a += 2.0 * math.pi
    return a


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class GoToPoint:
    def __init__(self, waypoints,
                 v_max=0.2,          # m/s, top driving speed
                 w_max=0.5,          # rad/s, top turning speed
                 w_min=0.1,          # rad/s, smallest turn speed (so it does not stall)
                 k_lin=0.5,          # 1/s, speed = k_lin * distance (slows down when close)
                 k_ang=1.0,          # 1/s, turn speed = k_ang * heading error
                 tol_dist=0.10,      # m, "arrived" distance
                 turn_enter=0.35,    # rad, start turning if error is bigger than this
                 turn_exit=0.08):    # rad, stop turning when error is smaller than this
        self.waypoints = list(waypoints)    # [(x, y), ...]
        self.i = 0
        self.mode = "TURN"
        self.v_max, self.w_max, self.w_min = v_max, w_max, w_min
        self.k_lin, self.k_ang = k_lin, k_ang
        self.tol_dist = tol_dist
        self.turn_enter, self.turn_exit = turn_enter, turn_exit

    @property
    def done(self):
        return self.i >= len(self.waypoints)

    def step(self, x, y, yaw):
        """Give the current pose. Returns (linear_x, angular_z, event).
        event is None, or a string when a waypoint was just reached."""
        if self.done:
            return 0.0, 0.0, None

        tx, ty = self.waypoints[self.i]
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)

        # 1) arrived at this waypoint?
        if dist < self.tol_dist:
            self.i += 1
            self.mode = "TURN"
            return 0.0, 0.0, f"reached waypoint {self.i} at ({tx:.2f}, {ty:.2f})"

        # 2) heading error: direction to the target minus the direction we face
        err = wrap_angle(math.atan2(dy, dx) - yaw)

        # 3) choose TURN or DRIVE (with two thresholds so it does not flip back and forth)
        if self.mode == "DRIVE" and abs(err) > self.turn_enter and dist > 2 * self.tol_dist:
            self.mode = "TURN"      # drifted off course: face the target again
        elif self.mode == "TURN" and abs(err) < self.turn_exit:
            self.mode = "DRIVE"

        if self.mode == "TURN":
            w = clamp(self.k_ang * err, -self.w_max, self.w_max)
            if abs(w) < self.w_min:
                w = math.copysign(self.w_min, err)
            return 0.0, w, None

        v = clamp(self.k_lin * dist, 0.05, self.v_max)
        return v, 0.0, None
