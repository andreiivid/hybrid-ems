class TorqueSplitController:
    """
    Rule-based torque split controller for a parallel hybrid powertrain.

    Strategy:
      - SOC above SOC_HIGH_THRESHOLD: EV-only (motor handles all torque)
      - SOC between SOC_LOW_THRESHOLD and SOC_HIGH_THRESHOLD: blended,
        engine share increases linearly as SOC drops
      - SOC at or below SOC_LOW_THRESHOLD: engine-priority, motor fills
        the gap up to what the engine can't cover
      - Regen braking (negative torque demand) always routes to the
        motor -- the engine cannot brake/regenerate
      - Thermal protection is NOT handled here -- it falls out naturally
        from calling Motor.max_available_torque(), which already
        derates based on temperature
    """

    SOC_HIGH_THRESHOLD = 0.30  # above this, EV-only
    SOC_LOW_THRESHOLD = 0.15   # at/below this, engine-priority

    def __init__(self):
        pass

    def split_torque(self, torque_demand_nm: float, soc: float) -> tuple[float, float]:
        """
        Decides how to split a torque demand between engine and motor.

        torque_demand_nm: total torque requested (positive = drive,
                           negative = regen braking)
        soc: current battery state of charge, 0.0 to 1.0

        Returns (engine_torque_cmd_nm, motor_torque_cmd_nm) -- these are
        REQUESTS, not guaranteed delivery. The plant blocks (Engine,
        Motor) will clamp them to what's actually achievable.
        """
        # Regen braking: engine can't regenerate, so motor handles all of it
        if torque_demand_nm < 0:
            return 0.0, torque_demand_nm

        # EV-only mode: SOC is healthy, no need to burn fuel
        if soc > self.SOC_HIGH_THRESHOLD:
            return 0.0, torque_demand_nm

        # Engine-priority mode: SOC is critically low, lean on engine
        if soc <= self.SOC_LOW_THRESHOLD:
            engine_share = 0.8
        else:
            # Blended zone: engine share ramps from 0 (at SOC_HIGH_THRESHOLD)
            # to 0.8 (at SOC_LOW_THRESHOLD) as SOC drops
            soc_range = self.SOC_HIGH_THRESHOLD - self.SOC_LOW_THRESHOLD
            soc_into_range = soc - self.SOC_LOW_THRESHOLD
            fraction_toward_low = 1.0 - (soc_into_range / soc_range)
            engine_share = 0.8 * fraction_toward_low

        engine_torque_cmd = torque_demand_nm * engine_share
        motor_torque_cmd = torque_demand_nm * (1.0 - engine_share)

        return engine_torque_cmd, motor_torque_cmd


if __name__ == "__main__":
    controller = TorqueSplitController()

    print("Torque split across SOC range, demand=200 Nm:")
    for soc in [0.7, 0.5, 0.30, 0.25, 0.20, 0.15, 0.10]:
        engine_cmd, motor_cmd = controller.split_torque(200, soc)
        print(f"SOC={soc:.2f} | engine={engine_cmd:>6.1f} Nm | motor={motor_cmd:>6.1f} Nm")

    print()
    print("Regen braking test, demand=-100 Nm, SOC=0.5:")
    engine_cmd, motor_cmd = controller.split_torque(-100, 0.5)
    print(f"engine={engine_cmd} Nm | motor={motor_cmd} Nm")