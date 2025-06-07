#!/home/marek/miniconda3/envs/py312/bin/python
"""
Created: 2025.02.23
Modified: 2025.03.13
"""


import sys
import random
from pathlib import Path
from turtle import home
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QSizePolicy, QHBoxLayout,
                            QSystemTrayIcon, QMenu)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from mkenvs import EnvVars
from mkquotes import FilePaths
from mkquotes import QuoteSelector

class QuoteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.quotes = self.read_quotes()
        self.shown_quotes = set()
        
        # Flaga wskazująca czy zamknięcie okna było celowe czy automatyczne
        self.auto_hide = False
        
        self.initUI()
        self.setupSystemTray()
        
    def read_quotes(self):
        try:
            pth = FilePaths("dawka-motywacji")
            quote_selector = QuoteSelector(pth)
            quotes = quote_selector.get_quotes()
            return quotes
        except FileNotFoundError:
            print(f"Nie znaleziono pliku: {str(pth)}")
            return []

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

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_application(self):
        self.timer.stop()
        QApplication.quit()

    def initUI(self):
        self.setWindowTitle('Cytat Motywacyjny')
        self.setMinimumWidth(400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.quote_label = QLabel("Ładowanie cytatu...")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        quote_font = QFont()
        quote_font.setPointSize(12)
        self.quote_label.setFont(quote_font)
        
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignRight)
        author_font = QFont()
        author_font.setPointSize(10)
        author_font.setItalic(True)
        self.author_label.setFont(author_font)
        
        button_layout = QHBoxLayout()
        
        next_quote_button = QPushButton('Losuj nowy cytat')
        next_quote_button.clicked.connect(self.show_quote)
        next_quote_button.setMinimumWidth(100)
        
        hide_button = QPushButton('Ukryj')
        hide_button.clicked.connect(self.hide_window)
        hide_button.setMinimumWidth(100)
        
        button_layout.addWidget(next_quote_button)
        button_layout.addWidget(hide_button)
        
        layout.addWidget(self.quote_label)
        layout.addWidget(self.author_label)
        layout.addLayout(button_layout)
        
        self.show_quote()
        
        # Timer do automatycznego pokazywania okna
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_show)
        self.timer.start(300000)  # 5 minut (300000 ms)

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

    def show_quote(self):
        quote_data = self.get_random_quote()
        if quote_data:
            quote = quote_data.tekst
            author = quote_data.autor
            self.quote_label.setText(quote)
            self.author_label.setText(f"— {author}")
            self.adjustSize()
        else:
            self.quote_label.setText("Nie udało się załadować cytatów")
            self.author_label.setText("")

    def auto_show(self):
        self.show_quote()
        self.show_and_raise()

    def hide_window(self):
        self.auto_hide = True
        self.hide()

    def closeEvent(self, event):
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Zapobieganie zamknięciu aplikacji po zamknięciu ostatniego okna
    app.setQuitOnLastWindowClosed(False)
    
    app.setStyle('Fusion')
    
    window = QuoteWindow()
    window.show()
    
    sys.exit(app.exec_())
