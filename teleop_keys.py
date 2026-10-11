"""
Manual Arrow Key Teleoperation for PacBot - Task 1B
Allows you to manually drive the car using Arrow Keys or WASD.

Controls:
  [Up Arrow]    / [W] : Forward
  [Down Arrow]  / [S] : Backward
  [Left Arrow]  / [A] : Rotate Left
  [Right Arrow] / [D] : Rotate Right
  [Space]             : Stop
  [Q]                 : Quit
"""
import sys
import tty
import termios
import select
import json
import math
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_SENSORS = "pacbot/sensors"
TOPIC_WHEEL_VEL = "pacbot/wheel_vel"

SPEED = 26.0
TURN_SPEED = 22.0

latest_sensors = {"fl": 0.0, "fr": 0.0, "sl": 0.0, "sr": 0.0, "yaw": 0.0}


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        latest_sensors["fl"] = data.get("fl", 0.0)
        latest_sensors["fr"] = data.get("fr", 0.0)
        latest_sensors["sl"] = data.get("sl", 0.0)
        latest_sensors["sr"] = data.get("sr", 0.0)
    except Exception:
        pass


def get_key():
    """Reads a single key or escape sequence non-blocking."""
    dr, _, _ = select.select([sys.stdin], [], [], 0.05)
    if not dr:
        return None
    ch = sys.stdin.read(1)
    if ch == '\x1b':
        # Arrow key escape sequence
        seq = sys.stdin.read(2)
        if seq == '[A':
            return 'UP'
        elif seq == '[B':
            return 'DOWN'
        elif seq == '[C':
            return 'RIGHT'
        elif seq == '[D':
            return 'LEFT'
    return ch.lower()


def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.subscribe(TOPIC_SENSORS)
    client.loop_start()

    print("=" * 50)
    print(" PacBot Manual Keyboard Teleoperation")
    print("=" * 50)
    print(" Controls:")
    print("   [Up Arrow]    / [W] : Forward")
    print("   [Down Arrow]  / [S] : Backward")
    print("   [Left Arrow]  / [A] : Turn Left")
    print("   [Right Arrow] / [D] : Turn Right")
    print("   [Space]             : Stop")
    print("   [Q]                 : Quit")
    print("=" * 50)

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    left_vel = 0.0
    right_vel = 0.0

    try:
        while True:
            key = get_key()
            if key in ('q', '\x03'):  # 'q' or Ctrl+C
                break
            elif key in ('UP', 'w'):
                left_vel = SPEED
                right_vel = SPEED
            elif key in ('DOWN', 's'):
                left_vel = -SPEED * 0.7
                right_vel = -SPEED * 0.7
            elif key in ('LEFT', 'a'):
                left_vel = -TURN_SPEED
                right_vel = +TURN_SPEED
            elif key in ('RIGHT', 'd'):
                left_vel = +TURN_SPEED
                right_vel = -TURN_SPEED
            elif key == ' ':
                left_vel = 0.0
                right_vel = 0.0

            # Publish command
            client.publish(TOPIC_WHEEL_VEL, json.dumps({
                "left": float(left_vel),
                "right": float(right_vel)
            }))

            fl = latest_sensors["fl"]
            fr = latest_sensors["fr"]
            front = min(latest_sensors["sl"], latest_sensors["sr"])
            print(f"\rL={fl:.2f}m | R={fr:.2f}m | Front={front:.2f}m | Cmd: L={left_vel:+.1f} R={right_vel:+.1f}   ", end="", flush=True)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        client.publish(TOPIC_WHEEL_VEL, json.dumps({"left": 0.0, "right": 0.0}))
        client.loop_stop()
        print("\nTeleop stopped.")


if __name__ == "__main__":
    main()
