import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QDoubleSpinBox, QTabWidget, QCheckBox, QGroupBox,
                           QFormLayout, QMessageBox, QHeaderView, QFileDialog, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import os

class MealOptimizer:
    def __init__(self):
        # Przykładowa baza danych składników (nazwa, kalorie, białko, tłuszcz, węglowodany, jednostka)
        self.ingredients_db = pd.DataFrame([
            {'name': 'Kurczak pierś', 'calories': 165, 'protein': 31, 'fat': 3.6, 'carbs': 0, 'unit': '100g'},
            {'name': 'Ryż biały', 'calories': 130, 'protein': 2.7, 'fat': 0.3, 'carbs': 28, 'unit': '100g'},
            {'name': 'Brokuły', 'calories': 34, 'protein': 2.8, 'fat': 0.4, 'carbs': 6.6, 'unit': '100g'},
            {'name': 'Oliwa z oliwek', 'calories': 884, 'protein': 0, 'fat': 100, 'carbs': 0, 'unit': '100ml'},
            {'name': 'Ciecierzyca', 'calories': 364, 'protein': 19, 'fat': 6, 'carbs': 61, 'unit': '100g'},
            {'name': 'Tofu', 'calories': 76, 'protein': 8, 'fat': 4.8, 'carbs': 1.9, 'unit': '100g'},
            {'name': 'Bataty', 'calories': 86, 'protein': 1.6, 'fat': 0.1, 'carbs': 20, 'unit': '100g'},
            {'name': 'Jajka', 'calories': 155, 'protein': 13, 'fat': 11, 'carbs': 1.1, 'unit': 'sztuka'},
            {'name': 'Łosoś', 'calories': 206, 'protein': 22, 'fat': 13, 'carbs': 0, 'unit': '100g'},
            {'name': 'Awokado', 'calories': 160, 'protein': 2, 'fat': 15, 'carbs': 9, 'unit': 'połowa'}
        ])

    def add_ingredient(self, name, calories, protein, fat, carbs, unit='100g'):
        """Dodaje nowy składnik do bazy danych"""
        new_ingredient = pd.DataFrame([{
            'name': name, 
            'calories': calories, 
            'protein': protein, 
            'fat': fat, 
            'carbs': carbs, 
            'unit': unit
        }])
        self.ingredients_db = pd.concat([self.ingredients_db, new_ingredient], ignore_index=True)
        print(f"Dodano składnik: {name}")

    def optimize_meal_linprog(self, target_calories, target_protein, target_fat, target_carbs, 
                             selected_ingredients=None, min_amounts=None, max_amounts=None):
        """
        Optymalizuje skład posiłku metodą programowania liniowego.
        
        Parameters:
        -----------
        target_calories : float
            Docelowa liczba kalorii
        target_protein : float
            Docelowa ilość białka (g)
        target_fat : float
            Docelowa ilość tłuszczu (g)
        target_carbs : float
            Docelowa ilość węglowodanów (g)
        selected_ingredients : list, optional
            Lista nazw składników do uwzględnienia (domyślnie wszystkie)
        min_amounts : dict, optional
            Słownik z minimalnymi ilościami składników (w jednostkach)
        max_amounts : dict, optional
            Słownik z maksymalnymi ilościami składników (w jednostkach)
            
        Returns:
        --------
        dict
            Słownik z optymalnymi ilościami składników i ich makroskładnikami
        """
        if selected_ingredients is None:
            selected_ingredients = self.ingredients_db['name'].tolist()
        
        # Filtrowanie wybranych składników
        ingredients = self.ingredients_db[self.ingredients_db['name'].isin(selected_ingredients)].copy()
        
        # Macierz kosztów (minimalizujemy odchylenie od celów)
        # Używamy "wagi" dla każdego składnika jako jego wartość kaloryczną
        c = ingredients['calories'].values
        
        # Macierz ograniczeń
        # Dla każdego makroskładnika mamy ograniczenie dolne i górne
        A_ub = []
        b_ub = []
        
        # Ograniczenia dla kalorii (±5%)
        A_ub.append(ingredients['calories'].values)  # <= target_calories * 1.05
        b_ub.append(target_calories * 1.05)
        A_ub.append(-ingredients['calories'].values)  # >= target_calories * 0.95
        b_ub.append(-target_calories * 0.95)
        
        # Ograniczenia dla białka (±10%)
        A_ub.append(ingredients['protein'].values)
        b_ub.append(target_protein * 1.1)
        A_ub.append(-ingredients['protein'].values)
        b_ub.append(-target_protein * 0.9)
        
        # Ograniczenia dla tłuszczu (±10%)
        A_ub.append(ingredients['fat'].values)
        b_ub.append(target_fat * 1.1)
        A_ub.append(-ingredients['fat'].values)
        b_ub.append(-target_fat * 0.9)
        
        # Ograniczenia dla węglowodanów (±10%)
        A_ub.append(ingredients['carbs'].values)
        b_ub.append(target_carbs * 1.1)
        A_ub.append(-ingredients['carbs'].values)
        b_ub.append(-target_carbs * 0.9)
        
        # Ograniczenia dla minimalnych i maksymalnych ilości
        if min_amounts is not None:
            for name, min_amount in min_amounts.items():
                if name in selected_ingredients:
                    idx = ingredients.index[ingredients['name'] == name].tolist()[0]
                    constraint = np.zeros(len(ingredients))
                    constraint[idx] = -1  # >= min_amount
                    A_ub.append(constraint)
                    b_ub.append(-min_amount)
        
        if max_amounts is not None:
            for name, max_amount in max_amounts.items():
                if name in selected_ingredients:
                    idx = ingredients.index[ingredients['name'] == name].tolist()[0]
                    constraint = np.zeros(len(ingredients))
                    constraint[idx] = 1  # <= max_amount
                    A_ub.append(constraint)
                    b_ub.append(max_amount)
        
        # Konwersja na tablice numpy dla scipy
        A_ub = np.array(A_ub)
        b_ub = np.array(b_ub)
        
        # Ograniczenia nieujemności
        bounds = [(0, None) for _ in range(len(ingredients))]
        
        # Rozwiązanie problemu optymalizacji
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if result.success:
            # Przygotowanie wyniku
            optimal_amounts = result.x
            meal_composition = pd.DataFrame({
                'ingredient': ingredients['name'].values,
                'amount': optimal_amounts,
                'unit': ingredients['unit'].values,
                'calories': ingredients['calories'].values * optimal_amounts,
                'protein': ingredients['protein'].values * optimal_amounts,
                'fat': ingredients['fat'].values * optimal_amounts,
                'carbs': ingredients['carbs'].values * optimal_amounts
            })
            
            # Usunięcie składników z ilością bliską zeru
            meal_composition = meal_composition[meal_composition['amount'] > 0.01]
            
            total = meal_composition[['calories', 'protein', 'fat', 'carbs']].sum()
            
            return {
                'success': True,
                'meal_composition': meal_composition,
                'total': total,
                'target': {
                    'calories': target_calories,
                    'protein': target_protein,
                    'fat': target_fat,
                    'carbs': target_carbs
                }
            }
        else:
            return {
                'success': False,
                'message': "Nie udało się znaleźć rozwiązania. Spróbuj zmienić parametry lub dodać więcej składników."
            }
    
    def optimize_meal_quadratic(self, target_calories, target_protein, target_fat, target_carbs, 
                             selected_ingredients=None, min_amounts=None, max_amounts=None):
        """
        Optymalizuje skład posiłku metodą programowania kwadratowego.
        Ta metoda minimalizuje kwadrat odchylenia od celów, co daje bardziej zrównoważone wyniki.
        """
        # Implementacja podobna do optimize_meal_linprog, ale używa minimize zamiast linprog
        # i minimalizuje sumę kwadratów odchyleń
        if selected_ingredients is None:
            selected_ingredients = self.ingredients_db['name'].tolist()
        
        ingredients = self.ingredients_db[self.ingredients_db['name'].isin(selected_ingredients)].copy()
        
        def objective(x):
            calories = np.sum(ingredients['calories'].values * x)
            protein = np.sum(ingredients['protein'].values * x)
            fat = np.sum(ingredients['fat'].values * x)
            carbs = np.sum(ingredients['carbs'].values * x)
            
            # Suma kwadratów odchyleń od celów
            return ((calories - target_calories) / target_calories) ** 2 + \
                   ((protein - target_protein) / target_protein) ** 2 + \
                   ((fat - target_fat) / target_fat) ** 2 + \
                   ((carbs - target_carbs) / target_carbs) ** 2
        
        # Ograniczenia (wszystkie nieujemne)
        bounds = [(0, None) for _ in range(len(ingredients))]
        
        # Dodatkowe ograniczenia dla minimalnych i maksymalnych ilości
        constraints = []
        
        if min_amounts is not None:
            for name, min_amount in min_amounts.items():
                if name in selected_ingredients:
                    idx = ingredients.index[ingredients['name'] == name].tolist()[0]
                    
                    def constraint_min(x, idx=idx, min_amount=min_amount):
                        return x[idx] - min_amount
                    
                    constraints.append({'type': 'ineq', 'fun': constraint_min})
        
        if max_amounts is not None:
            for name, max_amount in max_amounts.items():
                if name in selected_ingredients:
                    idx = ingredients.index[ingredients['name'] == name].tolist()[0]
                    
                    def constraint_max(x, idx=idx, max_amount=max_amount):
                        return max_amount - x[idx]
                    
                    constraints.append({'type': 'ineq', 'fun': constraint_max})
        
        # Punkt startowy
        x0 = np.ones(len(ingredients)) * 0.1
        
        # Rozwiązanie problemu optymalizacji
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            # Przygotowanie wyniku
            optimal_amounts = result.x
            meal_composition = pd.DataFrame({
                'ingredient': ingredients['name'].values,
                'amount': optimal_amounts,
                'unit': ingredients['unit'].values,
                'calories': ingredients['calories'].values * optimal_amounts,
                'protein': ingredients['protein'].values * optimal_amounts,
                'fat': ingredients['fat'].values * optimal_amounts,
                'carbs': ingredients['carbs'].values * optimal_amounts
            })
            
            # Usunięcie składników z ilością bliską zeru
            meal_composition = meal_composition[meal_composition['amount'] > 0.01]
            
            total = meal_composition[['calories', 'protein', 'fat', 'carbs']].sum()
            
            return {
                'success': True,
                'meal_composition': meal_composition,
                'total': total,
                'target': {
                    'calories': target_calories,
                    'protein': target_protein,
                    'fat': target_fat,
                    'carbs': target_carbs
                }
            }
        else:
            return {
                'success': False,
                'message': "Nie udało się znaleźć rozwiązania. Spróbuj zmienić parametry lub dodać więcej składników."
            }
    
    def visualize_results(self, result):
        """Wizualizuje wyniki optymalizacji"""
        if not result['success']:
            print(result['message'])
            return
        
        # Wykres składu posiłku (w gramach)
        plt.figure(figsize=(12, 10))
        
        # Wykres kołowy składników
        plt.subplot(2, 2, 1)
        amounts = result['meal_composition']['amount'].values
        labels = [f"{name} ({amount:.1f} {unit})" 
                 for name, amount, unit in zip(result['meal_composition']['ingredient'], 
                                              amounts, 
                                              result['meal_composition']['unit'])]
        plt.pie(amounts, labels=labels, autopct='%1.1f%%')
        plt.title('Skład posiłku (proporcje ilościowe)')
        
        # Wykres kołowy kalorii
        plt.subplot(2, 2, 2)
        calories = result['meal_composition']['calories'].values
        labels = [f"{name} ({cal:.1f} kcal)" 
                 for name, cal in zip(result['meal_composition']['ingredient'], calories)]
        plt.pie(calories, labels=labels, autopct='%1.1f%%')
        plt.title('Rozkład kalorii')
        
        # Wykres porównania celu i rzeczywistych wartości
        plt.subplot(2, 1, 2)
        categories = ['Kalorie', 'Białko (g)', 'Tłuszcz (g)', 'Węglowodany (g)']
        target_values = [result['target']['calories'], result['target']['protein'], 
                        result['target']['fat'], result['target']['carbs']]
        actual_values = [result['total']['calories'], result['total']['protein'], 
                         result['total']['fat'], result['total']['carbs']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        plt.bar(x - width/2, target_values, width, label='Cel')
        plt.bar(x + width/2, actual_values, width, label='Uzyskane')
        
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        plt.xticks(x, categories)
        plt.title('Porównanie celu i uzyskanych wartości')
        plt.legend()
        
        # Dodanie wartości liczbowych nad słupkami
        for i, v in enumerate(target_values):
            plt.text(i - width/2, v + 0.1, f"{v:.1f}", ha='center')
        
        for i, v in enumerate(actual_values):
            plt.text(i + width/2, v + 0.1, f"{v:.1f}", ha='center')
        
        plt.tight_layout()
        plt.show()
        
        # Wyświetlenie tabeli z dokładnymi wartościami
        print("\nSzczegółowy skład posiłku:")
        print(result['meal_composition'][['ingredient', 'amount', 'unit', 'calories', 'protein', 'fat', 'carbs']]
              .sort_values('calories', ascending=False)
              .to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        
        print("\nPodsumowanie makroskładników:")
        comparison = pd.DataFrame({
            'Makroskładnik': ['Kalorie', 'Białko (g)', 'Tłuszcz (g)', 'Węglowodany (g)'],
            'Cel': target_values,
            'Uzyskane': actual_values,
            'Różnica': [a - t for a, t in zip(actual_values, target_values)],
            'Różnica %': [(a - t) / t * 100 for a, t in zip(actual_values, target_values)]
        })
        print(comparison.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


# Przykład użycia
# Klasa MatplotlibCanvas do wyświetlania wykresów w interfejsie PyQt5
class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)

# Główne okno aplikacji
class MealOptimizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.optimizer = MealOptimizer()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Optymalizator Składu Posiłków")
        self.setGeometry(100, 100, 1200, 800)
        
        # Główny widget i układ
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # Zakładki
        self.tabs = QTabWidget()
        
        # Zakładka "Optymalizacja"
        self.optimization_tab = QWidget()
        self.tabs.addTab(self.optimization_tab, "Optymalizacja")
        
        # Zakładka "Baza składników"
        self.ingredients_tab = QWidget()
        self.tabs.addTab(self.ingredients_tab, "Baza składników")
        
        # Zakładka "Wyniki"
        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab, "Wyniki")
        
        # Inicjalizacja zakładek
        self.setup_optimization_tab()
        self.setup_ingredients_tab()
        self.setup_results_tab()
        
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)
        
        # Inicjalizacja danych
        self.update_ingredients_table()
        
    def setup_optimization_tab(self):
        layout = QVBoxLayout(self.optimization_tab)
        
        # Grupa docelowych makroskładników
        target_group = QGroupBox("Docelowe makroskładniki")
        target_layout = QFormLayout()
        
        self.target_calories = QSpinBox()
        self.target_calories.setRange(100, 10000)
        self.target_calories.setValue(700)
        self.target_calories.setSingleStep(50)
        
        self.target_protein = QSpinBox()
        self.target_protein.setRange(0, 500)
        self.target_protein.setValue(40)
        self.target_protein.setSingleStep(5)
        
        self.target_fat = QSpinBox()
        self.target_fat.setRange(0, 500)
        self.target_fat.setValue(25)
        self.target_fat.setSingleStep(5)
        
        self.target_carbs = QSpinBox()
        self.target_carbs.setRange(0, 500)
        self.target_carbs.setValue(60)
        self.target_carbs.setSingleStep(5)
        
        target_layout.addRow("Kalorie (kcal):", self.target_calories)
        target_layout.addRow("Białko (g):", self.target_protein)
        target_layout.addRow("Tłuszcz (g):", self.target_fat)
        target_layout.addRow("Węglowodany (g):", self.target_carbs)
        
        target_group.setLayout(target_layout)
        
        # Grupa wyboru metody optymalizacji
        method_group = QGroupBox("Metoda optymalizacji")
        method_layout = QVBoxLayout()
        
        self.method_combo = QComboBox()
        self.method_combo.addItem("Programowanie liniowe")
        self.method_combo.addItem("Programowanie kwadratowe")
        
        method_layout.addWidget(self.method_combo)
        method_group.setLayout(method_layout)
        
        # Grupa wyboru składników
        ingredients_group = QGroupBox("Wybór składników")
        ingredients_layout = QVBoxLayout()
        
        self.ingredients_table = QTableWidget()
        self.ingredients_table.setColumnCount(4)
        self.ingredients_table.setHorizontalHeaderLabels(["Składnik", "Wybierz", "Min. ilość", "Max. ilość"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        ingredients_layout.addWidget(self.ingredients_table)
        ingredients_group.setLayout(ingredients_layout)
        
        # Przycisk optymalizacji
        optimize_button = QPushButton("Optymalizuj")
        optimize_button.setFont(QFont("Arial", 12, QFont.Bold))
        optimize_button.clicked.connect(self.run_optimization)
        
        # Dodanie elementów do głównego układu
        layout.addWidget(target_group)
        layout.addWidget(method_group)
        layout.addWidget(ingredients_group)
        layout.addWidget(optimize_button)
        
    def setup_ingredients_tab(self):
        layout = QVBoxLayout(self.ingredients_tab)
        
        # Tabela składników
        self.ingredients_db_table = QTableWidget()
        self.ingredients_db_table.setColumnCount(6)
        self.ingredients_db_table.setHorizontalHeaderLabels(["Nazwa", "Kalorie", "Białko (g)", "Tłuszcz (g)", "Węglowodany (g)", "Jednostka"])
        self.ingredients_db_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Formularz dodawania nowego składnika
        add_group = QGroupBox("Dodaj nowy składnik")
        add_layout = QFormLayout()
        
        self.new_name = QLineEdit()
        self.new_calories = QDoubleSpinBox()
        self.new_calories.setRange(0, 1000)
        self.new_calories.setSingleStep(1)
        
        self.new_protein = QDoubleSpinBox()
        self.new_protein.setRange(0, 100)
        self.new_protein.setSingleStep(0.1)
        
        self.new_fat = QDoubleSpinBox()
        self.new_fat.setRange(0, 100)
        self.new_fat.setSingleStep(0.1)
        
        self.new_carbs = QDoubleSpinBox()
        self.new_carbs.setRange(0, 100)
        self.new_carbs.setSingleStep(0.1)
        
        self.new_unit = QLineEdit()
        self.new_unit.setText("100g")
        
        add_layout.addRow("Nazwa:", self.new_name)
        add_layout.addRow("Kalorie:", self.new_calories)
        add_layout.addRow("Białko (g):", self.new_protein)
        add_layout.addRow("Tłuszcz (g):", self.new_fat)
        add_layout.addRow("Węglowodany (g):", self.new_carbs)
        add_layout.addRow("Jednostka:", self.new_unit)
        
        add_group.setLayout(add_layout)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Dodaj składnik")
        add_button.clicked.connect(self.add_new_ingredient)
        
        delete_button = QPushButton("Usuń wybrany składnik")
        delete_button.clicked.connect(self.delete_selected_ingredient)
        
        import_button = QPushButton("Importuj z CSV")
        import_button.clicked.connect(self.import_ingredients)
        
        export_button = QPushButton("Eksportuj do CSV")
        export_button.clicked.connect(self.export_ingredients)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(import_button)
        buttons_layout.addWidget(export_button)
        
        # Dodanie elementów do głównego układu
        layout.addWidget(self.ingredients_db_table)
        layout.addWidget(add_group)
        layout.addLayout(buttons_layout)
        
    def setup_results_tab(self):
        layout = QVBoxLayout(self.results_tab)
        
        # Miejsce na wykresy
        self.plots_layout = QVBoxLayout()
        self.canvas = MatplotlibCanvas(width=10, height=8)
        self.plots_layout.addWidget(self.canvas)
        
        # Tabela z wynikami
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Składnik", "Ilość", "Jednostka", "Kalorie", "Białko (g)", "Tłuszcz (g)", "Węglowodany (g)"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Tabela z podsumowaniem
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels(["Makroskładnik", "Cel", "Uzyskane", "Różnica", "Różnica %"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.summary_table.setRowCount(4)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        export_results_button = QPushButton("Eksportuj wyniki do CSV")
        export_results_button.clicked.connect(self.export_results)
        
        save_plot_button = QPushButton("Zapisz wykres")
        save_plot_button.clicked.connect(self.save_plot)
        
        buttons_layout.addWidget(export_results_button)
        buttons_layout.addWidget(save_plot_button)
        
        # Dodanie elementów do głównego układu
        layout.addLayout(self.plots_layout)
        layout.addWidget(QLabel("Skład posiłku:"))
        layout.addWidget(self.results_table)
        layout.addWidget(QLabel("Podsumowanie makroskładników:"))
        layout.addWidget(self.summary_table)
        layout.addLayout(buttons_layout)
        
    def update_ingredients_table(self):
        # Aktualizacja tabeli składników w zakładce optymalizacji
        self.ingredients_table.setRowCount(len(self.optimizer.ingredients_db))
        
        for i, (_, row) in enumerate(self.optimizer.ingredients_db.iterrows()):
            # Nazwa składnika
            name_item = QTableWidgetItem(row['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.ingredients_table.setItem(i, 0, name_item)
            
            # Checkbox do wyboru
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.ingredients_table.setCellWidget(i, 1, checkbox)
            
            # Minimum
            min_spinbox = QDoubleSpinBox()
            min_spinbox.setRange(0, 10)
            min_spinbox.setSingleStep(0.1)
            min_spinbox.setValue(0)
            self.ingredients_table.setCellWidget(i, 2, min_spinbox)
            
            # Maximum
            max_spinbox = QDoubleSpinBox()
            max_spinbox.setRange(0, 10)
            max_spinbox.setSingleStep(0.1)
            max_spinbox.setValue(0)
            max_spinbox.setSpecialValueText("Brak")
            self.ingredients_table.setCellWidget(i, 3, max_spinbox)
        
        # Aktualizacja tabeli w zakładce bazy składników
        self.ingredients_db_table.setRowCount(len(self.optimizer.ingredients_db))
        
        for i, (_, row) in enumerate(self.optimizer.ingredients_db.iterrows()):
            self.ingredients_db_table.setItem(i, 0, QTableWidgetItem(row['name']))
            self.ingredients_db_table.setItem(i, 1, QTableWidgetItem(str(row['calories'])))
            self.ingredients_db_table.setItem(i, 2, QTableWidgetItem(str(row['protein'])))
            self.ingredients_db_table.setItem(i, 3, QTableWidgetItem(str(row['fat'])))
            self.ingredients_db_table.setItem(i, 4, QTableWidgetItem(str(row['carbs'])))
            self.ingredients_db_table.setItem(i, 5, QTableWidgetItem(row['unit']))
    
    def add_new_ingredient(self):
        name = self.new_name.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa składnika nie może być pusta.")
            return
        
        if name in self.optimizer.ingredients_db['name'].values:
            QMessageBox.warning(self, "Błąd", f"Składnik o nazwie '{name}' już istnieje.")
            return
        
        calories = self.new_calories.value()
        protein = self.new_protein.value()
        fat = self.new_fat.value()
        carbs = self.new_carbs.value()
        unit = self.new_unit.text().strip() or "100g"
        
        self.optimizer.add_ingredient(name, calories, protein, fat, carbs, unit)
        
        # Wyczyszczenie pól
        self.new_name.clear()
        self.new_calories.setValue(0)
        self.new_protein.setValue(0)
        self.new_fat.setValue(0)
        self.new_carbs.setValue(0)
        self.new_unit.setText("100g")
        
        # Aktualizacja tabel
        self.update_ingredients_table()
        
        QMessageBox.information(self, "Sukces", f"Dodano składnik: {name}")
    
    def delete_selected_ingredient(self):
        selected_rows = self.ingredients_db_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Nie wybrano żadnego składnika.")
            return
        
        names_to_delete = [self.ingredients_db_table.item(row.row(), 0).text() for row in selected_rows]
        
        confirm = QMessageBox.question(
            self, 
            "Potwierdzenie", 
            f"Czy na pewno chcesz usunąć następujące składniki?\n\n{', '.join(names_to_delete)}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            for name in names_to_delete:
                self.optimizer.ingredients_db = self.optimizer.ingredients_db[
                    self.optimizer.ingredients_db['name'] != name
                ]
            
            self.update_ingredients_table()
            QMessageBox.information(self, "Sukces", "Usunięto wybrane składniki.")
    
    def import_ingredients(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importuj składniki z CSV", "", "Pliki CSV (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            imported_df = pd.read_csv(file_path)
            
            required_columns = ['name', 'calories', 'protein', 'fat', 'carbs', 'unit']
            if not all(col in imported_df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in imported_df.columns]
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    f"Brakujące kolumny w pliku CSV: {', '.join(missing)}\n\n"
                    f"Wymagane kolumny: {', '.join(required_columns)}"
                )
                return
            
            # Dodanie składników
            count = 0
            for _, row in imported_df.iterrows():
                if row['name'] in self.optimizer.ingredients_db['name'].values:
                    continue
                
                self.optimizer.add_ingredient(
                    row['name'], row['calories'], row['protein'], 
                    row['fat'], row['carbs'], row['unit']
                )
                count += 1
            
            self.update_ingredients_table()
            QMessageBox.information(self, "Sukces", f"Zaimportowano {count} nowych składników.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas importowania: {str(e)}")
    
    def export_ingredients(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj składniki do CSV", "", "Pliki CSV (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            self.optimizer.ingredients_db.to_csv(file_path, index=False)
            QMessageBox.information(self, "Sukces", f"Wyeksportowano {len(self.optimizer.ingredients_db)} składników.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas eksportowania: {str(e)}")
    
    def export_results(self):
        if not hasattr(self, "last_result") or not self.last_result['success']:
            QMessageBox.warning(self, "Błąd", "Brak wyników do eksportu.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj wyniki do CSV", "", "Pliki CSV (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            self.last_result['meal_composition'].to_csv(file_path, index=False)
            QMessageBox.information(self, "Sukces", "Wyeksportowano wyniki do pliku CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas eksportowania: {str(e)}")
    
    def save_plot(self):
        if not hasattr(self, "last_result") or not self.last_result['success']:
            QMessageBox.warning(self, "Błąd", "Brak wykresu do zapisania.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wykres", "", "PNG (*.png);;JPEG (*.jpg);;PDF (*.pdf);;SVG (*.svg)"
        )
        
        if not file_path:
            return
        
        try:
            self.canvas.fig.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Sukces", "Zapisano wykres.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania: {str(e)}")
    
    def get_selected_ingredients(self):
        selected_ingredients = []
        min_amounts = {}
        max_amounts = {}
        
        for i in range(self.ingredients_table.rowCount()):
            name = self.ingredients_table.item(i, 0).text()
            checkbox = self.ingredients_table.cellWidget(i, 1)
            min_spinbox = self.ingredients_table.cellWidget(i, 2)
            max_spinbox = self.ingredients_table.cellWidget(i, 3)
            
            if checkbox.isChecked():
                selected_ingredients.append(name)
                
                min_value = min_spinbox.value()
                if min_value > 0:
                    min_amounts[name] = min_value
                
                max_value = max_spinbox.value()
                if max_value > 0:
                    max_amounts[name] = max_value
        
        return selected_ingredients, min_amounts, max_amounts
    
    def run_optimization(self):
        # Pobranie docelowych makroskładników
        target_calories = self.target_calories.value()
        target_protein = self.target_protein.value()
        target_fat = self.target_fat.value()
        target_carbs = self.target_carbs.value()
        
        # Pobranie wybranych składników i ich ograniczeń
        selected_ingredients, min_amounts, max_amounts = self.get_selected_ingredients()
        
        if not selected_ingredients:
            QMessageBox.warning(self, "Błąd", "Nie wybrano żadnych składników.")
            return
        
        # Wybór metody optymalizacji
        method = self.method_combo.currentText()
        
        try:
            if method == "Programowanie liniowe":
                result = self.optimizer.optimize_meal_linprog(
                    target_calories, target_protein, target_fat, target_carbs,
                    selected_ingredients, min_amounts, max_amounts
                )
            else:  # Programowanie kwadratowe
                result = self.optimizer.optimize_meal_quadratic(
                    target_calories, target_protein, target_fat, target_carbs,
                    selected_ingredients, min_amounts, max_amounts
                )
            
            if result['success']:
                self.last_result = result
                self.display_results(result)
                self.tabs.setCurrentIndex(2)  # Przełączenie na zakładkę wyników
            else:
                QMessageBox.warning(self, "Uwaga", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas optymalizacji: {str(e)}")
    
    def display_results(self, result):
        # Wyświetlenie wyników w tabeli
        meal_composition = result['meal_composition']
        self.results_table.setRowCount(len(meal_composition))
        
        for i, (_, row) in enumerate(meal_composition.iterrows()):
            self.results_table.setItem(i, 0, QTableWidgetItem(row['ingredient']))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{row['amount']:.2f}"))
            self.results_table.setItem(i, 2, QTableWidgetItem(row['unit']))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{row['calories']:.1f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{row['protein']:.1f}"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{row['fat']:.1f}"))
            self.results_table.setItem(i, 6, QTableWidgetItem(f"{row['carbs']:.1f}"))
        
        # Wyświetlenie podsumowania
        total = result['total']
        target = result['target']
        
        categories = ['Kalorie', 'Białko (g)', 'Tłuszcz (g)', 'Węglowodany (g)']
        target_values = [target['calories'], target['protein'], target['fat'], target['carbs']]
        actual_values = [total['calories'], total['protein'], total['fat'], total['carbs']]
        
        for i, (cat, target_val, actual_val) in enumerate(zip(categories, target_values, actual_values)):
            diff = actual_val - target_val
            diff_percent = diff / target_val * 100 if target_val != 0 else 0
            
            self.summary_table.setItem(i, 0, QTableWidgetItem(cat))
            self.summary_table.setItem(i, 1, QTableWidgetItem(f"{target_val:.1f}"))
            self.summary_table.setItem(i, 2, QTableWidgetItem(f"{actual_val:.1f}"))
            self.summary_table.setItem(i, 3, QTableWidgetItem(f"{diff:.1f}"))
            self.summary_table.setItem(i, 4, QTableWidgetItem(f"{diff_percent:.1f}%"))
        
        # Wyświetlenie wykresów
        self.canvas.fig.clear()
        
        # Wykres kołowy składników
        ax1 = self.canvas.fig.add_subplot(221)
        amounts = meal_composition['amount'].values
        labels = [f"{name}\n({amount:.1f} {unit})" 
                 for name, amount, unit in zip(meal_composition['ingredient'], 
                                              amounts, 
                                              meal_composition['unit'])]
        ax1.pie(amounts, labels=labels, autopct='%1.1f%%')
        ax1.set_title('Skład posiłku (proporcje ilościowe)')
        
        # Wykres kołowy kalorii
        ax2 = self.canvas.fig.add_subplot(222)
        calories = meal_composition['calories'].values
        labels = [f"{name}\n({cal:.1f} kcal)" 
                 for name, cal in zip(meal_composition['ingredient'], calories)]
        ax2.pie(calories, labels=labels, autopct='%1.1f%%')
        ax2.set_title('Rozkład kalorii')
        
        # Wykres porównania celu i rzeczywistych wartości
        ax3 = self.canvas.fig.add_subplot(212)
        x = np.arange(len(categories))
        width = 0.35
        
        ax3.bar(x - width/2, target_values, width, label='Cel')
        ax3.bar(x + width/2, actual_values, width, label='Uzyskane')
        
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.set_title('Porównanie celu i uzyskanych wartości')
        ax3.legend()
        
        # Dodanie wartości liczbowych nad słupkami
        for i, v in enumerate(target_values):
            ax3.text(i - width/2, v + 0.1, f"{v:.1f}", ha='center')
        
        for i, v in enumerate(actual_values):
            ax3.text(i + width/2, v + 0.1, f"{v:.1f}", ha='center')
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MealOptimizerApp()
    window.show()
    sys.exit(app.exec_())
