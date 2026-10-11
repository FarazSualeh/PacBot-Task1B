"""
eYRC 2026-27 PacBot - Task 1B
High-Speed Left-Hand Rule Maze Navigation in MuJoCo Simulation.

Key Specifications:
- Grid cell pitch: 0.22 m (clear width: ~0.208 m)
- Chassis box: 9.2 cm long x 8.6 cm wide (radius = 6.3 cm)
- Actuator ctrlrange: [-30, +30] rad/s
- Wheels: r = 0.017 m, track width = 0.078 m
- Manhattan alignment: headings strictly at 0°, 90°, 180°, -90°
"""
import json
import math
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_SENSORS = "pacbot/sensors"
TOPIC_WHEEL_VEL = "pacbot/wheel_vel"

# ── Speed parameters (rad/s) ──────────────────────────────────────────────────
MAX_MOTOR_VEL  = 29.5   # Hardware hard limit is ±30 rad/s
BASE_SPEED     = 28.0   # Fast straight-line cruise (~0.48 m/s)
APPROACH_SPEED = 15.0   # Deceleration floor when approaching front wall
SIDE_SPEED     = 24.0   # Intersection enter / transition speed

# ── PID & Heading gains ───────────────────────────────────────────────────────
KP      = 22.0          # Lateral wall centering proportional gain
KI      = 0.0
KD      = 2.2           # Lateral derivative gain
KP_HEAD = 18.0          # Strong gyro heading lock
MAX_CORR = 6.0          # Maximum steering correction (rad/s)

# ── Distance & Geometry thresholds (meters) ───────────────────────────────────
TARGET_SIDE        = 0.100  # Centered gap to side wall (10.0 cm)
SIDE_OPEN          = 0.165  # Distance > 16.5 cm indicates an open corridor
FRONT_STOP         = 0.115  # Cell center front-wall threshold (guarantees clearance)
FRONT_SLOW         = 0.230  # Start smooth deceleration 1 cell away
ADVANCE_LEFT_DIST  = 0.150  # Advance distance for open-front T-junctions
ENTER_DIST         = 0.080  # Advance distance into new corridor (8 cm)
ENTER_MIN_PROGRESS = 0.045  # Must travel 4.5 cm before front wall can re-trigger

WHEEL_RADIUS = 0.017        # meters
ALPHA        = 0.75         # Sensor low-pass filter coefficient
MAX_RANGE    = 1.0          # Sensor saturation cap


def _mqtt_client():
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        return mqtt.Client()


class PID:
    def __init__(self, kp, ki, kd, limit):
        self.kp, self.ki, self.kd, self.limit = kp, ki, kd, limit
        self.reset()

    def reset(self):
        self.i = 0.0
        self.prev = None
        self.d = 0.0

    def step(self, err, dt):
        if dt <= 0:
            return 0.0
        self.i += err * dt
        if self.ki > 0:
            cap = self.limit / self.ki
            self.i = max(-cap, min(cap, self.i))
        if self.prev is not None:
            raw_d = (err - self.prev) / dt
            self.d += 0.3 * (raw_d - self.d)
        self.prev = err
        out = self.kp * err + self.ki * self.i + self.kd * self.d
        return max(-self.limit, min(self.limit, out))


wall_pid = PID(KP, KI, KD, MAX_CORR)

