#!/usr/bin/env python
# Autor: marekkoc
# Created: 2025-05-11
# Update: 2025-05-11, 14:30

import sys
import os
import fitz  # PyMuPDF
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QTextEdit, QSplitter, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap, QImage, QTextCursor, QResizeEvent


class ScalablePDFView(QLabel):
    """Widget wyświetlający stronę PDF z automatycznym skalowaniem."""
    
    def __init__(self):
        super().__init__()
        self.original_pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 400)  # Zmniejszenie minimalnego rozmiaru
        
    def setPixmap(self, pixmap):
        """Zapisuje oryginalny pixmap i wyświetla go po skalowaniu."""
        self.original_pixmap = pixmap
        self._update_scaled_pixmap()
        
    def _update_scaled_pixmap(self):
        """Aktualizuje wyświetlany pixmap przy zachowaniu proporcji."""
        if self.original_pixmap is None:
            return
        
        # Określenie dostępnej przestrzeni
        available_width = self.width() - 10  # Margines
        available_height = self.height() - 10  # Margines
        
        if available_width <= 0 or available_height <= 0:
            return
            
        # Skalowanie z zachowaniem proporcji, wykorzystując maksymalną dostępną przestrzeń
        scaled_pixmap = self.original_pixmap.scaled(
            available_width, available_height,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        super().setPixmap(scaled_pixmap)
        
    def resizeEvent(self, event):
        """Obsługuje zdarzenie zmiany rozmiaru widgetu."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()


class PDFToTextConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_pdf = None
        self.current_page = 0
        self.total_pages = 0
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Konwerter PDF do tekstu")
        self.setGeometry(100, 100, 1200, 800)
        
        # Główny widget i layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Górny pasek z przyciskami - ograniczony do max 10% wysokości
        button_widget = QWidget()
        button_widget.setMaximumHeight(70)  # Zwiększenie maksymalnej wysokości
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(15)  # Zwiększony odstęp między przyciskami
        
        # Większe rozmiary przycisków
        button_size = QSize(150, 35)  # Zwiększony rozmiar przycisków
        
        self.open_btn = QPushButton("Otwórz PDF")
        self.open_btn.setMinimumSize(button_size)
        self.open_btn.clicked.connect(self.open_pdf)
        button_layout.addWidget(self.open_btn)
        
        self.extract_btn = QPushButton("Wyodrębnij tekst")
        self.extract_btn.setMinimumSize(button_size)
        self.extract_btn.clicked.connect(self.extract_text)
        self.extract_btn.setEnabled(False)
        button_layout.addWidget(self.extract_btn)
        
        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setMinimumSize(button_size)
        self.save_btn.clicked.connect(self.save_text)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.prev_btn = QPushButton("Poprzednia")
        self.prev_btn.setMinimumSize(button_size)
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        button_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Następna")
        self.next_btn.setMinimumSize(button_size)
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        button_layout.addWidget(self.next_btn)
        
        self.page_label = QLabel("Strona: 0/0")
        self.page_label.setMinimumWidth(100)  # Zapewnienie minimalnej szerokości dla etykiety
        button_layout.addWidget(self.page_label)
        
        # Dodanie elastycznego spacera na końcu
        button_layout.addStretch(1)
        
        # Dodanie panelu przycisków z małym udziałem w głównym layoucie
        main_layout.addWidget(button_widget)
        
        # Kontener na widoki PDF i tekstu (zajmuje pozostałą przestrzeń)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter do podziału na dwa panele
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel lewy - PDF
        self.pdf_panel = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_panel)
        pdf_layout.setContentsMargins(5, 5, 5, 5)
        pdf_layout.setSpacing(0)
        
        pdf_header = QLabel("PDF")
        pdf_header.setMaximumHeight(20)
        pdf_header.setAlignment(Qt.AlignCenter)
        pdf_layout.addWidget(pdf_header)
        
        # Dodanie obszaru przewijania i skalowanego widoku PDF
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.pdf_view = ScalablePDFView()
        
        scroll_area.setWidget(self.pdf_view)
        pdf_layout.addWidget(scroll_area, 1)  # Stretch factor 1 - zajmuje całą dostępną przestrzeń
        
        splitter.addWidget(self.pdf_panel)
        
        # Panel prawy - WYNIKI
        self.results_panel = QWidget()
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.setContentsMargins(5, 5, 5, 5)
        results_layout.setSpacing(0)
        
        results_header = QLabel("WYNIKI")
        results_header.setMaximumHeight(20)
        results_header.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(results_header)
        
        self.text_edit = QTextEdit()
        results_layout.addWidget(self.text_edit, 1)  # Stretch factor 1
        
        splitter.addWidget(self.results_panel)
        
        # Ustawienie proporcji splittera
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Dodaj splitter do kontenera z zawartością
        content_layout.addWidget(splitter)
        
        # Dodaj kontener z zawartością do głównego layoutu z dużym udziałem w przestrzeni
        main_layout.addWidget(content_widget, 1)  # Stretch factor 1
        
        # Ustaw widget centralny
        self.setCentralWidget(central_widget)
        
    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik PDF", "", "Pliki PDF (*.pdf)")
        
        if file_path:
            try:
                self.current_pdf = fitz.open(file_path)
                self.current_page = 0
                self.total_pages = len(self.current_pdf)
                
                self.page_label.setText(f"Strona: {self.current_page + 1}/{self.total_pages}")
                self.display_current_page()
                
                self.extract_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                
                if self.total_pages > 1:
                    self.next_btn.setEnabled(True)
                else:
                    self.next_btn.setEnabled(False)
                    
                self.prev_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można otworzyć pliku PDF: {str(e)}")
    
    def display_current_page(self):
        if self.current_pdf is None:
            return
            
        page = self.current_pdf[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        
        # Konwersja pixmapy na QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Ustawienie oryginalnego pixmapa - skalowanie zostanie wykonane w klasie ScalablePDFView
        self.pdf_view.setPixmap(pixmap)
        self.page_label.setText(f"Strona: {self.current_page + 1}/{self.total_pages}")
    
    def extract_text(self):
        if self.current_pdf is None:
            return
            
        text = ""
        if self.total_pages > 0:
            page = self.current_pdf[self.current_page]
            text = page.get_text()
            
        self.text_edit.setPlainText(text)
    
    def prev_page(self):
        if self.current_pdf is None or self.current_page <= 0:
            return
            
        self.current_page -= 1
        self.display_current_page()
        self.next_btn.setEnabled(True)
        
        if self.current_page == 0:
            self.prev_btn.setEnabled(False)
    
    def next_page(self):
        if self.current_pdf is None or self.current_page >= self.total_pages - 1:
            return
            
        self.current_page += 1
        self.display_current_page()
        self.prev_btn.setEnabled(True)
        
        if self.current_page == self.total_pages - 1:
            self.next_btn.setEnabled(False)
    
    def save_text(self):
        text = self.text_edit.toPlainText()
        if not text:
            QMessageBox.warning(self, "Ostrzeżenie", "Brak tekstu do zapisania.")
            return
            
        # Konwersja tekstu do formatu tabularycznego
        # Zakładamy, że każda linia to oddzielny wiersz
        lines = text.split('\n')
        
        # Usuwanie pustych linii
        lines = [line.strip() for line in lines if line.strip()]
        
        # Tworzenie DataFrame
        df = pd.DataFrame({"Tekst": lines})
        
        # Otwórz okno dialogowe do zapisania pliku
        file_path, file_filter = QFileDialog.getSaveFileName(
            self, "Zapisz plik", "", 
            "Plik CSV (*.csv);;Plik Excel (*.xlsx);;Plik JSON (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            # Zapisz w zależności od wybranego formatu
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            elif file_path.endswith('.json'):
                df.to_json(file_path, orient='records', lines=True)
            else:
                # Dodaj domyślne rozszerzenie .csv jeśli nie określono
                if '.' not in os.path.basename(file_path):
                    file_path += '.csv'
                df.to_csv(file_path, index=False)
                
            QMessageBox.information(self, "Sukces", f"Plik został zapisany: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku: {str(e)}")
    
    def resizeEvent(self, event):
        """Obsługa zmiany rozmiaru głównego okna."""
        super().resizeEvent(event)
        # Wymuszamy aktualizację UI przy zmianie rozmiaru
        if self.current_pdf is not None:
            # Opóźnione ponowne wyświetlenie strony - zapobiega problemom z wydajnością
            QApplication.processEvents()
            self.display_current_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFToTextConverter()
    window.show()
    sys.exit(app.exec_())
