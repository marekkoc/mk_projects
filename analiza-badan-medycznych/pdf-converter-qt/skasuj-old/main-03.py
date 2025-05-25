#!/usr/bin/env python
# Autor: marekkoc
# Created: 2025-05-11
# Update: 2025-05-22, simplified

import sys
import os
import fitz  # PyMuPDF
import pandas as pd
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QTextEdit, QSplitter, QMessageBox, QScrollArea,
                             QComboBox, QCheckBox, QDialog, QRadioButton,
                             QButtonGroup, QGroupBox, QToolBar, QAction)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QPixmap, QImage, QTextCursor, QPainter, QPen, 
                         QColor, QCursor, QIcon, QFont)


class PDFView(QLabel):
    """Widget do wyświetlania dokumentu PDF."""
    
    def __init__(self):
        super().__init__()
        self.original_pixmap = None
        self.current_pixmap = None
        
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 400)
    
    def setPixmap(self, pixmap):
        """Zapisuje oryginalny pixmap i aktualizuje wyświetlanie."""
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
            
        # Skalowanie z zachowaniem proporcji
        scaled_pixmap = self.original_pixmap.scaled(
            available_width, available_height,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        # Zapisanie aktualnego pixmapa
        self.current_pixmap = scaled_pixmap.copy()
        
        # Wyświetlenie zaktualizowanego pixmapa
        super().setPixmap(self.current_pixmap)
    
    def resizeEvent(self, event):
        """Obsługuje zdarzenie zmiany rozmiaru widgetu."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()


class ExportFormatDialog(QDialog):
    """Dialog wyboru formatu eksportu."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz format eksportu")
        self.resize(350, 200)
        
        layout = QVBoxLayout(self)
        
        # Grupa przycisków dla formatów
        format_group = QGroupBox("Format pliku")
        format_layout = QVBoxLayout()
        
        self.format_group = QButtonGroup(self)
        
        # Formaty eksportu
        self.csv_radio = QRadioButton("CSV (wartości oddzielone przecinkami)")
        self.txt_radio = QRadioButton("Zwykły tekst (TXT)")
        self.md_radio = QRadioButton("Markdown")
        
        # Dodanie przycisków do grupy
        self.format_group.addButton(self.csv_radio, 0)
        self.format_group.addButton(self.txt_radio, 1)
        self.format_group.addButton(self.md_radio, 2)
        
        # Domyślny wybór
        self.csv_radio.setChecked(True)
        
        # Dodanie przycisków do layoutu
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.txt_radio)
        format_layout.addWidget(self.md_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Opcje eksportu
        options_group = QGroupBox("Opcje eksportu")
        options_layout = QVBoxLayout()
        
        self.include_header_check = QCheckBox("Dołącz nagłówki (dla CSV)")
        self.include_header_check.setChecked(True)
        
        options_layout.addWidget(self.include_header_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Przyciski OK/Anuluj
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def get_selected_format(self):
        """Zwraca wybrany format eksportu."""
        format_id = self.format_group.checkedId()
        
        if format_id == 0:
            return "csv"
        elif format_id == 1:
            return "txt"
        elif format_id == 2:
            return "md"
        
        return "csv"  # Domyślny format
    
    def get_export_options(self):
        """Zwraca opcje eksportu."""
        return {
            "include_header": self.include_header_check.isChecked()
        }


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
        
        # Pasek narzędzi
        toolbar = QToolBar("Główny pasek narzędzi")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Górny pasek z przyciskami - ograniczony do max 10% wysokości
        button_widget = QWidget()
        button_widget.setMaximumHeight(70)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(15)
        
        # Większe rozmiary przycisków
        button_size = QSize(150, 35)
        
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
        self.page_label.setMinimumWidth(100)
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
        
        # Dodanie obszaru przewijania i widoku PDF
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.pdf_view = PDFView()
        
        scroll_area.setWidget(self.pdf_view)
        pdf_layout.addWidget(scroll_area, 1)
        
        splitter.addWidget(self.pdf_panel)
        
        # Panel prawy - WYNIKI
        self.results_panel = QWidget()
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.setContentsMargins(5, 5, 5, 5)
        results_layout.setSpacing(0)
        
        results_header = QLabel("WYNIKI")
        results_header.setMaximumHeight(20)
        results_header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        results_layout.addWidget(results_header)
        
        self.text_edit = QTextEdit()
        results_layout.addWidget(self.text_edit, 1)
        
        splitter.addWidget(self.results_panel)
        
        # Ustawienie proporcji splittera
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Dodaj splitter do kontenera z zawartością
        content_layout.addWidget(splitter)
        
        # Dodaj kontener z zawartością do głównego layoutu z dużym udziałem w przestrzeni
        main_layout.addWidget(content_widget, 1)
        
        # Pasek statusu
        self.statusBar().showMessage("Gotowy")
        
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
                self.save_btn.setEnabled(False)
                
                if self.total_pages > 1:
                    self.next_btn.setEnabled(True)
                else:
                    self.next_btn.setEnabled(False)
                    
                self.prev_btn.setEnabled(False)
                
                # Czyszczenie tekstu przy otwarciu nowego pliku
                self.text_edit.clear()
                
                self.statusBar().showMessage(f"Otwarto plik PDF: {os.path.basename(file_path)}")
                
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
        
        # Ustawienie pixmapa
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
        self.save_btn.setEnabled(True)
        
        self.statusBar().showMessage(f"Wyodrębniono tekst ze strony {self.current_page + 1}")
    
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
        """Zapisuje wyodrębniony tekst do pliku w wybranym formacie."""
        if not self.text_edit.toPlainText():
            QMessageBox.warning(self, "Ostrzeżenie", "Brak tekstu do zapisania.")
            return
        
        # Wyświetlenie dialogu wyboru formatu
        dialog = ExportFormatDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Pobranie wybranego formatu i opcji
        selected_format = dialog.get_selected_format()
        options = dialog.get_export_options()
        
        # Przygotowanie filtra dla okna dialogowego zapisywania
        filter_map = {
            "csv": "Plik CSV (*.csv)",
            "txt": "Plik tekstowy (*.txt)",
            "md": "Plik Markdown (*.md)"
        }
        
        # Przygotowanie domyślnego rozszerzenia
        default_ext = "." + selected_format
        
        # Otwórz okno dialogowe do zapisania pliku
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz plik", "", 
            f"{filter_map.get(selected_format, 'Wszystkie pliki (*)')}"
        )
        
        if not file_path:
            return
        
        # Sprawdzenie i dodanie rozszerzenia, jeśli nie zostało podane
        if not any(file_path.endswith(ext) for ext in [".csv", ".txt", ".md"]):
            file_path += default_ext
        
        try:
            self.save_full_text(file_path, selected_format, options)
                
            QMessageBox.information(self, "Sukces", f"Plik został zapisany: {file_path}")
            self.statusBar().showMessage(f"Zapisano plik: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku: {str(e)}")
    
    def save_full_text(self, file_path, format_type, options):
        """Zapisuje pełny tekst z pola tekstowego do pliku w określonym formacie."""
        text = self.text_edit.toPlainText()
        
        if not text:
            raise ValueError("Brak tekstu do zapisania")
        
        # Konwersja tekstu do formatu tabelarycznego dla CSV
        if format_type == "csv":
            # Zakładamy, że każda linia to oddzielny wiersz
            lines = text.split('\n')
            
            # Usuwanie pustych linii
            lines = [line.strip() for line in lines if line.strip()]
            
            # Tworzenie DataFrame
            df = pd.DataFrame({"Tekst": lines})
            
            # Zapisz jako CSV
            df.to_csv(file_path, index=False)
        
        elif format_type == "txt":
            # Zapisz jako zwykły tekst
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        
        elif format_type == "md":
            # Eksport do Markdown
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Wyodrębniony tekst z dokumentu PDF\n\n")
                f.write("```\n")
                f.write(text)
                f.write("\n```\n")
    
    def resizeEvent(self, event):
        """Obsługa zmiany rozmiaru głównego okna."""
        super().resizeEvent(event)
        # Wymuszamy aktualizację UI przy zmianie rozmiaru
        if self.current_pdf is not None:
            # Opóźnione ponowne wyświetlenie strony - zapobiega problemom z wydajnością
            QApplication.processEvents()
            self.display_current_page()


def main():
    """Główna funkcja programu."""
    app = QApplication(sys.argv)
    
    # Ustawienie stylów aplikacji
    app.setStyle("Fusion")
    
    # Niestandardowa paleta kolorów
    palette = app.palette()
    palette.setColor(palette.Window, QColor(245, 245, 245))
    palette.setColor(palette.WindowText, QColor(0, 0, 0))
    palette.setColor(palette.Base, QColor(255, 255, 255))
    palette.setColor(palette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(palette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(palette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(palette.Text, QColor(0, 0, 0))
    palette.setColor(palette.Button, QColor(240, 240, 240))
    palette.setColor(palette.ButtonText, QColor(0, 0, 0))
    palette.setColor(palette.Link, QColor(0, 120, 215))
    palette.setColor(palette.Highlight, QColor(0, 120, 215))
    palette.setColor(palette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # Ustawienie czcionki aplikacji
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = PDFToTextConverter()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
