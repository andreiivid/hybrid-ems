#include <stdio.h>

// Rule-based torque split controller -- C port of controller/torque_split.py
// for MIL/SIL equivalence verification.

#define SOC_HIGH_THRESHOLD 0.30
#define SOC_LOW_THRESHOLD  0.15

void split_torque(double torque_demand_nm, double soc,
                   double *engine_torque_nm, double *motor_torque_nm) {

    // Regen braking: engine can't regenerate, motor handles all of it
    if (torque_demand_nm < 0) {
        *engine_torque_nm = 0.0;
        *motor_torque_nm = torque_demand_nm;
        return;
    }

    // EV-only mode
    if (soc > SOC_HIGH_THRESHOLD) {
        *engine_torque_nm = 0.0;
        *motor_torque_nm = torque_demand_nm;
        return;
    }

    double engine_share;

    // Engine-priority mode
    if (soc <= SOC_LOW_THRESHOLD) {
        engine_share = 0.8;
    } else {
        // Blended zone: linear ramp from 0 to 0.8 as SOC drops
        double soc_range = SOC_HIGH_THRESHOLD - SOC_LOW_THRESHOLD;
        double soc_into_range = soc - SOC_LOW_THRESHOLD;
        double fraction_toward_low = 1.0 - (soc_into_range / soc_range);
        engine_share = 0.8 * fraction_toward_low;
    }

    *engine_torque_nm = torque_demand_nm * engine_share;
    *motor_torque_nm = torque_demand_nm * (1.0 - engine_share);
}

int main() {
    FILE *f = fopen("sil_output.csv", "w");
    if (f == NULL) {
        printf("Failed to open output file\n");
        return 1;
    }

    fprintf(f, "torque_demand_nm,soc,engine_torque_nm,motor_torque_nm\n");

    double torque_demands[] = {-150.0, -50.0, 0.0, 50.0, 100.0, 200.0, 300.0};
    double socs[] = {0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.60, 0.80};

    double engine_t, motor_t;
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 9; j++) {
            split_torque(torque_demands[i], socs[j], &engine_t, &motor_t);
            fprintf(f, "%.4f,%.4f,%.6f,%.6f\n", torque_demands[i], socs[j], engine_t, motor_t);
        }
    }

    fclose(f);
    printf("Wrote sil_output.csv\n");
    return 0;
}