@echo off
title T3 - Navigation AI
echo [T3] Starting task_1b.py navigation script...
wsl -d Ubuntu-22.04 -u root -- bash -c "cd /mnt/c/Users/Administrator/Downloads/task_1b/pacbot_ws && python3 task_1b.py"
pause
