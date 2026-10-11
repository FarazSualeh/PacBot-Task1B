#!/bin/bash
cd /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir
export vblank_mode=0
export LP_NUM_THREADS=4
export MESA_GLTHREAD=true

echo "=============================================="
echo " Checking MQTT broker..."
for i in {1..10}; do
    if timeout 1 bash -c '</dev/tcp/127.0.0.1/1883' 2>/dev/null; then
        echo " MQTT Broker is ONLINE and ready!"
        break
    fi
    echo " Waiting for MQTT broker (attempt $i/10)..."
    sleep 1
done

echo " Starting MuJoCo Simulator..."
echo " Look for the 3D window on your taskbar/screen."
echo " Alt+Tab to find it if behind other windows."
echo "=============================================="

if [ -f /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws/turbo_sim.so ]; then
    LD_PRELOAD=/mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws/turbo_sim.so LD_LIBRARY_PATH=./lib ./task_1b_launch "$@"
    STATUS=$?
else
    LD_LIBRARY_PATH=./lib ./task_1b_launch "$@"
    STATUS=$?
fi

if [ $STATUS -ne 0 ]; then
    echo "Launcher exited with status $STATUS. Retrying in safe mode..."
    LD_LIBRARY_PATH=./lib ./task_1b_launch "$@"
fi

echo "Simulator session ended."
read -p "Press Enter to close this terminal..."
