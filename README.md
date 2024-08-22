# Simple GUI for magnetic sensor from Sensys
Simple app for monitoring magnetic field

## How to use:
Only start .exe file, write correct serial port and press start. If changes in code are made and starting Python is not an option, create exe file (if not exists already)

### Create exe file:
```
pyinstaller --onefile --windowed --name MagneticSensorApp --icon=img/magnet.ico --add-data "img/magnet.ico;img" --add-data "img/giphy.gif;img" main.py
```

add versions to MagneticSensorApp (MagneticSensorApp-v1.0 etc.)
### Example 
pyinstaller --onefile --windowed --name MagneticSensorApp-v1.2 --icon=img/magnet.ico --add-data "img/magnet.ico;img" --add-data "img/giphy.gif;img" main.py

## For next version
Speed control, CAN communication - need 32bit Python, have 64bit

## History
### 0.9
First version, it works...
### 1.0
Stable version, works with hardcoded connection, loading screen during starting measuring
### 1.1
Connection setting, loading screen disabled, status bar work on 75%  (needs repair)
### 1.2
Add ctk style, add dropdown menu for port selection, save selection in file