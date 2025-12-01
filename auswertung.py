def auswertung(datafile):
    data=datafile
    demand=data['h0_dyn'].sum()
    solar = data['solar_kWh'].sum()
    consumed_from_solar = data['solar_energy_to_consume'].sum()
    battery_charge = data['Bat_Charge'].sum()
    battery_discharge = data['Bat_Discharge'].sum()
    Import = data['Import'].sum()
    saving = data['savings'].sum()

    result = [demand,solar,consumed_from_solar,battery_charge,battery_discharge,Import,saving]


    return result

