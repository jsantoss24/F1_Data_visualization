import os
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Cargar los datos
ruta_base = "./data"
results = pd.read_csv(f"{ruta_base}/results.csv")
drivers = pd.read_csv(f"{ruta_base}/drivers.csv")
races = pd.read_csv(f"{ruta_base}/races.csv")
constructors = pd.read_csv(f"{ruta_base}/constructors.csv")
constructor_results = pd.read_csv(f"{ruta_base}/constructor_results.csv")
lap_times = pd.read_csv(f"{ruta_base}/lap_times.csv")
pit_stops = pd.read_csv(f"{ruta_base}/pit_stops.csv")
circuits = pd.read_csv(f"{ruta_base}/circuits.csv")

# Preparar los datos
results_cleaned = results.merge(drivers, on="driverId").merge(races, on="raceId")
results_cleaned = results_cleaned[(results_cleaned["grid"] > 0) & (results_cleaned["positionOrder"] > 0)]

constructor_results_teams = constructor_results.merge(constructors[["constructorId", "name"]], on="constructorId", how="inner")
results_teams = constructor_results_teams.merge(races[["raceId", "year"]], on="raceId", how="inner")
results_drivers_races = results.merge(drivers, on="driverId").merge(races, on="raceId")

# Función para convertir milisegundos a formato "min:seg,ms"
def format_time(milliseconds):
    minutes = milliseconds // 60000
    seconds = (milliseconds % 60000) // 1000
    millis = milliseconds % 1000
    return f"{minutes}:{seconds:02d},{millis:03d}"

# Crear la aplicación Dash
app = Dash(__name__)

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Análisis de Fórmula 1", style={"textAlign": "center"}),

    # Selector de Año
    html.Label("Selecciona el Año:"),
    dcc.Dropdown(
        id="year-selector",
        options=sorted([{"label": year, "value": year} for year in results_cleaned["year"].unique()], key=lambda x: x["value"]),
        value=2021,
        clearable=False
    ),

    # Selector de Circuito
    html.Label("Selecciona el Circuito:"),
    dcc.Dropdown(
        id="circuit-selector",
        options=[{"label": name, "value": name} for name in races["name"].unique()],
        value=None,
        placeholder="Selecciona un circuito"
    ),

    # Gráficos
    html.Div([
        html.H2("1. Rendimiento de Pilotos por Temporadas"),
        dcc.Graph(id="pilot-performance"),
    ]),

    html.Div([
        html.H2("2. Consistencia de Pilotos Durante una Temporada"),
        dcc.Graph(id="pilot-consistency"),
    ]),

    html.Div([
        html.H2("3. Impacto de la Clasificación en los Resultados Finales"),
        dcc.Graph(id="classification-impact"),
    ]),

    html.Div([
        html.H2("4. Impacto de las Paradas en Boxes"),
        dcc.Graph(id="pitstop-impact"),
    ]),

    html.Div([
        html.H2("5. Rendimiento de Equipos por Temporada"),
        dcc.Graph(id="team-performance"),
    ]),

    html.Div([
        html.H2("6. Evolución de los Puntos de los Pilotos por Carrera"),
        dcc.Graph(id="race-points-evolution"),
    ]),

    html.Div([
        html.H2("7. Mejores Tiempos por Vuelta"),
        dcc.Graph(id="best-lap-times"),
    ]),

    html.Div([
        html.H2("8. Circuitos en el Mapa"),
        dcc.Graph(id="circuit-map"),
    ]),

    html.Div([
        html.H2("9. Distribución de Puntos por Piloto"),
        dcc.Graph(id="points-pie-chart"),
    ]),

    html.Div([
        html.H2("10. Títulos de Pilotos"),
        dcc.Graph(id="titles-bar-chart"),
    ]),
])

# Callbacks

