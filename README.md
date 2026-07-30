# Hybrid Powertrain Energy Management Simulation

A Python simulation of a parallel hybrid vehicle's energy management system (EMS) — modeling battery, electric motor, engine, and vehicle dynamics, arbitrated by a rule-based torque-split controller. Built as a resume project targeting Electrified Powertrain Controls Engineer roles, with reference specs drawn from a real Stellantis production vehicle.

## Why this project

This project mirrors the core responsibilities of an EMS controls role: reading vehicle-level requirements, designing control strategies (torque management, energy management), and validating them against real drive-cycle data — without requiring a MATLAB/Simulink license.

## Architecture

```
Driver demand (UDDS drive cycle)
        |
        v
Torque Split Controller (SOC-aware, rule-based)
     /          \
Engine torque   Motor torque
     \          /
   Vehicle Dynamics --> Vehicle speed
        ^
        |
   Battery (SOC) <---> Motor (thermal + torque-speed limits)
```

- **Battery** (`plant/battery.py`) — coulomb-counting SOC model with separate discharge and regen-charge power limits.
- **Motor** (`plant/motor.py`) — torque-speed curve (constant torque below base speed, constant power above), plus a lumped thermal model with derating above a threshold temperature.
- **Engine** (`plant/engine.py`) — idealized instant-torque source with a max limit. Deliberately simple; see Simplifications below.
- **Vehicle** (`plant/vehicle.py`) — longitudinal dynamics (drive force, aerodynamic drag, rolling resistance) via Newton's second law, plus a final drive ratio converting shaft torque to wheel torque.
- **Controller** (`controller/torque_split.py`) — decides the engine/motor torque split based on battery SOC:
  - SOC > 30%: EV-only
  - SOC 15-30%: blended, engine share ramps linearly from 0% to 80%
  - SOC ≤ 15%: engine-priority (80% engine / 20% motor)
  - Regenerative braking always routes 100% to the motor (the engine cannot recover energy)
  - Thermal protection is not special-cased in the controller — it falls out of calling `Motor.max_available_torque()`, which already derates for temperature. Clean separation of concerns: the motor protects itself, the controller doesn't need to know why torque was limited.

## Reference vehicle specs

Modeled after the **Jeep Wrangler 4xe** (Stellantis), a real parallel hybrid. Specs sourced from Stellantis media spec sheets where available; estimated values are marked.

| Component | Spec | Value | Source |
|---|---|---|---|
| Battery | Usable capacity | 15 kWh | Stellantis (gross 17.3 kWh, ~87% usable) |
| Battery | Operating voltage | 260-400V (330V nominal used) | Stellantis media spec sheet |
| Battery | Max discharge power | 70 kW | **Estimated** — not published |
| Battery | Max charge (regen) power | 30 kW | **Estimated** — not published |
| Motor | Peak power / torque | 100 kW / 245 Nm | Stellantis (134 hp / 181 lb-ft) |
| Motor | Max regen torque | 150 Nm | **Estimated** |
| Engine | Peak power / torque | 201 kW / 400 Nm | Stellantis (270 hp / 295 lb-ft, standalone 2.0L turbo) |
| Vehicle | Curb weight | 2,302 kg | Stellantis (Sahara 4xe trim) |
| Vehicle | Drag coefficient | 0.58 | Widely cited in automotive press, not Stellantis-published |
| Vehicle | Frontal area | 3.0 m² | Estimated, typical for vehicle class |

## Known simplifications

Documented explicitly because a real EMS engineer would want to know the model's limits before trusting its output:

- **Battery**: fixed nominal voltage (no voltage sag under load); no temperature effects on capacity or resistance.
- **Motor**: crude lumped thermal model (heating proportional to load fraction, simple Newtonian cooling) — not derived from real thermal mass/cooling-system data.
- **Engine**: no combustion dynamics — instant torque response, no throttle lag, no idle behavior, no fuel consumption tracking.
- **Vehicle**: rolling resistance treated as constant (real rolling resistance varies with speed); no road grade.
- **Controller**: linear SOC-based blending is a reasonable first-pass strategy, not an optimization-based approach (e.g., no dynamic programming or equivalent consumption minimization strategy, which real production EMS controllers often use).
- **Battery power scaling**: when the battery can't fully deliver requested power, torque is scaled down linearly — a simplification of real electrical behavior.

## Results

Simulated against the EPA's official UDDS (Urban Dynamometer Driving Schedule) drive cycle, comparing two starting battery conditions:

- **SOC=0.70 start** (EV-priority range): controller stays in EV-only mode the entire cycle, SOC drifts from 0.70 to 0.59.
- **SOC=0.25 start** (blended range): controller immediately blends engine and motor torque, SOC drain slows dramatically compared to the EV-only case (0.25 to ~0.21, then flattens) as the engine picks up load.
- Regenerative braking is confirmed active on every deceleration event in both scenarios — motor torque goes negative, engine torque stays at zero, exactly as designed.

See `data/sim_full_results.png` for the full comparison plot (speed tracking, SOC vs. time by scenario, and engine/motor torque split).

## Project structure

```
hybrid-ems/
├── plant/              # Physical system models
│   ├── battery.py
│   ├── motor.py
│   ├── engine.py
│   └── vehicle.py
├── controller/
│   └── torque_split.py # Rule-based EMS controller
├── controller_c/        # Hand-ported C version (MIL/SIL verification)
├── sim/
│   ├── load_drive_cycle.py
│   └── run_sim.py       # Full simulation loop
├── test/                # MIL/SIL equivalence tests
└── data/                # Drive cycle data and output plots
```

## Running it

```bash
python3 -m venv venv
source venv/bin/activate
pip install matplotlib numpy scipy

python3 sim/load_drive_cycle.py   # parses UDDS data, generates plot
python3 -m sim.run_sim            # runs full simulation, generates comparison plot
```

## Running the MIL/SIL equivalence test

```bash
cd controller_c && gcc -o torque_split torque_split.c && ./torque_split && cd ..
python3 -m test.test_equivalence
```

## MIL/SIL Verification

The rule-based controller was hand-ported from Python (`controller/torque_split.py`) to C (`controller_c/torque_split.c`) to mirror a real MIL/SIL verification workflow. An automated test (`test/test_equivalence.py`) sweeps 63 combinations of torque demand and SOC through both implementations and confirms outputs match within floating-point tolerance — all 63 cases pass.



