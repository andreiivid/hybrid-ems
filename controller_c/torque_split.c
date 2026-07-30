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
    double engine_t, motor_t;
    double test_socs[] = {0.70, 0.50, 0.30, 0.25, 0.20, 0.15, 0.10};
    int n = 7;

    printf("Torque split across SOC range, demand=200 Nm:\n");
    for (int i = 0; i < n; i++) {
        split_torque(200.0, test_socs[i], &engine_t, &motor_t);
        printf("SOC=%.2f | engine=%6.1f Nm | motor=%6.1f Nm\n", test_socs[i], engine_t, motor_t);
    }

    printf("\nRegen braking test, demand=-100 Nm, SOC=0.5:\n");
    split_torque(-100.0, 0.5, &engine_t, &motor_t);
    printf("engine=%.1f Nm | motor=%.1f Nm\n", engine_t, motor_t);

    return 0;
}