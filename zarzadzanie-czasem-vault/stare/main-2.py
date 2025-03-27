import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QGridLayout, 
                            QFrame, QColorDialog, QListWidget, QListWidgetItem,
                            QInputDialog, QFileDialog, QMessageBox, QDateEdit)
from PyQt5.QtGui import QColor, QPalette, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QDate
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
        
        # Predefiniowana paleta 16 kolorów
        self.color_palette = [
            "#FF5733", "#33A8FF", "#33FF57", "#F3FF33", 
            "#FF33F6", "#33FFF6", "#AAAAAA", "#FF8C33", 
            "#3357FF", "#8CFF33", "#FFDB33", "#FF33A8", 
            "#33FFDB", "#666666", "#C133FF", "#33FFA8"
        ]
        
        self.activities = [
            {"name": "Praca", "color": self.color_palette[0]},
            {"name": "Sen", "color": self.color_palette[1]},
            {"name": "Odpoczynek", "color": self.color_palette[2]},
            {"name": "Czytanie", "color": self.color_palette[3]},
            {"name": "Sport", "color": self.color_palette[4]},
            {"name": "Nauka", "color": self.color_palette[5]},
            {"name": "Bezczynność", "color": self.color_palette[6]}
        ]
        
        # Zmiana układu siatki: 24 wiersze (godziny) x 6 kolumn (10-minutowe bloki)
        self.grid_data = [[None for _ in range(6)] for _ in range(24)]
        self.selected_activity = None
        self.current_date = QDate.currentDate()
        
        self.init_ui()
        
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
        self.date_edit = QDateEdit(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.change_date)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        left_layout.addLayout(date_layout)
        
        # Lista aktywności
        activity_label = QLabel("Aktywności:")
        left_layout.addWidget(activity_label)
        
        self.activity_list = QListWidget()
        self.update_activity_list()
        self.activity_list.itemClicked.connect(self.select_activity)
        left_layout.addWidget(self.activity_list)
        
        # Przyciski zarządzania aktywnościami
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Dodaj")
        add_button.clicked.connect(self.add_activity)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edytuj")
        edit_button.clicked.connect(self.edit_activity)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Usuń")
        delete_button.clicked.connect(self.delete_activity)
        buttons_layout.addWidget(delete_button)
        
        left_layout.addLayout(buttons_layout)
        
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
                grid_layout.addWidget(square, row + 1, col + 1)
                row_squares.append(square)
            self.squares.append(row_squares)
        
        right_layout.addLayout(grid_layout)
        
        # Dodaj panele do głównego układu
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)
        
        self.load_day_data()
    
    def update_activity_list(self):
        self.activity_list.clear()
        for activity in self.activities:
            item = ActivityItem(activity["name"], activity["color"])
            self.activity_list.addItem(item)
    
    def select_activity(self, item):
        for i, activity in enumerate(self.activities):
            if activity["name"] == item.name:
                self.selected_activity = activity
                break
    
    def square_clicked(self, row, col):
        if self.selected_activity:
            self.grid_data[row][col] = self.selected_activity
            self.squares[row][col].set_activity(self.selected_activity)
        else:
            QMessageBox.warning(self, "Ostrzeżenie", "Najpierw wybierz aktywność!")
    
    def add_activity(self):
        name, ok = QInputDialog.getText(self, "Dodaj aktywność", "Nazwa aktywności:")
        if ok and name:
            color_dialog = QColorDialog(self)
            color = color_dialog.getColor()
            if color.isValid():
                color_hex = color.name()
                new_activity = {"name": name, "color": color_hex}
                self.activities.append(new_activity)
                self.update_activity_list()
    
    def edit_activity(self):
        if not self.activity_list.currentItem():
            QMessageBox.warning(self, "Ostrzeżenie", "Wybierz aktywność do edycji!")
            return
        
        current_item = self.activity_list.currentItem()
        current_index = self.activity_list.currentRow()
        
        name, ok = QInputDialog.getText(self, "Edytuj aktywność", 
                                       "Nazwa aktywności:", text=current_item.name)
        if ok and name:
            color_dialog = QColorDialog(self)
            color = color_dialog.getColor(QColor(current_item.color))
            if color.isValid():
                color_hex = color.name()
                self.activities[current_index]["name"] = name
                self.activities[current_index]["color"] = color_hex
                self.update_activity_list()
                
                # Aktualizuj siatkę
                self.update_grid()
    
    def delete_activity(self):
        if not self.activity_list.currentItem():
            QMessageBox.warning(self, "Ostrzeżenie", "Wybierz aktywność do usunięcia!")
            return
        
        current_index = self.activity_list.currentRow()
        reply = QMessageBox.question(self, "Potwierdzenie", 
                                    f"Czy na pewno chcesz usunąć '{self.activities[current_index]['name']}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            deleted_activity = self.activities.pop(current_index)
            self.update_activity_list()
            
            # Usuń aktywność z siatki
            for row in range(24):
                for col in range(6):
                    if (self.grid_data[row][col] is not None and 
                        self.grid_data[row][col]["name"] == deleted_activity["name"]):
                        self.grid_data[row][col] = None
                        self.squares[row][col].set_activity(None)
    
    def update_grid(self):
        for row in range(24):
            for col in range(6):
                if self.grid_data[row][col] is not None:
                    activity_name = self.grid_data[row][col]["name"]
                    # Znajdź aktualną aktywność o tej samej nazwie
                    found = False
                    for activity in self.activities:
                        if activity["name"] == activity_name:
                            self.grid_data[row][col] = activity
                            self.squares[row][col].set_activity(activity)
                            found = True
                            break
                    if not found:
                        self.grid_data[row][col] = None
                        self.squares[row][col].set_activity(None)
    
    def change_date(self, date):
        # Zapisz dane bieżącego dnia
        self.save_day_data()
        
        # Zmień datę i wczytaj dane dla nowej daty
        self.current_date = date
        self.load_day_data()
    
    def get_date_string(self):
        return self.current_date.toString("yyyy-MM-dd")
    
    def save_day_data(self):
        date_str = self.get_date_string()
        data = []
        for row in range(24):
            for col in range(6):
                if self.grid_data[row][col]:
                    data.append({
                        "row": row,
                        "col": col,
                        "activity": self.grid_data[row][col]["name"]
                    })
        
        try:
            # Wczytaj istniejące dane
            try:
                with open("time_data.json", "r") as file:
                    all_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                all_data = {}
            
            # Aktualizuj dane dla bieżącego dnia
            all_data[date_str] = data
            
            # Zapisz wszystkie dane
            with open("time_data.json", "w") as file:
                json.dump(all_data, file)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać danych: {str(e)}")
    
    def load_day_data(self):
        # Wyczyść siatkę
        for row in range(24):
            for col in range(6):
                self.grid_data[row][col] = None
                self.squares[row][col].set_activity(None)
        
        date_str = self.get_date_string()
        try:
            # Wczytaj dane
            try:
                with open("time_data.json", "r") as file:
                    all_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                return
            
            # Sprawdź czy istnieją dane dla wybranego dnia
            if date_str not in all_data:
                return
            
            # Wypełnij siatkę danymi
            for item in all_data[date_str]:
                row = item["row"]
                col = item["col"]
                activity_name = item["activity"]
                
                # Znajdź aktywność o podanej nazwie
                for activity in self.activities:
                    if activity["name"] == activity_name:
                        self.grid_data[row][col] = activity
                        self.squares[row][col].set_activity(activity)
                        break
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać danych: {str(e)}")
    
    def save_data(self):
        # Zapisz bieżący dzień
        self.save_day_data()
        
        # Zapisz listę aktywności
        try:
            with open("activities.json", "w") as file:
                json.dump(self.activities, file)
            QMessageBox.information(self, "Sukces", "Dane zostały zapisane pomyślnie.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać aktywności: {str(e)}")
    
    def load_data(self):
        try:
            # Wczytaj listę aktywności
            try:
                with open("activities.json", "r") as file:
                    self.activities = json.load(file)
                self.update_activity_list()
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Wczytaj dane dla bieżącego dnia
            self.load_day_data()
            
            QMessageBox.information(self, "Sukces", "Dane zostały wczytane pomyślnie.")
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
        stats_window.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(stats_window)
        
        # Utwórz wykres kołowy
        figure = plt.figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        
        ax = figure.add_subplot(111)
        
        labels = []
        sizes = []
        colors = []
        
        for activity_name, minutes in activity_times.items():
            labels.append(f"{activity_name} ({minutes} min)")
            sizes.append(minutes)
            
            # Znajdź kolor dla aktywności
            for activity in self.activities:
                if activity["name"] == activity_name:
                    colors.append(activity["color"])
                    break
            else:
                colors.append("#CCCCCC")  # Domyślny kolor
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title(f"Podział czasu dla {date_str}")
        
        canvas.draw()
        stats_window.show()
        
        # Zachowaj referencję do okna, aby nie zostało usunięte przez garbage collector
        self.stats_window = stats_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeManagementApp()
    window.show()
    sys.exit(app.exec_())
        