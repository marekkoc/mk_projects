"""

Created: 2025.01.07
Modified: 2025.01.07
"""

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
