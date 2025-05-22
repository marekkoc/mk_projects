#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

def get_layout():
    """Zwraca layout zakładki z badaniami krwi"""
    return html.Div([
        dcc.Graph(id="blood-graph"),
        html.Div(id="blood-stats")
    ])

def register_callbacks(app):
    """Rejestruje callbacki związane z zakładką badań krwi"""
    
    @app.callback(
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

    @app.callback(
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
