# RPM and Thrust Test Rig

You only need to do **Setup** and **Calibration** once. Start at **Test** for each run.

## Setup

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Under **Tools → Manage Libraries**, install:
   - `Q2HX711`
   - `RPM` (by Tyler Barnes)
3. Install [Python](https://www.python.org/downloads/), then run:
   ```
   python -m pip install pyserial
   ```
4. Open `static_thrust_testing-code.ino`, select **Board: Arduino Uno** and the Uno's COM port, then upload.

## Calibration

1. Open the Serial Monitor at **9600 baud**. With nothing touching the rig, wait for `Complete!`.
2. Apply a known weight in the thrust direction and read the thrust value. Then set:
   ```
   CALIBRATION = old value × shown ÷ actual weight
   ```
   and upload again. Results come out in the unit of the weight you used.
3. Close the Serial Monitor.

## Test (start here for each run)

1. **Wire it up.** Use 5V, not 3.3V, for the HX711.

   **HX711 → Arduino**

   | HX711 | Arduino       |
   |-------|---------------|
   | VCC   | 5V (analog)   |
   | GND   | GND (analog)  |
   | DT    | D3 (digital)  |
   | SCK   | D4 (digital)  |

   **Load cell → HX711** (already wired)

   | Load cell wire | HX711 |
   |----------------|-------|
   | Red            | E+    |
   | Black          | E−    |
   | White          | A−    |
   | Green          | A+    |

   **ESC → Arduino**

   | ESC                              | Arduino       |
   |----------------------------------|---------------|
   | Throttle channel signal (yellow) | D10 (digital) |
   | Ground                           | GND (analog)  |

   **Never connect the ESC + (red) wire.**
2. Hold the rig down, keep everyone out of the prop's path, and wear eye protection.
3. Turn the transmitter on with the throttle all the way down, then plug in the battery/fuse.
4. With hands off and the prop still, open a terminal in the project folder and run:
   ```
   python static_thrust_testing-logging.py
   ```
5. Wait for `Complete!`. Then step the throttle up about 10% at a time, holding each step (especially full throttle), and back down to 0.
6. Press **Ctrl+C** to stop, then unplug the battery. The CSV is saved in the same folder, and can be opened as an excel sheet. Clean up the time before and after the test so that the data is easily readable, **add the weight of the rig**, and create a nice graphic with _labeled_ maximum! 

## Notes

- A throttle value of `-1` means no receiver signal.
- Ignore the RPM column for now, since no RPM sensor is fitted yet.
- `loop_ms` is the time each reading took. Set `PRINT_LOOP_TIME = false` in the code to remove that column.
