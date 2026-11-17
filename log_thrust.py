"""Thrust rig serial logger.

Reads the CSV rows printed by RPMAndThrust.ino and saves them to a timestamped .csv file
in the same folder as this script. Start-up messages ("Taring...", etc.) are shown but not saved.

Usage:
    python log_thrust.py                 # auto-detects the Arduino port
    python log_thrust.py COM5            # or name the port
    python log_thrust.py COM5 --label 10x4.5prop_run1

Stop with Ctrl+C. Close the Arduino IDE Serial Monitor first (only one program can use the port).
Note: opening the port resets the Uno, which re-tares the load cell -- keep the prop still when starting.
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial is not installed. Run:  python -m pip install pyserial")

BAUD = 9600  # must match Serial.begin() in RPMAndThrust.ino


def find_port():
    ports = list(list_ports.comports())
    arduinos = [p for p in ports
                if "arduino" in (p.description or "").lower()
                or "ch340" in (p.description or "").lower()
                or (p.vid in (0x2341, 0x2A03, 0x1A86))]  # Arduino, Arduino.org, CH340 clones
    candidates = arduinos or ports
    if len(candidates) == 1:
        return candidates[0].device
    if not candidates:
        sys.exit("No serial ports found. Is the Arduino plugged in?")
    print("Several serial ports found; pick one and pass it as an argument:")
    for p in candidates:
        print(f"  {p.device}  {p.description}")
    sys.exit(1)


def parse_row(line):
    """Return a list of floats for a data row, or None for start-up/other text."""
    parts = [s.strip() for s in line.split(",")]
    if len(parts) not in (3, 4):
        return None
    try:
        return [float(s) for s in parts]
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description="Log thrust rig serial output to CSV.")
    ap.add_argument("port", nargs="?", help="serial port, e.g. COM5 (auto-detected if omitted)")
    ap.add_argument("--label", default="", help="text added to the file name, e.g. prop and run number")
    args = ap.parse_args()

    port = args.port or find_port()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"thrust_{stamp}" + (f"_{args.label}" if args.label else "") + ".csv"
    out_path = Path(__file__).resolve().parent / name

    try:
        ser = serial.Serial(port, BAUD, timeout=2)
    except serial.SerialException as e:
        sys.exit(f"Could not open {port}: {e}\n(Is the Arduino IDE Serial Monitor still open?)")

    print(f"Logging {port} -> {out_path}")
    print("Waiting for the Arduino to tare (keep the prop still)... Ctrl+C to stop.\n")

    rows = 0
    no_signal = 0
    t0 = None
    with ser, open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        header_written = False
        try:
            while True:
                line = ser.readline().decode("ascii", errors="replace").strip()
                if not line:
                    continue
                values = parse_row(line)
                if values is None:
                    print(f"[arduino] {line}")
                    continue

                if not header_written:
                    header = ["time_s", "thrust", "throttle_pct", "rpm"]
                    if len(values) == 4:
                        header.append("loop_ms")
                    writer.writerow(header)
                    header_written = True
                    t0 = time.monotonic()

                elapsed = round(time.monotonic() - t0, 3)
                writer.writerow([elapsed] + values)
                f.flush()  # keep data on disk even if the script is killed
                rows += 1
                if values[1] == -1:
                    no_signal += 1

                note = "  (NO THROTTLE SIGNAL)" if values[1] == -1 else ""
                print(f"{elapsed:8.2f} s | thrust {values[0]:8.3f} | throttle {values[1]:4.0f} % "
                      f"| rpm {values[2]:6.0f}" + (f" | loop {values[3]:.0f} ms" if len(values) == 4 else "")
                      + note)
        except KeyboardInterrupt:
            pass
        except serial.SerialException as e:
            print(f"\nSerial connection lost: {e}")

    print(f"\nSaved {rows} rows to {out_path}")
    if no_signal:
        print(f"Warning: {no_signal} rows had throttle = -1 (no receiver signal).")


if __name__ == "__main__":
    main()
