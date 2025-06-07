---
Utworzono: 2024-10-26T18:29:00
Zmodyfikowano: 2025-01-09T18:29:00
Źródło: chatGPT
tags:
---
# 1.Opis projektu

1. Hasła mogą być generowane w zaszumionym obrazie 3D. Gdyby obraz był bez szumu, to możemy go zakodować np. za pomocą ciągu RL.
2. Poszczególne litery będą zapisane na różnej głębokości i w kolejnych blokach obrazu
3. Wyświetlenie hasła będzie możliwe za pomocą funkcji MIP
4. hasło będzie przechowywane jako np plik JSON w którym najpierw będą:
	1. meta dane:
		1. data utworzenia
		2. data ostatniego otwarcia
		3. data modyfikacji???
		4. rozmiar obrazu
		5. do czego jest to haslo np bonito.pl
		6. rozmiar obrazu
	2.  obraz 3D który może być zakodowywany (jesli bedzi bez szumu) metodą RL
5. Program będzie rodzajem przeglądarki 3D z dodatkowymi opcjami:
	1. niewyświetlenie MIP
	2. dodanie szumu do MIP
	3. zapis MIP do pliku np w formacie png
---

# 2. Aplikacja konsolowa
Tworzenie aplikacji do przechowywania haseł to zadanie wymagające dużego nacisku na bezpieczeństwo. Oto kluczowe aspekty, które należy wziąć pod uwagę:

---

### **Funkcjonalność aplikacji do przechowywania haseł**
1. **Bezpieczne przechowywanie:**
   - Hasła muszą być zaszyfrowane przy użyciu algorytmu szyfrowania (np. AES).
   - Klucz szyfrujący powinien być chroniony (np. przechowywany w bezpiecznym miejscu, jak w systemowym Keychain).

2. **Proste zarządzanie:**
   - Dodawanie, edytowanie i usuwanie haseł.
   - Możliwość organizowania haseł w foldery/grupy.

3. **Łatwy dostęp:**
   - Funkcja wyszukiwania.
   - Opcja kopiowania hasła do schowka.

4. **Bezpieczeństwo dostępu:**
   - Autoryzacja przy użyciu głównego hasła.
   - Opcjonalne wsparcie dla dwuskładnikowego uwierzytelniania (2FA).

5. **Przenośność i synchronizacja (opcjonalnie):**
   - Możliwość eksportu/importu danych.
   - Synchronizacja przez chmurę z szyfrowaniem end-to-end.

6. **Przyjazny interfejs:**
   - Wersja na desktop i/lub mobilna.

---

### **Gotowe rozwiązania vs. Tworzenie własnego**
- **Gotowe rozwiązania**:
  Polecam rozważyć już istniejące i bezpieczne menedżery haseł, takie jak:
  - **Bitwarden** (open-source, darmowy z opcją premium).
  - **LastPass**, **Dashlane**, **1Password**.
  - **KeePass** (open-source, lokalne przechowywanie danych).

- **Tworzenie własnego rozwiązania**:
  Jeśli chcesz stworzyć swoją aplikację, możesz użyć poniższych technologii:

---

### **Tworzenie aplikacji w Pythonie**
Oto przykład prostej aplikacji konsolowej do przechowywania haseł:

#### 1. **Instalacja zależności:**
```bash
pip install cryptography
```

#### 2. **Kod aplikacji:**
```python
import os
import json
from cryptography.fernet import Fernet

# Funkcja generująca klucz
def generate_key():
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)

# Funkcja wczytująca klucz
def load_key():
    if not os.path.exists("key.key"):
        raise FileNotFoundError("Key file not found. Generate it using 'generate_key()'.")
    return open("key.key", "rb").read()

# Funkcje szyfrowania i odszyfrowania
def encrypt_password(password, key):
    fernet = Fernet(key)
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password, key):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_password.encode()).decode()

# Funkcje do zarządzania hasłami
def save_passwords(passwords, filename="passwords.json"):
    with open(filename, "w") as file:
        json.dump(passwords, file)

def load_passwords(filename="passwords.json"):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return {}

# Aplikacja główna
def main():
    key = load_key()
    passwords = load_passwords()

    while True:
        print("\nPassword Manager")
        print("1. Add Password")
        print("2. View Passwords")
        print("3. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            service = input("Enter the service name: ")
            username = input("Enter the username: ")
            password = input("Enter the password: ")
            encrypted_password = encrypt_password(password, key)
            passwords[service] = {"username": username, "password": encrypted_password}
            save_passwords(passwords)
            print("Password saved!")

        elif choice == "2":
            for service, credentials in passwords.items():
                decrypted_password = decrypt_password(credentials["password"], key)
                print(f"Service: {service}, Username: {credentials['username']}, Password: {decrypted_password}")

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid option.")

if __name__ == "__main__":
    # Generate a key if it doesn't exist (only needed once)
    if not os.path.exists("key.key"):
        print("Generating key...")
        generate_key()

    main()
```

---

### **Cechy tego rozwiązania**
- **Szyfrowanie:** Wszystkie hasła są szyfrowane za pomocą klucza.
- **Przechowywanie lokalne:** Hasła są przechowywane w pliku JSON.
- **Prostota:** Konsolowy interfejs użytkownika.

---

### **Uwagi dotyczące bezpieczeństwa**
1. **Bezpieczeństwo klucza szyfrującego:**
   - Klucz (`key.key`) powinien być odpowiednio chroniony (np. w systemowym Keychain).

2. **Kopiowanie do schowka:**
   - Można użyć biblioteki `pyperclip` do automatycznego kopiowania hasła do schowka.

