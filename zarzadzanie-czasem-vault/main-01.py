#!/home/marek/miniconda3/envs/py312/bin/python

"""
Created on 2025-02-27
Modified on 2025-03-03

@author: marek
"""
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QGridLayout, 
                            QFrame, QColorDialog, QListWidget, QListWidgetItem,
                            QInputDialog, QFileDialog, QMessageBox, QDateEdit,
                            QTabWidget)
from PyQt5.QtGui import QColor, QPalette, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer, QDateTime
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
import datetime

class ColorSquare(QFrame):
    clicked = pyqtSignal(int, int)
    
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.activity = None
        self.setFrameShape(QFrame.Box)
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        
    def mousePressEvent(self, event):
        self.clicked.emit(self.row, self.col)
        
    def set_activity(self, activity):
        self.activity = activity
        if activity:
            self.setStyleSheet(f"background-color: {activity['color']}; border: 1px solid black;")
        else:
            self.setStyleSheet("background-color: white; border: 1px solid black;")

class ActivityItem(QListWidgetItem):
    def __init__(self, name, color):
        super().__init__(name)
        self.name = name
        self.color = color
        self.setBackground(QColor(color))

class TimeManagementApp(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zarządzanie Czasem")
        self.setGeometry(100, 100, 1000, 800)
        
        # Ścieżki do plików
        self.autosave_file = "time_management_autosave.json"
        self.activities_file = "activities.json"
        
        # Inicjalizacja podstawowych struktur
        self.selected_activity = None
        self.current_date = QDate.currentDate()
        self.data_changed = False
        self.grid_data = [[None for _ in range(6)] for _ in range(24)]
        
        # Najpierw wczytaj aktywności z pliku
        self.activities = self.load_activities_from_file()
        
        # Następnie zainicjalizuj interfejs (który używa wczytanych aktywności)
        self.init_ui()
        
        # Na końcu wczytaj dane z autosave
        self.auto_load_data()
        
        # Wczytaj dane dla bieżącego dnia
        self.load_day_data()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Lewy panel z listą aktywności
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Wybór daty
        date_layout = QHBoxLayout()
        date_label = QLabel("Data:")
        
        # Dodanie strzałki w lewo
        prev_day_button = QPushButton("<")
        prev_day_button.setMaximumWidth(30)
        prev_day_button.clicked.connect(self.go_to_previous_day)
        date_layout.addWidget(prev_day_button)
        
        date_layout.addWidget(date_label)
        self.date_edit = QDateEdit(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.change_date)
        date_layout.addWidget(self.date_edit)
        
        # Dodanie strzałki w prawo
        next_day_button = QPushButton(">")
        next_day_button.setMaximumWidth(30)
        next_day_button.clicked.connect(self.go_to_next_day)
        date_layout.addWidget(next_day_button)
        
        left_layout.addLayout(date_layout)
        
        # Lista aktywności
        activity_label = QLabel("Aktywności:")
        left_layout.addWidget(activity_label)
        
        self.activity_list = QListWidget()
        self.update_activity_list()
        self.activity_list.itemClicked.connect(self.select_activity)
        left_layout.addWidget(self.activity_list)
        
         
        # Przyciski do zapisywania i wczytywania danych
        file_buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_data)
        file_buttons_layout.addWidget(save_button)
        
        load_button = QPushButton("Wczytaj")
        load_button.clicked.connect(self.load_data)
        file_buttons_layout.addWidget(load_button)
        
        left_layout.addLayout(file_buttons_layout)
        
        # Przycisk do generowania statystyk
        stats_button = QPushButton("Statystyki")
        stats_button.clicked.connect(self.show_statistics)
        left_layout.addWidget(stats_button)
        
        # Przycisk do czyszczenia wszystkich kwadratów
        clear_button = QPushButton("Wyczyść wszystko")
        clear_button.clicked.connect(self.clear_all_squares)
        left_layout.addWidget(clear_button)
        
        # Prawy panel z siatką czasu
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Etykiety godzin i nagłówek
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        
        # Dodaj etykiety dla 10-minutowych bloków
        for col in range(6):
            minutes = col * 10
            label = QLabel(f"{minutes:02d}")
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, 0, col + 1)
        
        # Dodaj etykiety godzin i kwadraty kolorów
        self.squares = []
        for row in range(24):
            hour_label = QLabel(f"{row:02d}:00")
            hour_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid_layout.addWidget(hour_label, row + 1, 0)
            
            row_squares = []
            for col in range(6):
                square = ColorSquare(row, col)
                square.clicked.connect(self.square_clicked)
                square.setMouseTracking(True)  # Włączenie śledzenia myszy
                grid_layout.addWidget(square, row + 1, col + 1)
                row_squares.append(square)
            self.squares.append(row_squares)
        
        right_layout.addLayout(grid_layout)
        
        # Dodaj panele do głównego układu
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)
        
        # Podłączenie zdarzeń myszy do głównego okna
        self.setMouseTracking(True)
        
        # Podłączenie zdarzenia zamknięcia okna
        self.closeEvent = self.handle_close_event
    
    def update_activity_list(self):
        self.activity_list.clear()
        for activity in self.activities:
            try:
                # Sprawdź, czy activity jest słownikiem
                if isinstance(activity, dict) and "name" in activity and "color" in activity:
                    item = ActivityItem(activity["name"], activity["color"])
                    # Upewnij się, że kolor jest poprawny
                    color = QColor(activity["color"])
                    if color.isValid():
                        item.setBackground(color)
                    else:
                        # Użyj domyślnego koloru, jeśli podany jest nieprawidłowy
                        item.setBackground(QColor("#CCCCCC"))
                    self.activity_list.addItem(item)
                else:
                    print(f"Błąd: Nieprawidłowy format aktywności: {activity}")
            except Exception as e:
                # Bezpieczne wyświetlanie błędu bez dostępu do potencjalnie nieprawidłowych kluczy
                print(f"Błąd podczas dodawania aktywności: {str(e)}")
    
    def select_activity(self, item):
        for i, activity in enumerate(self.activities):
            if activity["name"] == item.name:
                self.selected_activity = activity
                break
    
    def square_clicked(self, row, col):
        if not self.selected_activity:
            if self.grid_data[row][col] is not None:
                # Jeśli kliknięto na już zaznaczony kwadrat, odznacz go
                self.grid_data[row][col] = None
                self.squares[row][col].set_activity(None)
                self.data_changed = True  # Oznacz, że dane zostały zmienione
            else:
                QMessageBox.warning(self, "Ostrzeżenie", "Najpierw wybierz aktywność!")
            return
            
        # Jeśli kliknięto na już zaznaczony kwadrat z tą samą aktywnością, odznacz go
        if (self.grid_data[row][col] is not None and 
            isinstance(self.grid_data[row][col], dict) and 
            self.grid_data[row][col]["name"] == self.selected_activity["name"]):
            self.grid_data[row][col] = None
            self.squares[row][col].set_activity(None)
        else:
            # W przeciwnym razie ustaw wybraną aktywność
            self.grid_data[row][col] = self.selected_activity
            self.squares[row][col].set_activity(self.selected_activity)
        
        self.data_changed = True  # Oznacz, że dane zostały zmienione
    
    def update_grid(self):
        for row in range(24):
            for col in range(6):
                if self.grid_data[row][col] is not None:
                    activity_name = self.grid_data[row][col]["name"]
                    # Znajdź aktualną aktywność o tej samej nazwie
                    found = False
                    for activity in self.activities:
                        if isinstance(activity, dict) and "name" in activity and activity["name"] == activity_name:
                            self.grid_data[row][col] = activity
                            self.squares[row][col].set_activity(activity)
                            found = True
                            break
                    if not found:
                        self.grid_data[row][col] = None
                        self.squares[row][col].set_activity(None)
    
    def change_date(self, date):
        # Zapisz dane bieżącego dnia do pamięci (nie do pliku)
        self.update_memory_data()
        
        # Automatyczny zapis przy zmianie daty
        save_success = self.autosave_data()
        if not save_success:
            # Opcjonalnie: Informacja dla użytkownika
            # QMessageBox.warning(self, "Ostrzeżenie", "Nie udało się zapisać danych.")
            pass
        
        # Zmień datę i wczytaj dane dla nowej daty
        self.current_date = date
        self.load_day_data()
    
    def get_date_string(self):
        return self.current_date.toString("yyyy-MM-dd")
    
    def update_memory_data(self):
        # Zapisz dane bieżącego dnia do pamięci
        date_str = self.get_date_string()
        
        # Inicjalizuj strukturę danych w pamięci, jeśli nie istnieje
        if not hasattr(self, 'all_data'):
            self.all_data = {
                "created_at": self.get_current_datetime(),
                "updated_at": self.get_current_datetime(),
                "days": {}
            }
        
        # Aktualizuj datę ostatniej aktualizacji
        self.all_data["updated_at"] = self.get_current_datetime()
        
        # Przygotuj dane dla bieżącego dnia
        day_data = {}
        for row in range(24):
            for col in range(6):
                if self.grid_data[row][col]:
                    activity_name = self.grid_data[row][col]["name"]
                    
                    # Dodaj aktywność do słownika, jeśli jeszcze nie istnieje
                    if activity_name not in day_data:
                        day_data[activity_name] = []
                    
                    # Dodaj współrzędne kwadratu do listy dla danej aktywności
                    day_data[activity_name].append({
                        "row": row,
                        "col": col
                    })
        
        # Zapisz dane dla bieżącego dnia
        self.all_data["days"][date_str] = day_data
    
    def get_current_datetime(self):
        """Zwraca aktualną datę i czas w formacie ISO."""
        return datetime.datetime.now().isoformat()
    
    def autosave_data(self):
        """Automatycznie zapisuje dane do pliku autosave."""
        if not self.data_changed:
            return  # Nie zapisuj, jeśli dane nie zostały zmienione
        
        # Aktualizuj dane w pamięci
        self.update_memory_data()
        
        try:
            # Zapisz dane do pliku autosave
            with open(self.autosave_file, "w", encoding="utf-8") as file:
                file.write(self.custom_json_format(self.all_data))
            
            # Zresetuj flagę zmiany danych
            self.data_changed = False
            
            print(f"Automatyczny zapis: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            error_msg = f"Błąd automatycznego zapisu: {str(e)}"
            print(error_msg)
            # Opcjonalnie: Informacja dla użytkownika
            # QMessageBox.warning(self, "Ostrzeżenie", error_msg)
            return False
    
    def auto_load_data(self):
        """Automatycznie wczytuje dane z pliku autosave przy uruchomieniu."""
        if os.path.exists(self.autosave_file):
            try:
                # Wczytaj dane z pliku autosave
                with open(self.autosave_file, "r", encoding="utf-8") as file:
                    loaded_data = json.load(file)
                
                # Sprawdź format pliku
                if "days" in loaded_data:
                    # Ustaw datę utworzenia, jeśli nie istnieje
                    if "created_at" not in loaded_data:
                        loaded_data["created_at"] = self.get_current_datetime()
                    
                    # Ustaw datę aktualizacji
                    loaded_data["updated_at"] = self.get_current_datetime()
                    
                    # Wczytaj dane
                    self.all_data = loaded_data
                    
                    # Wczytaj dane dla bieżącego dnia
                    self.load_day_data()
                    
                    print(f"Automatyczne wczytanie: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print("Nieznany format pliku autosave")
            except Exception as e:
                print(f"Błąd automatycznego wczytywania: {str(e)}")
    
    def handle_close_event(self, event):
        """Obsługuje zdarzenie zamknięcia okna."""
        # Automatyczny zapis przy zamykaniu aplikacji
        self.autosave_data()
        event.accept()
    
    def custom_json_format(self, data):
        """Niestandardowe formatowanie JSON."""
        # Konwertuj dane do podstawowego JSON
        json_str = json.dumps(data, ensure_ascii=False)
        
        # Wczytaj jako słownik
        parsed = json.loads(json_str)
        
        # Niestandardowe formatowanie
        result = "{\n"
        
        # Dodaj pola created_at i updated_at na początku
        if "created_at" in parsed:
            result += f'  "created_at": "{parsed["created_at"]}",\n'
        if "updated_at" in parsed:
            result += f'  "updated_at": "{parsed["updated_at"]}",\n'
        
        # Formatowanie sekcji days
        result += '  "days": {\n'
        days_items = list(parsed["days"].items())
        for i, (date, day_data) in enumerate(days_items):
            result += f'    "{date}": {{\n'
            
            # Formatowanie aktywności dla danego dnia
            day_activities = list(day_data.items())
            for j, (activity_name, squares) in enumerate(day_activities):
                result += f'      "{activity_name}": [\n'
                
                # Formatowanie kwadratów dla danej aktywności
                for k, square in enumerate(squares):
                    square_str = f'        {{"row": {square["row"]}, "col": {square["col"]}}}'
                    if k < len(squares) - 1:
                        square_str += ','
                    result += square_str + '\n'
                
                result += '      ]'
                if j < len(day_activities) - 1:
                    result += ','
                result += '\n'
            
            result += '    }'
            if i < len(days_items) - 1:
                result += ','
            result += '\n'
        
        result += '  }\n'
        result += '}'
        
        return result
    
    def save_data(self):
        # Najpierw aktualizuj dane w pamięci
        self.update_memory_data()
        
        # Zapytaj o nazwę pliku
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz dane", "", "Pliki JSON (*.json);;Wszystkie pliki (*)"
        )
        
        if not file_name:
            return
        
        # Dodaj rozszerzenie .json jeśli nie zostało podane
        if not file_name.endswith('.json'):
            file_name += '.json'
        
        # Sprawdź czy plik już istnieje
        if os.path.exists(file_name):
            # Zapytaj użytkownika co chce zrobić
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Plik istnieje")
            msgBox.setText(f"Plik {file_name} już istnieje.")
            msgBox.setInformativeText("Co chcesz zrobić?")
            btnUpdate = msgBox.addButton("Zaktualizuj", QMessageBox.ActionRole)
            btnReplace = msgBox.addButton("Zastąp", QMessageBox.ActionRole)
            btnCancel = msgBox.addButton("Anuluj", QMessageBox.RejectRole)
            msgBox.exec_()
            
            if msgBox.clickedButton() == btnUpdate:
                try:
                    # Wczytaj istniejące dane
                    with open(file_name, "r", encoding="utf-8") as file:
                        existing_data = json.load(file)
                    
                    # Sprawdź format pliku
                    if "days" in existing_data:
                        # Zachowaj datę utworzenia
                        if "created_at" in existing_data:
                            self.all_data["created_at"] = existing_data["created_at"]
                        else:
                            self.all_data["created_at"] = self.get_current_datetime()
                        
                        # Aktualizuj datę ostatniej aktualizacji
                        self.all_data["updated_at"] = self.get_current_datetime()
                        
                        # Połącz dane dni, nadpisując istniejące dni jeśli się powtarzają
                        for date_key, date_data in self.all_data["days"].items():
                            existing_data["days"][date_key] = date_data
                        
                        # Aktualizuj datę ostatniej aktualizacji
                        existing_data["updated_at"] = self.get_current_datetime()
                        
                        # Zapisz połączone dane w niestandardowym formacie
                        with open(file_name, "w", encoding="utf-8") as file:
                            file.write(self.custom_json_format(existing_data))
                        
                        QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie zaktualizowane.")
                    else:
                        # Nieznany format - zapytaj czy zastąpić
                        reply = QMessageBox.question(self, "Nieznany format", 
                                                   "Plik ma nieznany format. Czy chcesz go zastąpić?",
                                                   QMessageBox.Yes | QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            # Ustaw datę utworzenia i aktualizacji
                            self.all_data["created_at"] = self.get_current_datetime()
                            self.all_data["updated_at"] = self.get_current_datetime()
                            
                            with open(file_name, "w", encoding="utf-8") as file:
                                file.write(self.custom_json_format(self.all_data))
                            QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie zapisane.")
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie udało się zaktualizować danych: {str(e)}")
                    return
            
            elif msgBox.clickedButton() == btnReplace:
                try:
                    # Ustaw datę utworzenia i aktualizacji
                    self.all_data["created_at"] = self.get_current_datetime()
                    self.all_data["updated_at"] = self.get_current_datetime()
                    
                    # Zastąp plik nowymi danymi w niestandardowym formacie
                    with open(file_name, "w", encoding="utf-8") as file:
                        file.write(self.custom_json_format(self.all_data))
                    QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie zapisane.")
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać danych: {str(e)}")
                    return
            
            elif msgBox.clickedButton() == btnCancel:
                return
        
        else:
            try:
                # Ustaw datę utworzenia i aktualizacji
                self.all_data["created_at"] = self.get_current_datetime()
                self.all_data["updated_at"] = self.get_current_datetime()
                
                # Zapisz dane z pamięci do pliku w niestandardowym formacie
                with open(file_name, "w", encoding="utf-8") as file:
                    file.write(self.custom_json_format(self.all_data))
                
                QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie zapisane.")
                
                # Zresetuj flagę zmiany danych
                self.data_changed = False
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać danych: {str(e)}")
    
    def load_data(self):
        # Zapytaj o nazwę pliku
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj dane", "", "Pliki JSON (*.json);;Wszystkie pliki (*)"
        )
        
        if not file_name:
            return
        
        try:
            # Wczytaj dane z pliku
            with open(file_name, "r", encoding="utf-8") as file:
                loaded_data = json.load(file)
                
            # Sprawdź format pliku
            if "days" in loaded_data:
                # Nowy format - zapytaj użytkownika co chce zrobić
                msgBox = QMessageBox()
                msgBox.setWindowTitle("Wybór danych")
                msgBox.setText("Co chcesz zrobić z wczytanymi danymi?")
                btnZastap = msgBox.addButton("Zastąp wszystkie dane", QMessageBox.ActionRole)
                btnPolacz = msgBox.addButton("Połącz z istniejącymi danymi", QMessageBox.ActionRole)
                btnAnuluj = msgBox.addButton("Anuluj", QMessageBox.RejectRole)
                msgBox.exec_()

                if msgBox.clickedButton() == btnZastap:
                    # Zachowaj datę utworzenia
                    if "created_at" in loaded_data:
                        loaded_data["created_at"] = loaded_data["created_at"]
                    else:
                        loaded_data["created_at"] = self.get_current_datetime()
                    
                    # Aktualizuj datę ostatniej aktualizacji
                    loaded_data["updated_at"] = self.get_current_datetime()
                    
                    # Zastąp wszystkie dane w pamięci
                    self.all_data = loaded_data
                    
                    # Wczytaj dane dla bieżącego dnia
                    self.load_day_data()
                    
                    # Zresetuj flagę zmiany danych
                    self.data_changed = False
                    
                    QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie wczytane.")
                
                elif msgBox.clickedButton() == btnPolacz:
                    # Jeśli nie mamy jeszcze danych w pamięci, inicjalizuj
                    if not hasattr(self, 'all_data'):
                        self.all_data = {
                            "created_at": self.get_current_datetime(),
                            "updated_at": self.get_current_datetime(),
                            "days": {}
                        }
                    
                    # Zachowaj datę utworzenia
                    if "created_at" not in self.all_data:
                        if "created_at" in loaded_data:
                            self.all_data["created_at"] = loaded_data["created_at"]
                        else:
                            self.all_data["created_at"] = self.get_current_datetime()
                    
                    # Aktualizuj datę ostatniej aktualizacji
                    self.all_data["updated_at"] = self.get_current_datetime()
                    
                    # Połącz dane dni, nadpisując istniejące dni jeśli się powtarzają
                    for date_key, date_data in loaded_data["days"].items():
                        self.all_data["days"][date_key] = date_data
                    
                    # Wczytaj dane dla bieżącego dnia
                    self.load_day_data()
                    
                    # Oznacz, że dane zostały zmienione
                    self.data_changed = True
                    
                    QMessageBox.information(self, "Sukces", "Dane zostały pomyślnie połączone.")
            
            else:
                # Stary format lub nieznany - spróbuj obsłużyć
                if isinstance(loaded_data, dict):
                    # To mogą być dane dzienne w starym formacie
                    # Konwertuj na nowy format
                    self.all_data = {
                        "created_at": self.get_current_datetime(),
                        "updated_at": self.get_current_datetime(),
                        "days": loaded_data
                    }
                    
                    # Wczytaj dane dla bieżącego dnia
                    self.load_day_data()
                    
                    # Oznacz, że dane zostały zmienione
                    self.data_changed = True
                    
                    QMessageBox.information(self, "Sukces", "Dane dzienne zostały pomyślnie wczytane i przekonwertowane.")
                else:
                    QMessageBox.warning(self, "Ostrzeżenie", "Nieznany format pliku.")
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać pliku: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać danych: {str(e)}")
    
    def show_statistics(self):
        date_str = self.get_date_string()
        
        # Zbierz dane o czasie spędzonym na każdej aktywności
        activity_times = {}
        for row in range(24):
            for col in range(6):
                if self.grid_data[row][col]:
                    activity_name = self.grid_data[row][col]["name"]
                    if activity_name not in activity_times:
                        activity_times[activity_name] = 0
                    activity_times[activity_name] += 10  # 10 minut na blok
        
        if not activity_times:
            QMessageBox.information(self, "Statystyki", "Brak danych do wyświetlenia.")
            return
        
        # Utwórz okno z wykresem
        stats_window = QWidget()
        stats_window.setWindowTitle(f"Statystyki dla {date_str}")
        stats_window.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(stats_window)
        
        # Dodanie zakładek dla różnych typów statystyk
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Zakładka z wykresem kołowym
        pie_tab = QWidget()
        pie_layout = QVBoxLayout(pie_tab)
        
        # Utwórz wykres kołowy
        pie_figure = plt.figure(figsize=(8, 6))
        pie_canvas = FigureCanvas(pie_figure)
        pie_layout.addWidget(pie_canvas)
        
        pie_ax = pie_figure.add_subplot(111)
        
        labels = []
        sizes = []
        colors = []
        
        for activity_name, minutes in activity_times.items():
            labels.append(f"{activity_name} ({minutes} min)")
            sizes.append(minutes)
            
            # Znajdź kolor dla aktywności
            for activity in self.activities:
                if isinstance(activity, dict) and "name" in activity and activity["name"] == activity_name:
                    colors.append(activity["color"])
                    break
            else:
                colors.append("#CCCCCC")  # Domyślny kolor
        
        # Dostosowanie rozmiaru czcionki
        plt.rcParams.update({'font.size': 10})
        wedges, texts, autotexts = pie_ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        
        # Ustawienie właściwości tekstu, aby był skalowalny
        for text in texts:
            text.set_fontsize('medium')
        for autotext in autotexts:
            autotext.set_fontsize('medium')
            
        pie_ax.axis('equal')
        pie_ax.set_title(f"Podział czasu dla {date_str}")
        
        # Dodanie funkcji do obsługi zmiany rozmiaru
        def on_resize(event):
            # Dostosowanie rozmiaru czcionki do wielkości wykresu
            size = min(event.width, event.height) / 50
            for text in texts:
                text.set_fontsize(size)
            for autotext in autotexts:
                autotext.set_fontsize(size)
            pie_figure.tight_layout()
            
        pie_figure.canvas.mpl_connect('resize_event', on_resize)
        
        pie_canvas.draw()
        
        # Zakładka z wykresem tygodniowym
        week_tab = QWidget()
        week_layout = QVBoxLayout(week_tab)
        
        # Utwórz wykres tygodniowy
        week_figure = plt.figure(figsize=(8, 6))
        week_canvas = FigureCanvas(week_figure)
        week_layout.addWidget(week_canvas)
        
        week_ax = week_figure.add_subplot(111)
        
        # Pobierz dane z całego tygodnia
        week_data = self.get_week_data()
        
        # Przygotuj dane do wykresu
        days = []
        activity_data = {}
        
        for day, day_activities in week_data.items():
            days.append(day)
            for activity_name, minutes in day_activities.items():
                if activity_name not in activity_data:
                    activity_data[activity_name] = []
                # Uzupełnij brakujące dni zerami
                while len(activity_data[activity_name]) < len(days) - 1:
                    activity_data[activity_name].append(0)
                activity_data[activity_name].append(minutes)
        
        # Uzupełnij brakujące wartości dla wszystkich aktywności
        for activity_name in activity_data:
            while len(activity_data[activity_name]) < len(days):
                activity_data[activity_name].append(0)
        
        # Rysuj wykres słupkowy
        bottom = [0] * len(days)
        for activity_name, minutes in activity_data.items():
            # Znajdź kolor dla aktywności
            color = "#CCCCCC"  # Domyślny kolor
            for activity in self.activities:
                if isinstance(activity, dict) and "name" in activity and activity["name"] == activity_name:
                    color = activity["color"]
                    break
            
            week_ax.bar(days, minutes, bottom=bottom, label=activity_name, color=color)
            bottom = [bottom[i] + minutes[i] for i in range(len(days))]
        
        week_ax.set_title("Aktywności w ciągu tygodnia")
        week_ax.set_xlabel("Dzień")
        week_ax.set_ylabel("Czas (minuty)")
        week_ax.legend()
        
        week_canvas.draw()
        
        # Dodaj zakładki do widgetu
        tabs.addTab(pie_tab, "Wykres kołowy")
        tabs.addTab(week_tab, "Wykres tygodniowy")
        
        stats_window.show()
        
        # Zachowaj referencję do okna, aby nie zostało usunięte przez garbage collector
        self.stats_window = stats_window
    
    def get_week_data(self):
        """Pobiera dane o aktywnościach z całego tygodnia."""
        week_data = {}
        
        # Pobierz datę bieżącego dnia
        current_date = self.current_date
        
        # Pobierz dane z 7 dni (bieżący dzień i 6 poprzednich)
        for i in range(7):
            # Oblicz datę
            date = current_date.addDays(-i)
            date_str = date.toString("yyyy-MM-dd")
            display_date = date.toString("dd.MM")
            
            # Sprawdź czy mamy dane w pamięci
            if hasattr(self, 'all_data') and "days" in self.all_data:
                if date_str in self.all_data["days"]:
                    # Zbierz dane o czasie spędzonym na każdej aktywności
                    activity_times = {}
                    
                    for activity_name, squares in self.all_data["days"][date_str].items():
                        if activity_name not in activity_times:
                            activity_times[activity_name] = 0
                        activity_times[activity_name] += len(squares) * 10  # 10 minut na blok
                    
                    week_data[display_date] = activity_times
                else:
                    week_data[display_date] = {}
            else:
                week_data[display_date] = {}
        
        return week_data

    # Nowa metoda do czyszczenia wszystkich kwadratów
    def clear_all_squares(self):
        reply = QMessageBox.question(self, "Potwierdzenie", 
                                    "Czy na pewno chcesz wyczyścić wszystkie kwadraty?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for row in range(24):
                for col in range(6):
                    self.grid_data[row][col] = None
                    self.squares[row][col].set_activity(None)
            
            # Dodanie flagi zmiany danych
            self.data_changed = True
            
            # Opcjonalnie: Informacja dla użytkownika
            QMessageBox.information(self, "Sukces", "Wszystkie kwadraty zostały wyczyszczone.")
    
    # Nowe metody do nawigacji po datach
    def go_to_previous_day(self):
        # Zapisz dane bieżącego dnia do pamięci
        self.update_memory_data()
        
        new_date = self.current_date.addDays(-1)
        self.date_edit.setDate(new_date)
        
    def go_to_next_day(self):
        # Zapisz dane bieżącego dnia do pamięci
        self.update_memory_data()
        
        new_date = self.current_date.addDays(1)
        self.date_edit.setDate(new_date)

    def load_day_data(self):
        # Wyczyść siatkę
        for row in range(24):
            for col in range(6):
                self.grid_data[row][col] = None
                self.squares[row][col].set_activity(None)
        
        # Jeśli mamy dane w pamięci dla bieżącego dnia, załaduj je
        date_str = self.get_date_string()
        if hasattr(self, 'all_data') and self.all_data and "days" in self.all_data:
            if date_str in self.all_data["days"]:
                day_data = self.all_data["days"][date_str]
                
                # Załaduj dane dla bieżącego dnia
                for activity_name, squares in day_data.items():
                    # Znajdź aktywność o podanej nazwie
                    activity_found = False
                    for activity in self.activities:
                        if isinstance(activity, dict) and "name" in activity and activity["name"] == activity_name:
                            # Ustaw aktywność dla wszystkich kwadratów
                            for square_data in squares:
                                row = square_data["row"]
                                col = square_data["col"]
                                self.grid_data[row][col] = activity
                                self.squares[row][col].set_activity(activity)
                            activity_found = True
                            break
                    
                    # Jeśli nie znaleziono aktywności, wyświetl ostrzeżenie
                    if not activity_found:
                        print(f"Ostrzeżenie: Nie znaleziono aktywności '{activity_name}' w bieżącej liście aktywności.")

    def load_activities_from_file(self):
        """Wczytuje aktywności z pliku activities.json."""
        try:
            if os.path.exists(self.activities_file):
                with open(self.activities_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if "activities" in data:  # Sprawdź czy istnieje klucz "activities"
                        activities = data["activities"]  # Pobierz listę aktywności
                        valid_activities = []
                        for activity in activities:
                            if isinstance(activity, dict) and "name" in activity and "color" in activity:
                                valid_activities.append(activity)
                            else:
                                print(f"Pominięto nieprawidłową aktywność: {activity}")
                        return valid_activities
                    else:
                        print("Brak klucza 'activities' w pliku JSON")
                        return []
            else:
                print(f"Nie znaleziono pliku {self.activities_file}")
                return []
        except Exception as e:
            print(f"Błąd wczytywania aktywności: {str(e)}")
            return []

    def save_activities_to_file(self, activities=None):
        """Zapisuje aktywności do pliku activities.json."""
        if activities is None:
            activities = self.activities
        
        try:
            with open(self.activities_file, "w", encoding="utf-8") as file:
                json.dump(activities, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania aktywności: {str(e)}")

    def load_autosave_data(self):
        """Wczytuje dane z pliku autosave, jeśli istnieje."""
        try:
            print(f"Próba wczytania pliku autosave: {self.autosave_file}")
            if os.path.exists(self.autosave_file):
                print(f"Plik {self.autosave_file} istnieje, wczytuję dane...")
                with open(self.autosave_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    print(f"Zawartość pliku: {data.keys()}")
                    
                    # Sprawdź format pliku
                    if "days" in data:
                        print("Znaleziono sekcję 'days' w pliku")
                        # Ustaw datę utworzenia, jeśli nie istnieje
                        if "created_at" not in data:
                            data["created_at"] = self.get_current_datetime()
                        
                        # Ustaw datę aktualizacji
                        data["updated_at"] = self.get_current_datetime()
                        
                        # Wczytaj dane
                        self.all_data = data
                        print(f"Wczytano dane z {len(data['days'])} dni")
                        
                        # Wczytaj dane dla bieżącego dnia
                        self.load_day_data()
                    else:
                        print("Brak sekcji 'days' w pliku autosave")
                    
                    # Wczytaj aktywności z pliku autosave
                    if "activities" in data:
                        print(f"Znaleziono {len(data['activities'])} aktywności w pliku")
                        self.activities = data["activities"]
            else:
                print(f"Plik {self.autosave_file} nie istnieje.")
        except Exception as e:
            print(f"Błąd podczas wczytywania danych z autosave: {str(e)}")
            import traceback
            traceback.print_exc()

    def save_autosave_data(self):
        """Zapisuje dane do pliku autosave."""
        try:
            data = {
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "activities": self.activities,
                "days": self.days_data
            }
            
            with open(self.autosave_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            
            print(f"Zapisano dane do pliku {self.autosave_file}")
        except Exception as e:
            print(f"Błąd podczas zapisywania danych do autosave: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeManagementApp()
    window.show()
    sys.exit(app.exec_())
        