## 1. Rendimiento de Pilotos
@app.callback(
    Output("pilot-performance", "figure"),
    Input("year-selector", "value")
)
def update_pilot_performance(selected_year):
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]
    points_by_driver = filtered_data.groupby("surname")["points"].sum().reset_index()

    fig = px.bar(
        points_by_driver.sort_values(by="points", ascending=False).head(20),
        x="points", y="surname", orientation="h",
        title=f"Puntos por Piloto en {selected_year} (Top 20)",
        labels={"points": "Puntos", "surname": "Piloto"},
        color="surname",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(height=700)
    return fig

## 2. Consistencia de Pilotos
@app.callback(
    Output("pilot-consistency", "figure"),
    Input("year-selector", "value")
)
def update_pilot_consistency(selected_year):
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]
    avg_positions = filtered_data.groupby("surname")["positionOrder"].mean().reset_index()

    fig = px.bar(
        avg_positions.sort_values(by="positionOrder"),
        x="positionOrder", y="surname", orientation="h",
        title=f"Consistencia de los Pilotos en {selected_year}",
        labels={"positionOrder": "Posición Promedio", "surname": "Piloto"},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    # Ajustar tamaño y márgenes del gráfico
    fig.update_layout(
        height=800,  # Cambia la altura
        width=1850,  # Cambia el ancho
        margin={"l": 100, "r": 100, "t": 50, "b": 100},  # Márgenes para espacio extra
    )
    return fig

## 3. Impacto de la Clasificación
@app.callback(
    Output("classification-impact", "figure"),
    Input("year-selector", "value")
)
def update_classification_impact(selected_year):
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]

    fig = px.scatter(
        filtered_data, x="grid", y="positionOrder",
        title=f"Impacto de la Clasificación en {selected_year}",
        labels={"grid": "Posición en Clasificación", "positionOrder": "Posición Final"},
        color="grid",
        color_continuous_scale="Viridis"
    )
    return fig

## 4. Impacto de las Paradas en Boxes
@app.callback(
    Output("pitstop-impact", "figure"),
    Input("year-selector", "value")
)
def update_pitstop_impact(selected_year):
    pit_stops_aggregated = pit_stops.groupby(["raceId", "driverId"]).size().reset_index(name="num_pit_stops")
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]
    merged_data = filtered_data.merge(pit_stops_aggregated, on=["raceId", "driverId"], how="left")

    fig = px.box(
        merged_data, x="num_pit_stops", y="positionOrder",
        title=f"Impacto de las Paradas en Boxes en {selected_year}",
        labels={"num_pit_stops": "Número de Paradas", "positionOrder": "Posición Final"}
    )
    return fig

## 5. Rendimiento de Equipos por Temporada
@app.callback(
    Output("team-performance", "figure"),
    Input("year-selector", "value")
)
def update_team_performance(selected_year):
    filtered_data = constructor_results[constructor_results["raceId"].isin(races[races["year"] == selected_year]["raceId"])]
    team_points = filtered_data.groupby("constructorId")["points"].sum().reset_index()
    team_points = team_points.merge(constructors[["constructorId", "name"]], on="constructorId")

    fig = px.bar(
        team_points.sort_values(by="points", ascending=False),
        x="points", y="name", orientation="h",
        title=f"Puntos por Equipo en {selected_year}",
        labels={"points": "Puntos", "name": "Equipo"},
        color="name",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    return fig

## 6. Evolución de los Puntos por Carrera
@app.callback(
    Output("race-points-evolution", "figure"),
    Input("year-selector", "value")
)
def update_race_points_evolution(selected_year):
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]
    race_points = filtered_data.groupby(["raceId", "surname"])["points"].sum().reset_index()
    race_points = race_points.merge(races[["raceId", "circuitId", "date"]], on="raceId", how="left")
    race_points = race_points.merge(circuits[["circuitId", "name"]], on="circuitId", how="left")
    race_points = race_points.dropna(subset=["name", "points"])
    race_points = race_points.sort_values(by=["date", "raceId"])
    race_points["cumulative_points"] = race_points.groupby("surname")["points"].cumsum()
    race_points = race_points.dropna(subset=["cumulative_points"])

    fig = px.line(
        race_points,
        x="name", y="cumulative_points", color="surname",
        title=f"Evolución de Puntos por Carrera en {selected_year}",
        labels={"name": "Circuito", "cumulative_points": "Puntos Acumulados", "surname": "Piloto"},
        color_discrete_sequence=px.colors.qualitative.Dark2
    )
    fig.update_layout(height=700)
    return fig

