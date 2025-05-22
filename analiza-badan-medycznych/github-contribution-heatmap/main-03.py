import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import calplot
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QLabel, QStatusBar, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont
from matplotlib.backend_bases import MouseButton

# Wyłączenie ostrzeżeń
import warnings
warnings.filterwarnings("ignore")

# Klasa do tworzenia płótna matplotlib w PyQt5
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=16, height=10, dpi=100):
        # Ustawienie stylu matplotlib
        plt.style.use('default')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Verdana', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)

class KalendarzAktywnosci(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Ustawienia okna
        self.setWindowTitle("Kalendarz Aktywności")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Główny widget i layout
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout(self.centralWidget)
        self.layout.setContentsMargins(10, 5, 10, 5)  # Zmniejszamy marginesy
        self.layout.setSpacing(5)  # Zmniejszamy odstępy między elementami
        
        # Tytuł - zmniejszamy jego rozmiar i ustawiamy stałą wysokość
        self.tytul = QLabel("Aktywność w 2023 roku")
        self.tytul.setAlignment(Qt.AlignCenter)
        self.tytul.setStyleSheet("font-weight: bold;")
        self.tytul.setFixedHeight(40)  # Ustawiamy stałą wysokość
        self.layout.addWidget(self.tytul)
        
        # Tworzenie płótna matplotlib - ustawiamy większy współczynnik rozciągania
        self.canvas = MplCanvas(self, width=16, height=10, dpi=100)
        self.layout.addWidget(self.canvas, 1)  # Dodajemy współczynnik stretch=1
        
        # Przyciski - umieszczamy w małym kontenerze
        buttonContainer = QWidget()
        buttonContainer.setFixedHeight(50)  # Stała wysokość dla przycisków
        self.buttonLayout = QHBoxLayout(buttonContainer)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)  # Usuwamy marginesy
        self.saveButton = QPushButton("Zapisz jako PNG")
        self.saveButton.clicked.connect(self.zapisz_png)
        self.buttonLayout.addWidget(self.saveButton)
        self.buttonLayout.addStretch(1)  # Dodajemy elastyczną przestrzeń
        self.layout.addWidget(buttonContainer)
        
        # Pasek statusu do wyświetlania informacji o klikniętym dniu
        self.statusBar = QStatusBar()
        self.statusBar.setFixedHeight(30)  # Stała wysokość paska statusu
        self.setStatusBar(self.statusBar)
        
        # Generowanie danych
        self.generuj_dane()
        
        # Rysowanie kalendarza
        self.rysuj_kalendarz()
        
        # Podłączenie funkcji do zdarzenia kliknięcia
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Timer do opóźnionego przerysowywania
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.delayed_resize)
        
        # Początkowe dostosowanie czcionek
        self.dostosuj_czcionki()
        
    def resizeEvent(self, event):
        """Obsługa zdarzenia zmiany rozmiaru okna"""
        super().resizeEvent(event)
        
        # Dostosuj czcionki interfejsu od razu
        self.dostosuj_czcionki()
        
        # Uruchom timer do opóźnionego przerysowania
        self.resize_timer.start(200)  # 200 ms opóźnienia

    def delayed_resize(self):
        """Opóźnione przerysowanie po zmianie rozmiaru"""
        self.rysuj_kalendarz()
        
    def dostosuj_czcionki(self):
        """Dostosowuje rozmiar czcionek i przycisków do rozmiaru okna"""
        # Pobierz aktualny rozmiar okna
        width = self.width()
        
        # Oblicz współczynnik skalowania (bazując na szerokości okna)
        # Zwiększamy bazowy rozmiar czcionek o 100% dla elementów wykresu
        scale_factor = max(1.0, min(3.0, width / 1600 * 2.0))
        
        # Dla tytułu używamy jeszcze mniejszego współczynnika (tylko 30% zwiększenia)
        title_scale_factor = max(0.5, min(1.0, width / 1600 * 1.3))
        
        # Dla przycisku używamy średniego współczynnika (50% zwiększenia)
        button_scale_factor = max(0.75, min(1.5, width / 1600 * 1.5))
        
        # Dla paska statusu używamy małego współczynnika (40% zwiększenia)
        status_scale_factor = max(0.6, min(1.2, width / 1600 * 1.4))
        
        # Dostosuj rozmiar czcionki tytułu
        font_size_title = int(16 * title_scale_factor)
        self.tytul.setStyleSheet(f"font-size: {font_size_title}pt; font-weight: bold;")
        
        # Dostosuj rozmiar czcionki przycisku
        font_size_button = int(10 * button_scale_factor)
        button_font = QFont()
        button_font.setPointSize(font_size_button)
        self.saveButton.setFont(button_font)
        
        # Dostosuj rozmiar przycisku
        button_width = int(150 * button_scale_factor)
        button_height = int(30 * button_scale_factor)
        self.saveButton.setMinimumSize(QSize(button_width, button_height))
        
        # Dostosuj rozmiar czcionki paska statusu
        font_size_status = int(10 * status_scale_factor)
        self.statusBar.setStyleSheet(f"font-size: {font_size_status}pt;")
        
    def generuj_dane(self):
        # Przykładowe dane
        dates = pd.date_range(start='2023-01-01', end='2023-12-31')
        activity = np.random.randint(0, 10, size=len(dates))
        self.data = pd.Series(activity, index=dates)
        
    def rysuj_kalendarz(self):
        # Tworzymy nową figurę bezpośrednio w płótnie
        self.canvas.fig.clear()
        
        # Dostosowanie rozmiaru czcionki na wykresie w zależności od rozmiaru okna
        width = self.width()
        # Zwiększamy bazowy rozmiar czcionek o 100%
        scale_factor = max(1.0, min(3.0, width / 1600 * 2.0))
        font_size_plot = int(10 * scale_factor)
        
        # Tworzymy dane do kalendarza
        all_days = self.data.index
        values = self.data.values
        
        # Tworzymy siatkę dla kalendarza (7 dni x 53 tygodnie)
        calendar_grid = np.full((7, 53), np.nan)
        
        # Wypełniamy siatkę danymi
        for date, value in zip(all_days, values):
            week = date.isocalendar()[1] - 1  # Numer tygodnia (0-52)
            weekday = date.weekday()  # Dzień tygodnia (0=poniedziałek, 6=niedziela)
            if 0 <= week < 53:
                calendar_grid[weekday, week] = value
        
        # Tworzymy wykres kalendarza
        self.ax = [self.canvas.fig.add_subplot(111, aspect='equal')]  # Dodajemy aspect='equal' dla kwadratowych komórek
        
        # Rysujemy heatmap
        cmap = plt.cm.get_cmap('viridis')
        mesh = self.ax[0].pcolormesh(calendar_grid, cmap=cmap, vmin=0, vmax=9, edgecolors='gray', linewidth=1.0)
        
        # Ustawiamy etykiety osi
        self.ax[0].set_yticks(np.arange(0.5, 7.5))
        self.ax[0].set_yticklabels(['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'])
        
        # Ustawiamy etykiety miesięcy
        month_positions = []
        month_labels = []
        for month in range(1, 13):
            first_day = pd.Timestamp(f'2023-{month:02d}-01')
            week = first_day.isocalendar()[1] - 1
            month_positions.append(week)
            month_labels.append(first_day.strftime('%b'))
        
        self.ax[0].set_xticks(month_positions)
        self.ax[0].set_xticklabels(month_labels)
        
        # Bezpośrednio ustawiamy rozmiar czcionki dla wszystkich elementów tekstowych
        for item in ([self.ax[0].title, self.ax[0].xaxis.label, self.ax[0].yaxis.label] +
                    self.ax[0].get_xticklabels() + self.ax[0].get_yticklabels()):
            item.set_fontsize(font_size_plot)
        
        # Dodanie paska kolorów
        cbar_ax = self.canvas.fig.add_axes([0.92, 0.3, 0.02, 0.4])
        cbar = self.canvas.fig.colorbar(mesh, cax=cbar_ax)
        cbar.set_label('Poziom aktywności')
        
        # Bezpośrednio ustawiamy rozmiar czcionki dla paska kolorów
        cbar.ax.yaxis.label.set_fontsize(font_size_plot)
        for t in cbar.ax.get_yticklabels():
            t.set_fontsize(font_size_plot)
        
        # Dostosowanie układu
        self.canvas.fig.tight_layout(rect=[0, 0.03, 0.9, 0.95])
        
        # Ustawienie równych proporcji dla osi x i y
        self.ax[0].set_aspect('equal')
        
        self.canvas.draw()
        
    def on_click(self, event):
        if event.button is MouseButton.LEFT and event.inaxes == self.ax[0]:
            # Pobierz współrzędne kliknięcia
            x, y = event.xdata, event.ydata
            
            # Konwersja współrzędnych na indeks dnia
            col = int(round(x))
            row = int(round(y))
            
            # Sprawdzamy, czy kliknięcie jest w zakresie kalendarza
            if 0 <= col < 53 and 0 <= row < 7:  # 53 tygodnie, 7 dni
                try:
                    # Próbujemy znaleźć datę na podstawie współrzędnych
                    date_idx = pd.Timestamp('2023-01-01') + pd.Timedelta(weeks=col) + pd.Timedelta(days=(6-row))
                    
                    # Sprawdzamy, czy data jest w naszym zbiorze danych
                    if date_idx in self.data.index:
                        value = self.data[date_idx]
                        self.statusBar.showMessage(f"Data: {date_idx.strftime('%d.%m.%Y')} (aktywność: {value})")
                    else:
                        self.statusBar.showMessage("Brak danych dla wybranego dnia")
                except:
                    self.statusBar.showMessage("Brak danych dla wybranego dnia")
    
    def zapisz_png(self):
        self.canvas.fig.savefig('kalendarz_2023.png', bbox_inches='tight', dpi=150)
        self.statusBar.showMessage("Zapisano jako kalendarz_2023.png", 3000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KalendarzAktywnosci()
    window.show()
    sys.exit(app.exec_())
