#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd

def get_layout():
    """Zwraca layout zakładki z tabelami danych"""
    return html.Div([
        html.H3("Dane poboru leku"),
        html.Div(id="medication-table"),
        html.H3("Dane badań krwi", className="mt-4"),
        html.Div(id="blood-table")
    ])

def register_callbacks(app):
    """Rejestruje callbacki związane z zakładką danych"""
    
    @app.callback(
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

    @app.callback(
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
