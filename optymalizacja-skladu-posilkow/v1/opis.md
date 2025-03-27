# Optymalizacja skladnikow
## optymalizacja.Przy przygotowywaniu posilkow zliczam kalorie i wszyskie makroelementy skladnikow. Czhcialby miec program ktory odobierze odpowiednia ilosc poszczegolnych skladnikow, w zalezonsci ile calosc ma miec kalori, tluczu, weglowodanow itp. Zaproponuj mi jakis algortym? czy da sie roziwzac taki problem?


To jest klasyczny problem optymalizacji, który można rozwiązać różnymi metodami programowania matematycznego. Najlepszym podejściem byłoby użycie programowania liniowego lub kwadratowego.

Oto jak można sformułować problem i rozwiązać go w Pythonie:

Zaproponowałem rozwiązanie tego problemu z użyciem dwóch podejść optymalizacyjnych:

1. **Programowanie liniowe** - używając funkcji `linprog` z biblioteki SciPy, która minimalizuje funkcję liniową przy zadanych ograniczeniach.

2. **Programowanie kwadratowe** - używając funkcji `minimize` z biblioteki SciPy, która minimalizuje sumę kwadratów odchyleń od celów (daje bardziej zrównoważone wyniki).

Program pozwala na:
- Utrzymanie bazy danych składników z ich wartościami odżywczymi
- Dodawanie własnych składników
- Określenie docelowych makroskładników (kalorie, białko, tłuszcz, węglowodany)
- Wybór konkretnych składników do posiłku
- Ustawienie minimalnych i maksymalnych ilości składników
- Wizualizację wyników (wykresy kołowe, porównanie z celami)

To rozwiązanie jest elastyczne - możesz dostosować ograniczenia i dodać więcej parametrów, np. mikroskładniki (witaminy, minerały), koszt składników czy preferencje smakowe.

Aby używać tego programu, potrzebujesz Pythona z bibliotekami numpy, pandas, scipy i matplotlib. Możesz też rozszerzyć go o interfejs graficzny używając np. biblioteki Tkinter lub stworzyć wersję webową używając Flask lub Streamlit.


## wyjasnij mi ten program prosze... jak dziala? jakie sa dane wejsciowe? jak zmieniac i dodawac skladnkiki? jaka jest funkcja celu? wszystko co powinienem wiedziec :)

Chętnie wyjaśnię, jak działa ten program do optymalizacji składu posiłków:

## Ogólny zarys działania

Program `MealOptimizer` służy do automatycznego doboru proporcji składników w posiłku tak, aby osiągnąć określone cele makroskładnikowe (kalorie, białko, tłuszcz, węglowodany). Używa technik optymalizacji matematycznej, aby znaleźć najlepsze rozwiązanie spełniające podane wymagania.

## Dane wejściowe

Główne dane wejściowe to:

1. **Baza danych składników** - każdy składnik ma następujące parametry:
   - Nazwa (np. "Kurczak pierś")
   - Kalorie (na jednostkę)
   - Zawartość białka (na jednostkę)
   - Zawartość tłuszczu (na jednostkę)
   - Zawartość węglowodanów (na jednostkę)
   - Jednostka (np. "100g", "sztuka")

2. **Docelowe wartości makroskładników**:
   - Kalorie (np. 700 kcal)
   - Białko (np. 40g)
   - Tłuszcz (np. 25g)
   - Węglowodany (np. 60g)

3. **Opcjonalne ograniczenia**:
   - Lista wybranych składników (jeśli chcesz ograniczyć wybór)
   - Minimalne ilości niektórych składników
   - Maksymalne ilości niektórych składników

## Jak dodawać i modyfikować składniki

1. **Dodawanie nowego składnika**:
   ```python
   optimizer = MealOptimizer()
   optimizer.add_ingredient('Banany', 89, 1.1, 0.3, 22.8, 'sztuka (100g)')
   ```
   Parametry to kolejno: nazwa, kalorie, białko, tłuszcz, węglowodany, jednostka.

2. **Modyfikacja istniejącej bazy danych**:
   Możesz zmodyfikować bezpośrednio ramkę danych `ingredients_db`:
   ```python
   # Zmiana wartości dla istniejącego składnika
   optimizer.ingredients_db.loc[optimizer.ingredients_db['name'] == 'Kurczak pierś', 'protein'] = 30
   
   # Usunięcie składnika
   optimizer.ingredients_db = optimizer.ingredients_db[optimizer.ingredients_db['name'] != 'Tofu']
   ```

