@echo off
title T1 - MQTT Broker
echo [T1] Starting mosquitto MQTT broker on port 1883...
echo Keep this window open!
echo.
wsl -d Ubuntu-22.04 mosquitto -v
pause
