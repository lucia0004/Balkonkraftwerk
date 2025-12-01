import pandas as pd
from demandlib import bdew
import holidays as holidays

def stromdaten(year=2010,energy_year=3000):
    # Stromverbrauchsdaten
    de_holidays = holidays.Germany(year)
    e_slp = bdew.ElecSlp(year=year, holidays=de_holidays)
    df = e_slp.get_scaled_power_profiles({"h0_dyn": energy_year}, conversion_factor=1)

    # Wetterdaten
    weather_path = "pvgis_15min.csv"
    weather = pd.read_csv(weather_path)
    weather['time'] = pd.to_datetime(weather['time'])
    weather.set_index('time', inplace=True)
    weather['solar_kWh'] = weather["P"]/1000*0.25

    # Daten kombiniert
    energy = pd.concat([df, weather['solar_kWh']], axis=1)
    energy = energy.fillna(0)

    return energy