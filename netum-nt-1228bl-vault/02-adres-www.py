#! /usr/bin/env python3

"""
Program do odczytu kodów kreskowych i QR z otwieraniem stron WWW
Wykorzystuje czytnik Netum NT-1228B

Created: 2025.03.04
Modified: 2025.03.04
"""

import sys
import re
import webbrowser
import time

def is_url(text):
    """Sprawdza, czy tekst jest adresem URL."""
    # Wzorzec do rozpoznawania adresów URL
    url_pattern = re.compile(
        r'^(https?:\/\/)?(www\.)?'  # protokół http(s) i www (opcjonalne)
        r'([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)'  # domena
        r'(\/[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]*)?$'  # ścieżka (opcjonalna)
    )
    return bool(url_pattern.match(text))

def open_url(url):
    """Otwiera adres URL w przeglądarce."""
    # Dodaj protokół http, jeśli nie został podany
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    print(f"Otwieram stronę: {url}")
    webbrowser.open_new_tab(url)

def main():
    print("Program do odczytu kodów kreskowych i QR")
    print("Proszę zeskanować kod kreskowy lub QR...")
    print("Naciśnij Ctrl+C, aby zakończyć program")
    
    # Upewnij się, że wyjście jest natychmiast wyświetlane
    sys.stdout.flush()
    
    while True:
        try:
            # Wyraźnie informuj użytkownika, że program czeka na dane
            print(">>> Czekam na skan... <<<")
            sys.stdout.flush()
            
            # Odczyt kodu kreskowego (wejście z czytnika)
            barcode = input()
            
            # Natychmiast pokaż, że coś zostało odczytane
            print(f"\nOdczytano kod: {barcode}")
            
            # Sprawdź, czy kod zawiera adres URL
            if is_url(barcode):
                print("Wykryto adres WWW.")
                open_url(barcode)
            else:
                print("Odczytany kod nie jest adresem WWW.")
            
            print("\nGotowy na kolejny skan...")
            sys.stdout.flush()
            
            # Krótka pauza, aby uniknąć zbyt szybkiego przetwarzania
            time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nZakończenie programu.")
            sys.exit()
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            print("Spróbuj ponownie...")
            sys.stdout.flush()
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Krytyczny błąd: {e}")
        print("Program zostanie zakończony za 5 sekund...")
        time.sleep(5)
        sys.exit(1)

