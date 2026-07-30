import csv
from pathlib import Path

from controller.torque_split import TorqueSplitController

SIL_CSV_PATH = Path(__file__).parent.parent / "controller_c" / "sil_output.csv"
TOLERANCE = 1e-4  # acceptable floating-point difference


def load_sil_results(path: Path) -> list[dict]:
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "torque_demand_nm": float(row["torque_demand_nm"]),
                "soc": float(row["soc"]),
                "engine_torque_nm": float(row["engine_torque_nm"]),
                "motor_torque_nm": float(row["motor_torque_nm"]),
            })
    return rows


def run_equivalence_test():
    controller = TorqueSplitController()
    sil_results = load_sil_results(SIL_CSV_PATH)

    passed = 0
    failed = 0

    for row in sil_results:
        mil_engine, mil_motor = controller.split_torque(
            row["torque_demand_nm"], row["soc"]
        )

        engine_diff = abs(mil_engine - row["engine_torque_nm"])
        motor_diff = abs(mil_motor - row["motor_torque_nm"])

        if engine_diff <= TOLERANCE and motor_diff <= TOLERANCE:
            passed += 1
        else:
            failed += 1
            print(f"MISMATCH at torque={row['torque_demand_nm']}, soc={row['soc']}:")
            print(f"  MIL (Python): engine={mil_engine:.6f}, motor={mil_motor:.6f}")
            print(f"  SIL (C):      engine={row['engine_torque_nm']:.6f}, motor={row['motor_torque_nm']:.6f}")

    print(f"\n{passed}/{len(sil_results)} test cases passed")
    if failed == 0:
        print("MIL/SIL EQUIVALENCE CONFIRMED")
    else:
        print(f"{failed} MISMATCHES FOUND")

    return failed == 0


if __name__ == "__main__":
    run_equivalence_test()