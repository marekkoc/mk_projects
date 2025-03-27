---
Utworzono: 2025-01-07T22:10:00
Zmodyfikowano: 2025-01-07T22:10:00
Źródło: chatGPT
tags: 
Katalog:
---

Poniżej znajdziesz minimalny kod w Pythonie do obsługi skanera kodów kreskowych podłączonego jako urządzenie USB (działającego w trybie HID, jak klawiatura). Jeśli skaner działa jako klawiatura, kod kreskowy będzie traktowany jak wprowadzenie z klawiatury. W takim przypadku możemy użyć standardowych metod wejścia w Pythonie.

### Kod minimalny

```python
import sys

def main():
    print("Please scan a barcode:")
    while True:
        try:
            # Odczyt kodu kreskowego (wejście z klawiatury)
            barcode = input("Scanned barcode: ")
            print(f"Barcode scanned: {barcode}")
        except KeyboardInterrupt:
            print("\nExiting program.")
            sys.exit()

if __name__ == "__main__":
    main()
```

### Jak działa ten kod:
1. Program uruchamia pętlę, która oczekuje na wprowadzenie danych.
2. Gdy zeskanujesz kod, dane są wyświetlane w terminalu.
3. Aby zakończyć program, możesz nacisnąć `Ctrl+C`.

---

### Rozszerzenie dla zaawansowanej obsługi USB
Jeśli skaner nie działa jako klawiatura, możesz użyć biblioteki `pyusb` do bezpośredniej obsługi urządzenia USB. 

**Instalacja `pyusb`:**
```bash
pip install pyusb
```

**Kod z `pyusb`:**
```python
import usb.core
import usb.util

def main():
    # Znajdź urządzenie USB (dostosuj VID i PID do swojego skanera)
    device = usb.core.find(idVendor=0x1234, idProduct=0x5678)  # Podmień VID i PID

    if device is None:
        print("Device not found.")
        return

    # Przygotowanie urządzenia
    device.set_configuration()

    print("Ready to scan barcodes. Press Ctrl+C to exit.")

    try:
        while True:
            data = device.read(0x81, 8)  # Odczyt danych z endpointu (dostosuj endpoint)
            barcode = ''.join([chr(x) for x in data if x != 0])
            print(f"Scanned barcode: {barcode}")
    except KeyboardInterrupt:
        print("\nExiting program.")
    except usb.core.USBError as e:
        print(f"USB Error: {e}")

if __name__ == "__main__":
    main()
```

### Jak działa kod z `pyusb`:
1. `usb.core.find` znajduje skaner kodów kreskowych na podstawie VID i PID (identyfikatory urządzenia USB).
2. Program odczytuje dane z endpointu urządzenia.
3. Dane są interpretowane jako kod kreskowy i wyświetlane w terminalu.

**Uwaga:** Aby znaleźć VID i PID urządzenia, możesz użyć narzędzi takich jak `lsusb` (Linux) lub Menedżer urządzeń (Windows).

---

Jeśli nie jesteś pewien, czy Twój skaner działa w trybie HID, zacznij od pierwszego, prostszego podejścia.