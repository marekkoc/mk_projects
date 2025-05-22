#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Importuj moduły aplikacji
from data_loader import load_medication_data, create_blood_test_data
from tabs import medication, blood_test, data_tabs

# Wczytaj dane
medication_df = load_medication_data()
blood_df = create_blood_test_data(medication_df)

# Inicjalizuj aplikację
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Definiuj layout aplikacji
app.layout = dbc.Container([
    html.H1("Analiza badań krwi i poboru leku"),
    
    dbc.Tabs([
        # Zakładka: Pobór leku
        dbc.Tab(label="Pobór leku", children=medication.get_layout()),
        
        # Zakładka: Badania krwi
        dbc.Tab(label="Badania krwi", children=blood_test.get_layout()),
        
        # Zakładka: Dane
        dbc.Tab(label="Dane", children=data_tabs.get_layout())
    ]),
    
    # Ukryte przechowywanie danych
    dcc.Store(id="medication-data", data=medication_df.to_dict('records')),
    dcc.Store(id="blood-data", data=blood_df.to_dict('records'))
], fluid=True)

# Zarejestruj callbacki z modułów
medication.register_callbacks(app)
blood_test.register_callbacks(app)
data_tabs.register_callbacks(app)

# Uruchom serwer
if __name__ == '__main__':
    app.run(debug=True)
