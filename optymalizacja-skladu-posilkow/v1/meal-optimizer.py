import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize
import matplotlib.pyplot as plt

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
if __name__ == "__main__":
    optimizer = MealOptimizer()
    
    # Dodanie własnych składników (opcjonalne)
    optimizer.add_ingredient('Banany', 89, 1.1, 0.3, 22.8, 'sztuka (100g)')
    
    # Określenie celów makroskładników
    target_calories = 700
    target_protein = 40
    target_fat = 25
    target_carbs = 60
    
    # Wybranie konkretnych składników (opcjonalne)
    selected_ingredients = ['Kurczak pierś', 'Ryż biały', 'Brokuły', 'Oliwa z oliwek', 'Banany']
    
    # Ustawienie minimalnych i maksymalnych ilości (opcjonalne)
    min_amounts = {'Kurczak pierś': 0.1, 'Brokuły': 0.5}
    max_amounts = {'Oliwa z oliwek': 0.2}
    
    # Optymalizacja metodą programowania liniowego
    result_linprog = optimizer.optimize_meal_linprog(
        target_calories, target_protein, target_fat, target_carbs,
        selected_ingredients, min_amounts, max_amounts
    )
    
    # Wizualizacja wyników
    if result_linprog['success']:
        print("Wyniki optymalizacji (programowanie liniowe):")
        optimizer.visualize_results(result_linprog)
    
    # Alternatywnie, optymalizacja metodą programowania kwadratowego
    result_quadratic = optimizer.optimize_meal_quadratic(
        target_calories, target_protein, target_fat, target_carbs,
        selected_ingredients, min_amounts, max_amounts
    )
    
    if result_quadratic['success']:
        print("\nWyniki optymalizacji (programowanie kwadratowe):")
        optimizer.visualize_results(result_quadratic)
