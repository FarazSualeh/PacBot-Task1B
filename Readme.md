# PacBot Task 1B — Maze Navigation

A Python-based maze navigation controller for the **eYRC 2026–27 PacBot Task 1B** simulator. This project uses MQTT communication to receive sensor readings and control the robot's wheel velocities while navigating a maze.

## Overview

The project combines a MuJoCo-based simulator, an MQTT broker, and a Python navigation controller.

The controller uses distance sensor readings and gyroscope data to estimate the robot's orientation, follow corridors, detect openings, and make turns while navigating the maze.

**Project status:** The simulator has displayed `MAZE SOLVED` during a local test. Results may vary with controller tuning, simulator configuration, and execution environment.

## Features

- Python-based autonomous navigation controller
- MQTT communication for sensor data and wheel commands
- Distance-sensor filtering
- Gyroscope-based heading tracking
- PID-based wall-following and steering correction
- Left-hand-rule maze navigation
- State-based movement, turning, and corridor entry
- MuJoCo simulator launch scripts
- Optional manual-control utilities
- Windows batch launchers for a WSL2 environment

## Technology Stack

- **Python** — navigation and control logic
- **Paho MQTT** — communication with the simulator
- **Mosquitto** — MQTT message broker
- **MuJoCo** — robot simulation
- **C / shared libraries** — optional simulator performance shim
- **Windows + WSL2 + Ubuntu 22.04** — development and execution environment

## Project Structure

```text
pacbot_ws/
├── README.md
├── .gitignore
├── requirements.txt
├── START_TASK1B.bat
├── task_1b.py
├── task_1b_boilerplate.py
├── task_1b_launch
├── teleop_keys.py
├── debug_sim.sh
├── run_sim.sh
├── run_1_broker.bat
├── run_2_simulator.bat
├── run_3_navigation.bat
├── run_manual_keys.bat
├── test_wsl.bat
├── turbo_sim.c
├── turbo_sim.so
├── lib/
│   ├── libglfw.so.3
│   ├── libmosquitto.so.1
│   ├── libmujoco.so.3.11.0
│   └── libsodium.so.23
└── meshes/
    ├── chassis_sim.stl
    └── roda_sim.stl
```

_This is the intended overview based on the current project files. Additional files or simulator dependencies may be required by the launch executable._

### Important files

| File                     | Purpose                                               |
| ------------------------ | ----------------------------------------------------- |
| `task_1b.py`             | Main autonomous navigation controller                 |
| `task_1b_boilerplate.py` | Starter controller/reference                          |
| `task_1b_launch`         | Simulator executable                                  |
| `START_TASK1B.bat`       | Starts the broker, simulator, and controller          |
| `run_sim.sh`             | Configures the environment and launches the simulator |
| `run_1_broker.bat`       | Broker launcher                                       |
| `run_2_simulator.bat`    | Simulator launcher                                    |
| `run_3_navigation.bat`   | Controller launcher                                   |
| `teleop_keys.py`         | Manual-control utility                                |
| `run_manual_keys.bat`    | Manual-control launcher                               |
| `debug_sim.sh`           | Simulator debugging utility                           |
| `turbo_sim.c`            | Source for an optional performance shim               |
| `turbo_sim.so`           | Compiled performance shim                             |
| `lib/`                   | Bundled shared libraries                              |
| `meshes/`                | Robot mesh assets                                     |

## How It Works

The system has three main components:

1. **MQTT broker:** Routes messages between the simulator and controller.
2. **Simulator:** Runs the robot and publishes sensor readings.
3. **Navigation controller:** Processes sensor data and publishes wheel velocity commands.

### MQTT topics

| Topic              | Direction              | Purpose                                       |
| ------------------ | ---------------------- | --------------------------------------------- |
| `pacbot/sensors`   | Simulator → controller | Sensor readings, gyroscope data, and timestep |
| `pacbot/wheel_vel` | Controller → simulator | Left and right wheel velocities               |

The controller connects to `localhost` on port `1883`.

### Navigation logic

The controller uses a state machine with states such as:

- `FOLLOW` — follows a corridor and monitors the front and side distances.
- `ADVANCE_LEFT` — advances toward an opening before turning left.
- `TURN` — rotates toward the target heading.
- `ENTER` — enters the newly selected corridor before resuming normal following.

PID and heading corrections help maintain the robot's direction. Distance thresholds determine when to slow down, detect openings, and initiate turns.

## Prerequisites

The documented local setup uses:

- Windows with WSL2
- Ubuntu 22.04
- Python 3
- Git
- Mosquitto MQTT broker
- Paho MQTT Python package
- The supplied simulator executable and its required libraries
- A working graphical display environment for MuJoCo

The Windows launch scripts assume a WSL distribution named `Ubuntu-22.04`. Other distributions may require changes.

## Installation

### 1. Clone the repository

Open PowerShell or a terminal and run:

```bash
git clone https://github.com/FarazSualeh/PacBot-Task1B.git
cd PacBot-Task1B
```

