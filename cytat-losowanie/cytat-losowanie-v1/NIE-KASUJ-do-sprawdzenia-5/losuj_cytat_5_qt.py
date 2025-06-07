#!/home/marek/miniconda3/envs/py312/bin/python
"""
Created: 2025.02.24
Modified: 2025.03.13
"""

import sys
import random
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QSizePolicy, QHBoxLayout,
                            QSystemTrayIcon, QMenu, QSpinBox, QFormLayout,
                            QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from mkquotes import FilePaths
from mkquotes import QuoteSelector

class QuoteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.quotes = self.read_quotes()
        self.shown_quotes = set()
        
        # Domyślne czasy (w minutach)
        self.work_time = 25
        self.break_time = 5
        
        # Flagi dla trybu pracy
        self.is_work_mode = True
        
        self.initUI()
        self.setupSystemTray()
        
        # Inicjalizacja timerów
        self.work_timer = QTimer(self)
        self.work_timer.timeout.connect(self.switch_to_break)
        
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.switch_to_work)
        
        # Rozpocznij od trybu pracy
        self.start_work_mode()

    def read_quotes(self):      
        pth = FilePaths("dawka-motywacji")
        quote_selector = QuoteSelector(pth)
        quotes = quote_selector.get_quotes()
        return quotes               
        
    def setupSystemTray(self):
        # Utworzenie ikony w zasobniku systemowym
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        # Menu kontekstowe dla ikony
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Pokaż cytat")
        show_action.triggered.connect(self.show_and_raise)
        
        quit_action = tray_menu.addAction("Zakończ")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Obsługa kliknięcia w ikonę
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def initUI(self):
        self.setWindowTitle('Cytat Motywacyjny - Pomodoro')
        self.setMinimumWidth(500)  # Zwiększamy minimalną szerokość
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Dodajemy label informujący o trybie
        self.mode_label = QLabel()
        self.mode_label.setAlignment(Qt.AlignCenter)
        mode_font = QFont()
        mode_font.setPointSize(14)
        mode_font.setBold(True)
        self.mode_label.setFont(mode_font)
        
        # Ustawienia dla cytatu
        self.quote_label = QLabel("Ładowanie cytatu...")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.quote_label.setMinimumHeight(100)  # Minimalna wysokość
        self.quote_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        quote_font = QFont()
        quote_font.setPointSize(12)
        self.quote_label.setFont(quote_font)
        
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignRight)
        author_font = QFont()
        author_font.setPointSize(10)
        author_font.setItalic(True)
        self.author_label.setFont(author_font)
        
        # Grupa ustawień czasów
        settings_group = QGroupBox("Ustawienia Pomodoro")
        settings_layout = QFormLayout()
        
        self.work_time_spin = QSpinBox()
        self.work_time_spin.setRange(1, 60)
        self.work_time_spin.setValue(self.work_time)
        self.work_time_spin.valueChanged.connect(self.update_work_time)
        
        self.break_time_spin = QSpinBox()
        self.break_time_spin.setRange(1, 30)
        self.break_time_spin.setValue(self.break_time)
        self.break_time_spin.valueChanged.connect(self.update_break_time)
        
        settings_layout.addRow("Czas pracy (min):", self.work_time_spin)
        settings_layout.addRow("Czas przerwy (min):", self.break_time_spin)
        settings_group.setLayout(settings_layout)
        
        # Przyciski
        button_layout = QHBoxLayout()
        
        next_quote_button = QPushButton('Losuj nowy cytat')
        next_quote_button.clicked.connect(self.show_quote)
        next_quote_button.setMinimumWidth(100)
        
        hide_button = QPushButton('Ukryj')
        hide_button.clicked.connect(self.hide_window)
        hide_button.setMinimumWidth(100)
        
        button_layout.addWidget(next_quote_button)
        button_layout.addWidget(hide_button)
        
        # Dodawanie wszystkich elementów do głównego layoutu
        layout.addWidget(self.mode_label)
        layout.addWidget(settings_group)
        layout.addWidget(self.quote_label)
        layout.addWidget(self.author_label)
        layout.addLayout(button_layout)
        
        self.show_quote()

    def update_work_time(self, value):
        self.work_time = value
        if self.is_work_mode:
            self.start_work_mode()
            
    def update_break_time(self, value):
        self.break_time = value
        if not self.is_work_mode:
            self.start_break_mode()
            
    def start_work_mode(self):
        self.is_work_mode = True
        self.mode_label.setText("Tryb pracy")
        self.mode_label.setStyleSheet("color: green")
        self.work_timer.start(self.work_time * 60000)  # Konwersja na milisekundy
        self.break_timer.stop()
        self.show_quote()
        
    def start_break_mode(self):
        self.is_work_mode = False
        self.mode_label.setText("Przerwa")
        self.mode_label.setStyleSheet("color: red")
        self.break_timer.start(self.break_time * 60000)  # Konwersja na milisekundy
        self.work_timer.stop()
        self.show_quote()
        
    def switch_to_break(self):
        self.start_break_mode()
        self.show_and_raise()
        
    def switch_to_work(self):
        self.start_work_mode()
        self.show_and_raise()

    def show_quote(self):
        quote_data = self.get_random_quote()
        if quote_data:
            quote = quote_data.tekst
            author = quote_data.autor
            self.quote_label.setText(quote)
            self.author_label.setText(f"— {author}")
            
            # Wymuszamy przeliczenie layoutu
            self.adjustSize()
            QApplication.processEvents()
            
            # Dodatkowe dostosowanie rozmiaru
            current_size = self.size()
            self.setMinimumHeight(current_size.height() + 50)  # Dodajemy margines
        else:
            self.quote_label.setText("Nie udało się załadować cytatów")
            self.author_label.setText("")

    def get_random_quote(self):
        if len(self.shown_quotes) == len(self.quotes):
            self.shown_quotes.clear()
        
        available_quotes = [(i, q) for i, q in enumerate(self.quotes) 
                          if i not in self.shown_quotes]
        if not available_quotes:
            return None
        
        index, quote = random.choice(available_quotes)
        self.shown_quotes.add(index)
        return quote

    def hide_window(self):
        self.hide()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def quit_application(self):
        self.work_timer.stop()
        self.break_timer.stop()
        QApplication.quit()

    def closeEvent(self, event):
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    
    window = QuoteWindow()
    window.show()
    
    sys.exit(app.exec_())
