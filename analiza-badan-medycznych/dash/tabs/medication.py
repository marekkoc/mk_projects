#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

def get_layout():
    """Zwraca layout zakładki z danymi o leku"""
    return html.Div([
        dcc.Graph(id="medication-graph"),
        html.Div(id="medication-stats")
    ])

def register_callbacks(app):
    """Rejestruje callbacki związane z zakładką leku"""
    
    @app.callback(
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

    @app.callback(
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
