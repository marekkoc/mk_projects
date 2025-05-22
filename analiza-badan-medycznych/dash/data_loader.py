#!/usr/bin/env python3
# copyright: marekkoc
# Created: 2025-05-11
# Updated: 2025-05-11

import pandas as pd
import numpy as np

def load_medication_data():
    """Wczytaj dane o leku z pliku medicine.txt"""
    try:
        df = pd.read_csv('medicine.txt', sep='\s+', 
                         skiprows=1,
                         names=['Date', 'Dose_nr', 'City'])
        df['Date'] = pd.to_datetime(df['Date'], format='%Y.%m.%d')
        return df
    except Exception as e:
        print(f"Błąd wczytywania danych: {e}")
        return pd.DataFrame(columns=['Date', 'Dose_nr', 'City'])

def create_blood_test_data(med_df):
    """Utwórz syntetyczne dane badań krwi na podstawie dat poboru leku"""
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
