class Engine:
    """
    Simplified idealized engine model: instant torque response up to a
    max limit, no combustion dynamics (throttle lag, idle, fuel maps).
    This is a deliberate simplification -- the EMS controller's job is to
    decide how much torque to request from engine vs. motor, not to model
    combustion physics.

    Reference specs: Jeep Wrangler 4xe 2.0L turbo I4 (standalone engine
    output, before hybrid combination) -- Stellantis media spec sheet.
    """

    MAX_TORQUE_NM = 400.0  # converted from 295 lb-ft

    def __init__(self):
        pass

    def available_torque(self) -> float:
        """
        Returns max torque the engine can produce right now.
        No speed-dependent curve for this simplified model -- treated as
        flat up to max, which is a reasonable EMS-level abstraction.
        """
        return self.MAX_TORQUE_NM

    def command_torque(self, torque_cmd_nm: float) -> float:
        """
        Requests a torque from the engine; returns what it actually
        delivers (clamped to available torque, floor of 0 -- no engine
        braking/regen modeled).
        """
        return max(0.0, min(torque_cmd_nm, self.available_torque()))


if __name__ == "__main__":
    engine = Engine()
    print(f"Max torque: {engine.MAX_TORQUE_NM} Nm")
    print(f"Requesting 200 Nm: delivered {engine.command_torque(200)} Nm")
    print(f"Requesting 500 Nm (over max): delivered {engine.command_torque(500)} Nm")
    print(f"Requesting -50 Nm (invalid): delivered {engine.command_torque(-50)} Nm")