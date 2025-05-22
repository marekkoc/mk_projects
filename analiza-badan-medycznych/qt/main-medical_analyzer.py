import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                            QComboBox, QTableView, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, QAbstractTableModel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Model dla wyświetlania danych w tabeli
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None

# Klasa wykresu wykorzystująca matplotlib
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

# Główna klasa aplikacji
class MedicalAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = None
        
        # Globalne ustawienia czcionek dla matplotlib - znacznie większe wartości
        plt.rcParams.update({
            'font.size': 32,
            'axes.labelsize': 30,
            'axes.titlesize': 44,
            'xtick.labelsize': 28,
            'ytick.labelsize': 28,
            'legend.fontsize': 32,
            'figure.titlesize': 60
        })
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Analizator Wyników Badań')
        self.setGeometry(100, 100, 1200, 800)
        
        # Główny widget i layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Górny panel przycisków
        top_panel = QHBoxLayout()
        
        # Przycisk importu CSV
        self.import_btn = QPushButton('Importuj CSV', self)
        self.import_btn.clicked.connect(self.import_csv)
        top_panel.addWidget(self.import_btn)
        
        # Label informacyjny
        self.status_label = QLabel('Nie wczytano danych')
        top_panel.addWidget(self.status_label)
        
        top_panel.addStretch()
        
        main_layout.addLayout(top_panel)
        
        # Zakładki
        self.tabs = QTabWidget()
        
        # Zakładka z danymi
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        
        # Tabela danych
        self.table_view = QTableView()
        data_layout.addWidget(self.table_view)
        
        self.tabs.addTab(self.data_tab, "Dane")
        
        # Zakładka z wizualizacją trendów
        self.trends_tab = QWidget()
        trends_layout = QVBoxLayout(self.trends_tab)
        
        # Panel kontrolny dla trendów
        trends_control = QHBoxLayout()
        
        self.param_label = QLabel('Wybierz parametr:')
        trends_control.addWidget(self.param_label)
        
        self.param_combo = QComboBox()
        self.param_combo.currentIndexChanged.connect(self.update_trend_plot)
        trends_control.addWidget(self.param_combo)
        
        trends_control.addStretch()
        
        trends_layout.addLayout(trends_control)
        
        # Kontener na wykres
        self.trend_canvas = MplCanvas(self, width=10, height=6)
        trends_layout.addWidget(self.trend_canvas)
        
        self.tabs.addTab(self.trends_tab, "Trendy Parametrów")
        
        # Zakładka z analizą wieloparametrową
        self.multi_tab = QWidget()
        multi_layout = QVBoxLayout(self.multi_tab)
        
        # Panel kontrolny dla wizualizacji wieloparametrowej
        multi_control = QHBoxLayout()
        
        self.param1_label = QLabel('Parametr 1:')
        multi_control.addWidget(self.param1_label)
        
        self.param1_combo = QComboBox()
        multi_control.addWidget(self.param1_combo)
        
        self.param2_label = QLabel('Parametr 2:')
        multi_control.addWidget(self.param2_label)
        
        self.param2_combo = QComboBox()
        multi_control.addWidget(self.param2_combo)
        
        self.plot_btn = QPushButton('Porównaj', self)
        self.plot_btn.clicked.connect(self.update_multi_plot)
        multi_control.addWidget(self.plot_btn)
        
        multi_control.addStretch()
        
        multi_layout.addLayout(multi_control)
        
        # Kontener na wykres
        self.multi_canvas = MplCanvas(self, width=10, height=6)
        multi_layout.addWidget(self.multi_canvas)
        
        self.tabs.addTab(self.multi_tab, "Analiza Wieloparametrowa")
        
        main_layout.addWidget(self.tabs)
    
    def import_csv(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, 
                                                 "Wybierz plik CSV z wynikami badań", 
                                                 "", 
                                                 "CSV Files (*.csv);;All Files (*)", 
                                                 options=options)
        if fileName:
            try:
                # Wczytanie danych
                self.data = pd.read_csv(fileName, parse_dates=['Data'])
                self.data.sort_values('Data', inplace=True)
                
                # Konwersja dat do formatu YYYY-MM-DD (bez godzin)
                self.data['Data'] = pd.to_datetime(self.data['Data']).dt.date
                
                # Aktualizacja interfejsu
                self.status_label.setText(f'Wczytano dane z {fileName}')
                
                # Wyświetlenie danych w tabeli
                model = PandasModel(self.data)
                self.table_view.setModel(model)
                
                # Aktualizacja comboboxów z parametrami
                params = [col for col in self.data.columns if col != 'Data']
                self.param_combo.clear()
                self.param_combo.addItems(params)
                
                self.param1_combo.clear()
                self.param1_combo.addItems(params)
                
                self.param2_combo.clear()
                self.param2_combo.addItems(params)
                
                # Aktualizacja wykresów
                if len(params) > 0:
                    self.update_trend_plot()
                    if len(params) > 1:
                        self.param2_combo.setCurrentIndex(1)
                        self.update_multi_plot()
                
                # Przełączenie na zakładkę z danymi
                self.tabs.setCurrentIndex(0)
                
            except Exception as e:
                QMessageBox.critical(self, "Błąd importu", f"Nie udało się wczytać pliku: {str(e)}")
                self.status_label.setText('Błąd wczytywania danych')
    
    def update_trend_plot(self):
        if self.data is None or self.param_combo.currentText() == '':
            return
        
        param = self.param_combo.currentText()
        
        # Czyszczenie wykresu
        self.trend_canvas.axes.clear()
        
        # Wyszukiwanie wartości referencyjnych (jeśli są)
        norm_cols = [col for col in self.data.columns if 'norma' in col.lower() and param.lower() in col.lower()]
        
        # Tworzenie wykresu trendu
        sns.set_style("whitegrid")
        sns.set_context("talk")  # Zwiększa wszystkie elementy wykresu
        ax = self.trend_canvas.axes
        
        # Przygotowanie danych - formatowanie dat
        dates = pd.to_datetime(self.data['Data']).dt.date
        
        # Wykres linii trendu
        ax.plot(dates, self.data[param], marker='o', linestyle='-', linewidth=3, markersize=15, label=param)
        
        # Dodanie zakresów referencyjnych, jeśli są dostępne
        if len(norm_cols) >= 2:
            # Zakładamy, że mamy kolumny z dolną i górną granicą normy
            lower_norm = min([self.data[col].iloc[0] for col in norm_cols])
            upper_norm = max([self.data[col].iloc[0] for col in norm_cols])
            
            ax.axhspan(lower_norm, upper_norm, alpha=0.2, color='green', label='Zakres normy')
            
            # Kolorowanie punktów poza normą
            for i, val in enumerate(self.data[param]):
                if val < lower_norm or val > upper_norm:
                    ax.plot(dates[i], val, 'ro', markersize=18)
        
        # Formatowanie wykresu z DUŻO większymi czcionkami
        ax.set_title(f'Trend parametru: {param}', fontsize=44, fontweight='bold')
        ax.set_xlabel('Data', fontsize=32, fontweight='bold')
        ax.set_ylabel(f'Wartość {param}', fontsize=32, fontweight='bold')
        ax.grid(True)
        ax.legend(fontsize=28)
        
        # Formatowanie dat na osi X
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # Ustawienie większych czcionek na osiach
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=28)
        plt.setp(ax.get_yticklabels(), fontsize=28)
        
        # Zwiększenie grubości osi
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
        
        # Zwiększenie rozmiaru znaczników na osiach
        ax.tick_params(width=2.5, length=10)
        
        self.trend_canvas.fig.tight_layout()
        self.trend_canvas.draw()
    
    def update_multi_plot(self):
        if self.data is None:
            return
        
        param1 = self.param1_combo.currentText()
        param2 = self.param2_combo.currentText()
        
        if param1 == '' or param2 == '':
            return
        
        # Czyszczenie wykresu i colorbaru
        self.multi_canvas.fig.clear()
        self.multi_canvas.axes = self.multi_canvas.fig.add_subplot(111)
        
        # Tworzenie wykresu porównawczego
        sns.set_style("whitegrid")
        sns.set_context("talk")  # Zwiększa wszystkie elementy wykresu
        ax = self.multi_canvas.axes
        
        # Przygotowanie danych - konwersja dat na liczby dla kolorów
        dates_numeric = pd.to_datetime(self.data['Data']).astype(int)
        
        # Dodanie punktów danych
        scatter = ax.scatter(self.data[param1], self.data[param2], 
                            c=dates_numeric, 
                            cmap='viridis', 
                            s=200,  # Znacznie zwiększony rozmiar punktów 
                            alpha=0.7)
        
        # Dodanie etykiet dat - tylko daty bez godzin z większą czcionką
        for i, date in enumerate(self.data['Data']):
            date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
            ax.annotate(date_str, 
                       (self.data[param1].iloc[i], self.data[param2].iloc[i]),
                       xytext=(8, 8), 
                       textcoords='offset points',
                       fontsize=24)  # Znacznie większy rozmiar czcionki etykiet
        
        # Formatowanie wykresu
        ax.set_title(f'Porównanie: {param1} vs {param2}', fontsize=44, fontweight='bold')
        ax.set_xlabel(param1, fontsize=32, fontweight='bold')
        ax.set_ylabel(param2, fontsize=32, fontweight='bold')
        ax.grid(True)
        
        # Zwiększenie rozmiaru czcionki dla osi
        plt.setp(ax.get_xticklabels(), fontsize=28)
        plt.setp(ax.get_yticklabels(), fontsize=28)
        
        # Zwiększenie grubości osi
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
            
        # Zwiększenie rozmiaru znaczników na osiach
        ax.tick_params(width=2.5, length=10)
        
        # Dodanie kolorowej skali dla czasu
        cbar = self.multi_canvas.fig.colorbar(scatter)
        cbar.set_label('Data badania', fontsize=32, fontweight='bold')
        cbar.ax.tick_params(labelsize=24)  # Zwiększenie rozmiaru czcionki na kolorbarze
        
        self.multi_canvas.fig.tight_layout()
        self.multi_canvas.draw()

# Uruchomienie aplikacji
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MedicalAnalyzer()
    window.show()
    sys.exit(app.exec_())
