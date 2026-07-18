import csv
import matplotlib.pyplot as plt
from pathlib import Path

from plant.battery import Battery
from plant.motor import Motor
from plant.vehicle import Vehicle



CSV_PATH = Path(__file__).parent.parent / "data" / "udds_drive_cycle.csv"


def load_drive_cycle(path: Path) -> list[tuple[float, float]]:
    """Returns list of (time_s, target_speed_mps) tuples."""
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((float(row["time_s"]), float(row["speed_mps"])))
    return rows

def run_simulation(drive_cycle, dt=1.0):
    battery = Battery()
    motor = Motor()
    vehicle = Vehicle()

    results = []

    for time_s, target_speed_mps in drive_cycle:
        # PLACEHOLDER driver demand: proportional to speed error.
        speed_error = target_speed_mps - vehicle.speed_ms

        # Estimate motor speed from vehicle speed BEFORE using it below
        wheel_speed_approx = vehicle.speed_ms / vehicle.WHEEL_RADIUS_M
        motor_speed_approx = wheel_speed_approx * vehicle.FINAL_DRIVE_RATIO

        motor_torque_cmd = speed_error * 150
        motor_torque_cmd = max(motor.min_available_torque(motor_speed_approx), motor_torque_cmd)
        motor_torque_cmd = min(motor_torque_cmd, motor.MAX_TORQUE_NM)

        # Motor: check what's actually available (torque-speed curve + thermal)
        available_torque = motor.max_available_torque(motor_speed_approx)
        min_torque = motor.min_available_torque(motor_speed_approx)
        actual_motor_torque = max(min_torque, min(motor_torque_cmd, available_torque))

        # Battery: does it have enough power to deliver this torque?
        power_needed_w = actual_motor_torque * motor_speed_approx
        power_delivered_w = battery.update(power_needed_w, dt)

        # If battery couldn't deliver full power, scale torque down proportionally
        if power_needed_w > 0:
            power_ratio = power_delivered_w / power_needed_w
            actual_motor_torque *= power_ratio

        motor.update_temp(actual_motor_torque, dt)

        wheel_torque = vehicle.motor_torque_to_wheel_torque(actual_motor_torque)
        actual_speed = vehicle.update(wheel_torque, dt)

        results.append({
            "time_s": time_s,
            "target_speed_mps": target_speed_mps,
            "actual_speed_mps": actual_speed,
            "soc": battery.soc,
            "motor_temp_c": motor.temp_c,
        })

    return results


if __name__ == "__main__":
    drive_cycle = load_drive_cycle(CSV_PATH)
    print(f"Loaded {len(drive_cycle)} drive cycle points")
    print(f"First: {drive_cycle[0]}")
    print(f"Last: {drive_cycle[-1]}")

    battery = Battery()
    motor = Motor()
    vehicle = Vehicle()
    results = run_simulation(drive_cycle)
    print(f"\nRan simulation for {len(results)} steps")
    print(f"Final SOC: {results[-1]['soc']:.4f}")
    print(f"Final motor temp: {results[-1]['motor_temp_c']:.1f} C")
    print(f"\nFirst 5 steps:")
    for r in results[:5]:
        print(r)

    times = [r["time_s"] for r in results]
    targets = [r["target_speed_mps"] for r in results]
    actuals = [r["actual_speed_mps"] for r in results]

    plt.figure(figsize=(11, 4))
    plt.plot(times, targets, label="Target (UDDS)", linewidth=1)
    plt.plot(times, actuals, label="Actual", linewidth=1, alpha=0.8)
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (m/s)")
    plt.title("Drive Cycle Tracking (placeholder proportional demand)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    from pathlib import Path
    plot_path = Path(__file__).parent.parent / "data" / "sim_tracking.png"
    plt.savefig(plot_path, dpi=150)
    print(f"\nPlot saved to {plot_path}")