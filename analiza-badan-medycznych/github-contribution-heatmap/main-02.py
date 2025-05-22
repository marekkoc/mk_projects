import calplot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backend_bases import MouseButton

# Wyłączenie ostrzeżeń
import warnings
warnings.filterwarnings("ignore")

# Ustawienie stylu matplotlib
plt.style.use('default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Verdana', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['figure.dpi'] = 100

# Przykładowe dane
dates = pd.date_range(start='2023-01-01', end='2023-12-31')
activity = np.random.randint(0, 10, size=len(dates))
data = pd.Series(activity, index=dates)

# Wyświetlanie kalendarza z poprawionymi parametrami
fig, ax = calplot.calplot(
    data, 
    cmap='viridis',
    figsize=(16, 10),
    suptitle='',  # Pusty tytuł, dodamy go później
    linewidth=1.0,
    edgecolor='gray',
    yearlabels=True,
    daylabels=['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'],  # Dłuższe etykiety dla lepszej widoczności
    dayticks=[0, 1, 2, 3, 4, 5, 6],
    vmin=0,
    vmax=9
)

# Dostosowanie paska kolorów - usunięcie starego i dodanie nowego
for cbar in fig.axes:
    if cbar != ax[0]:  # Jeśli to nie jest główny wykres
        cbar.remove()  # Usuń pasek kolorów

# Dodanie nowego paska kolorów po prawej stronie
cbar_ax = fig.add_axes([0.92, 0.3, 0.02, 0.4])  # [left, bottom, width, height]
sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(0, 9))
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label('Poziom aktywności')

# Dodanie tytułu
plt.suptitle('Aktywność w 2023 roku', fontsize=16, y=0.95)

# Dodanie tekstu informacyjnego
info_text = fig.text(0.5, 0.01, "Kliknij na dzień, aby zobaczyć szczegóły", 
                     ha='center', fontsize=12)

# Funkcja obsługująca kliknięcie myszy
def on_click(event):
    if event.button is MouseButton.LEFT and event.inaxes == ax[0]:
        # Pobierz współrzędne kliknięcia
        x, y = event.xdata, event.ydata
        
        # Konwersja współrzędnych na indeks dnia
        # Zaokrąglamy do najbliższej liczby całkowitej
        col = int(round(x))
        row = int(round(y))
        
        # Sprawdzamy, czy kliknięcie jest w zakresie kalendarza
        if 0 <= col < 53 and 0 <= row < 7:  # 53 tygodnie, 7 dni
            # Obliczamy datę na podstawie współrzędnych
            # Pierwszy dzień roku + numer tygodnia * 7 + dzień tygodnia
            try:
                # Próbujemy znaleźć datę na podstawie współrzędnych
                # Pierwszy dzień to lewy dolny róg (0,0)
                date_idx = pd.Timestamp('2023-01-01') + pd.Timedelta(weeks=col) + pd.Timedelta(days=(6-row))
                
                # Sprawdzamy, czy data jest w naszym zbiorze danych
                if date_idx in data.index:
                    value = data[date_idx]
                    info_text.set_text(f"Data: {date_idx.strftime('%d.%m.%Y')} (aktywność: {value})")
                    fig.canvas.draw_idle()  # Odświeżenie wykresu
                else:
                    info_text.set_text("Brak danych dla wybranego dnia")
                    fig.canvas.draw_idle()
            except:
                info_text.set_text("Brak danych dla wybranego dnia")
                fig.canvas.draw_idle()

# Podłączenie funkcji do zdarzenia kliknięcia
fig.canvas.mpl_connect('button_press_event', on_click)

# Dostosowanie układu
plt.tight_layout(rect=[0, 0.03, 0.9, 0.95])  # Pozostaw miejsce na tytuł, pasek kolorów i tekst informacyjny
plt.savefig('kalendarz_2023.png', bbox_inches='tight', dpi=150)
plt.show()