### 2. Open the Ubuntu environment

If WSL2 and Ubuntu 22.04 are already installed, open Ubuntu from the Start menu.

From Windows PowerShell, you can also run:

```powershell
wsl -d Ubuntu-22.04
```

### 3. Install system dependencies

In Ubuntu, update the package index and install the basic dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-pip mosquitto gcc libgl1
```

Additional packages may be necessary depending on the simulator binary and the Ubuntu installation.

### 4. Install Python dependencies

From the project directory inside Ubuntu:

```bash
python3 -m pip install -r requirements.txt
```

If the system Python environment is externally managed, use a virtual environment instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 5. Check the simulator files

Confirm that the executable and supporting files are present:

```bash
ls -l task_1b_launch
ls lib
ls meshes
```

If needed, make the launch scripts executable:

```bash
chmod +x task_1b_launch run_sim.sh debug_sim.sh
```

**Note:** The simulator must be run in the environment for which its executable and libraries were built. Windows and Linux binaries are not interchangeable.

## Running the Project

### Option A: Windows launcher

If your Windows installation matches the configured paths and distribution name, run:

```powershell
.\START_TASK1B.bat
```

The launcher attempts to start three processes:

1. MQTT broker
2. MuJoCo simulator
3. Navigation controller

The simulator window may open separately. Use Alt+Tab to find it if it is not visible.

**Configuration note:** The current launcher contains machine-specific paths, including the Windows project directory and WSL distribution name. Update these for your own computer before using the script.

### Option B: Start the components manually

Open three Ubuntu terminals.

**Terminal 1 — MQTT broker**

```bash
sudo service mosquitto start
sudo service mosquitto status
```

If the broker is already running, do not start a second instance on the same port.

**Terminal 2 — Simulator**

Navigate to the project directory, then launch the simulator using the supplied script:

```bash
cd /path/to/PacBot-Task1B
bash run_sim.sh
```

Replace `/path/to/PacBot-Task1B` with the actual path.

**Terminal 3 — Navigation controller**

Navigate to the same project directory and run:

```bash
cd /path/to/PacBot-Task1B
python3 task_1b.py
```

Start the broker and simulator before the controller.

To stop the controller, press `Ctrl+C` in its terminal. Stop the simulator and broker using their respective terminal or service controls.

## Manual Control and Debugging

The repository includes manual-control and diagnostic utilities, including `teleop_keys.py`, `run_manual_keys.bat`, and `debug_sim.sh`.

Their exact controls and requirements depend on the scripts and simulator configuration. Inspect the relevant script before running it.

To observe incoming sensor messages, run:

```bash
mosquitto_sub -h localhost -p 1883 -t pacbot/sensors -v
```

To send a test wheel command, run:

```bash
mosquitto_pub -h localhost -p 1883 \
  -t pacbot/wheel_vel \
  -m '{"left":0,"right":0}'
```

The example above sends a stop command. Use manual commands only when you intend to control the robot.

## Troubleshooting

### MQTT connection fails

Check the broker:

```bash
sudo service mosquitto status
```

If it is stopped:

```bash
sudo service mosquitto start
```

Confirm that the controller uses `localhost`, port `1883`, and the correct MQTT topics.

### Port 1883 is already in use

This often means another Mosquitto instance is running. Check the existing service and avoid launching a duplicate broker.

### MuJoCo window does not appear

- Check whether the simulator process is still running.
- Check the WSL graphical display configuration.
- Inspect the output from `run_sim.sh`.
- Confirm that the required shared libraries are available.

### Python cannot import Paho MQTT

Install the dependencies using the instructions above, preferably in the same Python environment used to launch `task_1b.py`.

### The robot does not solve the maze

- Confirm that the sensor messages are arriving.
- Check the sensor mapping and controller state transitions.
- Review the distance thresholds and steering gains.
- Inspect the simulator logs for errors and collisions.
- Test changes incrementally and evaluate each run.

## Performance Shim

The repository contains `turbo_sim.c` and `turbo_sim.so`. The C source overrides `nanosleep()` and attempts to disable GLFW vertical synchronization using `LD_PRELOAD`.

This is an optional, environment-dependent modification. It can change simulation timing and should not be assumed to preserve evaluation behavior. Test the simulator and scoring process with and without the shim, and follow the competition's evaluation rules.

## Notes for Contributors

- Keep local logs, temporary files, backups, and Python cache files out of Git.
- Avoid committing personal credentials or machine-specific configuration.
- Update hard-coded paths before sharing launch scripts.
- Verify that bundled binaries, libraries, and competition assets are permitted to be redistributed.
- Record evaluation results separately and report collision counts honestly.

## Disclaimer

This repository documents a personal implementation and local development setup for PacBot Task 1B. Successful execution on one machine does not guarantee identical results on other systems. Follow the official eYRC competition instructions and rules for simulator usage, redistribution, and evaluation.

## Repository:

GitHub: https://github.com/FarazSualeh/PacBot-Task1B
