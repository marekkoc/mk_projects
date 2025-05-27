#!/usr/bin/env python
# Autor: marekkoc
# Created: 2025-05-25
# Update: 2025-05-25

import pandas as pd
import re
from pathlib import Path
import argparse

def parse_text_file_to_dataframe(file_path):
    """
    Parsuje plik tekstowy do pandas DataFrame zgodnie z opisaną strukturą.
    
    Args:
        file_path (str): Ścieżka do pliku tekstowego
        
    Returns:
        pd.DataFrame: Sparsowana tabela danych
    """
    
    # Słownik na wartości z linii zaczynających się od %
    metadata = {}
    
    # Lista na nagłówki kolumn
    headers = []
    
    # Lista na wiersze danych
    data_rows = []
    
    # Flaga określająca czy znaleźliśmy nagłówki
    headers_found = False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Usuń białe znaki z początku i końca linii
            line = line.strip()
            
            # Pomiń puste linie
            if not line:
                continue
            
            # Pomiń komentarze (linie zaczynające się od #)
            if line.startswith('#'):
                continue
            
            # Obsłuż linie z metadanymi (zaczynające się od %)
            if line.startswith('%') and not line.startswith('%%'):
                # Usuń % i podziel na klucz:wartość
                metadata_line = line[1:].strip()
                if ':' in metadata_line:
                    key, value = metadata_line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                continue
            
            # Obsłuż nagłówki (linie zaczynające się od %%)
            if line.startswith('%%'):
                # Usuń %% i podziel według separatora |
                header_line = line[2:].strip()
                headers = [col.strip() for col in header_line.split('|')]
                headers_found = True
                continue
            
            # Obsłuż linie z danymi (tylko jeśli mamy już nagłówki)
            if headers_found and '|' in line:
                # Podziel linię według separatora |
                values = [val.strip() for val in line.split('|')]
                
                # Dopasuj liczbę wartości do liczby nagłówków
                while len(values) < len(headers):
                    values.append('')
                
                data_rows.append(values[:len(headers)])
    
    # Utwórz DataFrame z danych
    if headers and data_rows:
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Dodaj kolumny z metadanymi
        for key, value in metadata.items():
            df[key] = value
            
        return df
    else:
        # Zwróć pusty DataFrame jeśli nie ma danych
        return pd.DataFrame()

def replace_comma_with_dot(df, numeric_columns=None):
    """
    Zamienia przecinki na kropki w kolumnach numerycznych.
    
    Args:
        df (pd.DataFrame): DataFrame do przetworzenia
        numeric_columns (list): Lista kolumn do przetworzenia (domyślnie 'Result')
        
    Returns:
        pd.DataFrame: DataFrame z zamienionymi przecinkami na kropki
    """
    if numeric_columns is None:
        numeric_columns = ['Result', 'Reference Range']
    
    df_clean = df.copy()
    
    for col in numeric_columns:
        if col in df_clean.columns:
            # Zamień przecinki na kropki
            df_clean[col] = df_clean[col].astype(str).str.replace(',', '.')
    
    return df_clean


def clean_numeric_values(df, numeric_columns=None):
    """
    Czyści wartości numeryczne w DataFrame, usuwając znaki jak ↑, ↓ itp.
    
    Args:
        df (pd.DataFrame): DataFrame do oczyszczenia
        numeric_columns (list): Lista kolumn do oczyszczenia (domyślnie 'Result')
        
    Returns:
        pd.DataFrame: Oczyszczony DataFrame
    """
    if numeric_columns is None:
        numeric_columns = ['Result']
    
    df_clean = df.copy()
    
    for col in numeric_columns:
        if col in df_clean.columns:
            # Usuń znaki specjalne i konwertuj na numeric
            df_clean[col] = df_clean[col].str.replace(r'[↑↓→←]', '', regex=True)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    return df_clean

# Przykład użycia:
if __name__ == "__main__":


    parser = argparse.ArgumentParser(
        description='Konwertuje pliki TXT do CSV z obsługą metadanych.',
        epilog='''
Przykład użycia:
  python convert-txt-2-csv.py --file 20220314_Kalfarveien-1 ''')
    parser.add_argument('--file', type=str, default="20220314_Kalfarveien-1",
                      help='Nazwa pliku wejściowego bez rozszerzenia (domyślnie: 20220314_Kalfarveien-1)')
    parser.add_argument('--verbose', action='store_true',
                      help='Wyświetl szczegółowe informacje o procesie konwersji')
    args = parser.parse_args()

    # Sprawdź czy argument --file zawiera rozszerzenie i usuń je jeśli tak
    if '.' in args.file:
        original_file = args.file
        file_name_stem = Path(args.file).stem
        print(f"\nWykryto rozszerzenie w nazwie pliku.\nUsuwam rozszerzenie z '{original_file}' -> '{file_name_stem}'")
    else:
        file_name_stem = args.file
    
    # file_name_stem: str = args.file
    VERBOSE: bool = args.verbose

    # Przykład użycia funkcji
    txt_folder = Path("txt") 
    csv_folder = Path("csv") 
    if not csv_folder.exists():
        csv_folder.mkdir(parents=True, exist_ok=True)

    txt_extension: str = ".txt"
    csv_extension: str = ".csv"

    txt_file_name: Path = Path(file_name_stem).with_suffix(txt_extension) # versja 1
    csv_file_name: Path = Path(f"{file_name_stem}{csv_extension}") # Versja 2

    # OPERACJA ODWROTNA !!!
    # file_name_stem = txt_file_name.stem   
    # txt_extension = txt_file_name.suffix
    # csv_extension = csv_file_name.suffix


    txt_file_path = txt_folder / txt_file_name
    csv_file_path = csv_folder / csv_file_name
    
    if VERBOSE: print(f"\nPlik do sparsowania: {txt_file_path}") 
    try:
        # Parsuj plik
        df = parse_text_file_to_dataframe(txt_file_path)
        if VERBOSE: print("\tPlik sparsowany do DataFrame")
                
        # Oczyść wartości numeryczne ze znaków specjalnych np. ↑↓→←
        df_clean = clean_numeric_values(df)
        if VERBOSE: print("\tWartości numeryczne oczyszczone")

        # Zamień przecinki na kropki w kolumnach numerycznych
        df_clean = replace_comma_with_dot(df_clean)
        if VERBOSE: print("\tPrzecinki zamienione na kropki")
        
        # Zapisz do CSV jeśli chcesz
        df.to_csv(csv_file_path, index=False)
        if VERBOSE: print(f"Plik zapisany do CSV: {csv_file_path}\n")

    except FileNotFoundError:
        print(f"Plik {txt_file_path} nie został znaleziony.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
