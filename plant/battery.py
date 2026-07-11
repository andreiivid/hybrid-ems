class Battery:
    """
    Simplified equivalent-circuit battery model using coulomb counting.
    Reference specs: Jeep Wrangler 4xe (Stellantis media spec sheet).
    """

    PACK_CAPACITY_KWH = 15.0       # usable capacity
    NOMINAL_VOLTAGE = 330.0        # V, midpoint of 260-400V operating range
    MAX_DISCHARGE_POWER_KW = 70.0  # estimated — not published by Stellantis

    def __init__(self, initial_soc: float = 0.7):
        """
        initial_soc: starting state of charge, as a fraction (0.0 to 1.0)
        """
        self.soc = initial_soc
        self.capacity_as = (self.PACK_CAPACITY_KWH * 1000 / self.NOMINAL_VOLTAGE) * 3600
        # capacity in amp-seconds (amp-hours * 3600), so we can subtract
        # current * dt directly during coulomb counting

    def update(self, power_demand_w: float, dt: float) -> float:
        """
        Advance the battery state by one timestep.

        power_demand_w: power requested from the battery, in watts.
                         Positive = discharging (motor drawing power).
        dt: timestep duration, in seconds.

        Returns the actual power delivered, in watts (may be less than
        requested if it exceeds the max discharge power limit).
        """
        max_discharge_w = self.MAX_DISCHARGE_POWER_KW * 1000
        power_delivered_w = min(power_demand_w, max_discharge_w)

        current_a = power_delivered_w / self.NOMINAL_VOLTAGE
        charge_used_as = current_a * dt

        self.soc -= charge_used_as / self.capacity_as
        self.soc = max(0.0, min(1.0, self.soc))  # clamp between 0 and 1

        return power_delivered_w


if __name__ == "__main__":
    battery = Battery()
    print(f"Initial SOC: {battery.soc:.4f}")

    # Simulate 5 minutes (300s) of constant 20kW draw, in 60s steps
    for step in range(5):
        power_delivered = battery.update(power_demand_w=20000, dt=60)
        print(f"t={((step+1)*60):>4}s | delivered={power_delivered:>8.1f} W | SOC={battery.soc:.4f}")

    print()
    print("Testing power cap (requesting more than max discharge power):")
    battery2 = Battery()
    power_delivered = battery2.update(power_demand_w=100000, dt=1)  # requesting 100kW
    print(f"Requested: 100000 W | Delivered: {power_delivered} W")