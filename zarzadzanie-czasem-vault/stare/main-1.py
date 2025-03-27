import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QGridLayout, 
                            QFrame, QColorDialog, QListWidget, QListWidgetItem,
                            QInputDialog, QFileDialog, QMessageBox)
from PyQt5.QtGui import QColor, QPalette, QIcon
from PyQt5.QtCore import Qt, pyqtSignal
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
        self.setGeometry(100, 100, 800, 600)
        
        self.activities = [
            {"name": "Praca", "color": "#FF5733"},
            {"name": "Sen", "color": "#33A8FF"},
            {"name": "Odpoczynek", "color": "#33FF57"},
            {"name": "Czytanie", "color": "#F3FF33"},
            {"name": "Sport", "color": "#FF33F6"},
            {"name": "Nauka", "color": "#33FFF6"},
            {"name": "Bezczynność", "color": "#AAAAAA"}
        ]
        
        self.grid_data = [[None for _ in range(10)] for _ in range(10)]
        self.selected_activity = None
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Lewa strona - siatka kwadratów
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        grid_label = QLabel("Siatka czasu (każdy kwadrat = 10 minut, łącznie 1000 minut)")
        left_layout.addWidget(grid_label)
        
        grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        grid_widget.setLayout(self.grid_layout)
        
        self.squares = []
        for row in range(10):
            row_squares = []
            for col in range(10):
                square = ColorSquare(row, col)
                square.clicked.connect(self.on_square_clicked)
                self.grid_layout.addWidget(square, row, col)
                row_squares.append(square)
            self.squares.append(row_squares)
        
        left_layout.addWidget(grid_widget)
        
        # Dodanie wykresu statystyk
        self.figure = plt.figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        left_layout.addWidget(self.canvas)
        self.update_stats()
        
        # Prawa strona - panel kontrolny
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        activities_label = QLabel("Aktywności:")
        right_layout.addWidget(activities_label)
        
        self.activities_list = QListWidget()
        self.update_activities_list()
        self.activities_list.itemClicked.connect(self.on_activity_selected)
        right_layout.addWidget(self.activities_list)
        
        add_activity_btn = QPushButton("Dodaj aktywność")
        add_activity_btn.clicked.connect(self.add_activity)
        right_layout.addWidget(add_activity_btn)
        
        remove_activity_btn = QPushButton("Usuń aktywność")
        remove_activity_btn.clicked.connect(self.remove_activity)
        right_layout.addWidget(remove_activity_btn)
        
        clear_selection_btn = QPushButton("Wyczyść zaznaczenie")
        clear_selection_btn.clicked.connect(self.clear_selection)
        right_layout.addWidget(clear_selection_btn)
        
        clear_grid_btn = QPushButton("Wyczyść siatkę")
        clear_grid_btn.clicked.connect(self.clear_grid)
        right_layout.addWidget(clear_grid_btn)
        
        save_btn = QPushButton("Zapisz dane")
        save_btn.clicked.connect(self.save_data)
        right_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Wczytaj dane")
        load_btn.clicked.connect(self.load_data)
        right_layout.addWidget(load_btn)
        
        # Dodanie widgetów do głównego layoutu
        main_layout.addWidget(left_widget, 7)
        main_layout.addWidget(right_widget, 3)
        
    def update_activities_list(self):
        self.activities_list.clear()
        for activity in self.activities:
            item = ActivityItem(activity["name"], activity["color"])
            self.activities_list.addItem(item)
    
    def on_activity_selected(self, item):
        for i, activity in enumerate(self.activities):
            if activity["name"] == item.name:
                self.selected_activity = activity
                break
    
    def on_square_clicked(self, row, col):
        if self.selected_activity:
            if self.grid_data[row][col] == self.selected_activity:
                # Odznaczenie kwadratu
                self.grid_data[row][col] = None
                self.squares[row][col].set_activity(None)
            else:
                # Zaznaczenie kwadratu
                self.grid_data[row][col] = self.selected_activity
                self.squares[row][col].set_activity(self.selected_activity)
            self.update_stats()
    
    def add_activity(self):
        name, ok = QInputDialog.getText(self, "Nowa aktywność", "Nazwa aktywności:")
        if ok and name:
            color = QColorDialog.getColor()
            if color.isValid():
                self.activities.append({
                    "name": name,
                    "color": color.name()
                })
                self.update_activities_list()
    
    def remove_activity(self):
        current_item = self.activities_list.currentItem()
        if current_item:
            for i, activity in enumerate(self.activities):
                if activity["name"] == current_item.name:
                    # Usunięcie aktywności z siatki
                    for row in range(10):
                        for col in range(10):
                            if self.grid_data[row][col] == activity:
                                self.grid_data[row][col] = None
                                self.squares[row][col].set_activity(None)
                    
                    # Usunięcie aktywności z listy
                    del self.activities[i]
                    self.update_activities_list()
                    self.update_stats()
                    break
    
    def clear_selection(self):
        self.selected_activity = None
        self.activities_list.clearSelection()
    
    def clear_grid(self):
        reply = QMessageBox.question(self, "Potwierdzenie", 
                                     "Czy na pewno chcesz wyczyścić całą siatkę?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in range(10):
                for col in range(10):
                    self.grid_data[row][col] = None
                    self.squares[row][col].set_activity(None)
            self.update_stats()
    
    def update_stats(self):
        self.figure.clear()
        
        # Liczenie aktywności
        activity_counts = {}
        for activity in self.activities:
            activity_counts[activity["name"]] = 0
        
        for row in range(10):
            for col in range(10):
                if self.grid_data[row][col]:
                    activity_name = self.grid_data[row][col]["name"]
                    activity_counts[activity_name] += 1
        
        # Filtrowanie tylko tych aktywności, które mają wartości > 0
        labels = []
        sizes = []
        colors = []
        
        for activity in self.activities:
            count = activity_counts[activity["name"]]
            if count > 0:
                labels.append(f"{activity['name']} ({count*10} min)")
                sizes.append(count)
                colors.append(activity["color"])
        
        if sizes:
            ax = self.figure.add_subplot(111)
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Podział czasu')
        
        self.canvas.draw()
    
    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Zapisz dane", "", "JSON Files (*.json)")
        if filename:
            data = {
                "activities": self.activities,
                "grid_data": []
            }
            
            for row in range(10):
                for col in range(10):
                    if self.grid_data[row][col]:
                        data["grid_data"].append({
                            "row": row,
                            "col": col,
                            "activity": self.grid_data[row][col]["name"]
                        })
            
            with open(filename, 'w') as f:
                json.dump(data, f)
            
            QMessageBox.information(self, "Zapisano", "Dane zostały zapisane pomyślnie.")
    
    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Wczytaj dane", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Wczytanie aktywności
                self.activities = data["activities"]
                self.update_activities_list()
                
                # Wyczyszczenie siatki
                for row in range(10):
                    for col in range(10):
                        self.grid_data[row][col] = None
                        self.squares[row][col].set_activity(None)
                
                # Wczytanie danych siatki
                for item in data["grid_data"]:
                    row = item["row"]
                    col = item["col"]
                    activity_name = item["activity"]
                    
                    for activity in self.activities:
                        if activity["name"] == activity_name:
                            self.grid_data[row][col] = activity
                            self.squares[row][col].set_activity(activity)
                            break
                
                self.update_stats()
                QMessageBox.information(self, "Wczytano", "Dane zostały wczytane pomyślnie.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wczytywania danych: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeManagementApp()
    window.show()
    sys.exit(app.exec_())