3. **Wersja z GUI:**
   - Rozbuduj aplikację, używając bibliotek GUI, takich jak **Tkinter**, **PyQt** lub **Kivy**.

4. **Przechowywanie w chmurze:**
   - Zaimplementuj opcję synchronizacji z Google Drive lub Dropbox.

---

Jeśli chcesz, mogę pomóc w rozbudowie tej aplikacji lub stworzeniu wersji z GUI!

# Aplikacja z GUI
Rozbudowa aplikacji do przechowywania haseł z interfejsem graficznym (GUI) to świetny pomysł! Użyjemy biblioteki **PyQt5**, która pozwala tworzyć estetyczne i funkcjonalne aplikacje GUI.

### **Wersja GUI menedżera haseł**

#### 1. **Instalacja wymaganych bibliotek**
Zanim rozpoczniesz, zainstaluj PyQt5 i cryptography:
```bash
pip install pyqt5 cryptography
```

---

#### 2. **Kod aplikacji z GUI**
```python
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from cryptography.fernet import Fernet


# Funkcje szyfrowania
def generate_key():
    """Generuje klucz szyfrowania."""
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """Ładuje klucz szyfrowania z pliku."""
    if not os.path.exists("key.key"):
        raise FileNotFoundError("Brak pliku klucza. Wygeneruj klucz za pomocą 'generate_key()'.")
    return open("key.key", "rb").read()


def encrypt_password(password, key):
    """Szyfruje hasło."""
    fernet = Fernet(key)
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password, key):
    """Odszyfrowuje hasło."""
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_password.encode()).decode()


# Klasa główna aplikacji
class PasswordManager(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Password Manager")
        self.resize(600, 400)

        # Wczytanie klucza szyfrowania i haseł
        try:
            self.key = load_key()
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Klucz szyfrowania nie został znaleziony. Wygeneruj go!")
            generate_key()
            self.key = load_key()

        self.passwords = self.load_passwords()

        # Layout główny
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Pola do dodawania haseł
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("Nazwa usługi")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nazwa użytkownika")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")

        # Przycisk dodawania
        self.add_button = QPushButton("Dodaj hasło")
        self.add_button.clicked.connect(self.add_password)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.service_input)
        input_layout.addWidget(self.username_input)
        input_layout.addWidget(self.password_input)
        input_layout.addWidget(self.add_button)

        self.layout.addLayout(input_layout)

        # Tabela wyświetlająca hasła
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Usługa", "Nazwa użytkownika", "Hasło"])
        self.update_table()

        self.layout.addWidget(self.table)

        # Przycisk usuwania
        self.delete_button = QPushButton("Usuń zaznaczone")
        self.delete_button.clicked.connect(self.delete_password)
        self.layout.addWidget(self.delete_button)

    def load_passwords(self):
        """Wczytuje hasła z pliku JSON."""
        if os.path.exists("passwords.json"):
            with open("passwords.json", "r") as file:
                return json.load(file)
        return {}

    def save_passwords(self):
        """Zapisuje hasła do pliku JSON."""
        with open("passwords.json", "w") as file:
            json.dump(self.passwords, file)

    def add_password(self):
        """Dodaje nowe hasło do listy."""
        service = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not service or not username or not password:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być wypełnione!")
            return

        encrypted_password = encrypt_password(password, self.key)
        self.passwords[service] = {"username": username, "password": encrypted_password}
        self.save_passwords()
        self.update_table()

        self.service_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        QMessageBox.information(self, "Sukces", "Hasło zostało dodane!")

    def update_table(self):
        """Aktualizuje tabelę z hasłami."""
        self.table.setRowCount(len(self.passwords))
        for row, (service, credentials) in enumerate(self.passwords.items()):
            username = credentials["username"]
            password = decrypt_password(credentials["password"], self.key)
            self.table.setItem(row, 0, QTableWidgetItem(service))
            self.table.setItem(row, 1, QTableWidgetItem(username))
            self.table.setItem(row, 2, QTableWidgetItem(password))
        self.table.resizeColumnsToContents()

    def delete_password(self):
        """Usuwa zaznaczone hasła."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Zaznacz przynajmniej jedno hasło do usunięcia!")
            return

        for index in sorted(selected_rows, reverse=True):
            service = self.table.item(index.row(), 0).text()
            del self.passwords[service]
            self.table.removeRow(index.row())

        self.save_passwords()
        QMessageBox.information(self, "Sukces", "Zaznaczone hasła zostały usunięte!")


# Uruchamianie aplikacji
if __name__ == "__main__":
    app = QApplication([])
    manager = PasswordManager()
    manager.show()
    app.exec_()
```

---

#### **Funkcjonalności tej aplikacji:**
1. **Szyfrowanie haseł:** Wszystkie hasła są szyfrowane za pomocą `cryptography`.
2. **Przyjazny interfejs GUI:** Dodawanie, wyświetlanie i usuwanie haseł.
3. **Prostota obsługi:** Obsługuje zapisywanie do lokalnego pliku `passwords.json`.

#### **Instrukcje użytkowania:**
1. **Dodawanie haseł:** Wypełnij pola usługi, użytkownika i hasła, a następnie kliknij "Dodaj hasło".
2. **Przeglądanie haseł:** Wszystkie hasła są wyświetlane w tabeli.
3. **Usuwanie haseł:** Zaznacz wiersz w tabeli i kliknij "Usuń zaznaczone".

---

Jeśli potrzebujesz więcej funkcjonalności (np. synchronizacji z chmurą), daj znać – mogę pomóc to dodać! 😊
