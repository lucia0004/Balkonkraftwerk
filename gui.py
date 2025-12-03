import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pvigs_import import get_pvgis_hourly
from interpolation import interpolate_15min
from verbrauchsdaten import stromdaten
from batterierechnung import simulation


#region Eingabeparameter

st.title("Simulation eines Balkonkraftwerkes")
st.markdown("Gib in den folgenden Feldern die Daten für deine PV-Anlage ein:")

st.header("🔆 PV Anlage")

with st.container():
    st.markdown('<h3 style="font-size:20px; margin-bottom:5px;">📍 Standort des Balkonkraftwerks</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ko_lat = st.number_input("Breitengrad", value=48.3667, format="%.4f")
    with col2:
        ko_lon = st.number_input("Längengrad", value=10.9000, format="%.4f")

with st.container():
    st.markdown('<h3 style="font-size:20px; margin-bottom:5px;">⚡Technische Daten der PV-Anlage</h3>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        pv_peakpower = st.number_input("Maximale Leistung (kWp)", value=1.0)
        azimuth = st.slider("Azimuth (°)", min_value=-90, max_value=90, value=0)
    with col4:
        system_loss = st.number_input("Systemverlust (%)", value=14)
        slope = st.slider("Neigung (°)", min_value=0, max_value=90, value=60)

st.markdown('<h3 style="font-size:20px; margin-bottom:5px;">📅 Referenzjahr für Wetterdaten</h3>', unsafe_allow_html=True)
year = st.number_input(
    "2005–2023", 
    min_value=2005, max_value=2023, value=2017
)


st.header("🔋 Batterie")

has_battery = st.radio("Batterie vorhanden?", ("Ja", "Nein"))

battery_capacity = 0
eta_c = 0
eta_d = 0

if has_battery == "Ja":
    battery_capacity = st.number_input("Kapazität der Batterie (kWh)", value=2.7, step=0.1)
    col5, col6 = st.columns(2)
    with col5:
        eta_c = st.slider("Wirkungsgrad Ladevorgang", min_value=0.5, max_value=1.0, value=0.9)
    with col6:
        eta_d = st.slider("Wirkungsgrad Entladevorgang", min_value=0.5, max_value=1.0, value=0.9)
else:
    st.info("Keine Batterie ausgewählt. Batterieparameter werden ignoriert.")

st.header("🔌Verbrauch")
energy_consumption = st.number_input("Stromverbrauch pro Jahr in kWh", value=2500)    

st.header("💶 Kosten")

col7, col8 = st.columns(2)
with col7:
    costs_kWh = st.number_input("Preis pro kWh", value=0.30)
with col8:
    cost_PV = st.number_input("Preis der gesamten Anlage in €", value=1130)


if st.button("▶ Run Simulation"):
    with st.spinner("Simulation running"):
        get_pvgis_hourly(
            lat=ko_lat,
            lon=ko_lon,
            startyear=year,
            peakpower=pv_peakpower,
            loss=system_loss,
            angle=slope,
            aspect=azimuth
        )
        interpolate_15min()
        energy = stromdaten(year=year, energy_year=energy_consumption)
        data = simulation(
            df=energy, 
            battery_capacity_kWh=battery_capacity,
            eta_charge=eta_c,
            eta_discharge=eta_d,
            price=costs_kWh
        )

    st.session_state["data"] = data
    st.success("Simulation complete!")

#endregion


#region Ergebnisse

if "data" in st.session_state:

    data = st.session_state["data"]

    demand=data['h0_dyn'].sum()
    solar = data['solar_kWh'].sum()
    consumed_from_solar = data['solar_energy_to_consume'].sum()
    battery_charge = data['Bat_Charge'].sum()
    battery_discharge = data['Bat_Discharge'].sum()
    Import = data['Import'].sum()
    saving = data['savings'].sum()

    st.header("PV-Erträge")

    st.metric("Jährlicher PV-Ertrag", f"{solar:.1f} kWh")

    balkonkraftwerk = consumed_from_solar + battery_discharge
    eingespeist = solar - balkonkraftwerk
    anteil = balkonkraftwerk/solar*100

    col1, col2 = st.columns(2)
    with col1:
        st.metric("davon selbst genutzt:", f"{balkonkraftwerk:.1f} kWh")
    with col2:
        st.metric("davon unvergütet eingespeist:", f"{eingespeist:.1f} kWh")


    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=['Direktverbrauch', 'Ladung Batterie', 'Netzeinspeisung'],
            values=[consumed_from_solar, battery_charge, eingespeist],
            hole=0.3,
            marker=dict(colors=['#FDB813', '#2CA02C', '#1F77B4'])
        )])
        fig.update_layout(
            title=dict(
            text='Nutzung des erzeugten Stroms'),
            template='plotly_dark',
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.7,
                xanchor="right",
                x=0 
            ),
            margin=dict(r=30)
        )
        st.plotly_chart(fig)
    with col2:
        st.markdown("<div style='margin-top: 160px;'></div>", unsafe_allow_html=True)
        st.metric("Eigenverbrauchsanteil", f"{anteil:.1f} %")



    st.subheader("Visualisierung einer Woche")

    date_input = str(year)+"-01-01"

    week_start = st.date_input("Start der Woche", pd.to_datetime(date_input))
    week_start = pd.Timestamp(week_start)
    week_end   = week_start + pd.Timedelta(days=7)

    to_watt = 1000 / 0.25

    data_filtered = data.loc[week_start:week_end]
    selected = data_filtered[["h0_dyn", "solar_kWh"]]
    in_watt = selected * to_watt

    in_watt = in_watt.rename(columns={
    "h0_dyn": "Stromverbrauch",
    "solar_kWh": "PV Produktion"
    })

    fig = px.line(
        in_watt,
        labels={
            "value": "Leistung (W)",
            "index": "",
            "h0_dyn": "Stromverbrauch",
            "solar_kWh": "PV Produktion"
        },
        color_discrete_map={
        "Stromverbrauch": "#001AFF",  
        "PV Produktion": "#D1BF00"    
        }
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        title="Stromverbrauch und PV-Produktion innerhalb einer Woche",
        legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,        
        xanchor="center",
        x=0.5              
        ),
        legend_title_text="" 
    )

    st.plotly_chart(fig)


    fig = go.Figure(data=[go.Pie(
        labels=['Direkverbrauch PV', 'Entnahme Batterie', 'Netzbezug'],
        values=[consumed_from_solar, battery_discharge, Import],
        hole=0.3,
        marker=dict(colors=['#FDB813', '#2CA02C', '#1F77B4'])
    )])
    fig.update_layout(
        title=dict(
        text='Herkunft des jährlichen Strombedarfs'),
        template='plotly_dark',
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.7,
            xanchor="right",
            x=0 
        ),
        margin=dict(r=30)
    )

    col1, col2 = st.columns(2)
    selfsuf = balkonkraftwerk/demand*100

    with col1:
        st.plotly_chart(fig, use_container_width=True)
   
    with col2: 
        st.markdown("<div style='margin-top: 160px;'></div>", unsafe_allow_html=True)
        st.metric("Autarkiegrad", f"{selfsuf:.1f} %")

        
    st.subheader("Finanzielle Ergebnisse")

    st.metric("Einsparung pro Jahr:", f"{data["savings"].sum():.2f} €")


    data_forecast = data.copy()
    data_forecast.index = pd.to_datetime(data_forecast.index)
    freq = data_forecast.index.freq or pd.infer_freq(data_forecast.index)
    n = len(data_forecast)
    years_to_generate = 11 
    new_index = pd.date_range(
        start="2026-01-01",
        periods=n * years_to_generate,
        freq=freq
    )

    data_repeated = pd.concat([data_forecast] * years_to_generate, ignore_index=True)
    data_repeated.index = new_index
    data_forecast = data_repeated

    monthly_savings = data_forecast["savings"].resample("ME").sum() 
    total_savings = monthly_savings.cumsum()

    total_savings_with_cost = total_savings - cost_PV
    
    mask = total_savings_with_cost >= 0

    if mask.any():
        roi_idx = mask.idxmax()  
        roi_str = roi_idx.strftime("%b-%Y") 
        surplus_10y = total_savings_with_cost.iloc[119]
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=total_savings_with_cost.index,
                y=total_savings_with_cost.values,
                mode="lines+markers",
                name="Kumulierte Einsparungen"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[total_savings_with_cost.index[0], total_savings_with_cost.index[-1]],
                y=[0, 0],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="ROI (0 €)"
            )
        )

        fig.update_layout(
            title="Installation des Balkonkraftwerks ab 2026 (Prognose)",
            xaxis_title="Monat",
            yaxis_title="Kumulierte Einsparungen (€)",
            template="plotly_dark",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,  
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=50, b=80) 
        )


        col1, col2 = st.columns([3, 1])

        with col1:
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
            st.write(f"**Investition:** {cost_PV} €")
            st.write(f"**ROI erreicht:** {roi_str}")
            st.write(f"**Gewinn nach 10 Jahren:** {surplus_10y:,.2f} €")
    else:
        roi_idx = None         
        roi_str = "Balkonkraftwerk nicht rentabel"
        st.write(f"**Investition:** {cost_PV} €")
        st.write(f"{roi_str}")


#endregion
