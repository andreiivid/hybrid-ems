import csv
import matplotlib.pyplot as plt
from pathlib import Path

from plant.battery import Battery
from plant.motor import Motor
from plant.vehicle import Vehicle
from plant.engine import Engine
from controller.torque_split import TorqueSplitController



CSV_PATH = Path(__file__).parent.parent / "data" / "udds_drive_cycle.csv"


def load_drive_cycle(path: Path) -> list[tuple[float, float]]:
    """Returns list of (time_s, target_speed_mps) tuples."""
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((float(row["time_s"]), float(row["speed_mps"])))
    return rows

def run_simulation(drive_cycle, dt=1.0, initial_soc=0.7):
    battery = Battery(initial_soc=initial_soc)
    motor = Motor()
    vehicle = Vehicle()
    engine = Engine()
    controller = TorqueSplitController()

    results = []

    for time_s, target_speed_mps in drive_cycle:
        speed_error = target_speed_mps - vehicle.speed_ms
        total_torque_demand = speed_error * 150

        engine_torque_cmd, motor_torque_cmd = controller.split_torque(
            total_torque_demand, battery.soc
        )

        actual_engine_torque = engine.command_torque(engine_torque_cmd)

        wheel_speed_approx = vehicle.speed_ms / vehicle.WHEEL_RADIUS_M
        motor_speed_approx = wheel_speed_approx * vehicle.FINAL_DRIVE_RATIO

        available_torque = motor.max_available_torque(motor_speed_approx)
        min_torque = motor.min_available_torque(motor_speed_approx)
        actual_motor_torque = max(min_torque, min(motor_torque_cmd, available_torque))

        power_needed_w = actual_motor_torque * motor_speed_approx
        power_delivered_w = battery.update(power_needed_w, dt)

        if power_needed_w > 0:
            power_ratio = power_delivered_w / power_needed_w
            actual_motor_torque *= power_ratio

        motor.update_temp(actual_motor_torque, dt)

        total_actual_torque = actual_engine_torque + actual_motor_torque
        wheel_torque = vehicle.motor_torque_to_wheel_torque(total_actual_torque)
        actual_speed = vehicle.update(wheel_torque, dt)

        results.append({
            "time_s": time_s,
            "target_speed_mps": target_speed_mps,
            "actual_speed_mps": actual_speed,
            "soc": battery.soc,
            "motor_temp_c": motor.temp_c,
            "engine_torque_nm": actual_engine_torque,
            "motor_torque_nm": actual_motor_torque,
        })

    return results


if __name__ == "__main__":
    drive_cycle = load_drive_cycle(CSV_PATH)
    print(f"Loaded {len(drive_cycle)} drive cycle points")
    print(f"First: {drive_cycle[0]}")
    print(f"Last: {drive_cycle[-1]}")


    print("\nRunning EV-priority scenario (SOC=0.70)...")
    results_ev = run_simulation(drive_cycle, initial_soc=0.70)
    print(f"Final SOC: {results_ev[-1]['soc']:.4f} | Final motor temp: {results_ev[-1]['motor_temp_c']:.1f} C")

    print("\nRunning blended/engine-priority scenario (SOC=0.25)...")
    results_blend = run_simulation(drive_cycle, initial_soc=0.25)
    print(f"Final SOC: {results_blend[-1]['soc']:.4f} | Final motor temp: {results_blend[-1]['motor_temp_c']:.1f} C")

    times = [r["time_s"] for r in results_ev]

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

    # Top: speed tracking (using the EV scenario as representative)
    axes[0].plot(times, [r["target_speed_mps"] for r in results_ev], label="Target (UDDS)", linewidth=1)
    axes[0].plot(times, [r["actual_speed_mps"] for r in results_ev], label="Actual", linewidth=1, alpha=0.8)
    axes[0].set_ylabel("Speed (m/s)")
    axes[0].set_title("Drive Cycle Tracking")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Middle: SOC comparison between scenarios
    axes[1].plot(times, [r["soc"] for r in results_ev], label="Start SOC=0.70 (EV-priority)")
    axes[1].plot(times, [r["soc"] for r in results_blend], label="Start SOC=0.25 (blended)")
    axes[1].axhline(0.30, color="gray", linestyle="--", linewidth=1, label="SOC_HIGH_THRESHOLD")
    axes[1].axhline(0.15, color="black", linestyle="--", linewidth=1, label="SOC_LOW_THRESHOLD")
    axes[1].set_ylabel("SOC")
    axes[1].set_title("Battery SOC vs. Time, by Starting Condition")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    # Bottom: engine vs motor torque split, blended scenario only
    axes[2].plot(times, [r["engine_torque_nm"] for r in results_blend], label="Engine torque")
    axes[2].plot(times, [r["motor_torque_nm"] for r in results_blend], label="Motor torque", alpha=0.8)
    axes[2].set_ylabel("Torque (Nm)")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_title("Engine/Motor Torque Split (blended scenario, SOC=0.25 start)")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    plot_path = Path(__file__).parent.parent / "data" / "sim_full_results.png"
    plt.savefig(plot_path, dpi=150)
    print(f"\nPlot saved to {plot_path}")