bot = {
    "f":              None,
    "yaw":            0.0,
    "target_heading": 0.0,
    "state":          "FOLLOW",
    "travel":         0.0,
    "phase_start":    0.0,
    "count":          0,
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def start_turn(quarters):
    """
    Initiates turn by exact 90-degree increments:
    +1 = 90° Left (CCW)
    -1 = 90° Right (CW)
    +2 = 180° U-turn
    """
    bot["target_heading"] = wrap(bot["target_heading"] + quarters * (math.pi / 2.0))
    bot["state"] = "TURN"
    wall_pid.reset()


def _centering_corr(dist_left, dist_right, has_left, has_right, head_err):
    """Computes combined heading lock + wall centering correction."""
    corr = KP_HEAD * head_err

    # Lateral centering
    if has_left and has_right:
        lat = (dist_left - dist_right) / 2.0
    elif has_left:
        lat = dist_left - TARGET_SIDE
    elif has_right:
        lat = TARGET_SIDE - dist_right
    else:
        lat = 0.0
    corr += clamp(KP * lat, -3.5, 3.5)

    # Active safety wall repulsion (triggers if within 6.5 cm of either side)
    DANGER = 0.065
    if dist_left < DANGER:
        corr += clamp(35.0 * (DANGER - dist_left), 0.0, 5.0)
    elif dist_right < DANGER:
        corr -= clamp(35.0 * (DANGER - dist_right), 0.0, 5.0)

    return clamp(corr, -MAX_CORR, MAX_CORR)


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    fl       = data["fl"]            # Left ToF
    fr       = data["fr"]            # Right ToF
    sl       = data["sl"]            # Front-Left ToF
    sr       = data["sr"]            # Front-Right ToF
    yaw_rate = data["gyro"][2]       # rad/s about Z
    dt       = data["dt"]

    # Sensor filtering
    raw = {k: min(v, MAX_RANGE)
           for k, v in (("fl", fl), ("fr", fr), ("sl", sl), ("sr", sr))}
    if bot["f"] is None:
        bot["f"] = dict(raw)
    f = bot["f"]
    for k in raw:
        f[k] += ALPHA * (raw[k] - f[k])

    # Gyro integration
    bot["yaw"] = wrap(bot["yaw"] + yaw_rate * dt)

    dist_left  = f["fl"]
    dist_right = f["fr"]
    dist_front = min(f["sl"], f["sr"])

    has_left  = dist_left  < SIDE_OPEN
    has_right = dist_right < SIDE_OPEN
    state     = bot["state"]

    left_vel  = 0.0
    right_vel = 0.0

    # ── State Machine ─────────────────────────────────────────────────────────

    if state == "TURN":
        err = wrap(bot["target_heading"] - bot["yaw"])

        # Stop turn when aligned within ~1.1° AND angular rate has braked
        if abs(err) < 0.020 and abs(yaw_rate) < 1.0:
            # Snap yaw to exact target heading to eliminate all gyro integration drift!
            bot["yaw"] = bot["target_heading"]
            bot["state"] = "ENTER"
            bot["phase_start"] = bot["travel"]
            left_vel = SIDE_SPEED
            right_vel = SIDE_SPEED
        else:
            # High-speed PD rotation with real gyro damping
            w = 18.0 * err - 1.5 * yaw_rate
            # Ensure sufficient torque until tightly aligned
            if abs(err) > 0.035:
                min_w = 12.0
                if abs(w) < min_w:
                    w = math.copysign(min_w, err)
            w = clamp(w, -27.0, 27.0)
            left_vel  = -w
            right_vel = +w

    elif state == "ENTER":
        progress = bot["travel"] - bot["phase_start"]

        # Advance into the new corridor; switch to FOLLOW once established
        front_blocked = (dist_front <= FRONT_STOP) and (progress >= ENTER_MIN_PROGRESS)
        if front_blocked or (progress >= ENTER_DIST):
            bot["state"] = "FOLLOW"
            wall_pid.reset()
        else:
            speed = SIDE_SPEED
            if dist_front < FRONT_SLOW:
                frac = clamp((dist_front - FRONT_STOP) / (FRONT_SLOW - FRONT_STOP), 0.0, 1.0)
                speed = APPROACH_SPEED + (SIDE_SPEED - APPROACH_SPEED) * frac

            head_err = wrap(bot["target_heading"] - bot["yaw"])
            corr = _centering_corr(dist_left, dist_right, has_left, has_right, head_err)
            left_vel  = speed - corr
            right_vel = speed + corr

    elif state == "ADVANCE_LEFT":
        # Used only for open intersections with no front wall
        progress = bot["travel"] - bot["phase_start"]
        if (progress >= ADVANCE_LEFT_DIST) or (dist_front <= FRONT_STOP):
            start_turn(+1)
            left_vel  = 0.0
            right_vel = 0.0
        else:
            speed    = SIDE_SPEED
            head_err = wrap(bot["target_heading"] - bot["yaw"])
            corr = KP_HEAD * head_err
            if has_right:
                corr += clamp(KP * (TARGET_SIDE - dist_right), -2.0, 2.0)
            left_vel  = speed - corr
            right_vel = speed + corr

    elif state == "FOLLOW":
        if dist_front <= FRONT_STOP:
            # Reached cell center facing front wall: Left-Hand Rule
            if not has_left:
                start_turn(+1)   # Left is open: turn left
            elif not has_right:
                start_turn(-1)   # Right is open: turn right
            else:
                start_turn(+2)   # Dead end: U-turn (180°)
            left_vel  = 0.0
            right_vel = 0.0

        elif (not has_left) and (dist_front > 0.35):
            # Left opening with genuine open front (> 1.5 cells ahead)
            bot["state"]       = "ADVANCE_LEFT"
            bot["phase_start"] = bot["travel"]
            head_err = wrap(bot["target_heading"] - bot["yaw"])
            corr = KP_HEAD * head_err
            speed = SIDE_SPEED
            left_vel  = speed - corr
            right_vel = speed + corr

        else:
            # Normal corridor cruising: fast speed with smooth deceleration near wall
            speed = BASE_SPEED
            if dist_front < FRONT_SLOW:
                frac = clamp((dist_front - FRONT_STOP) / (FRONT_SLOW - FRONT_STOP), 0.0, 1.0)
                speed = APPROACH_SPEED + (BASE_SPEED - APPROACH_SPEED) * frac

            if has_left and has_right:
                lat_err = (dist_left - dist_right) / 2.0
            elif has_left:
                lat_err = dist_left - TARGET_SIDE
            elif has_right:
                lat_err = TARGET_SIDE - dist_right
            else:
                lat_err = 0.0

            u_lat  = wall_pid.step(lat_err, dt)
            u_head = KP_HEAD * wrap(bot["target_heading"] - bot["yaw"])
            corr   = u_lat + u_head

            # Safety repulsion if too close to any wall
            DANGER = 0.065
            if dist_left < DANGER:
                corr += clamp(35.0 * (DANGER - dist_left), 0.0, 5.0)
            elif dist_right < DANGER:
                corr -= clamp(35.0 * (DANGER - dist_right), 0.0, 5.0)

            corr = clamp(corr, -MAX_CORR, MAX_CORR)
            left_vel  = speed - corr
            right_vel = speed + corr

    # Actuator limits clamp
    left_vel  = clamp(left_vel,  -MAX_MOTOR_VEL, MAX_MOTOR_VEL)
    right_vel = clamp(right_vel, -MAX_MOTOR_VEL, MAX_MOTOR_VEL)

    # Odometry update
    linear_v       = ((left_vel + right_vel) / 2.0) * WHEEL_RADIUS
    bot["travel"] += linear_v * dt

    # Telemetry logging (every 25 cycles)
    bot["count"] += 1
    if bot["count"] % 25 == 0:
        deg_yaw = math.degrees(bot["yaw"])
        deg_tgt = math.degrees(bot["target_heading"])
        print(f"L={dist_left:.3f} R={dist_right:.3f} F={dist_front:.3f} "
              f"yaw={deg_yaw:+5.1f}° (tgt={deg_tgt:+5.1f}°) state={bot['state']}")

    client.publish(TOPIC_WHEEL_VEL, json.dumps({
        "left":  float(left_vel),
        "right": float(right_vel),
    }))


def main():
    client = _mqtt_client()
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.subscribe(TOPIC_SENSORS)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
