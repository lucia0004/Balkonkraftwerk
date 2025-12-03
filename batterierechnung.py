
import pandas as pd
from demandlib import bdew
import holidays as holidays
import plotly.express as px


#region Simulation

def simulation(df, battery_capacity_kWh, eta_charge, eta_discharge, price):

    df['SOC'] = 0.0
    df['Bat_Charge'] = 0.0
    df['Bat_Discharge'] = 0.0
    df['Bat_Energy'] = 0.0

    df['solar_energy_to_consume'] = 0.0
    df['solar_energy_to_battery'] = 0.0
    df['savings'] = 0.0

    if battery_capacity_kWh == 0 or battery_capacity_kWh is None:

        df['solar_energy_to_consume'] = df[['h0_dyn', 'solar_kWh']].min(axis=1)
        df['solar_energy_to_battery'] = 0.0

        df['Import'] = (df['h0_dyn'] - df['solar_kWh']).clip(lower=0)

        df['savings'] = price * (df['solar_energy_to_consume'])

        return df

    battery = Battery(
        capacity_kWh=battery_capacity_kWh,
        charge_eff=eta_charge,
        discharge_eff=eta_discharge
    )

    soc_list = []
    grid_import = []
    battery_charge = []
    battery_discharge = []
    battery_energy = []
    solar_to_consume = []
    solar_to_battery = []

    for load, pv in zip(df["h0_dyn"], df["solar_kWh"]):

        direct_solar = min(load, pv)
        solar_to_consume.append(direct_solar)

        net_load = load - pv

        if net_load > 0:
            delivered_energy = battery.discharge(net_load)
            battery_discharge.append(delivered_energy)
            grid_import.append(net_load - delivered_energy)
            battery_charge.append(0)

            solar_to_battery.append(0)

        else:
            surplus_energy = -net_load
            stored_energy = battery.charge(surplus_energy)

            battery_charge.append(stored_energy)
            battery_discharge.append(0)
            grid_import.append(0)

            solar_to_battery.append(stored_energy)

        soc_list.append(battery.soc)
        battery_energy.append(battery.get_energy_available())

    df['SOC'] = soc_list
    df['Bat_Charge'] = battery_charge
    df['Bat_Discharge'] = battery_discharge
    df['Bat_Energy'] = battery_energy
    df['Import'] = grid_import

    df['solar_energy_to_consume'] = solar_to_consume
    df['solar_energy_to_battery'] = solar_to_battery
    df['savings'] = price * (df['solar_energy_to_consume']+df['Bat_Discharge'])

    return df

#endregion




#region Definition Batterie

class Battery:
    def __init__(self, capacity_kWh, charge_eff, discharge_eff):
        self.capacity = capacity_kWh
        self.soc = 0.05
        self.charge_eff = charge_eff 
        self.discharge_eff = discharge_eff
        self.min_soc = 0.05


    def charge(self, energy_kWh):
        effective_energy = energy_kWh * self.charge_eff
        capacity_left = (1 - self.soc) * self.capacity
        energy_into_battery = min(effective_energy, capacity_left)
        self.soc += energy_into_battery / self.capacity

        return energy_into_battery


    def discharge(self, energy_kWh):
        required_from_battery = energy_kWh / self.discharge_eff
        usable_energy = (self.soc - self.min_soc) * self.capacity
        usable_energy = max(usable_energy, 0)

        if usable_energy >= required_from_battery:
            self.soc -= required_from_battery / self.capacity
            delivered_energy = energy_kWh
        else:
            delivered_energy = usable_energy * self.discharge_eff
            self.soc = self.min_soc

        return delivered_energy


    def get_energy_available(self):
        return self.soc * self.capacity
    
    def __repr__(self):
        return (
            f"Battery SOC: {self.soc:.2%}, "
            f"Energy: {self.get_energy_available():.2f} kWh, "
            f"Charge Eff: {self.charge_eff*100:.1f}%, "
            f"Discharge Eff: {self.discharge_eff*100:.1f}%"
        )

    
#endregion