## Funkcja celu

Program oferuje dwie metody optymalizacji z różnymi funkcjami celu:

1. **Programowanie liniowe** (`optimize_meal_linprog`):
   - Funkcja celu: minimalizacja całkowitej kaloryczności (co pośrednio faworyzuje składniki o najlepszym stosunku makroskładników do kalorii)
   - Ograniczenia: zakresy dla makroskładników (±5% dla kalorii, ±10% dla innych)
   
2. **Programowanie kwadratowe** (`optimize_meal_quadratic`):
   - Funkcja celu: minimalizacja sumy kwadratów znormalizowanych odchyleń od celów:
     ```
     ((kalorie - cel_kalorie)/cel_kalorie)² + 
     ((białko - cel_białko)/cel_białko)² + 
     ((tłuszcz - cel_tłuszcz)/cel_tłuszcz)² + 
     ((węglowodany - cel_węglowodany)/cel_węglowodany)²
     ```
   - Ta metoda daje bardziej zrównoważone wyniki, zwłaszcza gdy cele są trudne do osiągnięcia jednocześnie

## Jak korzystać z programu

Typowy przepływ pracy:

1. **Inicjalizacja optymalizatora**:
   ```python
   optimizer = MealOptimizer()
   ```

2. **Dodanie własnych składników** (opcjonalne):
   ```python
   optimizer.add_ingredient('Komosa ryżowa', 120, 4.4, 1.9, 21.3, '100g')
   ```

3. **Określenie celów makroskładnikowych**:
   ```python
   target_calories = 700
   target_protein = 40
   target_fat = 25
   target_carbs = 60
   ```

4. **Wybór konkretnych składników** (opcjonalne):
   ```python
   selected_ingredients = ['Kurczak pierś', 'Ryż biały', 'Brokuły', 'Oliwa z oliwek', 'Banany']
   ```

5. **Ustawienie minimalnych i maksymalnych ilości** (opcjonalne):
   ```python
   min_amounts = {'Kurczak pierś': 0.1, 'Brokuły': 0.5}  # min. 10g kurczaka, 50g brokułów
   max_amounts = {'Oliwa z oliwek': 0.2}  # max. 20ml oliwy
   ```

6. **Uruchomienie optymalizacji**:
   ```python
   result = optimizer.optimize_meal_quadratic(
       target_calories, target_protein, target_fat, target_carbs,
       selected_ingredients, min_amounts, max_amounts
   )
   ```

7. **Wizualizacja wyników**:
   ```python
   if result['success']:
       optimizer.visualize_results(result)
   ```

## Co warto wiedzieć dodatkowo

1. **Ograniczenia**:
   - Program pozwala na elastyczne określenie zakresu tolerancji dla celów (domyślnie ±5% dla kalorii i ±10% dla makroskładników)
   - Możesz zmodyfikować te zakresy w kodzie funkcji optymalizacyjnych

2. **Interpretacja wyników**:
   - `meal_composition` zawiera dokładny skład posiłku (ilości składników i ich wkład w makroskładniki)
   - `total` zawiera sumaryczne wartości makroskładników uzyskanego posiłku
   - Wizualizacja pokazuje porównanie celów z uzyskanymi wartościami oraz rozkład składników

3. **Wybór metody**:
   - Metoda liniowa jest szybsza, ale może dawać mniej zrównoważone wyniki
   - Metoda kwadratowa lepiej zrównoważy odchylenia od celów, ale może być wolniejsza

4. **Rozszerzenia**:
   - Możesz dodać więcej ograniczeń, np. mikroskładniki, koszt, indeks glikemiczny
   - Możesz zmodyfikować funkcję celu, np. aby minimalizować koszt lub maksymalizować zawartość konkretnych składników odżywczych

5. **Możliwe problemy**:
   - Jeśli cele są sprzeczne lub nieosiągalne z dostępnymi składnikami, program może nie znaleźć rozwiązania
   - W takim przypadku warto poluzować ograniczenia lub dodać więcej składników

Ten program stanowi dobry punkt wyjścia do dalszego rozwijania bardziej zaawansowanego narzędzia do planowania posiłków.
