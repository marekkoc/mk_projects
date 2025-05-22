#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Funkcja wczytująca dane o leku
def load_medication_data():
    try:
        df = pd.read_csv('medicine.txt', sep='\s+', 
                         skiprows=1,
                         names=['Date', 'Dose_nr', 'City'])
        df['Date'] = pd.to_datetime(df['Date'], format='%Y.%m.%d')
        return df
    except Exception as e:
        print(f"Błąd wczytywania danych: {e}")
        return pd.DataFrame(columns=['Date', 'Dose_nr', 'City'])

# Funkcja tworząca syntetyczne dane badań krwi
def create_blood_test_data(med_df):
    if med_df.empty:
        return pd.DataFrame()
    
    dates = []
    for date in med_df['Date']:
        dates.append(date - pd.Timedelta(days=1))
        dates.append(date + pd.Timedelta(days=7))
    dates = sorted(list(set(dates)))
    
    np.random.seed(42)
    blood_df = pd.DataFrame({
        'Date': dates,
        'Hemoglobin': [14.0 + np.random.normal(0, 0.5) for _ in range(len(dates))],
        'WBC': [7.0 + np.random.normal(0, 0.8) for _ in range(len(dates))],
        'Platelets': [250 + np.random.normal(0, 20) for _ in range(len(dates))]
    })
    return blood_df

# Wczytaj dane
medication_df = load_medication_data()
blood_df = create_blood_test_data(medication_df)

# Inicjalizuj aplikację
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout aplikacji
app.layout = dbc.Container([
    html.H1("Analiza badań krwi i poboru leku"),
    
    dbc.Tabs([
        # Zakładka: Pobór leku
        dbc.Tab(label="Pobór leku", children=[
            dcc.Graph(id="medication-graph"),
            html.Div(id="medication-stats")
        ]),
        
        # Zakładka: Badania krwi
        dbc.Tab(label="Badania krwi", children=[
            dcc.Graph(id="blood-graph"),
            html.Div(id="blood-stats")
        ]),
        
        # Zakładka: Dane
        dbc.Tab(label="Dane", children=[
            html.H3("Dane poboru leku"),
            html.Div(id="medication-table"),
            html.H3("Dane badań krwi", className="mt-4"),
            html.Div(id="blood-table")
        ])
    ]),
    
    # Ukryte przechowywanie danych
    dcc.Store(id="medication-data", data=medication_df.to_dict('records')),
    dcc.Store(id="blood-data", data=blood_df.to_dict('records'))
], fluid=True)

# Callback: Wykres poboru leku
@callback(
    Output("medication-graph", "figure"),
    Input("medication-data", "data")
)
def update_medication_graph(data):
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    
    df['Date'] = pd.to_datetime(df['Date'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=[1] * len(df),
        mode='markers+lines',
        marker=dict(size=15, color='darkblue'),
        text=df['Dose_nr'].astype(str),
        hovertemplate='Data: %{x}<br>Dawka: %{text}'
    ))
    
    fig.update_layout(
        title="Historia poboru leku",
        xaxis_title="Data",
        yaxis_visible=False,
        plot_bgcolor='white'
    )
    
    return fig

# Callback: Wykres badań krwi
@callback(
    Output("blood-graph", "figure"),
    [Input("blood-data", "data"),
     Input("medication-data", "data")]
)
def update_blood_graph(blood_data, med_data):
    blood_df = pd.DataFrame(blood_data)
    med_df = pd.DataFrame(med_data)
    
    if blood_df.empty:
        return go.Figure()
    
    blood_df['Date'] = pd.to_datetime(blood_df['Date'])
    
    fig = go.Figure()
    
    # Dodaj linie dla parametrów krwi
    for col in blood_df.columns:
        if col != 'Date':
            fig.add_trace(go.Scatter(
                x=blood_df['Date'],
                y=blood_df[col],
                mode='lines+markers',
                name=col
            ))
    
    # Dodaj pionowe linie dla dawek leku
    if not med_df.empty:
        med_df['Date'] = pd.to_datetime(med_df['Date'])
        
        for _, row in med_df.iterrows():
            fig.add_shape(
                type="line",
                x0=row['Date'],
                x1=row['Date'],
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="gray", dash="dash", width=1)
            )
            
            fig.add_annotation(
                x=row['Date'],
                y=1,
                yref="paper",
                text=f"Dawka #{int(row['Dose_nr'])}",
                showarrow=False,
                textangle=0,
                xanchor="left"
            )
    
    fig.update_layout(
        title="Wyniki badań krwi",
        xaxis_title="Data",
        yaxis_title="Wartość",
        legend_title="Parametry",
        plot_bgcolor='white'
    )
    
    return fig

# Callback: Tabela leku
@callback(
    Output("medication-table", "children"),
    Input("medication-data", "data")
)
def update_medication_table(data):
    df = pd.DataFrame(data)
    if df.empty:
        return html.Div("Brak danych")
    
    # Formatuj daty do wyświetlenia
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    
    return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

# Callback: Tabela badań
@callback(
    Output("blood-table", "children"),
    Input("blood-data", "data")
)
def update_blood_table(data):
    df = pd.DataFrame(data)
    if df.empty:
        return html.Div("Brak danych")
    
    # Formatuj daty i wartości liczbowe
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    numeric_cols = df.select_dtypes(include=['float64']).columns
    if len(numeric_cols) > 0:
        df[numeric_cols] = df[numeric_cols].round(2)
    
    return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

# Callback: Statystyki leku
@callback(
    Output("medication-stats", "children"),
    Input("medication-data", "data")
)
def update_medication_stats(data):
    df = pd.DataFrame(data)
    if df.empty or len(df) < 2:
        return html.Div("Niewystarczające dane")
    
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Days_Since_Last'] = (df['Date'] - df['Date'].shift(1)).dt.days
    avg_interval = df['Days_Since_Last'].dropna().mean()
    
    last_dose = df.iloc[-1]
    last_date = last_dose['Date'].strftime('%Y-%m-%d')
    next_date = (last_dose['Date'] + pd.Timedelta(days=avg_interval)).strftime('%Y-%m-%d')
    
    return html.Div([
        html.P(f"Liczba dawek: {len(df)}"),
        html.P(f"Średni odstęp: {avg_interval:.1f} dni"),
        html.P(f"Ostatnia dawka (#{int(last_dose['Dose_nr'])}): {last_date}"),
        html.P(f"Przewidywana następna dawka: {next_date}")
    ])

# Callback: Statystyki badań
@callback(
    Output("blood-stats", "children"),
    Input("blood-data", "data")
)
def update_blood_stats(data):
    df = pd.DataFrame(data)
    if df.empty:
        return html.Div("Brak danych")
    
    df['Date'] = pd.to_datetime(df['Date'])
    
    stats_rows = []
    for col in df.columns:
        if col != 'Date':
            avg_val = df[col].mean()
            min_val = df[col].min()
            max_val = df[col].max()
            
            row = html.Tr([
                html.Td(col),
                html.Td(f"{avg_val:.2f}"),
                html.Td(f"{min_val:.2f}"),
                html.Td(f"{max_val:.2f}")
            ])
            stats_rows.append(row)
    
    table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Parametr"),
                html.Th("Średnia"),
                html.Th("Minimum"),
                html.Th("Maksimum")
            ])),
            html.Tbody(stats_rows)
        ],
        bordered=True,
        striped=True
    )
    
    return table

if __name__ == '__main__':
    app.run(debug=True)
