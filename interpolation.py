import pandas as pd

def interpolate_15min():
    df = pd.read_csv("pvgis_hourly.csv")
    df["time"] = pd.to_datetime(df["time"])

    # Round time to nearest 15 min
    df["time"] = df["time"].dt.round("15min")

    # Set time as index
    df = df.set_index("time")

    # Resample to 15-min grid and interpolate all numeric columns
    df_15min = df.resample("15min").interpolate(method="linear")

    df_15min = df_15min.reset_index()
    df_15min.to_csv("pvgis_15min.csv", index=False)
    return df_15min





