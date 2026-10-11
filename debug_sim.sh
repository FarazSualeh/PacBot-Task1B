#!/bin/bash
cd /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir

echo "=== Testing without turbo_sim ==="
timeout 3s env LD_LIBRARY_PATH=./lib ./task_1b_launch
echo "Exit code without turbo_sim: $?"

echo "=== Testing with turbo_sim ==="
timeout 3s env LD_PRELOAD=./turbo_sim.so LD_LIBRARY_PATH=./lib ./task_1b_launch
echo "Exit code with turbo_sim: $?"
