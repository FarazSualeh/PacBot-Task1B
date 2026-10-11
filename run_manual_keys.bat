@echo off
title PacBot Manual Control (Arrow Keys)
echo ===================================================
echo  PacBot Manual Keyboard Teleoperation
echo  Press Arrow Keys (Up, Down, Left, Right) or WASD
echo  Press Space to Stop, Q to Quit
echo ===================================================
echo.
wsl -d Ubuntu-22.04 -u root -- bash -c "cd /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws; python3 teleop_keys.py"
pause
