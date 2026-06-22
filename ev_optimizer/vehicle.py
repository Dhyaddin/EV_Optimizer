"""Physical model of the electric vehicle and the charging physics.

A single `Vehicle` instance owns every battery/energy/charging calculation so
that the three algorithms share IDENTICAL physics (no duplicated formulas).
"""
from dataclasses import dataclass


@dataclass
class Vehicle:
    # Defaults model a common Malaysian EV (e.g. BYD Atto 3 Extended Range).
    battery_cap_kwh: float = 60.0    # usable battery capacity (kWh)
    max_dc_kw: float = 80.0          # vehicle's maximum DC charging intake (kW)
    base_kwh_per_km: float = 0.18    # baseline highway consumption (kWh/km)
    avg_speed_kmh: float = 90.0      # free-flow average highway speed (km/h)
    reserve_frac: float = 0.15       # range-anxiety floor: never below 15% SoC
    knee_frac: float = 0.80          # charging power tapers above 80% SoC
    soc_step_kwh: float = 3.0        # SoC discretisation step (5% of 60 kWh)

    # ---- derived limits ----
    @property
    def reserve_kwh(self) -> float:
        return self.reserve_frac * self.battery_cap_kwh

    @property
    def knee_kwh(self) -> float:
        return self.knee_frac * self.battery_cap_kwh

    # ---- driving physics ----
    def edge_energy(self, distance_km: float, traffic_factor: float) -> float:
        """Energy consumed on a leg; congestion raises consumption."""
        return self.base_kwh_per_km * distance_km * traffic_factor

    def edge_drive_hours(self, distance_km: float, traffic_factor: float) -> float:
        """Driving time on a leg; congestion slows the effective speed."""
        return distance_km / (self.avg_speed_kmh / traffic_factor)

    # ---- charging physics (non-linear taper) ----
    def effective_power(self, rated_kw: float, soc_kwh: float) -> float:
        """Effective charging power, capped by the vehicle and tapered past the knee."""
        p = min(rated_kw, self.max_dc_kw)
        if soc_kwh <= self.knee_kwh:
            return p
        frac = (self.battery_cap_kwh - soc_kwh) / (self.battery_cap_kwh - self.knee_kwh)
        return max(p * frac, 5.0)        # floor avoids div-by-zero near 100%

    def charge_time_hours(self, rated_kw: float, b_start: float, b_end: float) -> float:
        """Time to raise SoC from b_start->b_end (kWh), integrating the taper."""
        if b_end <= b_start:
            return 0.0
        hours, step, b = 0.0, 0.25, b_start
        while b < b_end:
            chunk = min(step, b_end - b)
            hours += chunk / self.effective_power(rated_kw, b)
            b += chunk
        return hours

    # ---- SoC grid helpers (used by DP and A*) ----
    def quantise_down(self, soc_kwh: float) -> float:
        """Snap an SoC to the grid, rounding DOWN (conservative on battery)."""
        return int(soc_kwh / self.soc_step_kwh) * self.soc_step_kwh

    def soc_levels(self):
        """All discrete SoC levels from 0 to full capacity."""
        levels, L = [], 0.0
        while L <= self.battery_cap_kwh + 1e-9:
            levels.append(round(L, 6))
            L += self.soc_step_kwh
        return levels

    def pct(self, kwh: float) -> float:
        return 100.0 * kwh / self.battery_cap_kwh