## 7. Mejores Tiempos por Vuelta
@app.callback(
    Output("best-lap-times", "figure"),
    [Input("year-selector", "value"), Input("circuit-selector", "value")]
)
def update_best_lap_times(selected_year, selected_circuit):
    lap_data = lap_times.merge(races[["raceId", "year", "name"]], on="raceId")
    filtered_data = lap_data[lap_data["year"] == selected_year]
    if selected_circuit:
        filtered_data = filtered_data[filtered_data["name"] == selected_circuit]
    best_laps = filtered_data.groupby("driverId")["milliseconds"].min().reset_index()
    best_laps = best_laps.merge(drivers, on="driverId")
    best_laps["formatted_time"] = best_laps["milliseconds"].apply(format_time)

    fig = px.bar(
        best_laps.sort_values(by="milliseconds"), x="formatted_time", y="surname", orientation="h",
        title=f"Mejores Tiempos por Vuelta en {selected_year}" + (f" - {selected_circuit}" if selected_circuit else ""),
        labels={"formatted_time": "Tiempo", "surname": "Piloto"},
        color="surname",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    # Ajustar tamaño y márgenes del gráfico
    fig.update_layout(
        height=800,  # Cambia la altura
        width=1850,  # Cambia el ancho
        margin={"l": 100, "r": 100, "t": 50, "b": 100},  # Márgenes para espacio extra
    )
    return fig



## 8. Circuitos en el Mapa
@app.callback(
    Output("circuit-map", "figure"),
    Input("year-selector", "value")
)
def update_circuit_map(selected_year):
    filtered_races = races[races["year"] == selected_year]
    circuits_map = filtered_races.merge(circuits, on="circuitId", how="inner")
    circuits_map = circuits_map.rename(columns={"name_y": "circuit_name"})

    fig = px.scatter_mapbox(
        circuits_map, lat="lat", lon="lng", hover_name="circuit_name",
        zoom=3,  # Cambié el zoom para visualizar mejor los circuitos
        title=f"Mapa de Circuitos en {selected_year}",
        labels={"circuit_name": "Circuito"}
    )
    # Actualización de diseño del mapa para mejorar su visibilidad
    fig.update_layout(
        mapbox_style="carto-positron",  # Elegir un estilo de mapa que sea más claro
        height=800,  # Cambia la altura del mapa
        width=1850,  # Cambia el ancho del mapa
        margin={"l": 100, "r": 100, "t": 50, "b": 100}  # Márgenes para un mejor ajuste
    )
    return fig


## 9. Distribución de Puntos por Piloto (Gráfico Circular)
@app.callback(
    Output("points-pie-chart", "figure"),
    Input("year-selector", "value")
)
def update_points_pie_chart(selected_year):
    filtered_data = results_cleaned[results_cleaned["year"] == selected_year]
    points_by_driver = filtered_data.groupby("surname")["points"].sum().reset_index()

    fig = px.pie(
        points_by_driver,
        names="surname", values="points",
        title=f"Distribución de Puntos en {selected_year}",
        labels={"surname": "Piloto", "points": "Puntos"},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    return fig

## 10. Títulos de Pilotos (Gráfico de Barras)
@app.callback(
    Output("titles-bar-chart", "figure"),
    Input("year-selector", "value")
)
def update_titles_bar_chart(selected_year):
    # Calcular los títulos correctamente (máximo de puntos por piloto cada temporada)
    season_winners = results_cleaned.groupby(["year", "surname"])["points"].sum().reset_index()

    # Asegurarse de contar solo al ganador por temporada
    season_winners = season_winners.loc[season_winners.groupby("year")["points"].idxmax()]

    # Contar los títulos por piloto
    titles_by_driver = season_winners["surname"].value_counts().reset_index()
    titles_by_driver.columns = ["surname", "titles"]

    # Filtrar títulos conocidos (limitar manualmente si necesario)
    known_titles = {
        "Schumacher": 7,
        "Hamilton": 7,
        "Fangio": 5,
        "Vettel": 4,
        "Prost": 4,
        "Verstappen": 4,
        "Senna": 3,
    }

    # Normalizar nombres de pilotos en los datos
    titles_by_driver["surname"] = titles_by_driver["surname"].str.strip()

    # Añadir títulos oficiales al gráfico
    titles_by_driver["official_titles"] = titles_by_driver["surname"].map(known_titles).fillna(0)

    # Filtrar los pilotos con al menos 1 título
    titles_by_driver = titles_by_driver[titles_by_driver["official_titles"] > 0]

    # Crear gráfico
    fig = px.bar(
        titles_by_driver.sort_values(by="official_titles", ascending=False),
        x="official_titles", y="surname", orientation="h",
        title="Títulos por Piloto (Oficiales)",
        labels={"official_titles": "Títulos", "surname": "Piloto"},
        color="surname",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(showlegend=False)  # Quitar leyenda si no es necesaria
    return fig



# Ejecutar la aplicación
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8050)))

