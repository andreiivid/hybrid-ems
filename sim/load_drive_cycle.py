from pathlib import Path
import csv
import matplotlib.pyplot as plt


RAW_PATH = Path(__file__).parent.parent / "data" / "uddscol_raw.txt"

with open(RAW_PATH, "r") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print(f"Line 0: {lines[0]!r}")
print(f"Line 1: {lines[1]!r}")
print(f"Line 2: {lines[2]!r}")

data_lines = lines[2:]  # skip the two header lines

rows = []
for line in data_lines:
    line = line.strip()  # remove the trailing \n
    if not line:
        continue  # skip any blank lines
    parts = line.split("\t")  # split on the tab character
    t = int(parts[0])
    speed_mph = float(parts[1])
    rows.append((t, speed_mph))

print(f"Parsed {len(rows)} rows")
print(f"First row: {rows[0]}")
print(f"Last row: {rows[-1]}")

MPH_TO_MS = 0.44704

CSV_PATH = Path(__file__).parent.parent / "data" / "udds_drive_cycle.csv"

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_s", "speed_mph", "speed_mps"])
    for t, speed_mph in rows:
        speed_mps = round(speed_mph * MPH_TO_MS, 4)
        writer.writerow([t, speed_mph, speed_mps])

print(f"Wrote CSV to {CSV_PATH}")

times = [r[0] for r in rows]
speeds_mps = [r[1] * MPH_TO_MS for r in rows]

plt.figure(figsize=(11, 4))
plt.plot(times, speeds_mps, linewidth=1)
plt.xlabel("Time (s)")
plt.ylabel("Speed (m/s)")
plt.title("EPA UDDS Drive Cycle")
plt.grid(True, alpha=0.3)
plt.tight_layout()

PLOT_PATH = Path(__file__).parent.parent / "data" / "udds_drive_cycle.png"
plt.savefig(PLOT_PATH, dpi=150)
print(f"Plot saved to {PLOT_PATH}")