#!/usr/bin/env python
# Autor: marekkoc
# Created: 2025-05-25
# Update: 2025-05-25

import pandas as pd
import glob
import os

def merge_txt_files(folder_path, output_file, separator='\t'):
    """
    Łączy wszystkie pliki txt z folderu w jeden plik, 
    ujednolicając kolejność kolumn.
    
    Args:
        folder_path (str): Ścieżka do folderu z plikami txt
        output_file (str): Nazwa pliku wynikowego
        separator (str): Separator w plikach (domyślnie tab)
    """
    
    # Znajdź wszystkie pliki txt
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    
    if not txt_files:
        print("Nie znaleziono plików txt w podanym folderze!")
        return
    
    print(f"Znaleziono {len(txt_files)} plików txt:")
    for file in txt_files:
        print(f"  - {os.path.basename(file)}")
    
    # Lista do przechowywania DataFrames
    dataframes = []
    all_columns = set()
    
    # Wczytaj wszystkie pliki i zbierz nazwy kolumn
    for file_path in txt_files:
        try:
            # Wczytaj plik
            df = pd.read_csv(file_path, sep=separator, encoding='utf-8')
            
            # Dodaj informację o źródłowym pliku (opcjonalnie)
            df['source_file'] = os.path.basename(file_path)
            
            dataframes.append(df)
            all_columns.update(df.columns)
            
            print(f"Wczytano {file_path}: {len(df)} wierszy, kolumny: {list(df.columns)}")
            
        except Exception as e:
            print(f"Błąd przy wczytywaniu {file_path}: {e}")
    
    if not dataframes:
        print("Nie udało się wczytać żadnego pliku!")
        return
    
    # Ujednolic kolumny we wszystkich DataFrame'ach
    all_columns = sorted(list(all_columns))  # Sortuj alfabetycznie
    
    print(f"\nWszystkie dostępne kolumny: {all_columns}")
    
    for i, df in enumerate(dataframes):
        # Dodaj brakujące kolumny z wartościami NaN
        for col in all_columns:
            if col not in df.columns:
                df[col] = None
        
        # Uporządkuj kolumny w tej samej kolejności
        dataframes[i] = df[all_columns]
    
    # Połącz wszystkie DataFrame'y
    merged_df = pd.concat(dataframes, ignore_index=True)
    
    print(f"\nPołączono dane:")
    print(f"  - Łączna liczba wierszy: {len(merged_df)}")
    print(f"  - Liczba kolumn: {len(merged_df.columns)}")
    print(f"  - Kolumny: {list(merged_df.columns)}")
    
    # Zapisz wynik
    merged_df.to_csv(output_file, sep=separator, index=False, encoding='utf-8')
    print(f"\nZapisano połączony plik jako: {output_file}")
    
    # Pokaż przykładowe dane
    print(f"\nPierwsze 5 wierszy:")
    print(merged_df.head())
    
    return merged_df

# Przykład użycia
if __name__ == "__main__":
    # Ustaw ścieżki
    folder_with_txt_files = "."  # Aktualny folder - zmień na swoją ścieżkę
    output_filename = "merged_data.txt"
    
    # Jeśli używasz przecinków jako separatora, zmień na ','
    separator = '\t'  # lub ',' dla CSV
    
    # Połącz pliki
    result = merge_txt_files(folder_with_txt_files, output_filename, separator)
    
    # Opcjonalne: usuń kolumnę source_file jeśli nie jest potrzebna
    if result is not None and 'source_file' in result.columns:
        result_clean = result.drop('source_file', axis=1)
        result_clean.to_csv("merged_data_clean.txt", sep=separator, index=False, encoding='utf-8')
        print("Zapisano również wersję bez kolumny source_file jako: merged_data_clean.txt")
