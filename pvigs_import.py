import pandas as pd
import requests


def get_pvgis_hourly(
    lat, lon,
    startyear=2010,
    peakpower=1,     
    loss=14,       
    angle=0,       
    aspect=0,        
    ):


    url = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"

    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peakpower,
        "loss": loss,
        "angle": angle,
        "aspect": aspect,
        "trackingtype": 0,
        "pvcalculation":1,
        "localtime": 1,
        #"raddatabase": "PVGIS-SARAH3",
        "outputformat": "json",
    }

    filename="pvgis_hourly.csv"

    params["startyear"] = int(startyear)
    params["endyear"] = int(startyear)

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()
    hourly = data["outputs"]["hourly"]

    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M")
    df = df.set_index("time")
    df.to_csv(filename)

    return df



