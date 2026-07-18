class Vehicle:
    """
    Simplified longitudinal vehicle dynamics model.
    Reference: Jeep Wrangler 4xe (Sahara 4xe trim, Stellantis media spec sheet
    for mass; drag/frontal area/rolling resistance are industry-typical
    estimates, not manufacturer-published).
    """

    MASS_KG = 2302.0
    DRAG_COEFFICIENT = 0.58
    FRONTAL_AREA_M2 = 3.0
    ROLLING_RESISTANCE_COEFF = 0.015
    WHEEL_RADIUS_M = 0.4

    AIR_DENSITY_KGM3 = 1.225
    GRAVITY_MS2 = 9.81

    FINAL_DRIVE_RATIO = 8.5  # typical for this vehicle class, motor RPM -> wheel RPM

    def __init__(self, initial_speed_ms: float = 0.0):
        self.speed_ms = initial_speed_ms

    def update(self, wheel_torque_nm: float, dt: float) -> float:
        """
        Advance vehicle speed by one timestep given total wheel torque.

        wheel_torque_nm: combined torque at the wheels (engine + motor,
                          already combined upstream), in Nm.
        dt: timestep duration, in seconds.

        Returns the updated speed, in m/s.
        """
        drive_force_n = wheel_torque_nm / self.WHEEL_RADIUS_M

        drag_force_n = 0.5 * self.AIR_DENSITY_KGM3 * self.DRAG_COEFFICIENT \
            * self.FRONTAL_AREA_M2 * self.speed_ms ** 2

        rolling_force_n = self.ROLLING_RESISTANCE_COEFF * self.MASS_KG * self.GRAVITY_MS2

        # Resistive forces only apply while moving; ignore direction for now
        if self.speed_ms <= 0:
            rolling_force_n = 0.0

        net_force_n = drive_force_n - drag_force_n - rolling_force_n
        acceleration_ms2 = net_force_n / self.MASS_KG

        self.speed_ms += acceleration_ms2 * dt
        self.speed_ms = max(0.0, self.speed_ms)  # no reverse rolling for now

        return self.speed_ms
    
    def motor_torque_to_wheel_torque(self, motor_torque_nm: float) -> float:
        """
        Converts torque at the motor/engine shaft to torque at the wheels,
        accounting for the final drive gear ratio.
        """
        return motor_torque_nm * self.FINAL_DRIVE_RATIO


if __name__ == "__main__":
    vehicle = Vehicle()
    print(f"Mass: {vehicle.MASS_KG} kg")

    print()
    print("Applying 200 Nm constant wheel torque:")
    for step in range(10):
        speed = vehicle.update(wheel_torque_nm=200, dt=1)
        print(f"t={step+1:>2}s | speed={speed:>6.2f} m/s ({speed*2.237:>5.1f} mph)")

    print()
    print("Testing motor-to-wheel torque conversion:")
    wheel_torque = vehicle.motor_torque_to_wheel_torque(motor_torque_nm=200)
    print(f"Motor torque=200 Nm -> Wheel torque={wheel_torque} Nm")