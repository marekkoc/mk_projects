#!/usr/bin/env python
# Autor: marekkoc
# Created: 2025-05-11
# Update: 2025-05-11, 12:45

import sys
import os
import fitz  # PyMuPDF
import pandas as pd
import markdown
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QTextEdit, QSplitter, QMessageBox, QScrollArea,
                             QComboBox, QCheckBox, QDialog, QRadioButton,
                             QButtonGroup, QGroupBox, QToolBar, QAction)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import (QPixmap, QImage, QTextCursor, QPainter, QPen, 
                         QColor, QCursor, QIcon, QFont)


class SelectableArea:
    """Klasa reprezentująca zaznaczony obszar na stronie PDF."""
    
    def __init__(self, start_point, end_point=None):
        self.start_point = start_point
        self.end_point = end_point if end_point else start_point
        self.text = ""
    
    def normalize(self):
        """Normalizuje koordynaty, aby start_point był zawsze w lewym górnym rogu."""
        x1, y1 = self.start_point.x(), self.start_point.y()
        x2, y2 = self.end_point.x(), self.end_point.y()
        
        return QRect(
            min(x1, x2), min(y1, y2),
            abs(x2 - x1), abs(y2 - y1)
        )
    
    def to_fitz_rect(self, scale_factor):
        """Konwertuje obszar do formatu fitz.Rect z uwzględnieniem skali."""
        rect = self.normalize()
        x1, y1, x2, y2 = rect.left(), rect.top(), rect.right(), rect.bottom()
        
        # Przekształcenie do współrzędnych dokumentu PDF
        x1 /= scale_factor
        y1 /= scale_factor
        x2 /= scale_factor
        y2 /= scale_factor
        
        return fitz.Rect(x1, y1, x2, y2)


