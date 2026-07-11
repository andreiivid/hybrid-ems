class Motor:
    """
    Simplified electric motor model with torque-speed limiting and
    thermal derating. Reference specs: Jeep Wrangler 4xe motor-generator
    unit (Stellantis media spec sheet): 134 hp / 181 lb-ft.
    """

    MAX_TORQUE_NM = 245.0      # peak torque, converted from 181 lb-ft
    MAX_POWER_W = 100000.0     # peak power, converted from 134 hp
    BASE_SPEED_RADS = MAX_POWER_W / MAX_TORQUE_NM
    # ^ the motor speed at which peak torque and peak power intersect

    MAX_TEMP_C = 150.0         # thermal shutdown-adjacent limit
    DERATE_START_TEMP_C = 120.0  # torque starts tapering above this
    AMBIENT_TEMP_C = 25.0

    def __init__(self, initial_temp_c: float = 25.0):
        self.temp_c = initial_temp_c

    def max_available_torque(self, speed_rads: float) -> float:
        if speed_rads <= 0:
            base_available = self.MAX_TORQUE_NM
        else:
            power_limited_torque = self.MAX_POWER_W / speed_rads
            base_available = min(self.MAX_TORQUE_NM, power_limited_torque)

        return base_available * self.thermal_derate_factor()
    
    def update_temp(self, torque_nm: float, dt: float) -> None:
        """
        Very simplified lumped thermal model: heating is proportional to
        how hard the motor is working (torque as a fraction of max),
        cooling pulls temp back toward ambient over time.
        """
        load_fraction = abs(torque_nm) / self.MAX_TORQUE_NM
        heating_rate = load_fraction * 5.0       # deg C per second at full load
        cooling_rate = (self.temp_c - self.AMBIENT_TEMP_C) * 0.01  # Newton cooling

        self.temp_c += (heating_rate - cooling_rate) * dt
        self.temp_c = max(self.AMBIENT_TEMP_C, self.temp_c)

    def thermal_derate_factor(self) -> float:
        """
        Returns a 0-1 multiplier applied to available torque based on temp.
        1.0 = no derating, below DERATE_START_TEMP_C.
        0.0 = fully derated, at or above MAX_TEMP_C.
        """
        if self.temp_c <= self.DERATE_START_TEMP_C:
            return 1.0
        if self.temp_c >= self.MAX_TEMP_C:
            return 0.0

        derate_range = self.MAX_TEMP_C - self.DERATE_START_TEMP_C
        temp_into_range = self.temp_c - self.DERATE_START_TEMP_C
        return 1.0 - (temp_into_range / derate_range)


if __name__ == "__main__":
    motor = Motor()
    print(f"Max torque: {motor.MAX_TORQUE_NM} Nm")
    print(f"Max power: {motor.MAX_POWER_W} W")
    print(f"Base speed: {motor.BASE_SPEED_RADS:.2f} rad/s ({motor.BASE_SPEED_RADS * 9.5493:.0f} RPM)")
    print(f"Initial temp: {motor.temp_c} C")
    print()
    for speed in [0, 100, motor.BASE_SPEED_RADS, 600, 800]:
        available = motor.max_available_torque(speed)
        print(f"Speed={speed:>7.1f} rad/s | Max available torque={available:>7.1f} Nm")

    print()
    print("Running motor at max torque, speed=200 rad/s, watching thermal derate:")
    motor2 = Motor()
    for step in range(30):
        available = motor2.max_available_torque(200)
        motor2.update_temp(torque_nm=available, dt=10)
        if step % 5 == 0:
            print(f"t={step*10:>4}s | temp={motor2.temp_c:>6.1f} C | available_torque={available:>6.1f} Nm")