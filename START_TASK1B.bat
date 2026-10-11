@echo off
title PacBot Task 1B - Launcher
echo ============================================
echo   eYRC 2026-27 PacBot - Task 1B Launcher
echo ============================================
echo.

echo [0/3] Cleaning up any old instances...
wsl -d Ubuntu-22.04 -u root -- bash -c "pkill -9 mosquitto 2>/dev/null; pkill -9 task_1b_launch 2>/dev/null; pkill -9 -f task_1b.py 2>/dev/null"
timeout /t 1 /nobreak >nul

echo [1/3] Starting MQTT Broker (wait 3 seconds)...
start "T1-MQTT-Broker" cmd /k wsl -d Ubuntu-22.04 -u root -- mosquitto -v
timeout /t 3 /nobreak >nul

echo [2/3] Starting MuJoCo Simulator (wait 4 seconds)...
start "T2-MuJoCo-Sim" cmd /k wsl -d Ubuntu-22.04 -u root -- bash /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws/run_sim.sh
timeout /t 4 /nobreak >nul

echo [3/3] Starting Navigation AI...
start "T3-Navigation-AI" cmd /k wsl -d Ubuntu-22.04 -u root -- bash -c "cd /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws; python3 task_1b.py"

echo.
echo ============================================
echo All 3 launched! Check your taskbar.
echo MuJoCo window takes 3-5 sec to appear.
echo Alt+Tab to find it if not visible.
echo ============================================
echo.
echo Press any key to close THIS launcher window.
echo The 3 simulation windows will keep running.
pause >nul