class SelectablePDFView(QLabel):
    """Widget umożliwiający zaznaczanie i wyodrębnianie obszarów z dokumentu PDF."""
    
    areaSelected = pyqtSignal(SelectableArea)  # Sygnał emitowany po zaznaczeniu obszaru
    
    def __init__(self):
        super().__init__()
        self.original_pixmap = None
        self.current_pixmap = None
        self.current_page_obj = None
        self.scale_factor = 1.0
        self.selection_mode = False
        self.current_area = None
        self.areas = []
        
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 400)
        
        # Umożliwienie śledzenia myszy
        self.setMouseTracking(True)
        
        # Zmiana kursora w trybie zaznaczania
        self.default_cursor = self.cursor()
        self.selection_cursor = QCursor(Qt.CrossCursor)
    
    def setPixmap(self, pixmap, page_obj=None):
        """Zapisuje oryginalny pixmap i aktualizuje wyświetlanie."""
        self.original_pixmap = pixmap
        self.current_page_obj = page_obj
        self._update_scaled_pixmap()
    
    def clearAreas(self):
        """Czyści wszystkie zaznaczone obszary."""
        self.areas = []
        self._update_display()
    
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
        
        # Obliczenie współczynnika skalowania
        self.scale_factor = scaled_pixmap.width() / self.original_pixmap.width()
        
        # Zapisanie aktualnego pixmapa
        self.current_pixmap = scaled_pixmap.copy()
        
        self._update_display()
    
    def _update_display(self):
        """Aktualizuje wyświetlany obraz z zaznaczonymi obszarami."""
        if self.current_pixmap is None:
            return
        
        # Kopia aktualnego pixmapa do rysowania
        display_pixmap = self.current_pixmap.copy()
        
        # Rysowanie wszystkich zaznaczonych obszarów
        painter = QPainter(display_pixmap)
        painter.setPen(QPen(QColor(0, 162, 232), 2, Qt.SolidLine))
        
        # Półprzezroczysty kolor wypełnienia
        selection_color = QColor(0, 162, 232, 40)  # RGBA (ostatni parametr to alpha - przezroczystość)
        
        # Rysowanie zapisanych obszarów
        for area in self.areas:
            rect = area.normalize()
            painter.fillRect(rect, selection_color)
            painter.drawRect(rect)
        
        # Rysowanie aktualnego zaznaczenia
        if self.current_area and self.current_area.end_point:
            rect = self.current_area.normalize()
            painter.fillRect(rect, selection_color)
            painter.drawRect(rect)
        
        painter.end()
        
        # Wyświetlenie zaktualizowanego pixmapa
        super().setPixmap(display_pixmap)
    
    def toggleSelectionMode(self, enabled):
        """Włącza lub wyłącza tryb zaznaczania."""
        self.selection_mode = enabled
        self.setCursor(self.selection_cursor if enabled else self.default_cursor)
    
    def mousePressEvent(self, event):
        """Obsługuje zdarzenie naciśnięcia przycisku myszy."""
        if self.selection_mode and event.button() == Qt.LeftButton:
            # Rozpoczęcie nowego zaznaczenia
            self.current_area = SelectableArea(event.pos())
            self._update_display()
    
    def mouseMoveEvent(self, event):
        """Obsługuje zdarzenie ruchu myszy."""
        if self.selection_mode and self.current_area and event.buttons() & Qt.LeftButton:
            # Aktualizacja końcowego punktu zaznaczenia
            self.current_area.end_point = event.pos()
            self._update_display()
    
    def mouseReleaseEvent(self, event):
        """Obsługuje zdarzenie zwolnienia przycisku myszy."""
        if self.selection_mode and event.button() == Qt.LeftButton and self.current_area:
            # Zakończenie zaznaczenia
            self.current_area.end_point = event.pos()
            
            # Sprawdzenie czy zaznaczenie ma minimalny rozmiar
            rect = self.current_area.normalize()
            if rect.width() > 5 and rect.height() > 5:
                # Pobranie tekstu z zaznaczonego obszaru
                if self.current_page_obj:
                    fitz_rect = self.current_area.to_fitz_rect(self.scale_factor)
                    self.current_area.text = self.current_page_obj.get_text("text", clip=fitz_rect)
                
                # Dodanie obszaru do listy zaznaczonych
                self.areas.append(self.current_area)
                
                # Emisja sygnału o zaznaczeniu obszaru
                self.areaSelected.emit(self.current_area)
            
            self.current_area = None
            self._update_display()
    
    def resizeEvent(self, event):
        """Obsługuje zdarzenie zmiany rozmiaru widgetu."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()


class ExportFormatDialog(QDialog):
    """Dialog wyboru formatu eksportu."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz format eksportu")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Grupa przycisków dla formatów
        format_group = QGroupBox("Format pliku")
        format_layout = QVBoxLayout()
        
        self.format_group = QButtonGroup(self)
        
        # Formaty eksportu
        self.csv_radio = QRadioButton("CSV (wartości oddzielone przecinkami)")
        self.excel_radio = QRadioButton("Excel (XLSX)")
        self.json_radio = QRadioButton("JSON")
        self.txt_radio = QRadioButton("Zwykły tekst (TXT)")
        self.html_radio = QRadioButton("HTML")
        self.md_radio = QRadioButton("Markdown")
        
        # Dodanie przycisków do grupy
        self.format_group.addButton(self.csv_radio, 0)
        self.format_group.addButton(self.excel_radio, 1)
        self.format_group.addButton(self.json_radio, 2)
        self.format_group.addButton(self.txt_radio, 3)
        self.format_group.addButton(self.html_radio, 4)
        self.format_group.addButton(self.md_radio, 5)
        
        # Domyślny wybór
        self.csv_radio.setChecked(True)
        
        # Dodanie przycisków do layoutu
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.txt_radio)
        format_layout.addWidget(self.html_radio)
        format_layout.addWidget(self.md_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Opcje eksportu
        options_group = QGroupBox("Opcje eksportu")
        options_layout = QVBoxLayout()
        
        self.include_header_check = QCheckBox("Dołącz nagłówki (dla CSV, Excel)")
        self.include_header_check.setChecked(True)
        
        self.include_page_info_check = QCheckBox("Dołącz informacje o stronie")
        self.include_page_info_check.setChecked(True)
        
        options_layout.addWidget(self.include_header_check)
        options_layout.addWidget(self.include_page_info_check)
        
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
            return "xlsx"
        elif format_id == 2:
            return "json"
        elif format_id == 3:
            return "txt"
        elif format_id == 4:
            return "html"
        elif format_id == 5:
            return "md"
        
        return "csv"  # Domyślny format
    
    def get_export_options(self):
        """Zwraca opcje eksportu."""
        return {
            "include_header": self.include_header_check.isChecked(),
            "include_page_info": self.include_page_info_check.isChecked()
        }


class PDFToTextConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_pdf = None
        self.current_page = 0
        self.total_pages = 0
        self.selected_texts = []
        
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
        
        # Przycisk wyboru trybu zaznaczania
        self.select_mode_btn = QPushButton("Tryb zaznaczania")
        self.select_mode_btn.setMinimumSize(button_size)
        self.select_mode_btn.setCheckable(True)
        self.select_mode_btn.clicked.connect(self.toggle_selection_mode)
        self.select_mode_btn.setEnabled(False)
        button_layout.addWidget(self.select_mode_btn)
        
        # Przycisk czyszczenia zaznaczonych obszarów
        self.clear_areas_btn = QPushButton("Wyczyść zaznaczenia")
        self.clear_areas_btn.setMinimumSize(button_size)
        self.clear_areas_btn.clicked.connect(self.clear_selected_areas)
        self.clear_areas_btn.setEnabled(False)
        button_layout.addWidget(self.clear_areas_btn)
        
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
        
        # Dodanie obszaru przewijania i widoku PDF z możliwością zaznaczania
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.pdf_view = SelectablePDFView()
        self.pdf_view.areaSelected.connect(self.on_area_selected)
        
        scroll_area.setWidget(self.pdf_view)
        pdf_layout.addWidget(scroll_area, 1)
        
        splitter.addWidget(self.pdf_panel)
        
        # Panel prawy - WYNIKI
        self.results_panel = QWidget()
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.setContentsMargins(5, 5, 5, 5)
        results_layout.setSpacing(0)
        
        results_header_layout = QHBoxLayout()
        results_header = QLabel("WYNIKI")
        results_header.setMaximumHeight(20)
        results_header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        results_header_layout.addWidget(results_header)
        
        # Dodanie etykiety informującej o liczbie zaznaczonych obszarów
        self.selected_areas_label = QLabel("Zaznaczone obszary: 0")
        self.selected_areas_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        results_header_layout.addWidget(self.selected_areas_label)
        
        results_layout.addLayout(results_header_layout)
        
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
    
    def toggle_selection_mode(self, checked):
        """Włącza lub wyłącza tryb zaznaczania obszarów na PDF."""
        self.pdf_view.toggleSelectionMode(checked)
        
        status = "Tryb zaznaczania włączony - zaznacz obszary na dokumencie" if checked else "Tryb zaznaczania wyłączony"
        self.statusBar().showMessage(status)
    
    def clear_selected_areas(self):
        """Czyści wszystkie zaznaczone obszary."""
        self.pdf_view.clearAreas()
        self.selected_texts = []
        self.update_selected_areas_count()
        self.text_edit.clear()
        self.statusBar().showMessage("Wyczyszczono wszystkie zaznaczenia")
    
    def update_selected_areas_count(self):
        """Aktualizuje licznik zaznaczonych obszarów."""
        count = len(self.selected_texts)
        self.selected_areas_label.setText(f"Zaznaczone obszary: {count}")
    
    def on_area_selected(self, area):
        """Obsługuje zdarzenie zaznaczenia nowego obszaru."""
        if area.text.strip():
            # Dodanie informacji o stronie i pozycji
            area_info = {
                "page": self.current_page + 1,
                "text": area.text.strip(),
                "rect": [
                    area.start_point.x(), area.start_point.y(),
                    area.end_point.x(), area.end_point.y()
                ]
            }
            
            self.selected_texts.append(area_info)
            self.update_selected_areas_count()
            
            # Aktualizacja wyświetlanego tekstu
            self.update_text_display()
            
            self.statusBar().showMessage(f"Zaznaczono obszar zawierający {len(area.text)} znaków")
        else:
            self.statusBar().showMessage("Zaznaczony obszar nie zawiera tekstu")
    
    def update_text_display(self):
        """Aktualizuje wyświetlany tekst z wszystkich zaznaczonych obszarów."""
        text = ""
        
        for i, area_info in enumerate(self.selected_texts):
            if i > 0:
                text += "\n\n"
            
            text += f"--- Obszar {i+1} (Strona {area_info['page']}) ---\n"
            text += area_info["text"]
        
        self.text_edit.setPlainText(text)
        self.save_btn.setEnabled(bool(self.selected_texts))
    
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
                self.select_mode_btn.setEnabled(True)
                self.clear_areas_btn.setEnabled(True)
                
                if self.total_pages > 1:
                    self.next_btn.setEnabled(True)
                else:
                    self.next_btn.setEnabled(False)
                    
                self.prev_btn.setEnabled(False)
                
                # Czyszczenie zaznaczonych obszarów przy otwarciu nowego pliku
                self.clear_selected_areas()
                
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
        
        # Ustawienie oryginalnego pixmapa i obiektu strony
        self.pdf_view.setPixmap(pixmap, page)
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
        
        # Oczyszczenie zaznaczonych obszarów przy zmianie strony
        self.pdf_view.clearAreas()
    
    def next_page(self):
        if self.current_pdf is None or self.current_page >= self.total_pages - 1:
            return
            
        self.current_page += 1
        self.display_current_page()
        self.prev_btn.setEnabled(True)
        
        if self.current_page == self.total_pages - 1:
            self.next_btn.setEnabled(False)
        
        # Oczyszczenie zaznaczonych obszarów przy zmianie strony
        self.pdf_view.clearAreas()
    
    def save_text(self):
        """Zapisuje wyodrębniony tekst do pliku w wybranym formacie."""
        if not self.text_edit.toPlainText() and not self.selected_texts:
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
            "xlsx": "Plik Excel (*.xlsx)",
            "json": "Plik JSON (*.json)",
            "txt": "Plik tekstowy (*.txt)",
            "html": "Plik HTML (*.html)",
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
        if not any(file_path.endswith(ext) for ext in [".csv", ".xlsx", ".json", ".txt", ".html", ".md"]):
            file_path += default_ext
        
        try:
            # Jeśli mamy zaznaczone obszary, używamy ich
            if self.selected_texts:
                self.save_selected_texts(file_path, selected_format, options)
            else:
                # W przeciwnym razie używamy całego tekstu
                self.save_full_text(file_path, selected_format, options)
                
            QMessageBox.information(self, "Sukces", f"Plik został zapisany: {file_path}")
            self.statusBar().showMessage(f"Zapisano plik: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku: {str(e)}")
    
    def save_selected_texts(self, file_path, format_type, options):
        """Zapisuje zaznaczone obszary tekstu do pliku w określonym formacie."""
        include_page_info = options.get("include_page_info", True)
        
        if format_type in ["csv", "xlsx"]:
            # Przygotowanie danych do formatu tabularycznego
            data = []
            for item in self.selected_texts:
                row = {}
                if include_page_info:
                    row["Strona"] = item["page"]
                row["Tekst"] = item["text"]
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Eksport do odpowiedniego formatu
            if format_type == "csv":
                df.to_csv(file_path, index=False)
            elif format_type == "xlsx":
                df.to_excel(file_path, index=False)
        
        elif format_type == "json":
            # Eksport do JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.selected_texts, f, ensure_ascii=False, indent=2)
        
        elif format_type == "txt":
            # Eksport do zwykłego tekstu
            with open(file_path, "w", encoding="utf-8") as f:
                for i, item in enumerate(self.selected_texts):
                    if i > 0:
                        f.write("\n\n")
                    
                    if include_page_info:
                        f.write(f"--- Obszar {i+1} (Strona {item['page']}) ---\n")
                    
                    f.write(item["text"])
        
        elif format_type == "html":
            # Eksport do HTML
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write("<meta charset=\"utf-8\">\n")
                f.write("<title>Wyodrębniony tekst z PDF</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write(".area { margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; }\n")
                f.write(".area-header { font-weight: bold; margin-bottom: 10px; color: #333; }\n")
                f.write(".area-content { white-space: pre-wrap; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                f.write("<h1>Wyodrębniony tekst z dokumentu PDF</h1>\n")
                
                for i, item in enumerate(self.selected_texts):
                    f.write(f"<div class=\"area\">\n")
                    
                    if include_page_info:
                        f.write(f"<div class=\"area-header\">Obszar {i+1} (Strona {item['page']})</div>\n")
                    
                    f.write(f"<div class=\"area-content\">{item['text']}</div>\n")
                    f.write("</div>\n")
                
                f.write("</body>\n</html>")
        
        elif format_type == "md":
            # Eksport do Markdown
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Wyodrębniony tekst z dokumentu PDF\n\n")
                
                for i, item in enumerate(self.selected_texts):
                    if include_page_info:
                        f.write(f"## Obszar {i+1} (Strona {item['page']})\n\n")
                    
                    f.write(f"{item['text']}\n\n")
                    f.write("---\n\n")
    
    def save_full_text(self, file_path, format_type, options):
        """Zapisuje pełny tekst z pola tekstowego do pliku w określonym formacie."""
        text = self.text_edit.toPlainText()
        
        if not text:
            raise ValueError("Brak tekstu do zapisania")
        
        # Konwersja tekstu do formatu tabelarycznego dla CSV i Excel
        if format_type in ["csv", "xlsx"]:
            # Zakładamy, że każda linia to oddzielny wiersz
            lines = text.split('\n')
            
            # Usuwanie pustych linii
            lines = [line.strip() for line in lines if line.strip()]
            
            # Tworzenie DataFrame
            df = pd.DataFrame({"Tekst": lines})
            
            # Zapisz w zależności od wybranego formatu
            if format_type == "csv":
                df.to_csv(file_path, index=False)
            elif format_type == "xlsx":
                df.to_excel(file_path, index=False)
        
        elif format_type == "json":
            # Prosty format JSON dla pełnego tekstu
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"tekst": text}, f, ensure_ascii=False, indent=2)
        
        elif format_type == "txt":
            # Zapisz jako zwykły tekst
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        
        elif format_type == "html":
            # Eksport do HTML
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write("<meta charset=\"utf-8\">\n")
                f.write("<title>Wyodrębniony tekst z PDF</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write(".content { white-space: pre-wrap; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                f.write("<h1>Wyodrębniony tekst z dokumentu PDF</h1>\n")
                f.write(f"<div class=\"content\">{text}</div>\n")
                f.write("</body>\n</html>")
        
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
