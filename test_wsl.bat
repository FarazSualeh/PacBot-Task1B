@echo off
echo Testing with -u root /bin/sh:
wsl.exe -d Ubuntu-22.04 -u root /bin/sh -c "echo SH_OK"
echo Err: %errorlevel%
echo.
echo Testing with -u root /bin/bash:
wsl.exe -d Ubuntu-22.04 -u root /bin/bash -c "echo BASH_OK"
echo Err: %errorlevel%
